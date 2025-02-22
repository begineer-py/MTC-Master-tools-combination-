import os
import sys
import time
import subprocess
import json
import signal
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def run_harvester_directly(domain):
    """直接運行 theHarvester 命令"""
    harvester_path = os.path.join(project_root, 'tools', 'theHarvester', 'theHarvester.py')
    
    if not os.path.exists(harvester_path):
        print(f"[!] 找不到 theHarvester 腳本: {harvester_path}")
        return False, None
    
    cmd = [
        sys.executable,
        harvester_path,
        '-d', domain,
        '-b', 'all'  # 移除 -t 參數
    ]
    
    print(f"\n[*] 執行命令: {' '.join(cmd)}\n")
    
    try:
        # 設置 startupinfo 以隱藏控制台窗口
        startupinfo = None
        if os.name == 'nt':  # Windows系統
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # 使用subprocess直接運行命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # 設置超時時間（5分鐘）
        timeout = 300
        start_time = time.time()
        output_lines = []
        error_lines = []
        
        # 實時讀取和打印輸出
        while True:
            # 檢查是否超時
            if time.time() - start_time > timeout:
                print(f"\n[!] 掃描超時（{timeout}秒）")
                # 在Windows上使用taskkill強制結束進程
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
                else:
                    process.kill()
                return False, "掃描超時"
            
            # 非阻塞方式讀取輸出
            output_line = process.stdout.readline()
            error_line = process.stderr.readline()
            
            if output_line:
                line = output_line.rstrip()
                print(line)
                output_lines.append(line)
            if error_line:
                line = error_line.rstrip()
                print(line, file=sys.stderr)
                error_lines.append(line)
            
            # 檢查進程是否結束
            if process.poll() is not None:
                # 讀取剩餘輸出
                remaining_out, remaining_err = process.communicate()
                if remaining_out:
                    for line in remaining_out.splitlines():
                        print(line)
                        output_lines.append(line)
                if remaining_err:
                    for line in remaining_err.splitlines():
                        print(line, file=sys.stderr)
                        error_lines.append(line)
                break
            
            # 短暫休眠以減少CPU使用
            time.sleep(0.1)
        
        # 保存輸出到文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(project_root, 'test', f'harvester_output_{domain}_{timestamp}.txt')
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
                if error_lines:
                    f.write('\n\nErrors:\n')
                    f.write('\n'.join(error_lines))
            print(f"\n[*] 掃描輸出已保存到: {output_file}")
        except Exception as e:
            print(f"[!] 保存輸出文件時出錯: {str(e)}")
        
        return process.returncode == 0, None
        
    except Exception as e:
        print(f"[!] 執行命令時出錯: {str(e)}")
        return False, str(e)

def test_harvester():
    """測試 theHarvester 掃描功能"""
    try:
        print("\n" + "="*50)
        print("開始測試 theHarvester 掃描器")
        print("="*50 + "\n")
        
        # 測試目標
        test_domains = [
            'hackerone.com',
            'github.com',
            'microsoft.com'
        ]
        
        results = []
        for i, domain in enumerate(test_domains, 1):
            print(f"\n[*] 測試 {i}/{len(test_domains)}: {domain}")
            print("-"*50)
            
            try:
                # 執行掃描
                start_time = time.time()
                success, error = run_harvester_directly(domain)
                end_time = time.time()
                
                # 記錄結果
                result = {
                    'domain': domain,
                    'success': success,
                    'error': error,
                    'duration': end_time - start_time
                }
                results.append(result)
                
                # 打印結果
                print(f"\n[*] 掃描耗時: {result['duration']:.2f} 秒")
                print(f"[*] 掃描狀態: {'成功' if success else '失敗'}")
                if error:
                    print(f"[!] 錯誤信息: {error}")
                
            except Exception as e:
                print(f"\n[!] 測試出錯: {str(e)}")
                results.append({
                    'domain': domain,
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - start_time
                })
            
            print("\n" + "-"*50)
            
            # 等待一段時間再進行下一個測試
            if i < len(test_domains):
                print("\n[*] 等待 30 秒後進行下一個測試...")
                time.sleep(30)
        
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
        success_count = sum(1 for r in results if r['success'])
        print(f"測試總結:")
        print(f"- 總測試數: {len(results)}")
        print(f"- 成功數量: {success_count}")
        print(f"- 失敗數量: {len(results) - success_count}")
        
        return all(r['success'] for r in results)
        
    except Exception as e:
        print(f"\n[!] 測試過程出錯: {str(e)}")
        return False

if __name__ == '__main__':
    # 確保在正確的目錄中運行
    os.chdir(project_root)
    
    # 運行測試
    success = test_harvester()
    sys.exit(0 if success else 1) 