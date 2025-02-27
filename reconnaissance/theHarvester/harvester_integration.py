import logging
from typing import Dict, Tuple, Optional, List
import json
from datetime import datetime
import os

from .commnd_run import CommandRunner
from .up_date_to_db import HarvesterDBUpdater
from .url_generator import create_url_generator
from .output_parser import create_output_parser

class HarvesterIntegration:
    """theHarvester 整合類
    
    整合並協調以下組件：
    1. CommandRunner: 執行命令
    2. OutputParser: 解析輸出
    3. URLGenerator: 生成URL
    4. DBUpdater: 更新數據庫
    """
    
    def __init__(self):
        self._setup_logger()
        self.command_runner = CommandRunner()
        self.output_parser = create_output_parser()
        self.url_generator = create_url_generator()
        self.db_updater = HarvesterDBUpdater()
        
        # 設置可用的搜索源
        self.available_sources = [
            'bing',         # 必應搜索
            'duckduckgo',   # DuckDuckGo 搜索
            'urlscan',      # URL 掃描
            'yahoo',        # 雅虎搜索
            'baidu',        # 百度搜索
            'crtsh',        # 證書透明度
            'dnsdumpster',  # DNS信息
            'hackertarget', # 基礎設施信息
            'otx',          # 威脅情報
            'rapiddns',     # DNS記錄
            'sublist3r',    # 子域名
            'threatcrowd',  # 威脅情報
        ]
        
    def _setup_logger(self):
        """設置日誌記錄器"""
        self.logger = logging.getLogger('HarvesterIntegration')
        self.logger.setLevel(logging.INFO)
        
        # 創建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 添加文件處理器
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'harvester.log'),
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
    def run_scan(self, 
                domain: str, 
                target_id: int,
                sources: str = 'all',
                limit: Optional[int] = None,
                save_output: bool = True) -> Tuple[bool, Dict]:
        """運行完整的掃描流程
        
        Args:
            domain: 目標域名
            target_id: 目標ID
            sources: 搜索源（'all' 或逗號分隔的列表）
            limit: 結果數量限制
            save_output: 是否保存輸出到文件
            
        Returns:
            tuple: (成功標誌, 結果字典)
        """
        try:
            self.logger.info(f"開始對 {domain} 進行掃描")
            
            # 1. 準備搜索源
            source_list = self._prepare_sources(sources)
            self.logger.info(f"使用搜索源: {', '.join(source_list)}")
            
            # 2. 執行命令獲取輸出
            outputs = self.command_runner.run_multiple_sources(domain, source_list)
            if not outputs:
                raise Exception("命令執行未返回任何結果")
            
            # 3. 解析每個輸出
            all_results = []
            for i, output in enumerate(outputs, 1):
                self.logger.info(f"解析第 {i}/{len(outputs)} 個輸出")
                result = self.output_parser.parse_output(output)
                if result:
                    all_results.append(result)
                    
            # 4. 合併結果
            merged_result = self._merge_results(all_results)
            if not merged_result:
                raise Exception("未能合併結果")
                
            # 5. 生成額外的URL
            self.logger.info("生成額外的URL")
            enriched_result = self.url_generator.generate_urls_from_results(merged_result)
            
            # 6. 更新數據庫
            self.logger.info(f"更新目標 {target_id} 的數據庫記錄")
            self.db_updater.update_db_result(target_id, enriched_result)
            
            # 7. 保存輸出（如果需要）
            if save_output:
                self._save_results(domain, enriched_result)
            
            self.logger.info("掃描完成")
            return True, enriched_result
            
        except Exception as e:
            error_msg = f"掃描過程出錯: {str(e)}"
            self.logger.error(error_msg)
            self.db_updater.update_db_result(target_id, None, error_msg)
            return False, {"error": error_msg}
            
    def _prepare_sources(self, sources: str) -> List[str]:
        """準備搜索源列表
        
        Args:
            sources: 'all' 或逗號分隔的搜索源列表
            
        Returns:
            list: 搜索源列表
        """
        if sources.lower() == 'all':
            return self.available_sources
        return [s.strip() for s in sources.split(',') if s.strip() in self.available_sources]
        
    def _merge_results(self, results: List[Dict]) -> Dict:
        """合併多個結果
        
        Args:
            results: 結果列表
            
        Returns:
            dict: 合併後的結果
        """
        if not results:
            return self._create_empty_result()
            
        merged = {
            'urls': set(),
            'hosts': set(),
            'emails': set(),
            'ips': set(),
            'asns': set(),
            'linkedin': set(),
            'dns_records': set(),
            'ip_ranges': set(),
            'reverse_dns': set()
        }
        
        # 合併所有結果
        for result in results:
            for key in merged:
                if key in result:
                    # 確保添加的是列表中的每個元素
                    if isinstance(result[key], list):
                        merged[key].update(result[key])
                    elif isinstance(result[key], set):
                        merged[key].update(result[key])
                    elif isinstance(result[key], str):
                        merged[key].add(result[key])
                        
        # 轉換為排序後的列表
        return {k: sorted(list(v)) for k, v in merged.items()}
        
    def _create_empty_result(self) -> Dict:
        """創建空結果字典"""
        return {
            'urls': [],
            'hosts': [],
            'emails': [],
            'ips': [],
            'asns': [],
            'linkedin': [],
            'dns_records': [],
            'ip_ranges': [],
            'reverse_dns': []
        }
        
    def _save_results(self, domain: str, result: Dict):
        """保存結果到文件
        
        Args:
            domain: 目標域名
            result: 掃描結果
        """
        try:
            # 創建輸出目錄
            output_dir = os.path.join('output', 'harvester')
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(
                output_dir,
                f'harvester_{domain}_{timestamp}.json'
            )
            
            # 保存JSON格式的結果
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"結果已保存到: {filename}")
            
            # 同時保存文本格式
            txt_filename = filename.replace('.json', '.txt')
            self.output_parser.save_to_file(result, txt_filename)
            
        except Exception as e:
            self.logger.error(f"保存結果時出錯: {str(e)}")

    def save_results(self, target_id: int, scan_id: int, results: Dict):
        """保存掃描結果到數據庫和文件"""
        try:
            # 更新數據庫記錄
            self.logger.info(f"更新目標 {target_id} 的數據庫記錄")
            
            # 準備JSON輸出目錄
            output_dir = os.path.join('output', 'harvester')
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成輸出文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            domain = results.get('domain', 'unknown')
            json_filename = f'harvester_{domain}_{timestamp}.json'
            txt_filename = f'harvester_{domain}_{timestamp}.txt'
            
            json_path = os.path.join(output_dir, json_filename)
            txt_path = os.path.join(output_dir, txt_filename)
            
            # 保存JSON格式結果
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)
            self.logger.info(f"結果已保存到: {json_path}")
            
            # 保存文本格式結果
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"=== theHarvester 掃描結果 ===\n")
                f.write(f"目標域名: {domain}\n")
                f.write(f"掃描時間: {timestamp}\n\n")
                
                # 寫入主機信息
                if results.get('hosts'):
                    f.write("發現的主機名:\n")
                    for host in results['hosts']:
                        f.write(f"- {host}\n")
                    f.write("\n")
                
                # 寫入郵件地址
                if results.get('emails'):
                    f.write("發現的郵件地址:\n")
                    for email in results['emails']:
                        f.write(f"- {email}\n")
                    f.write("\n")
                
                # 寫入IP地址
                if results.get('ips'):
                    f.write("發現的IP地址:\n")
                    for ip in results['ips']:
                        f.write(f"- {ip}\n")
                    f.write("\n")
                
                # 寫入URL
                if results.get('urls'):
                    f.write("發現的URL:\n")
                    for url in results['urls']:
                        f.write(f"- {url}\n")
                    f.write("\n")
                
                # 寫入ASN信息
                if results.get('asns'):
                    f.write("發現的ASN:\n")
                    for asn in results['asns']:
                        f.write(f"- {asn}\n")
                    f.write("\n")
                
            self.logger.info(f"結果已保存到文件: {txt_path}")
            
            return json_path, txt_path
            
        except Exception as e:
            self.logger.error(f"保存結果時出錯: {str(e)}")
            return None, None

def create_harvester_integration() -> HarvesterIntegration:
    """創建 HarvesterIntegration 實例"""
    return HarvesterIntegration()

if __name__ == '__main__':
    # 設置日誌級別
    logging.basicConfig(level=logging.INFO)
    
    # 測試代碼
    integration = create_harvester_integration()
    test_domain = 'example.com'
    
    print(f"\n[*] 測試目標: {test_domain}")
    print("="*50)
    
    # 創建 Flask 應用上下文
    from app import create_app
    app = create_app()
    with app.app_context():
        success, result = integration.run_scan(
            domain=test_domain,
            target_id=1,
            sources='bing,baidu',
            save_output=True
        )
        
        if success:
            print("\n[*] 掃描結果:")
            print("="*50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("\n[!] 掃描失敗:")
            print(result['error']) 