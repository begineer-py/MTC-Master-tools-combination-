import os
import sys
import time
import subprocess
import json
import signal
import threading
import queue
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class HarvesterTestThread(threading.Thread):
    """theHarvester 測試線程"""
    
    def __init__(self, domain, source, harvester_path, result_queue):
        threading.Thread.__init__(self)
        self.domain = domain
        self.source = source
        self.harvester_path = harvester_path
        self.result_queue = result_queue
        self.daemon = True
    
    def run(self):
        start_time = time.time()
        try:
            cmd = [
                sys.executable,
                self.harvester_path,
                '-d', self.domain,
                '-b', self.source,
                '-n',         # DNS 查詢
                '-c',         # DNS 暴力破解
                '-t',         # 網頁爬取
                '-l', '1000'  # 增加搜索深度到 1000
            ]
            
            print(f"\n[*] 線程 {self.source} 開始執行: {' '.join(cmd)}\n")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            error_lines = []
            
            # 設置超時時間（10分鐘）
            timeout = 600
            while True:
                # 檢查是否超時
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    print(f"\n[!] 搜索源 {self.source} 掃描超時 (已運行 {int(elapsed_time)} 秒)")
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()
                    self.result_queue.put({
                        'source': self.source,
                        'success': False,
                        'error': f'掃描超時 (運行時間: {int(elapsed_time)} 秒)',
                        'duration': elapsed_time,
                        'output': output_lines,
                        'errors': error_lines
                    })
                    return
                
                # 讀取輸出
                output_line = process.stdout.readline()
                error_line = process.stderr.readline()
                
                if output_line:
                    line = output_line.rstrip()
                    print(f"[{self.source}] {line}")
                    output_lines.append(line)
                if error_line:
                    line = error_line.rstrip()
                    print(f"[{self.source}] Error: {line}", file=sys.stderr)
                    error_lines.append(line)
                
                # 檢查進程是否結束
                if process.poll() is not None:
                    remaining_out, remaining_err = process.communicate()
                    if remaining_out:
                        for line in remaining_out.splitlines():
                            print(f"[{self.source}] {line}")
                            output_lines.append(line)
                    if remaining_err:
                        for line in remaining_err.splitlines():
                            print(f"[{self.source}] Error: {line}", file=sys.stderr)
                            error_lines.append(line)
                    break
                
                time.sleep(0.1)
            
            # 保存輸出到文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(project_root, 'test', f'harvester_output_{self.domain}_{self.source}_{timestamp}.txt')
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(output_lines))
                    if error_lines:
                        f.write('\n\nErrors:\n')
                        f.write('\n'.join(error_lines))
                print(f"\n[*] 搜索源 {self.source} 輸出已保存到: {output_file}")
            except Exception as e:
                print(f"[!] 保存輸出文件時出錯: {str(e)}")
            
            # 返回結果
            self.result_queue.put({
                'source': self.source,
                'success': process.returncode == 0,
                'error': '\n'.join(error_lines) if error_lines else None,
                'duration': time.time() - start_time,
                'output': output_lines,
                'errors': error_lines
            })
            
        except Exception as e:
            print(f"[!] 搜索源 {self.source} 執行出錯: {str(e)}")
            self.result_queue.put({
                'source': self.source,
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time,
                'output': output_lines if 'output_lines' in locals() else [],
                'errors': error_lines if 'error_lines' in locals() else [str(e)]
            })

def test_harvester():
    """測試 theHarvester 掃描功能"""
    try:
        print("\n" + "="*50)
        print("開始測試 theHarvester 掃描器")
        print("="*50 + "\n")
        
        # 測試目標和搜索源
        test_domains = ['hackerone.com']
        # 只使用不需要 API 的搜索源
        test_sources = [
            'baidu',        # 百度搜索
            'bing',         # 必應搜索
            'crtsh',        # 證書透明度日誌
            'dnsdumpster',  # DNS 信息
            'duckduckgo',   # DuckDuckGo 搜索
            'google',       # 谷歌搜索
            'hackertarget', # 基本域名信息
            'otx',          # Open Threat Exchange
            'rapiddns',     # DNS 記錄
            'sublist3r',    # 子域名
            'threatcrowd',  # 威脅情報
            'urlscan',      # URL 掃描
            'yahoo'         # 雅虎搜索
        ]
        
        harvester_path = os.path.join(project_root, 'tools', 'theHarvester', 'theHarvester.py')
        if not os.path.exists(harvester_path):
            print(f"[!] 找不到 theHarvester 腳本: {harvester_path}")
            return False
        
        results = []
        for domain in test_domains:
            print(f"\n[*] 測試目標: {domain}")
            print("-"*50)
            
            # 創建結果隊列和線程列表
            result_queue = queue.Queue()
            threads = []
            
            # 創建並啟動所有線程
            for source in test_sources:
                thread = HarvesterTestThread(
                    domain=domain,
                    source=source,
                    harvester_path=harvester_path,
                    result_queue=result_queue
                )
                threads.append(thread)
                thread.start()
                time.sleep(1)  # 每個線程啟動間隔1秒
            
            # 等待所有線程完成
            for thread in threads:
                thread.join(timeout=720)  # 12分鐘超時，確保有足夠時間處理
            
            # 收集所有結果
            domain_results = []
            while not result_queue.empty():
                result = result_queue.get()
                domain_results.append(result)
            
            # 按源名稱排序結果
            domain_results.sort(key=lambda x: x['source'])
            results.extend(domain_results)
            
            # 打印結果統計
            success_count = sum(1 for r in domain_results if r['success'])
            print(f"\n[*] 目標 {domain} 測試完成:")
            print(f"- 總測試數: {len(domain_results)}")
            print(f"- 成功數量: {success_count}")
            print(f"- 失敗數量: {len(domain_results) - success_count}")
        
        # 保存測試結果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = os.path.join(project_root, 'test', f'test_results_{timestamp}.json')
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n[*] 測試結果已保存到: {result_file}")
        except Exception as e:
            print(f"[!] 保存結果文件時出錯: {str(e)}")
        
        print("\n" + "="*50)
        print("測試完成")
        print("="*50 + "\n")
        
        # 打印總結
        total_success = sum(1 for r in results if r['success'])
        print(f"總測試結果:")
        print(f"- 總測試數: {len(results)}")
        print(f"- 成功數量: {total_success}")
        print(f"- 失敗數量: {len(results) - total_success}")
        
        return True
        
    except Exception as e:
        print(f"\n[!] 測試過程出錯: {str(e)}")
        return False

if __name__ == '__main__':
    # 確保在正確的目錄中運行
    os.chdir(project_root)
    
    # 運行測試
    success = test_harvester()
    sys.exit(0 if success else 1) 