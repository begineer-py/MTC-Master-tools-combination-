import logging
import json
import os
import subprocess
from .commnd_run import CommandRunner
from .up_date_to_db import HarvesterDBUpdater
from .url_generator import create_url_generator
from .output_parser import create_output_parser

class HarvesterScanner:
    """theHarvester 掃描器"""
    
    def __init__(self):
        self._setup_logger()
        self.command_runner = CommandRunner()
        self.db_updater = HarvesterDBUpdater()
        self.url_generator = create_url_generator()
        self.output_parser = create_output_parser()
        # 讀取常見路徑列表
        self.common_paths = self._load_common_paths()
        # 只保留擅長 URL 發現的搜索源
        self.available_sources = [
            'bing',         # 必應搜索（最好的 URL 來源之一）
            'duckduckgo',   # DuckDuckGo 搜索
            'urlscan',      # URL 掃描專用
            'yahoo',        # 雅虎搜索
            'baidu'         # 百度搜索
        ]
        
    def _setup_logger(self):
        """設置日志記錄器"""
        self.logger = logging.getLogger('HarvesterScanner')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def _load_common_paths(self):
        """從文件加載常見路徑列表"""
        try:
            path_file = os.path.join(os.path.dirname(__file__), 'common_path.txt')
            with open(path_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.logger.error(f"加載常見路徑文件失敗: {str(e)}")
            # 返回一個基本的路徑列表作為備份
            return ['', 'api', 'docs', 'admin']
    
    def run_harvester(self, domain, target_id, limit=None, sources='all'):
        """運行 theHarvester 掃描
        
        Args:
            domain: 目標域名
            target_id: 目標ID
            limit: 結果限制數
            sources: 數據源（逗號分隔的字符串或'all'）
            
        Returns:
            tuple: (success, result)
        """
        try:
            self.logger.info(f"開始掃描目標: {domain}")
            
            # 確定要使用的搜索源
            if sources == 'all':
                source_list = self.available_sources
            else:
                source_list = [s.strip() for s in sources.split(',')]
            
            # 運行掃描
            outputs = []
            for source in source_list:
                try:
                    # 使用 cp950 編碼來處理中文 Windows 系統
                    cmd = [
                        'python',
                        '-u',  # 使用無緩衝輸出
                        'theHarvester.py',
                        '-d', domain,
                        '-b', source,
                        '-f', f'json_output_{source}.json'
                    ]
                    if limit:
                        cmd.extend(['-l', str(limit)])
                    
                    self.logger.info(f"執行命令: {' '.join(cmd)}")
                    
                    process = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding='cp950',
                        errors='replace',
                        check=False
                    )
                    
                    # 檢查命令執行狀態
                    if process.returncode != 0:
                        self.logger.error(f"源 {source} 執行失敗: {process.stderr}")
                        continue
                    
                    # 讀取輸出文件
                    output_file = f'json_output_{source}.json'
                    if os.path.exists(output_file):
                        with open(output_file, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            if file_content.strip():
                                outputs.append(file_content)
                        os.remove(output_file)  # 清理臨時文件
                    
                    # 處理標準輸出
                    if process.stdout.strip():
                        outputs.append(process.stdout)
                    
                except Exception as e:
                    self.logger.error(f"處理源 {source} 時出錯: {str(e)}")
                    continue
            
            # 解析結果
            all_results = []
            for output in outputs:
                if output.strip():  # 只處理非空輸出
                    result = self.output_parser.parse_output(output)
                    if result:
                        all_results.append(result)
            
            if not all_results:
                self.logger.warning("未找到任何結果")
                return False, {}
            
            # 合併所有結果
            final_result = {
                'hosts': set(),
                'emails': set(),
                'ips': set(),
                'urls': set(),
                'asns': set()
            }
            
            for result in all_results:
                for key in final_result:
                    if key in result:
                        final_result[key].update(result[key])
            
            # 轉換為列表並排序
            final_result = {k: sorted(list(v)) for k, v in final_result.items()}
            
            return True, final_result
            
        except Exception as e:
            self.logger.error(f"掃描過程出錯: {str(e)}")
            return False, {}

if __name__ == '__main__':
    # 設置日誌級別為 DEBUG
    logging.basicConfig(level=logging.DEBUG)
    
    # 測試代碼
    scanner = HarvesterScanner()
    test_domain = 'hackerone.com'  # 使用具體的測試域名
    print(f"\n[*] 開始掃描目標: {test_domain}")
    print("="*50)
    
    # 創建 Flask 應用上下文
    from app import create_app
    app = create_app()
    with app.app_context():
        success, result = scanner.run_harvester(
            domain=test_domain,
            target_id=1,
            limit=100,
            sources='bing,baidu'  # 使用兩個搜索源進行測試
        )
        
        print("\n[*] 掃描結果:")
        print("="*50)
        print(json.dumps(result, indent=2, ensure_ascii=False)) 