import aiohttp
import asyncio
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init
from urllib.parse import urlparse

# Initialize colorama for color output
init(autoreset=True)

# 為 Windows 設置事件循環策略
if os.name == 'nt':  # Windows 系統
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ASCII Art and Introduction
def print_intro():
    if os.name == 'nt':
        os.system('cls')  # Clear screen for Windows
    else:
        os.system('clear')  # Clear screen for Unix-based systems
    print(Fore.BLUE + r"""


  _____                      _____             _             
 |  __ \                    |  __ \           | |            
 | |__) |___  ___ ___  _ __ | |__) |__ _ _ __ | |_ ___  _ __ 
 |  _  // _ \/ __/ _ \| '_ \|  _  // _` | '_ \| __/ _ \| '__|
 | | \ \  __/ (_| (_) | | | | | \ \ (_| | |_) | || (_) | |   
 |_|  \_\___|\___\___/|_| |_|_|  \_\__,_| .__/ \__\___/|_|   
                                        | |                  
                                        |_|                  

  
""")
    time.sleep(0.5)
    print(Fore.MAGENTA + "Developed by: Dr. Aubrey W. Love II (AKA Rogue Payload)")
    time.sleep(0.5)
    print(Fore.GREEN + "ReconRaptor: Advanced payload injector and domain reconnaissance tool.")
    time.sleep(0.5)

# File paths for our data
DOMAINS_FILE = "domains.txt"
PAYLOADS_FILE = "payloads.txt"
USERAGENTS_FILE = "useragents.txt"
RESULTS_FILE = "hacked.txt"

max_retries = 3  # Adjust this to your preference

def load_file(filename):
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print(Fore.RED + f"[ERROR] File not found: {filename}")
        return []

# Rotate user agents for each request
def get_random_user_agent(user_agents):
    return random.choice(user_agents)

async def fetch_url(session, url, payload, user_agent):
    headers = {"User-Agent": user_agent}
    try:
        async with session.get(url, headers=headers, timeout=10, ssl=False) as response:
            if response.status == 200:
                text = await response.text()
                return text
            else:
                print(Fore.YELLOW + f"[INFO] Status code {response.status} for {url}")
    except Exception as e:
        print(Fore.RED + f"[ERROR] {url} - {e}")
    return None

async def test_payloads(domain, payloads, user_agents):
    # 解析域名和端口，以及可能的路徑
    if ':' in domain:
        host_port, *path_parts = domain.split('/', 1)
        host, port = host_port.rsplit(':', 1)
        base_path = path_parts[0] if path_parts else ''
        protocol = 'http' if port == '80' else 'https'
    else:
        host = domain
        protocol = 'https'  # 默認使用 https
        port = '443'
        base_path = ''
    
    # 創建一個禁用 SSL 驗證的 session
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for payload in payloads:
            # 構造正確的 URL，包含基礎路徑
            if base_path:
                url = f"{protocol}://{host}:{port}/{base_path}/{payload}"
            else:
                url = f"{protocol}://{host}:{port}/{payload}"
            
            # 清理 URL 中的多餘斜杠
            url = url.replace('//', '/').replace(':/', '://')
            user_agent = get_random_user_agent(user_agents)

            print(Fore.YELLOW + f"[INFO] Testing payload: {payload} on {domain}")
            try:
                before_content = await fetch_url(session, url, "", user_agent)
                if not before_content:
                    continue

                # 構造注入 URL
                if base_path:
                    injected_url = f"{protocol}://{host}:{port}/{base_path}/{payload}"
                else:
                    injected_url = f"{protocol}://{host}:{port}/{payload}"
                injected_url = injected_url.replace('//', '/').replace(':/', '://')
                
                after_content = await fetch_url(session, injected_url, payload, user_agent)

                if after_content and before_content != after_content:
                    print(Fore.GREEN + f"[SUCCESS] Potential vulnerability found on {url} with payload {payload}")
                    with open(RESULTS_FILE, "a") as result_file:
                        result_file.write(f"URL: {url}\nPayload: {payload}\n--- Before ---\n{before_content[:500]}\n--- After ---\n{after_content[:500]}\n{'-'*50}\n")

            except Exception as e:
                print(Fore.RED + f"[ERROR] Failed to test {url}: {str(e)}")
                continue

async def main():
    print_intro()

    domains = load_file(DOMAINS_FILE)
    payloads = load_file(PAYLOADS_FILE)
    user_agents = load_file(USERAGENTS_FILE)

    print(Fore.GREEN + f"Locked onto {len(domains)} Domains!")

    with ThreadPoolExecutor() as executor:
        futures = []
        for domain in domains:
            futures.append(asyncio.ensure_future(test_payloads(domain, payloads, user_agents)))

        await asyncio.gather(*futures)

    print(Fore.GREEN + "[COMPLETED] All domains and payloads tested.")

if __name__ == "__main__":
    asyncio.run(main())
