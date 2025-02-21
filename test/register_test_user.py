import requests

def register_test_user():
    """註冊測試用戶"""
    url = 'http://localhost:5000/register'
    data = {
        'username': 'test_user',
        'password': 'test_password'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"狀態碼: {response.status_code}")
        print(f"響應內容: {response.text}")
    except Exception as e:
        print(f"註冊失敗: {str(e)}")

if __name__ == '__main__':
    register_test_user() 