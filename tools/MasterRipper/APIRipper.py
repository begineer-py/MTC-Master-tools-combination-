import requests
import re
import time
import os
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Configurable Parameters
TARGET_FILE = 'Targets.txt'
SUCCESS_FILE = 'success.txt'
PAYLOADS_FILE = 'APIPayloads.txt'
MAX_DEPTH = 10
TIMEOUT = 10  # seconds for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 2  # Delay to prevent rate-limiting

# Headers for requests (without predefined API keys/tokens)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Content-Type": "application/json"
}

# Read payloads from the external file
def load_payloads():
    with open(PAYLOADS_FILE, 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

# Function to search for API keys, tokens, and other sensitive data in the response body
def extract_api_keys_and_tokens(response_text):
    api_keys = []
    token_patterns = [
        # Example patterns for different types of tokens or keys (these can be adjusted)
        r"(?i)(?:api[-_]?key\s*[:=]?\s*)[\"']?([a-fA-F0-9]{32,})[\"']?",  # Standard API key pattern
        r"(?i)(?:Bearer\s+)[\"']?([a-zA-Z0-9\-_]{20,})[\"']?",  # Bearer Token
        r"(?i)(?:access[-_]?token\s*[:=]?\s*)[\"']?([a-fA-F0-9]{32,})[\"']?",  # OAuth Token
        r"(?i)(?:Authorization\s*[:=]?\s*)[\"']?([a-zA-Z0-9\-_]{20,})[\"']?",  # General Authorization Header
        r"(?i)(?:client[-_]?secret\s*[:=]?\s*)[\"']?([a-fA-F0-9]{32,})[\"']?",  # Client Secret Key
    ]
    
    # Search for the patterns in the response text (JSON, HTML, etc.)
    for pattern in token_patterns:
        found_keys = re.findall(pattern, response_text)
        api_keys.extend(found_keys)

    return api_keys

# Function to make requests and inject any discovered API keys or tokens into headers
def make_request_with_token_injection(url, method="GET", headers=None, params=None, body=None):
    response = None
    retries = 0
    while retries < MAX_RETRIES:
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=body, timeout=TIMEOUT)

            if response.status_code == 200:
                # If the response is successful, try to extract any API keys or tokens
                api_keys = extract_api_keys_and_tokens(response.text)
                if api_keys:
                    print(f"Found API keys or tokens: {api_keys}")
                    # Here you could add the found tokens dynamically to headers for further requests
                    headers["Authorization"] = f"Bearer {api_keys[0]}"  # Example of using first found token
                break
        except requests.RequestException as e:
            print(f"Error making request to {url}: {e}")
            retries += 1
            time.sleep(1)

    return response

# Extract input parameters from a webpage using BeautifulSoup
def extract_params(url):
    response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=TIMEOUT)
    soup = BeautifulSoup(response.text, 'html.parser')
    params = []

    # Find all forms and input fields
    for form in soup.find_all('form'):
        for input_tag in form.find_all('input'):
            param_name = input_tag.get('name')
            if param_name:
                params.append(param_name)
    return params

# Test the payloads on the API parameters
def test_api(url, method, params, payloads, headers=None):
    success = []
    
    # Loop through all input parameters and test payloads
    for param in params:
        for payload in payloads:
            payload_url = f"{url}?{param}={payload}"
            try:
                response = make_request_with_token_injection(payload_url, method, headers=headers)
                if "error" in response.text.lower() or "unauthorized" in response.text.lower():
                    success.append((payload_url, payload, response.text))
            except requests.RequestException as e:
                print(f"Error testing {payload_url}: {e}")
                
    return success

# Save the successful API results into a file
def save_success(success_results):
    with open(SUCCESS_FILE, 'a') as f:
        for result in success_results:
            f.write(f"URL: {result[0]}\nPayload: {result[1]}\nResponse:\n{result[2]}\n\n{'='*50}\n")

# Crawl the site and test API on multiple pages
def crawl_and_test_api(base_url):
    # Load API payloads
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
            results = test_api(url, "GET", params, payloads, headers=HEADERS)
            if results:
                success_results.extend(results)
        
        # Parse and add any new links to the crawl queue
        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(url, href)
            if full_url not in visited:
                to_visit.append(full_url)
        
        depth += 1
        time.sleep(RATE_LIMIT_DELAY)  # Delay to prevent rate-limiting

    if success_results:
        save_success(success_results)
        print(f"API vulnerabilities found. Results saved to {SUCCESS_FILE}")
    else:
        print("No API vulnerabilities found.")

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
        print(f"Starting API scan on target: {target}")
        crawl_and_test_api(target)
        print(f"Finished API scan for {target}")

if __name__ == "__main__":
    main()
