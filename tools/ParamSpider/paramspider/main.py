import argparse
import os
import logging
import colorama
from colorama import Fore, Style
from urllib.parse import urlparse, parse_qs, urlencode
import requests
import os.path
import sys

# 添加當前目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import client

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    return logger

logger = setup_logging()

def fetch_urls(domain):
    """從多個來源獲取 URL"""
    all_urls = set()
    
    try:
        # 1. 從 Wayback Machine 獲取
        wayback_url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=txt&collapse=urlkey&fl=original&page=/"
        response = requests.get(wayback_url, timeout=30)
        if response.status_code == 200:
            urls = response.text.splitlines()
            all_urls.update(urls)
            
        # 2. 直接訪問常見的登入路徑
        common_paths = []
        try:
            # 嘗試從當前目錄讀取
            common_path_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "common_path.txt")
            if not os.path.exists(common_path_file):
                # 如果當前目錄沒有，嘗試從項目根目錄讀取
                common_path_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "tools", "ParamSpider", "paramspider", "common_path.txt")
            
            with open(common_path_file, "r", encoding='utf-8') as f:
                common_paths = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"讀取 common_path.txt 時出錯: {str(e)}")
            # 使用默認路徑列表
            common_paths = ["/login", "/admin", "/user", "/api"]
        for path in common_paths:
            test_urls = [
                f"https://{domain}{path}",
                f"http://{domain}{path}"
            ]
            
            for test_url in test_urls:
                try:
                    response = requests.head(test_url, timeout=5, allow_redirects=True)
                    if response.status_code == 200:
                        all_urls.add(test_url)
                        logger.info(f"找到有效的登入頁面: {test_url}")
                except Exception:
                    continue
                    
        # 3. 檢查相關子域名
        subdomains = [
            f"auth.{domain}",
            f"login.{domain}",
            f"account.{domain}",
            f"accounts.{domain}",
            f"id.{domain}"
        ]
        
        for subdomain in subdomains:
            try:
                test_url = f"https://{subdomain}"
                response = requests.head(test_url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    all_urls.add(test_url)
                    logger.info(f"找到有效的子域名: {test_url}")
            except Exception:
                continue
                
        return list(all_urls)
        
    except Exception as e:
        logger.error(f"獲取 URL 時出錯: {str(e)}")
        return list(all_urls)

def clean_url(url, placeholder="FUZZ"):
    """清理單個 URL"""
    try:
        url = str(url).strip()
        if not url:
            return ""
            
        parsed = urlparse(url)
        
        # 處理端口
        if (parsed.port == 80 and parsed.scheme == "http") or \
           (parsed.port == 443 and parsed.scheme == "https"):
            netloc = parsed.netloc.rsplit(":", 1)[0]
            parsed = parsed._replace(netloc=netloc)
            
        # 處理參數
        if parsed.query:
            query_params = parse_qs(parsed.query)
            cleaned_params = {key: [placeholder] for key in query_params}
            cleaned_query = urlencode(cleaned_params, doseq=True)
            parsed = parsed._replace(query=cleaned_query)
            
        return parsed.geturl()
    except Exception as e:
        logger.error(f"清理 URL 時出錯: {str(e)}")
        return ""

def clean_urls(urls, placeholder="FUZZ"):
    """清理 URL 列表"""
    cleaned_urls = set()
    for url in urls:
        try:
            cleaned_url = clean_url(url, placeholder)
            if cleaned_url:
                cleaned_urls.add(cleaned_url)
        except Exception as e:
            logger.error(f"清理 URL 列表時出錯: {str(e)}")
            continue
    return list(cleaned_urls)

def fetch_and_clean_urls(domain, placeholder="FUZZ"):
    """獲取並清理 URL"""
    try:
        logger.info(f"[INFO] 開始獲取 {domain} 的 URL")
        
        # 獲取 URL
        urls = fetch_urls(domain)
        if not urls:
            logger.warning(f"[WARNING] 未找到 {domain} 的 URL")
            return []
            
        logger.info(f"[INFO] 找到 {len(urls)} 個 URL")
        
        # 清理 URL 並排除 JavaScript 文件
        cleaned_urls = set()
        js_urls = set()
        for url in urls:
            try:
                # 檢查是否為 JavaScript 文件
                if url.lower().endswith('.js'):
                    js_urls.add(url)
                    continue
                    
                cleaned_url = clean_url(url, placeholder)
                if cleaned_url:
                    cleaned_urls.add(cleaned_url)
            except Exception as e:
                logger.error(f"清理 URL 時出錯: {str(e)}")
                continue
                
        logger.info(f"[INFO] 清理後剩餘 {len(cleaned_urls)} 個非 JS URL")
        logger.info(f"[INFO] 已排除 {len(js_urls)} 個 JS 文件")
        
        # 分類 URL
        parameterized_urls = []
        static_urls = []
        for url in cleaned_urls:
            if "?" in url:
                parameterized_urls.append(url)
            else:
                static_urls.append(url)
        
        # 輸出統計信息
        logger.info(f"\n[INFO] URL 統計:")
        logger.info(f"- 帶參數的 URL: {len(parameterized_urls)} 個")
        logger.info(f"- 靜態 URL: {len(static_urls)} 個")
        
        # 輸出 URL 路徑類型
        if cleaned_urls:
            logger.info("\n[INFO] 找到的 URL 路徑類型:")
            paths = set(urlparse(url).path for url in cleaned_urls)
            for path in paths:
                logger.info(f"- {path}")
        
        # 返回所有非 JS URL
        return list(cleaned_urls)
        
    except Exception as e:
        logger.error(f"處理 URL 時出錯: {str(e)}")
        return []

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="Mining URLs from Web Archives")
    parser.add_argument("-d", "--domain", help="Domain name to fetch URLs for")
    parser.add_argument("-l", "--list", help="File containing list of domains")
    parser.add_argument("-p", "--placeholder", help="Placeholder for parameter values", default="FUZZ")
    args = parser.parse_args()

    if not args.domain and not args.list:
        parser.error("Please provide either -d/--domain or -l/--list option")

    all_urls = []
    
    try:
        if args.domain:
            urls = fetch_and_clean_urls(args.domain, args.placeholder)
            all_urls.extend(urls)

        if args.list:
            with open(args.list, "r") as f:
                domains = [line.strip() for line in f if line.strip()]
                
            for domain in domains:
                # 移除協議前綴
                domain = domain.replace('https://', '').replace('http://', '')
                urls = fetch_and_clean_urls(domain, args.placeholder)
                all_urls.extend(urls)
        
        # 輸出結果
        logger.info(f"\n[INFO] Total unique URLs found: {len(all_urls)}")
        for url in sorted(set(all_urls)):
            print(url)
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        return []
        
    return all_urls

if __name__ == "__main__":
    main()