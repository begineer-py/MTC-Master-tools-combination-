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

    @staticmethod
    def _is_soft_redirect(response) -> bool:
        """
        基於規則的快速檢測。
        判定該響應是否為軟跳轉/空殼，需要瀏覽器介入。
        """
        try:
            # 1. 快速過濾非 HTML
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                return False

            html = response.text
            # 如果 body 為空，直接視為失敗/需要重試，不一定要在這裡判斷，
            # 但如果只有幾字節，極有可能是 js 跳轉
            if not html:
                return False

            if len(html) > 100000:  # 太大的通常不是跳轉頁
                return False

            soup = BeautifulSoup(html, "html.parser")

            # 2. 鐵證：Meta Refresh
            if soup.find("meta", attrs={"http-equiv": re.compile(r"^refresh$", re.I)}):
                return True

            # 3. 鐵證：SAML/Form 自動提交
            scripts = soup.find_all("script")
            script_text = " ".join([s.get_text() for s in scripts]).lower()

            if soup.find("form") and (
                ".submit()" in script_text or "document.forms" in script_text
            ):
                return True

            # 4. 鐵證：JS 重定向關鍵字
            # 必須非常小心，只匹配明確的賦值行為
            js_redirect_patterns = [
                r"(window|self|top)\.location(\.href)?\s*=",
                r"location\.replace\(",
                r"location\.assign\(",
            ]
            for pattern in js_redirect_patterns:
                if re.search(pattern, script_text):
                    return True

            # 5. 輔助：內容密度極低 (針對 React/Vue 空殼)
            # 移除干擾項，看純文本
            for tag in soup(["script", "style", "meta", "noscript"]):
                tag.extract()
            text = soup.get_text(strip=True)

            # 如果有腳本但沒內容 -> 判定為空殼
            # 這裡設定閾值為 50 字元
            if len(text) < 50 and len(scripts) > 0:
                return True

            return False
        except Exception as e:
            logger.error(f"Soft redirect detection failed: {e}")
            return False

    @log_function_call()
    def send(self):
        logger.info(f"Spider 发送请求 - URL: {self.url}")

        last_received_response = None
        should_upgrade_to_flaresolverr = False  # 控制標誌位

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

                # 檢測 1: Cloudflare 攔截
                if self._is_blocked_by_cloudflare(response.text):
                    logger.warning(
                        f"curl_cffi 請求 {response.url} 成功，但內容是 Cloudflare 挑戰。升級到 FlareSolverr。"
                    )
                    should_upgrade_to_flaresolverr = True
                    break  # 跳出重試循環，進入 FS 流程

                # 檢測 2: 軟跳轉 / 空殼頁面 (新增邏輯)
                if response.status_code == 200 and self._is_soft_redirect(response):
                    logger.warning(
                        f"curl_cffi 檢測到軟跳轉/SPA空殼 (SAML/JS/Meta): {response.url}。升級到 FlareSolverr。"
                    )
                    should_upgrade_to_flaresolverr = True
                    break  # 跳出重試循環，進入 FS 流程

                if response.status_code == 204 or len(response.content) == 0:
                    self.content_fetch_status = "FAILED_NO_CONTENT"
                else:
                    self.content_fetch_status = "SUCCESS_FETCHED"

                logger.info(
                    f"Spider 成功通過 curl_cffi 請求 {response.url}，狀態碼 {response.status_code}，狀態: {self.content_fetch_status}"
                )
                return response, self.used_flaresolverr, self.content_fetch_status

            except cffi_requests.RequestsError as e:
                # 捕獲 curl_cffi 特有的網路層錯誤
                self.content_fetch_status = "FAILED_NETWORK_ERROR"
                logger.warning(
                    f"curl_cffi 遭遇網路層錯誤 (RequestsError): {e}. 決定升級到 FlareSolverr。"
                )
                should_upgrade_to_flaresolverr = True  # 網路錯誤也嘗試一下 FS
                break

            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                self.content_fetch_status = "FAILED_NETWORK_ERROR"
                logger.warning(f"httpx 遭遇網路層錯誤: {e}. 決定升級到 FlareSolverr。")
                should_upgrade_to_flaresolverr = True
                break

            except Exception as e:
                # 其他未預期的應用層錯誤，重試
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
        # 只有當 flaresolverr_url 存在，並且 (被標記需要升級 或 cffi 全失敗但我們想試試) 時才執行
        if self.flaresolverr_url and (
            should_upgrade_to_flaresolverr
            or self.content_fetch_status == "FAILED_NETWORK_ERROR"
        ):
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

    # ... (其餘部分 _get_cookies_dict, _call_flaresolverr, translate_into_json 保持原樣)
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
                    final_redirected_url = solution["url"]

                    request_obj = httpx.Request(
                        method=self.method,
                        url=final_redirected_url,
                        headers=self.headers,
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
                        f"Spider 通过 FlareSolverr 成功请求 {final_redirected_url}，状态码 {mock_response.status_code}，最終URL {solution['url']}。"
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

    @log_function_call()
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
            response_url = str(response.url)
            was_redirected_chain = response_url != self.url

            redirect_history_list = []
            # 如果真的有 history (雖然後面不太可能有)，保留這個邏輯也無妨
            if hasattr(response, "history") and response.history:
                for r_hist in response.history:
                    redirect_history_list.append(
                        {
                            "status_code": r_hist.status_code,
                            "url": str(r_hist.url),
                            "headers": dict(r_hist.headers),
                        }
                    )

            response_text = response.text
            response_cookies = dict(response.cookies)

        content_type = response.headers.get("Content-Type", "")
        logger.info(f"Final URL: {response_url}")
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
