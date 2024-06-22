import requests
import re
import logging
import concurrent.futures
from requests.exceptions import ProxyError
import socket
import socks
import schedule
import time
from contextlib import contextmanager
# 强制 requests 库使用 IPv4
requests.packages.urllib3.util.connection.HAS_IPV6 = False

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# HTTP代理源
http_sources = [
    "https://api.openproxylist.xyz/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
    "https://github.com/ProxyScraper/ProxyScraper/raw/main/http.txt",
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=ipport&format=text&timeout=20000",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=https",
    "https://openproxy.space/list/http",
    "https://proxyspace.pro/http.txt",
    "https://proxyspace.pro/https.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
    "https://raw.githubusercontent.com/andigwandi/free-proxy/main/proxy_list.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt",
    "https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/http/global/http_checked.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
    "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
    "https://raw.githubusercontent.com/im-razvan/proxy_list/main/http.txt",
    "https://raw.githubusercontent.com/Master-Mind-007/Auto-Parse-Proxy/main/https.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/MrMarble/proxy-list/main/all.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    "https://raw.githubusercontent.com/NotUnko/autoproxies/main/proxies/https",
    "https://raw.githubusercontent.com/ObcbO/getproxy/master/file/http.txt",
    "https://raw.githubusercontent.com/ObcbO/getproxy/master/file/https.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Https.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/Sage520/Proxy-List/main/http.txt",
    "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/free.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/http_proxies.txt",
    "https://raw.githubusercontent.com/themiralay/Proxy-List-World/master/data.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/http.txt",
    "https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/https.txt",
    "https://raw.githubusercontent.com/tuanminpay/live-proxy/master/http.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=https",
]

# SOCKS4代理源
socks4_sources = [
    "https://api.openproxylist.xyz/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks4.txt",
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=socks4&proxy_format=ipport&format=text&timeout=20000",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
    "https://openproxy.space/list/socks4",
    "https://proxyspace.pro/socks4.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks4_proxies.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks4/global/socks4_checked.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/Master-Mind-007/Auto-Parse-Proxy/main/socks4.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",
    "https://raw.githubusercontent.com/NotUnko/autoproxies/main/proxies/socks4",
    "https://raw.githubusercontent.com/ObcbO/getproxy/master/file/socks4.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks4/socks4.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks4.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/Sage520/Proxy-List/main/socks4.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/socks4_proxies.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/socks4.txt",
    "https://raw.githubusercontent.com/tuanminpay/live-proxy/master/socks4.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
]

# SOCKS5代理源
socks5_sources = [
    "https://api.openproxylist.xyz/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt",
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=socks5&proxy_format=ipport&format=text&timeout=20000",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
    "https://openproxy.space/list/socks5",
    "https://proxyspace.pro/socks5.txt",
    "https://raw.githubusercontent.com/AGDDoS/AGProxy/master/proxies/socks5.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks5_proxies.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks5/global/socks5_checked.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/im-razvan/proxy_list/main/socks5.txt",
    "https://raw.githubusercontent.com/Master-Mind-007/Auto-Parse-Proxy/main/socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
    "https://raw.githubusercontent.com/NotUnko/autoproxies/main/proxies/socks5",
    "https://raw.githubusercontent.com/ObcbO/getproxy/master/file/socks5.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks5/socks5.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/Sage520/Proxy-List/main/socks5.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/socks5_proxies.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/socks5.txt",
    "https://raw.githubusercontent.com/tuanminpay/live-proxy/master/socks5.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
]

# 匹配代理IP和端口的正则表达式
proxy_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+:\d+)')

# 从网页获取代理列表
def fetch_proxies(url):
    try:
        # 使用空代理字典进行请求，确保直接使用本地网络连接
        response = requests.get(url, proxies={}, timeout=10)
        proxies = proxy_pattern.findall(response.text)
        return proxies
    except requests.RequestException as e:
        logging.error(f"Error fetching proxies from {url}: {e}")
        return []

# 检测HTTP代理
def check_http_proxy(proxy):
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    }
    try:
        response = requests.get('http://www.example.com', proxies=proxies, timeout=2)
        if response.status_code == 200:
            logging.info(f"HTTP proxy {proxy} is working.")
            return proxy
    except (requests.RequestException, ProxyError):
        logging.info(f"HTTP proxy {proxy} failed.")
    return None

@contextmanager
def socks_proxy(proxy, socks_type):
    ip, port = proxy.split(':')
    default_socket = socket.socket
    socks.set_default_proxy(socks_type, ip, int(port))
    socket.socket = socks.socksocket
    try:
        yield
    finally:
        socket.socket = default_socket

# 检测SOCKS4代理
def check_socks4_proxy(proxy):
    try:
        ip, port = proxy.split(':')
        port = int(port)
        if not 0 <= port <= 65535:
            logging.info(f"SOCKS4 proxy {proxy} has an invalid port.")
            return None
    except ValueError:
        logging.info(f"SOCKS4 proxy {proxy} has an invalid format.")
        return None

    with socks_proxy(proxy, socks.SOCKS4):
        try:
            response = requests.get('http://www.example.com', timeout=2)
            if response.status_code == 200:
                logging.info(f"SOCKS4 proxy {proxy} is working.")
                return proxy
        except (requests.RequestException, ProxyError, socks.ProxyError):
            logging.info(f"SOCKS4 proxy {proxy} failed.")
    return None

# 检测SOCKS5代理
def check_socks5_proxy(proxy):
    try:
        ip, port = proxy.split(':')
        port = int(port)
        if not 0 <= port <= 65535:
            logging.info(f"SOCKS5 proxy {proxy} has an invalid port.")
            return None
    except ValueError:
        logging.info(f"SOCKS5 proxy {proxy} has an invalid format.")
        return None

    with socks_proxy(proxy, socks.SOCKS5):
        try:
            response = requests.get('http://www.example.com', timeout=2)
            if response.status_code == 200:
                logging.info(f"SOCKS5 proxy {proxy} is working.")
                return proxy
        except (requests.RequestException, ProxyError, socks.ProxyError):
            logging.info(f"SOCKS5 proxy {proxy} failed.")
    return None

# 多线程检测代理
def check_proxies(proxies, check_function):
    checked_proxies = set()
    working_proxies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
        future_to_proxy = {executor.submit(check_function, proxy): proxy for proxy in proxies if proxy not in checked_proxies}
        for future in concurrent.futures.as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            checked_proxies.add(proxy)
            if future.result():
                working_proxies.append(proxy)
    return working_proxies

def run_proxy_check():
    http_proxies = []
    socks4_proxies = []
    socks5_proxies = []

    for source in http_sources:
        http_proxies.extend(fetch_proxies(source))
    for source in socks4_sources:
        socks4_proxies.extend(fetch_proxies(source))
    for source in socks5_sources:
        socks5_proxies.extend(fetch_proxies(source))

    http_working_proxies = check_proxies(http_proxies, check_http_proxy)
    socks4_working_proxies = check_proxies(socks4_proxies, check_socks4_proxy)
    socks5_working_proxies = check_proxies(socks5_proxies, check_socks5_proxy)

    logging.info(f"Working HTTP proxies: {http_working_proxies}")
    logging.info(f"Working SOCKS4 proxies: {socks4_working_proxies}")
    logging.info(f"Working SOCKS5 proxies: {socks5_working_proxies}")

    # 保存有效的HTTP代理到文件
    with open("output/valid_http_proxies.txt", "w") as file:
        file.write("\n".join(http_working_proxies))
        logging.info(f"已将 {len(http_working_proxies)} 个有效的 HTTP 代理保存到 valid_http_proxies.txt 文件中")

    # 保存有效的SOCKS4代理到文件
    with open("output/valid_socks4_proxies.txt", "w") as file:
        file.write("\n".join(socks4_working_proxies))
        logging.info(f"已将 {len(socks4_working_proxies)} 个有效的 SOCKS4 代理保存到 valid_socks4_proxies.txt 文件中")

    # 保存有效的SOCKS5代理到文件
    with open("output/valid_socks5_proxies.txt", "w") as file:
        file.write("\n".join(socks5_working_proxies))
        logging.info(f"已将 {len(socks5_working_proxies)} 个有效的 SOCKS5 代理保存到 valid_socks5_proxies.txt 文件中")

    # 合并所有有效的代理并保存到总文件
    all_valid_proxies = http_working_proxies + socks4_working_proxies + socks5_working_proxies
    with open("output/all_valid_proxies.txt", "w") as file:
        file.write("\n".join(all_valid_proxies))
        logging.info(f"已将所有的 {len(all_valid_proxies)} 个有效代理保存到 all_valid_proxies.txt 文件中")

    logging.info("代理检测和保存完成。")

if __name__ == "__main__":
    # 初次运行代理检测任务
    run_proxy_check()

    # 设置每60分钟运行一次代理检测任务
    schedule.every(60).minutes.do(run_proxy_check)

    # 持续运行定时任务
    while True:
        schedule.run_pending()
        time.sleep(1)
