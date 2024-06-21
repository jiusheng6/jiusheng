import os
import time
import logging
import geoip2.database
import ping3
import pycountry
import concurrent.futures
from operator import itemgetter
from flask import Flask, jsonify, request
from threading import Thread

# 设置日志配置
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ProxyManager:
    def __init__(self, update_interval=300):  # 默认更新间隔5分钟
        self.proxies = {
            'http': [],
            'socks4': [],
            'socks5': []
        }
        self.update_interval = update_interval
        self.last_update_time = 0
        self.country_code_to_name = {country.alpha_2: country.name for country in pycountry.countries}  # 国家代码到国家名称的映射

        # 加载GeoIP数据库
        geoip_path = os.path.join('output', 'GeoLite2-City.mmdb')
        logging.debug(f"Trying to load GeoIP database from: {geoip_path}")
        try:
            self.geoip_reader = geoip2.database.Reader(geoip_path)
            logging.info("GeoIP database loaded successfully")
        except FileNotFoundError:
            logging.error(f"GeoIP database not found at {geoip_path}")
            self.geoip_reader = None

    def get_country_name(self, country_code_or_name):
        # 尝试将输入解释为国家代码
        country_name = self.country_code_to_name.get(country_code_or_name.upper(), None)
        if country_name:
            return country_name
        # 如果不是有效的国家代码，假设它是一个国家名称
        return country_code_or_name

    def load_proxies(self):
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            logging.debug("Skipping update, not enough time has passed since last update")
            return

        proxy_files = {
            'http': 'output/valid_http_proxies.txt',
            'socks4': 'output/valid_socks4_proxies.txt',
            'socks5': 'output/valid_socks5_proxies.txt'
        }

        new_proxies = {
            'http': [],
            'socks4': [],
            'socks5': []
        }

        for proxy_type, file_path in proxy_files.items():
            try:
                with open(file_path, 'r') as file:
                    proxies = file.read().splitlines()
                    logging.info(f"Loaded {len(proxies)} {proxy_type} proxies from {file_path}")
                    new_proxies[proxy_type] = self.process_proxies(proxies, proxy_type)
            except FileNotFoundError:
                logging.error(f"Proxy file not found: {file_path}")

        self.proxies = new_proxies
        self.last_update_time = current_time
        logging.info("Proxy list updated successfully")

    def process_proxies(self, proxies, proxy_type):
        processed_proxies = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_proxy = {executor.submit(self.process_single_proxy, proxy, proxy_type): proxy for proxy in proxies}
            for future in concurrent.futures.as_completed(future_to_proxy):
                try:
                    processed_proxy = future.result()
                    if processed_proxy:
                        processed_proxies.append(processed_proxy)
                        logging.debug(f"Processed proxy: {processed_proxy}")
                except Exception as e:
                    logging.error(f"Error processing proxy: {str(e)}")

        logging.info(f"Processed {len(processed_proxies)} {proxy_type} proxies")
        return sorted(processed_proxies, key=itemgetter('latency'))

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
        self.load_proxies()  # 确保数据是最新的
        country_name = self.get_country_name(country)  # 获取正确的国家名称
        if proxy_type:
            return [proxy for proxy in self.proxies[proxy_type] if proxy['country'].lower() == country_name.lower()]
        else:
            return [proxy for proxy_list in self.proxies.values() for proxy in proxy_list if proxy['country'].lower() == country_name.lower()]

    def update_loop(self):
        while True:
            self.load_proxies()
            time.sleep(self.update_interval)


# 初始化Flask应用
app = Flask(__name__)

# 创建ProxyManager实例
proxy_manager = ProxyManager(update_interval=300)  # 每5分钟更新一次


@app.route('/proxies', methods=['GET'])
def get_proxies():
    country = request.args.get('country')
    proxy_type = request.args.get('type')

    proxy_manager.load_proxies()  # 确保代理数据是最新的

    if country:
        proxies = proxy_manager.get_proxies_by_country(country, proxy_type)
    elif proxy_type:
        proxies = proxy_manager.proxies.get(proxy_type, [])
    else:
        proxies = [proxy for proxy_list in proxy_manager.proxies.values() for proxy in proxy_list]

    logging.info(f"Returning {len(proxies)} proxies")
    return jsonify(proxies)


if __name__ == '__main__':
    # 在单独的线程中启动更新循环
    update_thread = Thread(target=proxy_manager.update_loop, daemon=True)
    update_thread.start()

    app.run(debug=True, port=8000)
