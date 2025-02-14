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
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Initialize colorama for colored output
init(autoreset=True)

# Logging configuration
logging.basicConfig(
    filename="xss_tester.log",
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
 __   __ _____ _____ _____  _                       
 \ \ / // ____/ ____|  __ \(_)                      
  \ V /| (___| (___ | |__) |_ _ __  _ __   ___ _ __ 
   > <  \___ \\___ \|  _  /| | '_ \| '_ \ / _ \ '__|
  / . \ ____) |___) | | \ \| | |_) | |_) |  __/ |   
 /_/ \_\_____/_____/|_|  \_\_| .__/| .__/ \___|_|   
                             | |   | |              
                             |_|   |_|              
 
    """
    print(Fore.MAGENTA + banner)

# Initial Loading Sequence
def initial_loading():
    print_banner()
    print(Fore.YELLOW + "Automated XSS Tester")
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

# Function to read XSS payloads from file
def load_xss_payloads():
    try:
        with open("XSSPayloads.txt", "r") as file:
            return [line.strip() for line in file if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print(Fore.RED + "Error: 'XSSPayloads.txt' not found. Please add your payloads and try again.")
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

# Extracting input parameters from forms and URLs on the page
async def extract_input_parameters(page_content, base_url):
    soup = BeautifulSoup(page_content, "html.parser")
    form_inputs = []

    # Find all form elements
    for form in soup.find_all("form"):
        for input_tag in form.find_all("input"):
            input_name = input_tag.get("name")
            input_type = input_tag.get("type", "text")
            if input_name and input_type != "hidden":
                form_inputs.append((input_name, input_type))
    
    # Check URL parameters
    parsed_url = urlparse(base_url)
    url_params = parsed_url.query
    if url_params:
        for param in url_params.split("&"):
            name, _ = param.split("=", 1) if "=" in param else (param, "")

            if name:
                form_inputs.append((name, "url"))

    return form_inputs

# Inject XSS payloads into URL parameters or form fields
async def inject_payloads_async(url, payloads, user_agents, form_inputs):
    results = []
    for name, _ in form_inputs:
        for payload in payloads:
            injected_url = f"{url}&{name}={payload}"
            original_content, original_status = await download_page_async(url, user_agents)
            injected_content, injected_status = await download_page_async(injected_url, user_agents)

            if injected_content and (payload in injected_content):
                logging.info(f"XSS detected in URL: {injected_url}")
                results.append((url, injected_url, injected_content))

    return results

# Crawling function to discover pages and parameters
async def crawl_and_find_parameters(url, user_agents, payloads):
    pages_to_crawl = [url]
    visited_pages = set()
    results = []

    while pages_to_crawl:
        current_url = pages_to_crawl.pop()
        if current_url in visited_pages or len(visited_pages) > 100000:
            continue
        visited_pages.add(current_url)

        logging.info(Fore.CYAN + f"Crawling: {current_url}")

        page_content, status_code = await download_page_async(current_url, user_agents)
        if page_content:
            form_inputs = await extract_input_parameters(page_content, current_url)
            page_results = await inject_payloads_async(current_url, payloads, user_agents, form_inputs)
            results.extend(page_results)

            # Extract links to crawl deeper
            soup = BeautifulSoup(page_content, "html.parser")
            for link in soup.find_all("a", href=True):
                link_url = urljoin(current_url, link["href"])
                if link_url not in visited_pages:
                    pages_to_crawl.append(link_url)

    return results

# Process all URLs asynchronously
async def process_urls_async(urls, payloads, user_agents):
    tasks = [crawl_and_find_parameters(url, user_agents, payloads) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

# Main function with asyncio
async def main_async():
    setup_temp_directory()
    urls = initial_loading()
    if not urls:
        return

    payloads = load_xss_payloads()
    if not payloads:
        print(Fore.RED + "Error: No payloads loaded. Please check XSSPayloads.txt.")
        return

    user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"]
    results = await process_urls_async(urls, payloads, user_agents)

    for result in results:
        if result:
            for original_url, injected_url, response in result:
                async with aio_open("success.txt", "a") as success_log:
                    await success_log.write(f"XSS DETECTED!\n")
                    await success_log.write(f"Original URL: {original_url}\n")
                    await success_log.write(f"Injected URL: {injected_url}\n")
                    await success_log.write(f"Response:\n{response}\n\n")

if __name__ == "__main__":
    asyncio.run(main_async())
