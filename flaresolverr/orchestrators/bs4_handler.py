# flaresolverr/orchestrators/bs4_handler.py

import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin
from c2_core.config.logging import log_function_call

# 媽的，用 DEBUG 級別來看最詳細的情報，用 INFO 來看總結
# 你可以在 settings.py 裡調整日誌級別來控制輸出
logger = logging.getLogger(__name__)


class BS4Handler:
    """
    媽的，這是 BeautifulSoup 的專家。
    所有跟 HTML 解析相關的髒活累活都歸他管。
    吃進 HTML，吐出結構化的 JSON 數據。
    (v2.0 審訊室版本，帶全程詳細日誌)
    """

    @classmethod
    def get_empty_analysis(cls) -> Dict[str, Any]:
        return {
            "title": None,
            "forms": [],
            "links": [],
            "scripts": [],
            "comments": [],
            "meta_tags": [],
            "iframes": [],
        }

    # 每個 _parse_* 方法都加上詳細日誌

    @log_function_call()
    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        logger.info("--- 開始解析 Title (<title>) ---")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            logger.info(f"成功提取 Title: '{title}'")
            return title
        logger.warning("未找到 <title> 標籤或內容為空。")
        return None

    @log_function_call()
    def _parse_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        logger.info("--- 開始解析表單 (<form>) ---")
        forms_data = []
        form_tags = soup.find_all("form")
        logger.info(f"找到 {len(form_tags)} 個 <form> 標籤。")
        for i, form_tag in enumerate(form_tags):
            logger.debug(f"  [表單 {i+1}/{len(form_tags)}] 正在處理...")
            action = form_tag.get("action", "")
            method = form_tag.get("method", "GET").upper()
            parameters = []
            input_tags = form_tag.find_all(["input", "textarea", "select", "button"])
            logger.debug(f"    - 在此表單中找到 {len(input_tags)} 個輸入相關標籤。")
            for tag in input_tags:
                name = tag.get("name")
                if not name:
                    logger.debug(f"      - 跳過一個沒有 'name' 屬性的標籤: {tag.name}")
                    continue
                # ... (其餘邏輯不變)
                parameters.append({"name": name, "type": tag.get("type", "text")})

            form_info = {"action": action, "method": method, "parameters": parameters}
            logger.debug(f"    - 收集到表單數據: {form_info}")
            forms_data.append(form_info)

        logger.info(f"表單解析完成，共收集到 {len(forms_data)} 個表單。")
        return forms_data

    @log_function_call()
    def _parse_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        logger.info("--- 開始解析連結 (<a>) ---")
        links = []
        a_tags = soup.find_all("a", href=True)
        logger.info(f"找到 {len(a_tags)} 個帶 'href' 的 <a> 標籤。")
        for i, tag in enumerate(a_tags):
            href = tag["href"]
            logger.debug(f"  [連結 {i+1}/{len(a_tags)}] 正在處理 href: '{href}'")

            if href.strip() and not href.startswith("#"):
                logger.debug(f"    - href 有效，準備合併 URL。")
                absolute_url = urljoin(base_url, href)
                link_data = {"text": tag.get_text(strip=True), "href": absolute_url}
                logger.debug(f"    - 收集到連結數據: {link_data}")
                links.append(link_data)
            else:
                logger.debug(f"    - 操，這個 href 是空的或是錨點，跳過。")

        logger.info(f"連結解析完成，共收集到 {len(links)} 條有效連結。")
        return links

    def _parse_iframes(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        logger.info("--- 開始解析內聯框架 (<iframe>) ---")
        iframes = []
        iframe_tags = soup.find_all("iframe", src=True)
        logger.info(f"找到 {len(iframe_tags)} 個帶 'src' 的 <iframe> 標籤。")
        for i, tag in enumerate(iframe_tags):
            src = tag["src"]
            logger.debug(f"  [Iframe {i+1}/{len(iframe_tags)}] 正在處理 src: '{src}'")
            absolute_src = urljoin(base_url, src)
            iframe_data = {"src": absolute_src}
            logger.debug(f"    - 收集到 iframe 數據: {iframe_data}")
            iframes.append(iframe_data)
        logger.info(f"Iframe 解析完成，共收集到 {len(iframes)} 個。")
        return iframes

    @log_function_call()
    def _parse_comments(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        logger.info("--- 開始解析註釋 (<!--...-->) ---")
        comments = []
        comment_nodes = soup.find_all(string=lambda text: isinstance(text, Comment))
        logger.info(f"找到 {len(comment_nodes)} 條註釋。")
        for i, comment in enumerate(comment_nodes):
            content = comment.strip()
            logger.debug(
                f"  [註釋 {i+1}/{len(comment_nodes)}] 內容 (前80字符): {content[:80]}"
            )
            comments.append({"content": content})
        logger.info(f"註釋解析完成，共收集到 {len(comments)} 條。")
        return comments

    @log_function_call()
    def _parse_meta_tags(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        logger.info("--- 開始解析元標籤 (<meta>) ---")
        meta_tags = []
        all_meta_tags = soup.find_all("meta")
        logger.info(f"找到 {len(all_meta_tags)} 個 <meta> 標籤。")
        for i, tag in enumerate(all_meta_tags):
            attrs = {k: v for k, v in tag.attrs.items()}
            logger.debug(f"  [Meta {i+1}/{len(all_meta_tags)}] 收集到屬性: {attrs}")
            meta_tags.append(attrs)
        logger.info(f"Meta 標籤解析完成，共收集到 {len(meta_tags)} 個。")
        return meta_tags

    @log_function_call()
    def _parse_scripts(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, Optional[str]]]:
        logger.info("--- 開始解析腳本 (<script>) ---")
        scripts = []
        script_tags = soup.find_all("script")
        logger.info(f"找到 {len(script_tags)} 個 <script> 標籤。")
        for i, tag in enumerate(script_tags):
            src = tag.get("src")
            logger.debug(
                f"  [腳本 {i+1}/{len(script_tags)}] 正在處理標籤: {str(tag)[:100]}..."
            )
            if src:
                logger.debug(f"    - 判斷為外部腳本。src: '{src}'")
                absolute_src = urljoin(base_url, src)
                script_data = {"src": absolute_src, "content": None}
                logger.debug(f"    - 收集到外部腳本數據: {script_data}")
                scripts.append(script_data)
            else:
                logger.debug(f"    - 判斷為內聯腳本。")
                content = tag.get_text(strip=True)
                if content:
                    logger.debug(
                        f"    - 成功提取內聯內容 (前80字符): {content[:80]}..."
                    )
                    script_data = {"src": None, "content": content}
                    scripts.append(script_data)
                else:
                    logger.debug(f"    - 內聯腳本內容為空，跳過。")
        logger.info(f"腳本解析完成，共收集到 {len(scripts)} 條。")
        return scripts

    def analyze_html(self, html_content: str, base_url: str) -> Dict[str, Any]:
        logger.info(
            f"BS4Handler 開始對 base_url='{base_url}' 的 HTML 內容進行全面分析。"
        )
        if not html_content:
            logger.warning("傳入的 HTML 內容為空，返回空的分析結果。")
            return self.get_empty_analysis()

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # --- 你的除錯日誌，非常好用，我們先留著 ---
            # logger.error(f"{soup}") # 這個太大了，可以先註解掉
            logger.info(f"傳入的 Base URL: {base_url}")

            # --- 流水線作業！ ---
            title = self._parse_title(soup)
            forms = self._parse_forms(soup)
            links = self._parse_links(soup, base_url)
            scripts = self._parse_scripts(soup, base_url)
            comments = self._parse_comments(soup)
            meta_tags = self._parse_meta_tags(soup)
            iframes = self._parse_iframes(soup, base_url)

            analysis_result = {
                "title": title,
                "forms": forms,
                "links": links,
                "scripts": scripts,
                "comments": comments,
                "meta_tags": meta_tags,
                "iframes": iframes,
            }

            # --- 最終總結報告 ---
            logger.info(
                f"BS4Handler 完成全方位分析。摘要: "
                f"Title='{bool(title)}', "
                f"Forms={len(forms)}, Links={len(links)}, Scripts={len(scripts)}, "
                f"Comments={len(comments)}, Meta={len(meta_tags)}, Iframes={len(iframes)}"
            )

            return analysis_result

        except Exception as e:
            logger.exception(f"媽的，BS4Handler 在解析 HTML 時發生了致命錯誤: {e}")
            return self.get_empty_analysis()
