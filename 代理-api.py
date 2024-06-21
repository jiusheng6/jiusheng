import os
import time
import logging
import geoip2.database
import ping3
import pycountry
import concurrent.futures
from operator import itemgetter
from flask import Flask, jsonify, request
import threading
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 设置日志配置
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

class ProxyManager:
    def __init__(self):
        self.proxies = {
            'http': [],
            'socks4': [],
            'socks5': []
        }
        self.country_code_to_name = {country.alpha_2: country.name for country in pycountry.countries}
        self.geoip_reader = self.load_geoip_database()
        self.lock = threading.Lock()  # 使用threading模块的Lock

    def load_geoip_database(self):
        geoip_path = os.path.join('output', 'GeoLite2-City.mmdb')
        logging.debug(f"Trying to load GeoIP database from: {geoip_path}")
        try:
            return geoip2.database.Reader(geoip_path)
        except FileNotFoundError:
            logging.error(f"GeoIP database not found at {geoip_path}")
            return None

    def load_proxies_async(self, proxy_files):
        with self.lock:
            self.proxies = {'http': [], 'socks4': [], 'socks5': []}  # 清空旧代理列表
        with concurrent.futures.ThreadPoolExecutor(max_workers=2000) as executor:
            futures = {executor.submit(self.load_proxies_from_file, proxy_type, file_path): proxy_type for proxy_type, file_path in proxy_files.items()}
            for future in concurrent.futures.as_completed(futures):
                proxy_type = futures[future]
                new_proxies = future.result()
                with self.lock:
                    self.proxies[proxy_type].extend(new_proxies)
                logging.info(f"Loaded and processed {len(new_proxies)} {proxy_type} proxies")

    def load_proxies_from_file(self, proxy_type, file_path):
        try:
            with open(file_path, 'r') as file:
                proxies = file.read().splitlines()
                logging.info(f"Loaded {len(proxies)} {proxy_type} proxies from {file_path}")
                return self.process_proxies(proxies, proxy_type)
        except FileNotFoundError:
            logging.error(f"Proxy file not found: {file_path}")
            return []

    def process_proxies(self, proxies, proxy_type):
        processed_proxies = []
        for proxy in proxies:
            processed_proxy = self.process_single_proxy(proxy, proxy_type)
            if processed_proxy:
                processed_proxies.append(processed_proxy)
        return processed_proxies

    def process_single_proxy(self, proxy, proxy_type):
        try:
            ip, port = proxy.split(':')
            country = "Unknown"
            city = "Unknown"
            if self.geoip_reader:
                geo_data = self.geoip_reader.city(ip)
                country = geo_data.country.name
                city = geo_data.city.name
            latency = self.measure_latency(ip)
            return {
                'ip': ip,
                'port': port,
                'type': proxy_type,
                'country': country,
                'city': city,
                'latency': latency
            }
        except Exception as e:
            logging.error(f"Error processing proxy {proxy}: {str(e)}")
            return None

    def measure_latency(self, ip):
        try:
            return ping3.ping(ip, timeout=2) * 1000  # 转换为毫秒
        except Exception as e:
            logging.warning(f"Failed to measure latency for {ip}: {str(e)}")
            return float('inf')

    def get_proxies_by_country(self, country, proxy_type=None):
        with self.lock:
            country_name = self.get_country_name(country)
            if proxy_type:
                return [proxy for proxy in self.proxies[proxy_type] if proxy['country'].lower() == country_name.lower()]
            else:
                return [proxy for proxy_list in self.proxies.values() for proxy in proxy_list if proxy['country'].lower() == country_name.lower()]

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, proxy_manager):
        self.proxy_manager = proxy_manager

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt') and 'output' in event.src_path:
            logging.info(f"Detected change in {event.src_path}")
            # Assuming file names follow the format 'valid_[type]_proxies.txt'
            proxy_type = os.path.basename(event.src_path).split('_')[1]
            proxy_files = {proxy_type: event.src_path}
            self.proxy_manager.load_proxies_async(proxy_files)

def start_watch(proxy_manager):
    path = 'output'
    event_handler = FileChangeHandler(proxy_manager)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@app.route('/proxies', methods=['GET'])
def get_proxies():
    country = request.args.get('country')
    proxy_type = request.args.get('type')
    proxies = proxy_manager.get_proxies_by_country(country, proxy_type)
    return jsonify(proxies)

if __name__ == '__main__':
    proxy_manager = ProxyManager()
    Thread(target=start_watch, args=(proxy_manager,), daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=8000)
