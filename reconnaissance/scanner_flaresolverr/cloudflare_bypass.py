import sys
import os

# 添加項目根目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
import json
import logging
from datetime import datetime, UTC
from instance.models import db, crawler_each_url, crawler_each_form, crawler_each_js, crawler_each_image, crawler_each_html, crawler_each_security, FormParameter
import random
from reconnaissance.scanner_flaresolverr.html_parser import HtmlParser
import argparse
from urllib.parse import urlparse, urljoin, parse_qs
import time
from reconnaissance.scanner_flaresolverr.deduplication import HTMLDeduplicator
from bs4 import BeautifulSoup
from contextlib import contextmanager

@contextmanager
def session_scope():
    """提供事务范围的会话上下文管理器"""
    session = db.session
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def setup_logging():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # 移除 reconfigure 調用，改用 encoding 參數
    try:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    except Exception as e:
        print(f"設置日誌時出錯: {str(e)}")
    
    return logger

logger = setup_logging()

class CloudflareBypass:
    def __init__(self, flaresolverr_url="http://localhost:8191/v1", app=None):
        self.flaresolverr_url = flaresolverr_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.app = app._get_current_object() if hasattr(app, '_get_current_object') else app
        
        # 設置類級別的日誌記錄器
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
    
    def _get_random_user_agent(self):
        """從文件中隨機獲取 User-Agent"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ua_file = os.path.join(current_dir, 'user_agent.txt')
        try:
            with open(ua_file, 'r') as f:
                user_agents = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                return random.choice(user_agents)
        except Exception as e:
            self.logger.error(f"讀取 User-Agent 文件出錯：{str(e)}")
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def fetch_js_content(self, js_url):
        """獲取 JavaScript 文件內容"""
        try:
            response = self.send_request_to_flaresolverr(js_url)
            if response and response.get('solution', {}).get('response'):
                js_content = response['solution']['response']
                content_type = response.get('solution', {}).get('headers', {}).get('content-type', '').lower()
                if 'javascript' in content_type or js_url.lower().endswith('.js'):
                    return js_content.strip()
                return None
        except Exception as e:
            self.logger.error(f"獲取 JS 內容時出錯: {str(e)}")
            return None
            
    def fetch_image_content(self, img_url):
        """使用 FlareSolverr 獲取圖片內容"""
        try:
            # 確保 URL 是 ASCII 編碼
            img_url = img_url.encode('ascii', 'ignore').decode('ascii')
            response = self.send_request_to_flaresolverr(img_url)
            
            if response and response.get('solution', {}).get('response'):
                # 從 headers 中獲取內容類型
                content_type = response['solution'].get('headers', {}).get('content-type', '').lower()
                
                # 檢查是否為圖片類型
                if content_type.startswith('image/'):
                    image_data = response['solution']['response'].encode('utf-8')
                    image_type = content_type.split('/')[-1]  # 從 content-type 獲取圖片類型
                    return image_data, image_type
                    
                # 如果沒有 content-type，根據 URL 後綴判斷
                elif any(img_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                    image_data = response['solution']['response'].encode('utf-8')
                    image_type = img_url.split('.')[-1].lower()
                    return image_data, image_type
                    
            return None, None
            
        except Exception as e:
            self.logger.error(f"獲取圖片內容時出錯: {str(e)}")
            return None, None

    def send_request_to_flaresolverr(self, url, headers=None):
        """發送請求到 FlareSolverr"""
        try:
            data = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            }
            if headers:
                data["headers"] = dict(headers)

            response = requests.post(
                self.flaresolverr_url,
                headers={"Content-Type": "application/json"},
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok":
                    return result
                self.logger.error(f"FlareSolverr 返回錯誤: {result.get('message', '未知錯誤')}")
            else:
                self.logger.error(f"FlareSolverr 請求失敗，狀態碼: {response.status_code}")
            return None
        except Exception as e:
            self.logger.error(f"請求過程出錯: {str(e)}")
            return None

    def make_request(self, url, target_id):
        """處理請求並保存結果"""
        try:
            response = self.send_request_to_flaresolverr(url)
            if not response or not response.get('solution', {}).get('response'):
                self.logger.error(f"無法獲取 {url} 的響應")
                return False

            html_content = response['solution']['response']
            status_code = response['solution'].get('status', 0)
            headers = response['solution'].get('headers', {})
            
            # 使用應用上下文和事務管理
            with self.app.app_context():
                with session_scope() as session:
                    try:
                        # 創建 URL 記錄
                        url_record = crawler_each_url(
                            target_id=target_id,
                            url=url,
                            status_code=status_code,
                            content_type=headers.get('content-type', '')
                        )
                        session.add(url_record)
                        session.flush()  # 获取 url_record 的 ID

                        # 使用 HtmlParser 解析內容
                        parser = HtmlParser(base_url=url)
                        parser.parse(html_content)
                        
                        # 詳細輸出解析結果
                        self.logger.info(f"\n{'='*50}\n解析 URL: {url}")
                        self.logger.info(f"狀態碼: {status_code}")
                        self.logger.info(f"Content-Type: {headers.get('content-type', '')}")
                        
                        # 輸出表單信息
                        self.logger.info("\n表單信息:")
                        for idx, form in enumerate(parser.forms, 1):
                            self.logger.info(f"\n表單 {idx}:")
                            self.logger.info(f"Method: {form.get('method', 'N/A')}")
                            self.logger.info(f"Action: {form.get('action', 'N/A')}")
                            self.logger.info(f"ID: {form.get('id', 'N/A')}")
                            self.logger.info(f"Class: {form.get('class', 'N/A')}")
                            self.logger.info("輸入字段:")
                            for input_field in form.get('inputs', []):
                                self.logger.info(f"  - 名稱: {input_field.get('name', 'N/A')}")
                                self.logger.info(f"    類型: {input_field.get('type', 'N/A')}")
                                self.logger.info(f"    必填: {input_field.get('required', False)}")
                                self.logger.info(f"    ID: {input_field.get('id', 'N/A')}")
                                self.logger.info(f"    Class: {input_field.get('class', 'N/A')}")
                        
                        # 輸出腳本信息
                        self.logger.info("\n腳本信息:")
                        for script in parser.scripts:
                            if 'url' in script:
                                self.logger.info(f"外部腳本: {script['url']}")
                            elif 'content' in script:
                                content_preview = script['content'][:100] + '...' if len(script['content']) > 100 else script['content']
                                self.logger.info(f"內聯腳本: {content_preview}")
                        
                        # 輸出元標籤信息
                        self.logger.info("\nMeta 標籤:")
                        for meta in parser.meta_tags:
                            self.logger.info(f"名稱: {meta.get('name', 'N/A')}")
                            self.logger.info(f"內容: {meta.get('content', 'N/A')}")
                        
                        self.logger.info(f"\n{'='*50}")
                        
                        # 保存解析結果
                        self._save_parsed_results(parser, url_record, headers, session)
                        
                        return True
                    except Exception as e:
                        self.logger.error(f"保存數據時出錯: {str(e)}")
                        raise

        except Exception as e:
            self.logger.error(f"請求處理出錯: {str(e)}")
            return False

    def _save_parsed_results(self, parser, url_record, headers, session):
        """保存所有解析結果"""
        try:
            # 保存表單
            forms = parser.get_forms()
            self.logger.info(f"開始保存 {len(forms)} 個表單")
            
            try:
                # 首先處理 URL 參數
                parsed_url = urlparse(url_record.url)
                if parsed_url.query:
                    # 創建一個特殊的表單記錄用於 URL 參數
                    url_params_form = crawler_each_form(
                        crawler_each_url_id=url_record.id,
                        form=json.dumps({'method': 'GET', 'action': parsed_url.path}),
                        form_method='GET',
                        form_action=parsed_url.path
                    )
                    session.add(url_params_form)
                    session.flush()

                    # 解析並保存 URL 參數
                    url_params = parse_qs(parsed_url.query, keep_blank_values=True)
                    for param_name, param_values in url_params.items():
                        param_value = param_values[0] if param_values else ''
                        param = FormParameter(
                            form_id=url_params_form.id,
                            name=param_name,
                            param_type='url_parameter',
                            parameter_source='URL',
                            default_value=param_value,
                            required=False
                        )
                        session.add(param)
                        self.logger.info(f"已添加 URL 參數: {param_name} = {param_value}")
                    self.logger.info("URL 參數保存成功")
            except Exception as e:
                self.logger.error(f"處理 URL 參數時出錯: {str(e)}")
                raise

            try:
                # 處理表單參數
                for form in forms:
                    form_data = {
                        'method': form.get('method', 'GET'),
                        'action': form.get('action', ''),
                        'id': form.get('id', ''),
                        'class': form.get('class', ''),
                        'inputs': form.get('inputs', [])
                    }
                    
                    form_record = crawler_each_form(
                        crawler_each_url_id=url_record.id,
                        form=json.dumps(form_data, ensure_ascii=False),
                        form_method=form_data['method'],
                        form_action=form_data['action']
                    )
                    
                    session.add(form_record)
                    session.flush()
                    
                    # 保存表單參數
                    for input_field in form_data['inputs']:
                        param = FormParameter(
                            form_id=form_record.id,
                            name=input_field.get('name', ''),
                            param_type=input_field.get('type', 'text'),
                            parameter_source=form_data['method'].upper(),
                            required=input_field.get('required', False),
                            default_value=input_field.get('value', ''),
                            placeholder=input_field.get('placeholder', '')
                        )
                        session.add(param)
                        self.logger.info(f"已添加{form_data['method']}參數: {param.name} ({param.param_type})")
                
                self.logger.info("表單參數保存成功")
            except Exception as e:
                self.logger.error(f"保存表單參數時出錯: {str(e)}")
                raise

            try:
                # 保存其他資源（JS、圖片等）
                self._save_resources(parser, url_record, headers, session)
                self.logger.info("所有資源保存成功")
            except Exception as e:
                self.logger.error(f"保存資源時出錯: {str(e)}")
                raise
                
        except Exception as e:
            self.logger.error(f"保存解析結果時出錯: {str(e)}")
            raise

    def _save_resources(self, parser, url_record, headers, session):
        """保存 JS、圖片等資源"""
        # 保存 JavaScript
        js_files = parser.get_javascript_files()
        self.logger.info(f"開始保存 {len(js_files)} 個 JavaScript 文件")
        
        for js_url in js_files:
            try:
                js_content = self.fetch_js_content(js_url)
                if js_content:
                    js_record = crawler_each_js(
                        crawler_each_url_id=url_record.id,
                        js=js_content,
                        js_url=js_url
                    )
                    session.add(js_record)
            except Exception as e:
                self.logger.error(f"保存 JavaScript 時出錯: {str(e)}")
                continue

        # 保存圖片
        images = parser.get_images()
        self.logger.info(f"開始保存 {len(images)} 個圖片")
        
        for img_url in images:
            try:
                image_data, image_type = self.fetch_image_content(img_url)
                if image_data and image_type:
                    image_record = crawler_each_image(
                        crawler_each_url_id=url_record.id,
                        image=image_data,
                        image_url=img_url,
                        image_type=image_type
                    )
                    session.add(image_record)
            except Exception as e:
                self.logger.error(f"保存圖片時出錯: {str(e)}")
                continue

        # 保存 HTML
        try:
            html_content = parser.get_text_content()
            html_record = crawler_each_html(
                crawler_each_url_id=url_record.id,
                html=html_content
            )
            session.add(html_record)
        except Exception as e:
            self.logger.error(f"保存 HTML 時出錯: {str(e)}")

        # 保存安全信息
        try:
            security_info = {
                'headers': dict(headers),
                'meta_tags': parser.meta_tags
            }
            security_record = crawler_each_security(
                crawler_each_url_id=url_record.id,
                security=json.dumps(security_info, ensure_ascii=False)
            )
            session.add(security_record)
        except Exception as e:
            self.logger.error(f"保存安全信息時出錯: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Cloudflare 繞過工具')
    parser.add_argument('url', help='要訪問的 URL')
    parser.add_argument('--flaresolverr', default='http://localhost:8191/v1',
                      help='FlareSolverr 服務的 URL (默認: http://localhost:8191/v1)')
    args = parser.parse_args()

    try:
        bypass = CloudflareBypass(args.flaresolverr)
        response = bypass.make_request(args.url, args.url)
        
        if response:
            logger.info("[√] 成功繞過 Cloudflare")
            return 0
        else:
            logger.error("[×] 繞過失敗")
            return 1
            
    except Exception as e:
        logger.error(f"[×] 執行出錯: {str(e)}")
        return 1
    
if __name__ == "__main__":
    sys.exit(main()) 