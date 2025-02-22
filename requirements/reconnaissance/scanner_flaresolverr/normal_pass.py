import requests
from datetime import datetime, UTC
from instance.models import db, Target, crawler, crawler_html, crawler_js, crawler_resource, crawler_form
from urllib.parse import urlparse, urljoin
import logging
import json
import random
import os
from reconnaissance.scanner_flaresolverr.html_parser import HtmlParser

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_user_agents():
    """加載 User-Agent 列表"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ua_file = os.path.join(current_dir, 'user_agent.txt')
        with open(ua_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"加載 User-Agent 文件時出錯：{str(e)}")
        return ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36']

def get_random_user_agent():
    """獲取隨機 User-Agent"""
    user_agents = load_user_agents()
    return random.choice(user_agents)

def fetch_js_content(url, base_url=None):
    """獲取 JS 文件內容"""
    try:
        if not url.startswith(('http://', 'https://')):
            if base_url:
                url = urljoin(base_url, url)
            else:
                logger.error(f"無法解析相對路徑 JS URL: {url}")
                return None

        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        # 檢查內容類型
        content_type = response.headers.get('content-type', '').lower()
        if 'javascript' in content_type or url.endswith(('.js', '.jsx')):
            logger.info(f"[+] 成功獲取 JS 內容：{url}")
            return response.text
        else:
            # 如果內容類型不匹配但 URL 以 .js 結尾，仍然返回內容
            if url.endswith(('.js', '.jsx')):
                logger.warning(f"[!] URL 內容類型不匹配但仍返回內容：{url} (Content-Type: {content_type})")
                return response.text
            logger.warning(f"[!] URL 返回非 JavaScript 內容：{url} (Content-Type: {content_type})")
            return None

    except Exception as e:
        logger.error(f"獲取 JS 內容時出錯：{str(e)}")
        return None

def analyze_form(form, base_url):
    """分析表單詳細信息"""
    form_data = {
        'action': normalize_url(form.get('action', ''), base_url),
        'method': form.get('method', 'GET').upper(),
        'id': form.get('id', ''),
        'name': form.get('name', ''),
        'class': ' '.join(form.get('class', [])),
        'enctype': form.get('enctype', 'application/x-www-form-urlencoded'),
        'inputs': [],
        'buttons': [],
        'selects': [],
        'textareas': []
    }

    # 分析輸入字段
    for input_tag in form.find_all('input'):
        input_data = {
            'name': input_tag.get('name', ''),
            'type': input_tag.get('type', 'text'),
            'id': input_tag.get('id', ''),
            'class': ' '.join(input_tag.get('class', [])),
            'value': input_tag.get('value', ''),
            'placeholder': input_tag.get('placeholder', ''),
            'required': input_tag.get('required') is not None,
            'pattern': input_tag.get('pattern', ''),
            'maxlength': input_tag.get('maxlength', ''),
            'minlength': input_tag.get('minlength', '')
        }
        form_data['inputs'].append(input_data)

    # 分析按鈕
    for button in form.find_all('button'):
        button_data = {
            'type': button.get('type', 'submit'),
            'name': button.get('name', ''),
            'id': button.get('id', ''),
            'class': ' '.join(button.get('class', [])),
            'text': button.get_text(strip=True)
        }
        form_data['buttons'].append(button_data)

    # 分析選擇框
    for select in form.find_all('select'):
        select_data = {
            'name': select.get('name', ''),
            'id': select.get('id', ''),
            'class': ' '.join(select.get('class', [])),
            'required': select.get('required') is not None,
            'options': []
        }
        for option in select.find_all('option'):
            option_data = {
                'value': option.get('value', ''),
                'text': option.get_text(strip=True),
                'selected': option.get('selected') is not None
            }
            select_data['options'].append(option_data)
        form_data['selects'].append(select_data)

    # 分析文本區域
    for textarea in form.find_all('textarea'):
        textarea_data = {
            'name': textarea.get('name', ''),
            'id': textarea.get('id', ''),
            'class': ' '.join(textarea.get('class', [])),
            'placeholder': textarea.get('placeholder', ''),
            'required': textarea.get('required') is not None,
            'rows': textarea.get('rows', ''),
            'cols': textarea.get('cols', ''),
            'maxlength': textarea.get('maxlength', ''),
            'minlength': textarea.get('minlength', ''),
            'value': textarea.get_text(strip=True)
        }
        form_data['textareas'].append(textarea_data)

    return form_data

def normalize_url(url, base_url):
    """標準化 URL"""
    if not url:
        return base_url
    if url.startswith('//'):
        return f'https:{url}'
    if url.startswith('/'):
        parsed_base = urlparse(base_url)
        return f'{parsed_base.scheme}://{parsed_base.netloc}{url}'
    if not url.startswith(('http://', 'https://')):
        return urljoin(base_url, url)
    return url

def scan_normal_website(url, target_id):
    """掃描普通網站的入口函數"""
    try:
        # 創建爬蟲記錄
        crawl = crawler(target_id=target_id)
        db.session.add(crawl)
        db.session.commit()
        
        # 準備請求頭
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 發送請求
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        # 使用 HTML 解析器
        parser = HtmlParser(base_url=url)
        parser.parse(response.text)
        
        # 開始事務
        with db.session.begin_nested():
            # 保存 HTML 內容
            html_record = crawler_html(
                crawler_id=crawl.id,
                html_content=response.text,
                html_url=url
            )
            db.session.add(html_record)
            db.session.flush()
            logger.info(f"[+] 成功保存 HTML 記錄 (ID: {html_record.id})")
            
            # 保存表單
            for form in parser.forms:
                form_data = analyze_form(form, url)
                form_record = crawler_form(
                    crawler_id=crawl.id,
                    form_data=json.dumps(form_data),
                    form_type=form_data['method'],
                    form_url=form_data['action']
                )
                db.session.add(form_record)
                logger.info(f"[+] 成功保存表單數據")
            
            # 保存 JS 文件
            for script in parser.scripts:
                try:
                    if script.get('url'):
                        js_content = fetch_js_content(script['url'], url)
                        if js_content:
                            logger.info(f"[+] 成功獲取 JS 內容：{script['url']}")
                            js_record = crawler_js(
                                crawler_id=crawl.id,
                                js_content=js_content,
                                js_url=script['url']
                            )
                            db.session.add(js_record)
                        else:
                            logger.warning(f"[!] 無法獲取 JS 內容：{script['url']}")
                    elif script.get('content'):
                        js_record = crawler_js(
                            crawler_id=crawl.id,
                            js_content=script['content'],
                            js_url=url + "#inline-js"
                        )
                        db.session.add(js_record)
                except Exception as e:
                    logger.error(f"處理 JS 內容時出錯：{str(e)}")
                    continue
            
            # 保存其他資源
            for resource in parser.styles + parser.images:
                try:
                    resource_type = 'css' if resource in parser.styles else 'image'
                    resource_record = crawler_resource(
                        crawler_id=crawl.id,
                        resource_url=resource.get('url', ''),
                        resource_type=resource_type,
                        resource_data=json.dumps(resource)
                    )
                    db.session.add(resource_record)
                except Exception as e:
                    logger.error(f"保存資源時出錯：{str(e)}")
                    continue
        
        # 提交事務
        db.session.commit()
        logger.info(f"成功掃描網站 {url}")
        return True, "掃描完成"
        
    except requests.exceptions.RequestException as e:
        error_message = f"請求錯誤：{str(e)}"
        logger.error(error_message)
        if crawl:
            crawl.error_message = error_message
            crawl.completed_at = datetime.now(UTC)
            db.session.commit()
        return False, error_message
        
    except Exception as e:
        error_message = f"掃描過程出錯：{str(e)}"
        logger.error(error_message)
        if crawl:
            crawl.error_message = error_message
            crawl.completed_at = datetime.now(UTC)
            db.session.commit()
        return False, error_message

def main(url, user_id=None):
    """主函數"""
    try:
        # 檢查 URL 格式
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        # 解析域名
        domain = urlparse(url).netloc
        if not domain:
            return False, "無效的 URL 格式"
            
        # 查找目標
        target = Target.query.filter_by(target_ip=url).first()
        if not target:
            logger.error(f"找不到目標：{url}")
            return False, "目標不存在"
            
        # 執行掃描
        return scan_normal_website(url, target.id)
        
    except Exception as e:
        error_message = f"執行過程出錯：{str(e)}"
        logger.error(error_message)
        return False, error_message
