import os
import logging
import threading
import time
from datetime import datetime
from queue import Queue
from flask import Flask, jsonify, request
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import geoip2.database
import ping3
import pycountry
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# 设置日志配置
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

class ProxyManager:
    def __init__(self, max_workers=20):
        self.proxies = defaultdict(list)
        self.proxy_sets = defaultdict(set)
        self.country_code_to_name = {country.alpha_2: country.name for country in pycountry.countries}
        self.geoip_reader = self.load_geoip_database()
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queue = Queue()
        self.latency_cache = {}
        self.latency_cache_time = {}

    def load_geoip_database(self):
        geoip_path = os.path.join('output', 'GeoLite2-City.mmdb')
        logging.debug(f"Trying to load GeoIP database from: {geoip_path}")
        try:
            return geoip2.database.Reader(geoip_path)
        except FileNotFoundError:
            logging.error(f"GeoIP database not found at {geoip_path}")
            return None

    def load_proxies_async(self, proxy_files):
        for proxy_type, file_path in proxy_files.items():
            self.load_proxies_from_file(proxy_type, file_path)

    def load_proxies_from_file(self, proxy_type, file_path):
        try:
            with self.lock:
                # 清空该类型的代理列表和集合
                self.proxies[proxy_type] = []
                self.proxy_sets[proxy_type] = set()

            with open(file_path, 'r') as file:
                for line in file:
                    proxy = line.strip()
                    if proxy:
                        self.queue.put((proxy, proxy_type))
            logging.info(f"Loaded proxies from file: {file_path}")
        except FileNotFoundError:
            logging.error(f"Proxy file not found: {file_path}")

        # 启动处理线程
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        while True:
            try:
                proxy, proxy_type = self.queue.get(timeout=1)
                future = self.executor.submit(self.process_single_proxy, proxy, proxy_type)
                future.add_done_callback(self.add_proxy_callback)
            except Queue.Empty:
                time.sleep(1)  # 如果队列为空，等待一秒再次检查

    def process_single_proxy(self, proxy, proxy_type):
        try:
            ip, port = proxy.split(':')
            country = "Unknown"
            city = "Unknown"
            if self.geoip_reader:
                try:
                    geo_data = self.geoip_reader.city(ip)
                    country = geo_data.country.name or "Unknown"
                    city = geo_data.city.name or "Unknown"
                except geoip2.errors.AddressNotFoundError:
                    logging.warning(f"IP address not found in GeoIP database: {ip}")
            latency = self.measure_latency(ip)
            
            if latency == float('inf'):
                logging.info(f"Proxy {ip}:{port} is invalid (high latency)")
                return None
            
            return {
                'ip': ip,
                'port': port,
                'type': proxy_type,
                'country': country,
                'city': city,
                'latency': latency,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error processing proxy {proxy}: {str(e)}")
            return None

    def add_proxy_callback(self, future):
        try:
            result = future.result()
            if result is not None and 'type' in result:
                proxy_key = f"{result['ip']}:{result['port']}"
                with self.lock:
                    if proxy_key not in self.proxy_sets[result['type']]:
                        self.proxies[result['type']].append(result)
                        self.proxy_sets[result['type']].add(proxy_key)
                        logging.info(f"Added proxy: {proxy_key} ({result['type']}) - Last check: {result['last_check']}")
                    else:
                        logging.debug(f"Proxy already exists: {proxy_key} ({result['type']})")
            else:
                logging.warning(f"Invalid result from process_single_proxy: {result}")
        except Exception as e:
            logging.error(f"Error in add_proxy_callback: {str(e)}")
        finally:
            logging.debug(f"Current proxy count: {sum(len(proxies) for proxies in self.proxies.values())}")

    def measure_latency(self, ip):
        current_time = time.time()
        if ip in self.latency_cache and current_time - self.latency_cache_time.get(ip, 0) < 300:
            return self.latency_cache[ip]
        
        try:
            result = ping3.ping(ip, timeout=2)
            latency = result * 1000 if result is not None else float('inf')
            self.latency_cache[ip] = latency
            self.latency_cache_time[ip] = current_time
            return latency
        except Exception as e:
            logging.warning(f"Failed to measure latency for {ip}: {str(e)}")
            return float('inf')

    def get_proxies_by_country(self, country, proxy_type=None):
        country_name = self.get_country_name(country).lower()
        with self.lock:
            if proxy_type:
                return [proxy for proxy in self.proxies.get(proxy_type, [])
                        if proxy.get('country', '').lower() == country_name]
            else:
                return [proxy for proxy_list in self.proxies.values()
                        for proxy in proxy_list
                        if proxy.get('country', '').lower() == country_name]

    def get_country_name(self, country_code_or_name):
        if not country_code_or_name:
            return "Unknown"
        country_name = self.country_code_to_name.get(country_code_or_name.upper())
        return country_name if country_name else country_code_or_name

    def get_available_countries(self):
        country_counts = defaultdict(lambda: defaultdict(int))
        with self.lock:
            for proxy_type, proxy_list in self.proxies.items():
                for proxy in proxy_list:
                    country = proxy.get('country')
                    if country and country != "Unknown":
                        country_counts[country][proxy_type] += 1
        
        country_data = []
        for country_name, counts in country_counts.items():
            country_code = next((code for code, name in self.country_code_to_name.items() if name == country_name), None)
            if country_code:
                country_data.append({
                    "name": country_name,
                    "code": country_code,
                    "counts": dict(counts),
                    "total": sum(counts.values())
                })
        
        return sorted(country_data, key=lambda x: x['total'], reverse=True)

    def get_stats(self):
        with self.lock:
            stats = {
                "total_proxies": sum(len(proxies) for proxies in self.proxies.values()),
                "proxies_by_type": {proxy_type: len(proxies) for proxy_type, proxies in self.proxies.items()},
                "proxies_by_country": defaultdict(lambda: defaultdict(int))
            }
            
            for proxy_type, proxies in self.proxies.items():
                for proxy in proxies:
                    country = proxy.get('country', 'Unknown')
                    stats["proxies_by_country"][country][proxy_type] += 1
            
            # Convert defaultdict to regular dict for JSON serialization
            stats["proxies_by_country"] = dict(stats["proxies_by_country"])
            for country in stats["proxies_by_country"]:
                stats["proxies_by_country"][country] = dict(stats["proxies_by_country"][country])
            
            return stats

    def is_proxy_valid(self, proxy):
        # 检查上次验证时间是否超过1小时
        last_check = datetime.fromisoformat(proxy['last_check'])
        if (datetime.now() - last_check).total_seconds() < 3600:  # 3600秒 = 1小时
            return proxy['latency'] != float('inf')  # 即使在1小时内，如果延迟是Infinity也视为无效
        
        # 如果超过1小时，重新验证
        latency = self.measure_latency(proxy['ip'])
        if latency == float('inf'):
            return False
        
        # 更新代理信息
        proxy['latency'] = latency
        proxy['last_check'] = datetime.now().isoformat()
        return True

    def remove_invalid_proxies(self):
        removed_count = 0
        with self.lock:
            for proxy_type in list(self.proxies.keys()):  # 使用列表复制键，因为我们可能会在循环中修改字典
                valid_proxies = []
                for proxy in self.proxies[proxy_type]:
                    if self.is_proxy_valid(proxy):
                        valid_proxies.append(proxy)
                    else:
                        removed_count += 1
                        self.proxy_sets[proxy_type].remove(f"{proxy['ip']}:{proxy['port']}")
                        logging.info(f"Removed invalid proxy: {proxy['ip']}:{proxy['port']} ({proxy_type})")
                self.proxies[proxy_type] = valid_proxies
        logging.info(f"Removed {removed_count} invalid proxies")

    def start_periodic_cleanup(self, interval=3600):
        def cleanup():
            while True:
                time.sleep(interval)
                self.remove_invalid_proxies()

        threading.Thread(target=cleanup, daemon=True).start()

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, proxy_manager):
        self.proxy_manager = proxy_manager

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            logging.info(f"Detected change in {event.src_path}")
            proxy_type = os.path.basename(event.src_path).split('_')[1].split('.')[0]  # Extract proxy type from filename
            proxy_files = {proxy_type: event.src_path}
            self.proxy_manager.load_proxies_async(proxy_files)
            # 强制立即进行一次清理
            self.proxy_manager.remove_invalid_proxies()

def start_watch(proxy_manager):
    path = 'output'
    event_handler = FileChangeHandler(proxy_manager)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        stop_event = threading.Event()
        stop_event.wait()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@app.route('/proxies', methods=['GET'])
def get_proxies():
    country = request.args.get('country')
    proxy_type = request.args.get('type')
    if not country:
        return jsonify({"error": "Country parameter is required"}), 400
    if proxy_type and proxy_type not in proxy_manager.proxies:
        return jsonify({"error": f"Invalid proxy type: {proxy_type}"}), 400
    
    proxies = proxy_manager.get_proxies_by_country(country, proxy_type)
    # 在返回之前过滤掉无效代理
    valid_proxies = [proxy for proxy in proxies if proxy_manager.is_proxy_valid(proxy)]
    logging.info(f"Returning {len(valid_proxies)} valid proxies for country: {country}, type: {proxy_type}")
    return jsonify(valid_proxies)

@app.route('/countries', methods=['GET'])
def get_countries():
    countries = proxy_manager.get_available_countries()
    logging.info(f"Returning data for {len(countries)} countries")
    return jsonify(countries)

@app.route('/stats', methods=['GET'])
def get_stats():
    stats = proxy_manager.get_stats()
    logging.info(f"Returning stats: total proxies = {stats['total_proxies']}")
    return jsonify(stats)

if __name__ == '__main__':
    proxy_manager = ProxyManager()
    proxy_manager.start_periodic_cleanup()
    watch_thread = threading.Thread(target=start_watch, args=(proxy_manager,), daemon=True)
    watch_thread.start()
    app.run(debug=False, host='0.0.0.0', port=8000)
