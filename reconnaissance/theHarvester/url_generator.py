import os
import logging
from typing import Set, List, Dict, Optional

class URLGenerator:
    """URL 生成器類"""
    
    def __init__(self):
        self.logger = logging.getLogger('URLGenerator')
        self.logger.setLevel(logging.INFO)
        self.common_paths = self._load_common_paths()
        
    def _load_common_paths(self) -> List[str]:
        """從文件加載常見路徑列表"""
        try:
            path_file = os.path.join(os.path.dirname(__file__), 'common_path.txt')
            with open(path_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.logger.error(f"加載常見路徑文件失敗: {str(e)}")
            # 返回一個基本的路徑列表作為備份
            return ['', 'api', 'docs', 'admin']
            
    def generate_host_urls(self, host: str) -> Set[str]:
        """為主機生成所有可能的 URL
        
        Args:
            host: 主機名
            
        Returns:
            set: 生成的 URL 集合
        """
        urls = set()
        print(f"\n[*] 為主機 {host} 生成 URL:")
        
        # 生成基本 URL
        for protocol in ['http', 'https']:
            base_url = f"{protocol}://{host}"
            urls.add(base_url)
            print(f"[+] 生成基本 URL: {base_url}")
            
        # 生成帶路徑的 URL
        for path in self.common_paths:
            for protocol in ['http', 'https']:
                url = f"{protocol}://{host}/{path}".rstrip('/')
                urls.add(url)
                print(f"[+] 生成路徑 URL: {url}")
                
        return urls
        
    def generate_ip_urls(self, ip: str) -> Set[str]:
        """為 IP 地址生成所有可能的 URL
        
        Args:
            ip: IP 地址
            
        Returns:
            set: 生成的 URL 集合
        """
        urls = set()
        if not ip.startswith(('*', '[', '-', '2')):  # 排除 IPv6 地址
            print(f"\n[*] 為 IP {ip} 生成 URL:")
            for protocol in ['http', 'https']:
                url = f"{protocol}://{ip}"
                urls.add(url)
                print(f"[+] 生成 IP URL: {url}")
                
        return urls
        
    def generate_urls_from_results(self, scan_results: Dict) -> Dict:
        """從掃描結果生成所有可能的 URL
        
        Args:
            scan_results: 掃描結果字典
            
        Returns:
            dict: 包含生成的 URL 的結果字典
        """
        all_urls = set()
        
        # 從主機生成 URL
        if 'hosts' in scan_results:
            for host in scan_results['hosts']:
                all_urls.update(self.generate_host_urls(host))
                
        # 從 IP 生成 URL
        if 'ips' in scan_results:
            for ip in scan_results['ips']:
                all_urls.update(self.generate_ip_urls(ip))
                
        # 添加已發現的 URL
        if 'urls' in scan_results:
            all_urls.update(scan_results['urls'])
            
        # 更新結果字典
        scan_results['urls'] = sorted(list(all_urls))
        
        # 打印統計信息
        print("\n[*] URL 生成統計:")
        print(f"- 總計生成 URL: {len(all_urls)} 個")
        print("\n[*] URL 示例:")
        for url in list(all_urls)[:5]:
            print(f"- {url}")
        if len(all_urls) > 5:
            print(f"... 還有 {len(all_urls)-5} 個")
            
        return scan_results
        
    def generate_urls_for_target(self, domain: str, include_subdomains: bool = True) -> Set[str]:
        """為目標域名生成所有可能的 URL
        
        Args:
            domain: 目標域名
            include_subdomains: 是否包含子域名
            
        Returns:
            set: 生成的 URL 集合
        """
        urls = set()
        
        # 生成主域名的 URL
        urls.update(self.generate_host_urls(domain))
        
        # 生成常見子域名的 URL
        if include_subdomains:
            common_subdomains = [
                'www', 'api', 'dev', 'test', 'stage', 'staging',
                'prod', 'admin', 'portal', 'mail', 'smtp', 'pop',
                'imap', 'ftp', 'sftp', 'blog', 'docs', 'support',
                'help', 'kb', 'wiki', 'webmail', 'remote', 'vpn',
                'ns1', 'ns2', 'dns1', 'dns2', 'mx1', 'mx2'
            ]
            
            for subdomain in common_subdomains:
                full_domain = f"{subdomain}.{domain}"
                urls.update(self.generate_host_urls(full_domain))
                
        return urls

def create_url_generator() -> URLGenerator:
    """創建 URL 生成器實例"""
    return URLGenerator()

if __name__ == '__main__':
    # 設置日誌級別
    logging.basicConfig(level=logging.INFO)
    
    # 測試代碼
    generator = create_url_generator()
    test_domain = 'example.com'
    
    print(f"\n[*] 測試目標: {test_domain}")
    print("="*50)
    
    # 測試為目標生成 URL
    urls = generator.generate_urls_for_target(test_domain)
    
    print("\n[*] 生成的 URL:")
    print("="*50)
    for url in sorted(urls)[:10]:
        print(url)
    if len(urls) > 10:
        print(f"... 還有 {len(urls)-10} 個 URL") 