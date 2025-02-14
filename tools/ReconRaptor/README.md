# 🦖 ReconRaptor

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Version](https://img.shields.io/badge/Version-1.0-orange)
![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen)

**ReconRaptor** is a high-performance, asynchronous vulnerability reconnaissance tool. It is designed for thorough, rapid testing of multiple domains and subdomains, using advanced payload injection, Tor integration, and proxy/user-agent rotation. ReconRaptor is optimized for **multi-threaded and asynchronous** operations to enable fast and efficient testing while minimizing resource use and maintaining stealth.

---

## 📜 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Detailed Workflow](#detailed-workflow)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

## ✨ Features

- **Asynchronous Operations**: Leveraging `aiohttp` and `asyncio` to handle concurrent requests efficiently.
- **Proxy & User-Agent Rotation**: Avoids detection and bypasses rate limits by cycling through user agents and proxies.
- **Tor Integration**: Integrates Tor for IP masking and anonymity, with auto IP renewal to avoid blocks.
- **Content Comparison**: Injects payloads and verifies vulnerabilities by comparing page contents before and after injections.
- **Modular Payload and Proxy System**: Customize payloads and proxy lists to adapt to different targets and scopes.
- **Comprehensive Logging**: All confirmed vulnerabilities are logged to `hacked.txt` with before-and-after content snapshots.

---

## 🚀 Installation

To install ReconRaptor, ensure you have Python 3.8+ and follow these steps:

```bash
# Clone the repository
git clone https://github.com/YourUsername/ReconRaptor.git
cd ReconRaptor

# Install dependencies
pip install -r requirements.txt
```

**Note:** _Tor must be installed and running on your system. To install Tor:_
```bash
    # Ubuntu/Debian: 
    sudo apt install tor
    # MacOS: 
    brew install tor
```

## 🔧 Configuration

ReconRaptor is configured with four main input files:

* domains.txt: List of domains or subdomains to scan.
* payloads.txt: Payloads to inject into each domain and subdomain.
* useragents.txt: List of user-agent strings for rotation to avoid detection.
* proxies.txt: List of proxies (optional) to route requests through.

### Folder Structure
```bash
ReconRaptor/
├── ReconRaptor.py         # Main script
├── domains.txt            # Target domains/subdomains
├── payloads.txt           # Payloads for injection
├── proxies.txt            # Proxy list (optional)
└── useragents.txt         # User-Agent list
```

## ⚙️ Usage

Run ReconRaptor with the following command:

```bash
python3 ReconRaptor.py
```
### Command-line Arguments (optional)
* `-d` or `--domains`: Specify a `custom domains.txt` file.
* `-p` or `--payloads`: Specify a `custom payloads.txt` file.
* `-u` or `--useragents`: Specify a `custom useragents.txt` file.
* `-x` or `--proxies`: Specify a custom `proxies.txt` file.

***Example:***
```bash
python3 ReconRaptor.py -d my_domains.txt -p my_payloads.txt
```
- **Output:** Results will be saved in `hacked.txt` with URLs, payloads, and page content changes, if any vulnerabilities are confirmed.

## 🕹️ Detailed Workflow

ReconRaptor operates in the following stages:
- **Tor Initialization:** Checks if Tor is running. If not, attempts to start it. Tor IP renewal occurs periodically.
- **Proxy Verification:** Proxies are tested for connectivity before each request to ensure they are live.
- **Sequential Payload Injection:** For each domain, all payloads are injected in sequence.
- **Page Content Comparison:** Captures the page content before and after payload injection to detect changes.
- **Logging:** Logs successful injections, saving confirmed vulnerabilities in hacked.txt.

## 🔥 Examples

Here are a few usage examples for specific scenarios.
### Basic Usage
Run the script with default files:
```bash
python3 ReconRaptor.py
```
### Custom Input Files
Specify a custom domains list and payloads file:
```bash
python3 ReconRaptor.py -d custom_domains.txt -p custom_payloads.txt
```
### Using Specific Proxies
Load a specific proxy list and user-agent file:
```bash
python3 ReconRaptor.py -x premium_proxies.txt -u custom_useragents.txt
```

## 📄 Sample domains.txt, payloads.txt, and useragents.txt
### domains.txt
```plaintext
www.example.com
api.example.com
test.example.com
```
### payloads.txt
```plaintext
../../../../etc/passwd
../../../../etc/hosts
/config.php
/admin
```
### useragents.txt
```plaintext
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
```

## 🛠️ Troubleshooting

If you encounter issues while setting up or running ReconRaptor, here are some steps to resolve them.

### Activating the ReconRaptor Conda Environment
Ensure you have created and activated the `ReconRaptor` environment with the necessary dependencies:

```bash
# Activate the environment (assuming you've set it up with `conda create -n ReconRaptor python=3.10`)
conda activate ReconRaptor
```
_This ensures all required packages and dependencies are properly isolated within the environment._


### Configuring Tor with Correct torrc Settings

For ReconRaptor to use Tor’s control port, certain settings must be enabled in the torrc file:
- Locate and Edit torrc: The Tor configuration file (torrc) is usually located at /etc/tor/torrc on Linux systems.
```bash
sudo nano /etc/tor/torrc
```
Modify torrc for ControlPort and Authentication: Add the following lines to enable the ControlPort and disable CookieAuthentication:
```plaintext
ControlPort 9051
CookieAuthentication 0
```
Alternatively, if you want to secure the control port with a password, generate a hashed password and use it here:
```bash
tor --hash-password "your_password"
```
Then add this to torrc:
```plaintext
ControlPort 9051
HashedControlPassword <hashed_password_output>
```
Restart Tor to Apply Changes: After modifying torrc, restart the Tor service:
```bash
sudo systemctl restart tor
```
Verify Tor Setup: Confirm Tor is running and listening on the correct port by checking:
```bash
netstat -tuln | grep 9051
```
Following these steps ensures that ReconRaptor has the necessary permissions to connect to Tor’s control port and can rotate IPs as expected during scanning.


## 🤝 Contributing
Contributions are welcome! Feel free to fork the repository and submit a pull request. Please ensure that your code is well-documented and tested.

* Fork the repo and create your branch: `git checkout -b feature/YourFeature`
* Commit changes: `git commit -m 'Add YourFeature'`
* Push to branch: `git push origin feature/YourFeature`
* Open a pull request!


## 💬 Contact
Questions or suggestions? Reach out via GitHub Issues or contact me at roguepayload@globalbughunters.com.

- ***Warning:*** **ReconRaptor** is a powerful tool designed for ethical hacking and authorized security testing only. Unauthorized use on systems you do not own or have permission to test may violate laws and regulations.