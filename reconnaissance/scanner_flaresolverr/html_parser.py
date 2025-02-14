import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
import sys
def setup_logging():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    handler.stream.reconfigure(encoding='utf-8')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
logger = setup_logging()
class HtmlParser:
    """HTML 解析器類，用於解析網頁內容並提取有用信息"""
    
    def __init__(self, base_url: str):
        """
        初始化 HTML 解析器
        
        Args:
            base_url: 基礎 URL，用於解析相對路徑
        """
        self.base_url = base_url
        self.soup = None
        self.forms = []
        self.links = []
        self.images = []
        self.scripts = []
        self.styles = []
        self.meta_tags = []
        
    def parse(self, html_content: str) -> None:
        """
        解析 HTML 內容
        
        Args:
            html_content: HTML 字符串
        """
        try:
            self.soup = BeautifulSoup(html_content, 'html.parser')
            self._parse_forms()
            self._parse_links()
            self._parse_images()
            self._parse_scripts()
            self._parse_styles()
            self._parse_meta_tags()
        except Exception as e:
            logger.error(f"解析 HTML 時發生錯誤: {str(e)}")
            raise
            
    def _normalize_url(self, url: str) -> Optional[str]:
        """
        標準化 URL
        
        Args:
            url: 原始 URL
            
        Returns:
            標準化後的 URL 或 None
        """
        if not url:
            return None
            
        try:
            # 處理相對路徑
            normalized_url = urljoin(self.base_url, url)
            parsed = urlparse(normalized_url)
            return normalized_url if parsed.scheme and parsed.netloc else None
        except Exception as e:
            logger.error(f"URL 標準化失敗: {str(e)}")
            return None
            
    def _parse_forms(self) -> None:
        """解析表單，包括傳統表單和模擬表單"""
        try:
            forms = []
            
            # 1. 解析傳統 form 標籤
            for form in self.soup.find_all('form'):
                form_data = self._extract_form_data(form)
                if form_data:
                    forms.append(form_data)
            
            # 2. 解析可能的模擬表單
            for div in self.soup.find_all(['div', 'section'], class_=lambda x: x and ('form' in x.lower() or 'login' in x.lower())):
                form_data = self._extract_simulated_form_data(div)
                if form_data:
                    forms.append(form_data)
                
            # 3. 檢查 iframe
            for iframe in self.soup.find_all('iframe'):
                iframe_src = self._normalize_url(iframe.get('src', ''))
                if iframe_src:
                    form_data = {
                        'method': 'GET',  # 默認值
                        'action': iframe_src,
                        'id': iframe.get('id', ''),
                        'class': 'iframe-form',
                        'is_iframe': True,
                        'inputs': []
                    }
                    forms.append(form_data)
            
            self.forms = forms
            
        except Exception as e:
            logger.error(f"解析表單時發生錯誤: {str(e)}")
            self.forms = []

    def _extract_form_data(self, form_element) -> dict:
        """從表單元素中提取數據"""
        form_data = {
            'method': form_element.get('method', 'GET').upper(),
            'action': self._normalize_url(form_element.get('action', '')),
            'id': form_element.get('id', ''),
            'class': ' '.join(form_element.get('class', [])) if form_element.get('class') else '',
            'enctype': form_element.get('enctype', 'application/x-www-form-urlencoded'),
            'inputs': []
        }
        
        # 解析輸入字段
        for input_tag in form_element.find_all(['input', 'textarea', 'select', 'button']):
            input_data = {
                'name': input_tag.get('name', ''),
                'type': input_tag.get('type', 'text'),
                'required': input_tag.get('required') is not None,
                'value': input_tag.get('value', ''),
                'placeholder': input_tag.get('placeholder', ''),
                'id': input_tag.get('id', ''),
                'class': ' '.join(input_tag.get('class', [])) if input_tag.get('class') else ''
            }
            form_data['inputs'].append(input_data)
        
        return form_data if form_data['inputs'] else None

    def _extract_simulated_form_data(self, element) -> dict:
        """從模擬表單元素中提取數據"""
        # 檢查是否包含登入相關的關鍵字
        text_content = element.get_text().lower()
        if not any(keyword in text_content for keyword in ['login', 'sign in', 'username', 'password', 'email']):
            return None
        
        form_data = {
            'method': 'POST',  # 模擬表單通常使用 POST
            'action': self._normalize_url(element.get('data-action', '')),
            'id': element.get('id', ''),
            'class': ' '.join(element.get('class', [])) if element.get('class') else '',
            'is_simulated': True,
            'inputs': []
        }
        
        # 解析可能的輸入字段
        input_elements = element.find_all(['input', 'textarea', 'select', 'button', 'div', 'span'], 
                                        class_=lambda x: x and ('input' in x.lower() or 'field' in x.lower()))
        
        for input_element in input_elements:
            input_data = {
                'name': input_element.get('name', '') or input_element.get('data-name', ''),
                'type': input_element.get('type', 'text'),
                'required': input_element.get('required') is not None or input_element.get('aria-required') == 'true',
                'value': input_element.get('value', ''),
                'placeholder': input_element.get('placeholder', ''),
                'id': input_element.get('id', ''),
                'class': ' '.join(input_element.get('class', [])) if input_element.get('class') else ''
            }
            form_data['inputs'].append(input_data)
        
        return form_data if form_data['inputs'] else None
            
    def _parse_links(self) -> None:
        """解析鏈接"""
        try:
            for link in self.soup.find_all(['a', 'link']):
                href = self._normalize_url(link.get('href'))
                if href:
                    link_data = {
                        'url': href,
                        'text': link.get_text(strip=True),
                        'title': link.get('title', ''),
                        'rel': link.get('rel', []),
                        'type': 'link' if link.name == 'a' else 'resource'
                    }
                    self.links.append(link_data)
        except Exception as e:
            logger.error(f"解析鏈接時發生錯誤: {str(e)}")
            
    def _parse_images(self) -> None:
        """解析圖片"""
        try:
            for img in self.soup.find_all(['img', 'source', 'picture']):
                src = self._normalize_url(img.get('src') or img.get('data-src'))
                if src:
                    image_data = {
                        'url': src,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'width': img.get('width', ''),
                        'height': img.get('height', '')
                    }
                    self.images.append(image_data)
        except Exception as e:
            logger.error(f"解析圖片時發生錯誤: {str(e)}")
            
    def _parse_scripts(self) -> None:
        """解析腳本"""
        try:
            for script in self.soup.find_all('script'):
                script_data = {
                    'type': script.get('type', 'text/javascript'),
                    'async': script.get('async') is not None,
                    'defer': script.get('defer') is not None
                }
                
                # 處理外部腳本
                if script.get('src'):
                    script_data['url'] = self._normalize_url(script['src'])
                # 處理內聯腳本
                elif script.string:
                    script_data['content'] = script.string.strip()
                
                self.scripts.append(script_data)
                
        except Exception as e:
            logger.error(f"解析腳本時發生錯誤: {str(e)}")
            
    def _parse_styles(self) -> None:
        """解析樣式表"""
        try:
            # 外部樣式表
            for style in self.soup.find_all('link', rel='stylesheet'):
                href = self._normalize_url(style.get('href'))
                if href:
                    style_data = {
                        'url': href,
                        'media': style.get('media', 'all'),
                        'type': style.get('type', 'text/css')
                    }
                    self.styles.append(style_data)
            
            # 內聯樣式
            for style in self.soup.find_all('style'):
                if style.string:
                    style_data = {
                        'content': style.string.strip(),
                        'media': style.get('media', 'all'),
                        'type': style.get('type', 'text/css')
                    }
                    self.styles.append(style_data)
                    
        except Exception as e:
            logger.error(f"解析樣式表時發生錯誤: {str(e)}")
            
    def _parse_meta_tags(self) -> None:
        """解析元標籤"""
        try:
            for meta in self.soup.find_all('meta'):
                meta_data = {
                    'name': meta.get('name', ''),
                    'content': meta.get('content', ''),
                    'property': meta.get('property', ''),
                    'charset': meta.get('charset', '')
                }
                self.meta_tags.append(meta_data)
        except Exception as e:
            logger.error(f"解析元標籤時發生錯誤: {str(e)}")
            
    def get_title(self) -> str:
        """獲取頁面標題"""
        try:
            title_tag = self.soup.find('title')
            return title_tag.get_text(strip=True) if title_tag else ''
        except Exception as e:
            logger.error(f"獲取標題時發生錯誤: {str(e)}")
            return ''
            
    def get_text_content(self) -> str:
        """獲取頁面純文本內容"""
        try:
            return self.soup.get_text(strip=True)
        except Exception as e:
            logger.error(f"獲取文本內容時發生錯誤: {str(e)}")
            return ''
            
    def get_summary(self) -> Dict[str, Any]:
        """獲取解析摘要"""
        return {
            'title': self.get_title(),
            'forms_count': len(self.forms),
            'links_count': len(self.links),
            'images_count': len(self.images),
            'scripts_count': len(self.scripts),
            'styles_count': len(self.styles),
            'meta_tags_count': len(self.meta_tags)
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """將所有解析結果轉換為字典格式"""
        forms_data = []
        for form in self.forms:
            form_data = {
                'action': self._normalize_url(form.get('action', '')),
                'method': form.get('method', 'GET').upper(),
                'inputs': []
            }
            
            # 解析表單輸入字段
            for input_tag in form.find_all(['input', 'textarea', 'select']):
                input_data = {
                    'name': input_tag.get('name', ''),
                    'type': input_tag.get('type', 'text'),
                    'required': input_tag.get('required') is not None,
                    'value': input_tag.get('value', '')
                }
                form_data['inputs'].append(input_data)
                
            forms_data.append(form_data)
            
        return {
            'title': self.get_title(),
            'forms': forms_data,
            'links': self.links,
            'images': self.images,
            'scripts': self.scripts,
            'styles': self.styles,
            'meta_tags': self.meta_tags
        }

    def get_forms(self):
        """獲取所有表單"""
        return self.forms if self.forms else []

    def get_javascript_files(self):
        """獲取所有 JavaScript 文件的 URL"""
        js_files = []
        for script in self.scripts:
            if 'url' in script:
                js_files.append(script['url'])
        return js_files

    def get_images(self):
        """獲取所有圖片的 URL"""
        image_urls = []
        for image in self.images:
            if 'url' in image:
                image_urls.append(image['url'])
        return image_urls 