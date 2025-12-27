# flaresolverr/my_spider.py
import os
import httpx
import random
import re
import time
import json
from c2_core.config.logging import log_function_call
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 修正：只引入 requests 接口
from curl_cffi import requests as cffi_requests

logger = logging.getLogger(__name__)


@log_function_call()
class MySpider:
    def __init__(
        self,
        url,
        headers=None,
        method="GET",
        cookie_string="",
        flaresolverr_url=None,
        max_retries=3,
        flaresolverr_max_retries=1,
        CURL_CFFI_TIMEOUT_SECONDS=10,
    ):
        self.url = url
        self.headers = headers if headers is not None else {}
        self.cookie_string = cookie_string
        self.method = method
        self.flaresolverr_url = flaresolverr_url
        self.max_retries = max_retries
        self.flaresolverr_max_retries = flaresolverr_max_retries
        self.min_body_length = 50
        self.used_flaresolverr = False
        # 初始狀態
        self.content_fetch_status = "PENDING"
        self.CURL_CFFI_TIMEOUT_SECONDS = CURL_CFFI_TIMEOUT_SECONDS
        logger.info(f"Spider 初始化 - URL: {self.url}")

    def _is_blocked_by_cloudflare(self, response_text):
        blocked_patterns = [
            r"challenge-form",
            r"jschl_vc",
            r"cf-browser-verification",
            r"Just a moment...",
            r"checking your browser",
            "/cdn-cgi/challenge-platform/",
        ]
        for pattern in blocked_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return True
        return False

    @log_function_call()
    def send(self):
        logger.info(f"Spider 发送请求 - URL: {self.url}")

        last_received_response = None

        # --- 階段一：使用 curl_cffi (主力部隊) ---
        logger.info(
            f"尝试使用 curl_cffi (伪装模式) 请求 {self.url} (Timeout: {self.CURL_CFFI_TIMEOUT_SECONDS}s)"
        )
        for retry_count in range(self.max_retries + 1):
            try:
                response = cffi_requests.request(
                    method=self.method.upper(),
                    url=self.url,
                    headers=self.headers,
                    cookies=self._get_cookies_dict(),
                    timeout=self.CURL_CFFI_TIMEOUT_SECONDS,
                    impersonate="chrome120",
                    allow_redirects=True,
                    verify=False,
                )

                last_received_response = response

                if self._is_blocked_by_cloudflare(response.text):
                    logger.warning(
                        f"curl_cffi 請求 {response.url} 成功，但內容是 Cloudflare 挑戰。升級到 FlareSolverr。"
                    )
                    self.content_fetch_status = (
                        "SUCCESS_FETCHED"  # 雖然是被擋，但HTTP層面成功了
                    )
                    break

                if response.status_code == 204 or len(response.content) == 0:
                    self.content_fetch_status = "FAILED_NO_CONTENT"
                else:
                    self.content_fetch_status = "SUCCESS_FETCHED"

                logger.info(
                    f"Spider 成功通過 curl_cffi 請求 {response.url}，狀態碼 {response.status_code}，狀態: {self.content_fetch_status}"
                )
                return response, self.used_flaresolverr, self.content_fetch_status

            # --- 修正這裡：直接捕獲 RequestsError ---
            except cffi_requests.RequestsError as e:
                # 捕獲 curl_cffi 特有的網路層錯誤 (Connection, Timeout 等都繼承自此)
                self.content_fetch_status = "FAILED_NETWORK_ERROR"
                logger.warning(
                    f"curl_cffi 遭遇網路層錯誤 (RequestsError): {e}. 決定升級到 FlareSolverr。"
                )
                break

            # 也要捕獲 httpx 的錯誤，以防萬一混用了什麼庫導致的（雖然主要請求是用 cffi）
            # 但根據你的代碼結構，這裡主要是防禦性編程
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                self.content_fetch_status = "FAILED_NETWORK_ERROR"
                logger.warning(f"httpx 遭遇網路層錯誤: {e}. 決定升級到 FlareSolverr。")
                break

            except Exception as e:
                # 其他未預期的應用層錯誤
                logger.error(
                    f"curl_cffi 遭遇未知錯誤: {type(e).__name__} - {e} (第 {retry_count+1} 次)"
                )
                if retry_count < self.max_retries:
                    time.sleep(2**retry_count)
                else:
                    logger.error(f"curl_cffi 請求 {self.url} 多次失敗。")
                    if not last_received_response:
                        self.content_fetch_status = "FAILED_NETWORK_ERROR"
                    break

        # --- 階段二：使用 FlareSolverr (重裝甲) ---
        if self.flaresolverr_url:
            self.used_flaresolverr = True
            logger.info(f"升級到 FlareSolverr 請求 {self.url}")

            flaresolverr_response = self._call_flaresolverr()
            if flaresolverr_response:
                if (
                    flaresolverr_response.status_code == 204
                    or len(flaresolverr_response.content) == 0
                ):
                    self.content_fetch_status = "FAILED_NO_CONTENT"
                else:
                    self.content_fetch_status = "SUCCESS_FETCHED"

                logger.info(f"FlareSolverr 成功，最終狀態: {self.content_fetch_status}")
                return (
                    flaresolverr_response,
                    self.used_flaresolverr,
                    self.content_fetch_status,
                )
            else:
                self.content_fetch_status = "FAILED_NETWORK_ERROR"
                logger.error(
                    f"FlareSolverr 最終失敗，最終狀態: {self.content_fetch_status}"
                )

        logger.error(
            f"请求 {self.url} 最终失败，返回最后一个获取的响应 (如果有的话)。最终状态: {self.content_fetch_status}"
        )
        return last_received_response, self.used_flaresolverr, self.content_fetch_status

    # ... (其他方法如 _get_cookies_dict, _call_flaresolverr, translate_into_json 保持不變)
    def _get_cookies_dict(self):
        cookies_dict = {}
        if self.cookie_string:
            for part in self.cookie_string.split(";"):
                if "=" in part:
                    key, value = part.strip().split("=", 1)
                    cookies_dict[key] = value
        return cookies_dict

    def _call_flaresolverr(self):
        cookies_dict = self._get_cookies_dict()
        for fs_retry_count in range(self.flaresolverr_max_retries + 1):
            try:
                custom_headers_list = [
                    {"name": k, "value": v} for k, v in self.headers.items()
                ]
                flaresolverr_payload = {
                    "cmd": f"request.{self.method.lower()}",
                    "url": self.url,
                    "maxTimeout": 60000,
                    "cookies": (
                        [{"name": k, "value": v} for k, v in cookies_dict.items()]
                        if cookies_dict
                        else []
                    ),
                    "customHeaders": custom_headers_list,
                }

                with httpx.Client() as client:
                    fs_response = client.post(
                        f"{self.flaresolverr_url}/v1",
                        json=flaresolverr_payload,
                        timeout=65,
                    )
                fs_response.raise_for_status()
                fs_json_data = fs_response.json()

                if fs_json_data.get("status") == "ok":
                    solution = fs_json_data["solution"]
                    status_code = solution["status"]
                    headers = httpx.Headers(
                        {h["name"]: h["value"] for h in solution.get("headers", [])}
                    )
                    content = solution["response"].encode("utf-8")
                    request_obj = httpx.Request(
                        method=self.method, url=self.url, headers=self.headers
                    )

                    mock_response = httpx.Response(
                        status_code=status_code,
                        headers=headers,
                        content=content,
                        request=request_obj,
                    )

                    for c_item in solution.get("cookies", []):
                        mock_response.cookies.set(c_item["name"], c_item["value"])

                    logger.info(
                        f"Spider 通过 FlareSolverr 成功请求 {solution['url']}，状态码 {mock_response.status_code}。"
                    )
                    return mock_response

                else:
                    logger.error(
                        f"Flaresolverr 服务回应失败: {fs_json_data.get('message')} (第 {fs_retry_count+1} 次)"
                    )

            except httpx.RequestError as e:
                logger.error(f"连接 FlareSolverr 失败: {e} (第 {fs_retry_count+1} 次)")

            if fs_retry_count < self.flaresolverr_max_retries:
                time.sleep(3)
        return None

    def translate_into_json(self, response):
        if response is None:
            return {
                "status_code": None,
                "response_headers": {},
                "response_body_decoded": "",
                "response_body_length": 0,
                "response_cookies": {},
                "response_text": "",
                "response_url": self.url,
                "if_redirect": False,
                "redirect_history": [],
                "content_type": "",
                "used_flaresolverr": self.used_flaresolverr,
                "content_fetch_status": self.content_fetch_status,
            }

        is_cffi_response = "curl_cffi" in str(type(response))

        if is_cffi_response:
            was_redirected_chain = str(response.url) != self.url
            redirect_history_list = []
            response_text = response.text
            response_url = str(response.url)
            response_cookies = dict(response.cookies)
        else:  # 是 httpx.Response 对象 (来自 FlareSolverr)
            was_redirected_chain = bool(response.history)
            redirect_history_list = []
            if response.history:
                for r_hist in response.history:
                    redirect_history_list.append(
                        {
                            "status_code": r_hist.status_code,
                            "url": str(r_hist.url),
                            "headers": dict(r_hist.headers),
                        }
                    )
            response_text = response.text
            response_url = str(response.url)
            response_cookies = dict(response.cookies)

        content_type = response.headers.get("Content-Type", "")

        return {
            "status_code": response.status_code,
            "response_headers": dict(response.headers),
            "response_body_decoded": response.content.decode("utf-8", errors="ignore"),
            "response_body_length": len(response.content),
            "response_cookies": response_cookies,
            "response_text": response_text,
            "response_url": response_url,
            "if_redirect": was_redirected_chain,
            "redirect_history": redirect_history_list,
            "content_type": content_type,
            "used_flaresolverr": self.used_flaresolverr,
            "content_fetch_status": self.content_fetch_status,
            "is_external_redirect": was_redirected_chain,
        }
