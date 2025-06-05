import subprocess
# 使用curl发送http请求 並且設計下載文件 支持POST 和 GET 方法
# 下載文件 並且保存到同目錄下
# 一律叫做download_file 

def curl_use(url, method, data=None):

    try:
        if method == "GET":
            result = subprocess.check_output(["curl", "-s", "-X", method, url])
        elif method == "POST":
            result = subprocess.check_output(["curl", "-s", "-X", method, url, "-d", data])
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl command: {e}")
    