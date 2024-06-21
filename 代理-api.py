import os
import logging
import threading
from queue import Queue
from flask import Flask, jsonify, request
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import geoip2.database
import ping3
import pycountry
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置日志配置
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

class ProxyManager:
    def __init__(self, max_workers=20):
        self.proxies = {
            'http': [],
            'socks4': [],
            'socks5': []
        }
        self.country_code_to_name = {country.alpha_2: country.name for country in pycountry.countries}
        self.geoip_reader = self.load_geoip_database()
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queue = Queue()

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
            with open(file_path, 'r') as file:
                proxies = file.read().splitlines()
                for proxy in proxies:
                    self.queue.put((proxy, proxy_type))
        except FileNotFoundError:
            logging.error(f"Proxy file not found: {file_path}")

        # 启动处理线程
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        while True:
            proxy, proxy_type = self.queue.get()
            future = self.executor.submit(self.process_single_proxy, proxy, proxy_type)
            future.add_done_callback(self.add_proxy_callback)

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

    def add_proxy_callback(self, future):
        result = future.result()
        if result:
            with self.lock:
                self.proxies[result['type']].append(result)
            logging.info(f"Added proxy: {result['ip']}:{result['port']} ({result['type']})")

    def measure_latency(self, ip):
        try:
            result = ping3.ping(ip, timeout=2)
            return result * 1000 if result is not None else float('inf')
        except Exception as e:
            logging.warning(f"Failed to measure latency for {ip}: {str(e)}")
            return float('inf')

    def get_proxies_by_country(self, country, proxy_type=None):
        with self.lock:
            country_name = self.get_country_name(country)
            filtered_proxies = [proxy for proxy in self.proxies[proxy_type] if proxy['country'].lower() == country_name.lower()] if proxy_type else [proxy for proxy_list in self.proxies.values() for proxy in proxy_list if proxy['country'].lower() == country_name.lower()]
            return filtered_proxies

    def get_country_name(self, country_code_or_name):
        if not country_code_or_name:
            return "Unknown"
        country_name = self.country_code_to_name.get(country_code_or_name.upper(), None)
        return country_name if country_name else country_code_or_name

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, proxy_manager):
        self.proxy_manager = proxy_manager

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            logging.info(f"Detected change in {event.src_path}")
            proxy_type = os.path.basename(event.src_path).split('_')[1]
            proxy_files = {proxy_type: event.src_path}
            self.proxy_manager.load_proxies_async(proxy_files)

def start_watch(proxy_manager):
    path = 'output'
    event_handler = FileChangeHandler(proxy_manager)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    observer.join()

@app.route('/proxies', methods=['GET'])
def get_proxies():
    country = request.args.get('country')
    proxy_type = request.args.get('type')
    if not country:
        return jsonify({"error": "Country parameter is required"}), 400
    proxies = proxy_manager.get_proxies_by_country(country, proxy_type)
    return jsonify(proxies)

if __name__ == '__main__':
    proxy_manager = ProxyManager()
    threading.Thread(target=start_watch, args=(proxy_manager,), daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=8000)
