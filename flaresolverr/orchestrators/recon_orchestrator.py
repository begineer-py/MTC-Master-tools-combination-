# flaresolverr/orchestrators/recon_orchestrator.py
import os
import logging
from typing import List, Dict, Any
from .bs4_handler import BS4Handler
import hashlib

# 操，注意這個 import 路径！
from ..my_spider import MySpider

# 把 TechScanner 也導入進來
from ..web_tech.tech_scanner import TechScanner


# 導入本地項目內的分析引擎
from flaresolverr.gf.hacker_gf.pygf import PatternAnalyzer


logger = logging.getLogger(__name__)


class ReconOrchestrator:
    """
    v1.0 指揮官：
    1. 負責協調 MySpider, TechScanner 和 PatternAnalyzer。
    2. 吃進一個 URL，吐出一個包含所有戰果的字典。
    3. 自己不干髒活，只負責指揮和打包。
    """

    def __init__(self, url: str, method: str = "GET", cookie_string: str = ""):
        self.url = url
        self.method = method
        self.cookie_string = cookie_string
        self.spider = MySpider(
            url=self.url,
            method=self.method,
            cookie_string=self.cookie_string,
            flaresolverr_url=os.getenv("FLARESOLVERR_URL") or "http://127.0.0.1:8191",
        )
        self.analyzer = PatternAnalyzer()
        self.tech_scanner = TechScanner()
        self.bs4_handler = BS4Handler()
        self.content_fetch_status = "PENDING"

        logger.info(f"指揮官就位，目標鎖定: {self.url}")

    def run(self) -> dict:
        logger.info(f"作戰開始: {self.url}")

        # --- 第一階段：派遣先鋒部隊 (MySpider) ---
        response, used_flaresolverr, self.content_fetch_status = self.spider.send()

        tech_stack_data = {
            "technologies": [],
            "fingerprints_matched": [],
            "error": "Spider failed, tech scan skipped.",
        }

        # 如果連 response 對象都沒有，直接報錯
        if not response:
            logger.error(f"作戰失敗: 先鋒部隊未能為 {self.url} 奪取任何情報。")
            return {
                "success": False,
                "url": self.url,
                "error": "Spider failed to get a response.",
                "spider_result": None,
                "analysis_result": None,
                "tech_stack_result": tech_stack_data,
                "content_fetch_status": self.content_fetch_status,  # <--- 這裡也要返回狀態
            }

        logger.info(
            f"先鋒部隊成功返回情報 for {self.url}, 狀態碼: {response.status_code}"
        )

        # --- 第二階段：情報整理 ---
        spider_json_report = self.spider.translate_into_json(response)

        # 關鍵：獲取 Content-Type 並標準化
        response_headers = spider_json_report.get("response_headers", {})
        # 處理 key 大小寫可能不一致的問題 (Content-Type vs content-type)
        content_type = next(
            (v for k, v in response_headers.items() if k.lower() == "content-type"), ""
        ).lower()

        logger.info(f"偵測到的 Content-Type: {content_type}")

        # 準備響應文本
        response_text = spider_json_report.get("response_text", "")

        # 判斷是否為「可分析文本」 (Text-based)
        # 如果是 image/gif, application/zip 等二進位，這個標誌為 False
        analyzable_types = ["text", "html", "json", "xml", "javascript", "ecmascript"]
        is_text_content = (
            any(t in content_type for t in analyzable_types) or not content_type
        )

        # --- 第三階段：技術偵測 (TechScanner) ---
        # 技術偵測通常基於 Headers 和 HTML，如果是純圖片也可以跑 Headers 部分，所以這裡不強制過濾
        tech_stack_data = self.tech_scanner.scan(
            response_headers=spider_json_report.get("response_headers", {}),
            response_text=(
                response_text if is_text_content else ""
            ),  # 如果是二進位，不要傳內容進去亂搞
            response_cookies=spider_json_report.get("response_cookies", {}),
            url=spider_json_report.get("response_url", self.url),
        )
        logger.info(
            f"技術偵測完成，發現 {len(tech_stack_data.get('technologies', []))} 種技術。"
        )

        # --- 第四階段：HTML 結構化分析 (BS4Handler) ---
        html_analysis = self.bs4_handler.get_empty_analysis()

        # 只有當 Content-Type 包含 html 且確實有內容時，才跑 BeautifulSoup
        if "html" in content_type and response_text and len(response_text) > 0:
            final_url = spider_json_report.get("response_url", self.url)
            html_analysis = (
                self.bs4_handler.analyze_html(response_text, base_url=final_url)
                or html_analysis
            )
            logger.info(f"HTML 分析完成。Title: {html_analysis.get('title')}")
        else:
            logger.info(f"跳過 HTML 分析 (非 HTML 內容或內容為空)。")

        # 提取 BS4 分析結果
        extracted_title = html_analysis.get("title")
        forms_found = html_analysis.get("forms", [])
        links_found = html_analysis.get("links", [])
        scripts_found = html_analysis.get("scripts", [])
        comments_found = html_analysis.get("comments", [])
        meta_tags_found = html_analysis.get("meta_tags", [])
        iframes_found = html_analysis.get("iframes", [])

        # 更新 Spider 報告中的標題
        spider_json_report["title"] = extracted_title

        # --- 第五階段：情報洩漏分析 (HackerGF) ---
        analysis_findings = []

        # 這裡是最重要的過濾：
        # 1. 必須是文本類型 (is_text_content)
        # 2. 必須有內容
        # 3. 避免對明顯的二進位擴展名跑正則 (即使 Content-Type 騙人)
        is_binary_url = any(
            self.url.lower().endswith(ext)
            for ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".ico",
                ".woff",
                ".ttf",
                ".pdf",
                ".zip",
            ]
        )

        if is_text_content and response_text and not is_binary_url:
            lines = response_text.splitlines()
            # 限制行數或長度，避免對超大 JS 文件跑正則導致卡死 (可選，這裡先不加)
            analysis_findings = self.analyzer.run_all_patterns(lines)
            logger.info(f"HackerGF 分析完成，發現 {len(analysis_findings)} 個潛在點。")
        else:
            logger.info(f"跳過 HackerGF 分析 (非文本內容、二進位 URL 或內容為空)。")
        if response_text:
            # 使用 md5 算法，更輕量，速度更快
            raw_response_hash = hashlib.md5(
                response_text.encode("utf-8", errors="ignore")
            ).hexdigest()
            logger.info(f"計算響應內容 MD5 Hash: {raw_response_hash}")
        else:
            logger.info("響應內容為空，跳過 Hash 計算。")
        # --- 第六階段：打包最終戰報 ---
        logger.info(f"作戰成功結束 for {self.url}")

        return {
            "success": True,
            "final_url": self.url,
            "error": None,
            "spider_result": spider_json_report,
            "analysis_result": analysis_findings,
            "tech_stack_result": tech_stack_data,
            "forms_result": forms_found,
            "used_flaresolverr": used_flaresolverr,
            "links_result": links_found,
            "scripts_result": scripts_found,
            "comments_result": comments_found,
            "meta_tags_result": meta_tags_found,
            "iframes_result": iframes_found,
            "content_fetch_status": self.content_fetch_status,  # 確保傳回狀態
            "raw_response_hash": raw_response_hash,
        }
