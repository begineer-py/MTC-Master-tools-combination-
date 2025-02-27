import subprocess
import sys
import os
import time
from datetime import datetime
import re
from typing import Dict, List, Set

class TheHarvesterTester:
    """theHarvester 測試類"""
    
    def __init__(self):
        self.harvester_path = os.path.join('tools', 'theHarvester', 'theHarvester.py')
        
    def _parse_output(self, output: str) -> Dict:
        """解析輸出內容
        
        Args:
            output: 命令輸出內容
            
        Returns:
            dict: 解析後的結果
        """
        result = {
            'ips': set(),
            'emails': set(),
            'hosts': set(),
            'urls': set(),
            'asns': set()
        }
        
        current_section = None
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 識別部分
            if '[*] IPs found:' in line:
                current_section = 'ips'
                continue
            elif '[*] Emails found:' in line:
                current_section = 'emails'
                continue
            elif '[*] Hosts found:' in line:
                current_section = 'hosts'
                continue
            elif '[*] URLs found:' in line or '[*] Interesting URLs found:' in line:
                current_section = 'urls'
                continue
            elif '[*] ASNs found:' in line:
                current_section = 'asns'
                continue
            elif line.startswith('--------------------'):
                continue
                
            # 處理數據
            if current_section and not line.startswith('[*]'):
                if current_section == 'hosts':
                    parts = line.split(':')
                    host = parts[0].strip()
                    if host and not host.startswith(('*', '[', '-')):
                        result['hosts'].add(host)
                        if len(parts) > 1:
                            ip = parts[1].strip()
                            if ip:
                                result['ips'].add(ip)
                elif current_section == 'emails':
                    if '@' in line:
                        result['emails'].add(line)
                elif current_section == 'ips':
                    if re.match(r'^[\d\.]+$', line):
                        result['ips'].add(line)
                elif current_section == 'urls':
                    if line.startswith(('http://', 'https://')):
                        result['urls'].add(line)
                elif current_section == 'asns':
                    result['asns'].add(line)
                    
        return {k: sorted(list(v)) for k, v in result.items()}
        
    def run_test(self, domain: str, source: str = 'all') -> Dict:
        """運行測試
        
        Args:
            domain: 目標域名
            source: 數據源（默認'all'）
            
        Returns:
            dict: 測試結果
        """
        try:
            print(f"\n{'='*50}")
            print(f"開始測試 theHarvester - 目標: {domain}")
            print(f"{'='*50}\n")
            
            # 構建命令
            cmd = [
                sys.executable,
                self.harvester_path,
                '-d', domain,
                '-l', '500',     # 減少結果數量限制
                '-n',
                '-t'
            ]
            
            # 處理搜索源
            if source != 'all':
                for s in source.split(','):
                    s = s.strip()
                    if s:  # 確保不是空字符串
                        cmd.extend(['-b', s])
            else:
                cmd.extend(['-b', 'all'])
            
            print(f"執行命令: {' '.join(cmd)}\n")
            print("[*] 預計執行時間約5-10分鐘...\n")
            
            # 運行命令，設置超時時間為10分鐘
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            error_lines = []
            start_time = time.time()
            timeout = 600  # 10分鐘超時
            
            # 實時讀取輸出
            while True:
                # 檢查是否超時
                if time.time() - start_time > timeout:
                    print("\n[!] 執行超時，強制終止進程")
                    process.kill()
                    break
                
                # 使用communicate設置超時
                try:
                    output, error = process.communicate(timeout=1)
                    if output:
                        for line in output.splitlines():
                            print(f" {line.strip()}")
                            output_lines.append(line.strip())
                    if error:
                        for line in error.splitlines():
                            print(f" {line.strip()}", file=sys.stderr)
                            error_lines.append(line.strip())
                    break
                except subprocess.TimeoutExpired:
                    continue
                except Exception as e:
                    print(f"\n[!] 讀取輸出時出錯: {str(e)}")
                    break
                
                # 檢查進程是否結束
                if process.poll() is not None:
                    break
                    
            # 解析輸出
            parsed_result = self._parse_output('\n'.join(output_lines))
            
            # 打印搜索統計
            print("\n[*] 搜索統計:")
            print(f"- 發現的主機數: {len(parsed_result['hosts'])}")
            print(f"- 發現的IP數: {len(parsed_result['ips'])}")
            print(f"- 發現的郵箱數: {len(parsed_result['emails'])}")
            print(f"- 發現的URL數: {len(parsed_result['urls'])}")
            print(f"- 發現的ASN數: {len(parsed_result['asns'])}")
            print(f"- 執行時間: {int(time.time() - start_time)} 秒")
            
            return {
                'success': process.returncode == 0 if process.returncode is not None else False,
                'parsed_result': parsed_result,
                'error': '\n'.join(error_lines) if error_lines else None
            }
                
        except Exception as e:
            print(f"\n執行測試時出錯: {str(e)}")
            return {
                'success': False,
                'parsed_result': None,
                'error': str(e)
            }
            
def main(mode='source'):
    """主函數
    Args:
        mode: 'all' 使用所有搜索源, 'source' 使用source.txt中的源
    """
    tester = TheHarvesterTester()
    target_domain = 'hackerone.com'
    
    if mode == 'all':
        # 直接使用all模式
        print("\n[*] 使用所有可用搜索源")
        result = tester.run_test(target_domain, 'all')
        
        # 打印結果
        if result['parsed_result']:
            for key, values in result['parsed_result'].items():
                if values:
                    print(f"\n[+] {key}: {len(values)} 個")
                    for value in values:
                        print(f"  - {value}")
                        
        if result['error']:
            print(f"\n[!] 錯誤: {result['error']}")
            
    else:  # mode == 'source'
        # 從source.txt讀取搜索源
        try:
            with open(os.path.join(os.path.dirname(__file__), "source.txt"), 'r', encoding='utf-8') as f:
                sources = [line.strip() for line in f if line.strip()]
                sources_str = ','.join(sources)
                print(f"\n[*] 使用source.txt中的搜索源: {sources_str}")
                result = tester.run_test(target_domain, sources_str)
                
                # 打印結果
                if result['parsed_result']:
                    for key, values in result['parsed_result'].items():
                        if values:
                            print(f"\n[+] {key}: {len(values)} 個")
                            for value in values:
                                print(f"  - {value}")
                                
                if result['error']:
                    print(f"\n[!] 錯誤: {result['error']}")
                    
        except Exception as e:
            print(f"\n[!] 讀取source.txt失敗: {str(e)}")

if __name__ == '__main__':
    # 使用 'all' 或 'source' 作為參數
    main('all')  # 或 main('source')
                
