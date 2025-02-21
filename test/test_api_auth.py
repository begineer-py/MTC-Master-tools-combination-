import requests
import json
import sys
import os
from colorama import init, Fore, Style
from pathlib import Path
from datetime import datetime, timedelta

# 初始化 colorama
init()

# 添加項目根目錄到 Python 路徑
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 測試配置
BASE_URL = 'http://localhost:5000'
TEST_USER = {
    'username': 'test_user',
    'password': 'test_password'
}

class APITester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.api_key = "94f34968985ff2383fd6d4953d548abe1261c32a0b20b01c00c568cba8c4b509ea9fe94efa92d8ea11e25c1506b18a4acda59e2f1e9651ce8ee1958e5526e2f4"
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.test_results = []

    def print_result(self, test_name, response, expected_status=200):
        """打印測試結果"""
        try:
            success = response.status_code == expected_status
            color = Fore.GREEN if success else Fore.RED
            
            print(f"\n{color}{'='*50}")
            print(f"測試: {test_name}")
            print(f"狀態碼: {response.status_code} (預期: {expected_status})")
            
            try:
                response_json = response.json()
                print(f"響應內容: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
                success = success and response_json.get('success', False)
            except json.JSONDecodeError:
                print(f"響應內容: {response.text}")
                success = False
            
            print(f"結果: {'通過' if success else '失敗'}")
            print(f"{'='*50}{Style.RESET_ALL}\n")
            
            self.test_results.append({
                'name': test_name,
                'success': success,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'response': response.text
            })
            
        except Exception as e:
            print(f"{Fore.RED}測試過程中發生錯誤: {str(e)}{Style.RESET_ALL}")
            self.test_results.append({
                'name': test_name,
                'success': False,
                'error': str(e)
            })

    def test_auth(self):
        """測試 API 認證"""
        try:
            response = requests.get(
                f"{self.base_url}/api/test_auth",
                headers=self.headers
            )
            self.print_result("API 認證測試", response)
        except Exception as e:
            print(f"{Fore.RED}請求失敗: {str(e)}{Style.RESET_ALL}")

    def test_check_api(self, user_id=1, target_id=1):
        """測試 API Key 檢查"""
        try:
            data = {
                'user_id': user_id,
                'target_id': target_id,
                'api_key': self.api_key
            }
            response = requests.post(
                f"{self.base_url}/api/check_api",
                headers=self.headers,
                json=data
            )
            self.print_result("API Key 檢查", response)
        except Exception as e:
            print(f"{Fore.RED}請求失敗: {str(e)}{Style.RESET_ALL}")

    def test_get_api_key(self, user_id=1, target_id=1):
        """測試獲取 API Key"""
        try:
            data = {
                'user_id': user_id,
                'target_id': target_id
            }
            response = requests.post(
                f"{self.base_url}/api/get_api_key",
                headers=self.headers,
                json=data
            )
            self.print_result("獲取 API Key", response)
        except Exception as e:
            print(f"{Fore.RED}請求失敗: {str(e)}{Style.RESET_ALL}")

    def test_make_api_key(self, user_id=1, target_id=1):
        """測試生成新的 API Key"""
        try:
            data = {
                'user_id': user_id,
                'target_id': target_id
            }
            response = requests.post(
                f"{self.base_url}/api/make_api_key",
                headers=self.headers,
                json=data
            )
            self.print_result("生成新的 API Key", response)
        except Exception as e:
            print(f"{Fore.RED}請求失敗: {str(e)}{Style.RESET_ALL}")

    def test_delete_api_key(self, user_id=1, target_id=1):
        """測試刪除 API Key"""
        try:
            data = {
                'user_id': user_id,
                'target_id': target_id
            }
            response = requests.post(
                f"{self.base_url}/api/delete_api_key",
                headers=self.headers,
                json=data
            )
            self.print_result("刪除 API Key", response)
        except Exception as e:
            print(f"{Fore.RED}請求失敗: {str(e)}{Style.RESET_ALL}")

    def test_invalid_api_key(self):
        """測試無效的 API Key"""
        try:
            invalid_headers = self.headers.copy()
            invalid_headers['X-API-Key'] = 'invalid_key'
            response = requests.get(
                f"{self.base_url}/api/test_auth",
                headers=invalid_headers
            )
            self.print_result("無效的 API Key測試", response, expected_status=401)
        except Exception as e:
            print(f"{Fore.RED}請求失敗: {str(e)}{Style.RESET_ALL}")

    def run_all_tests(self):
        """運行所有測試"""
        print(f"{Fore.CYAN}開始運行 API 認證測試...{Style.RESET_ALL}")
        
        try:
            self.test_auth()
            self.test_check_api()
            self.test_get_api_key()
            self.test_make_api_key()
            self.test_delete_api_key()
            self.test_invalid_api_key()
            
            # 打印測試總結
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            
            print(f"\n{Fore.CYAN}測試總結:")
            print(f"總測試數: {total_tests}")
            print(f"通過測試: {passed_tests}")
            print(f"失敗測試: {total_tests - passed_tests}")
            print(f"通過率: {(passed_tests/total_tests)*100:.2f}%{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}測試過程中發生錯誤: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)

def register():
    """註冊測試用戶"""
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/register",
        data=TEST_USER,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        allow_redirects=True
    )
    if response.status_code not in [200, 302]:
        print(f"註冊失敗: {response.text}")
    return True  # 即使用戶已存在也繼續測試

def login():
    """登錄測試用戶並返回 session"""
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/login",
        data=TEST_USER,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        allow_redirects=True
    )
    if response.status_code not in [200, 302]:
        raise Exception(f"登錄失敗: {response.text}")
    return session

def run_test(endpoint, method='GET', session=None, data=None):
    """運行測試並返回結果"""
    url = f"{BASE_URL}/api{endpoint}"
    
    if session is None:
        session = requests.Session()
    
    headers = session.headers.copy()
    headers.update({'Accept': 'application/json'})
    
    if method == 'GET':
        response = session.get(url, headers=headers)
    elif method == 'POST':
        response = session.post(url, json=data, headers=headers)
    elif method == 'DELETE':
        response = session.delete(url, headers=headers)
    
    print(f"\n測試 {endpoint}:")
    print(f"狀態碼: {response.status_code}")
    try:
        json_response = response.json()
        print(f"響應: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
    except:
        print(f"響應: {response.text}")
    
    return response

def test_api_auth():
    """測試 API 認證功能"""
    # 1. 註冊測試用戶（如果不存在）
    register()
    
    # 2. 登錄獲取 session
    session = login()
    
    # 3. 生成 API Key
    print("\n=== 生成 API Key ===")
    response = run_test('/key/generate', 'POST', session=session, data={'expires_in': 1})
    assert response.status_code == 200
    api_key = response.json()['data']['api_key']
    
    # 4. 使用 API Key 測試認證
    print("\n=== 測試 API 認證 ===")
    api_session = requests.Session()
    api_session.headers.update({'X-API-Key': api_key})
    response = run_test('/test_auth', session=api_session)
    assert response.status_code == 200
    
    # 5. 獲取 API Key 信息
    print("\n=== 獲取 API Key 信息 ===")
    response = run_test('/key/info', session=session)
    assert response.status_code == 200
    
    # 6. 測試無效的 API Key
    print("\n=== 測試無效的 API Key ===")
    invalid_session = requests.Session()
    invalid_session.headers.update({'X-API-Key': 'invalid_key'})
    response = run_test('/test_auth', session=invalid_session)
    assert response.status_code == 401
    
    # 7. 撤銷 API Key
    print("\n=== 撤銷 API Key ===")
    response = run_test('/key/revoke', 'POST', session=session)
    assert response.status_code == 200
    
    # 8. 確認撤銷後的 API Key 無效
    print("\n=== 確認撤銷後的 API Key ===")
    response = run_test('/test_auth', session=api_session)
    assert response.status_code == 401

if __name__ == '__main__':
    try:
        test_api_auth()
        print("\n所有測試通過！")
    except AssertionError as e:
        print(f"\n測試失敗: {str(e)}")
    except Exception as e:
        print(f"\n測試出錯: {str(e)}") 