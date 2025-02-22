import os
import sys
import json
import logging
import traceback
import subprocess
from datetime import datetime
from flask import current_app
from urllib.parse import urlparse, parse_qs
from .url_filter import URLFilter

# 添加 ParamSpider 到 Python 路徑
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)

from tools.ParamSpider.paramspider.main import fetch_and_clean_urls, setup_logging

class ParamSpiderScanner:
    def __init__(self, target_id, user_id, crawler_id, exclude='', threads=50):
        self.target_id = target_id
        self.user_id = user_id
        self.crawler_id = crawler_id
        self.exclude = exclude
        self.threads = threads
        self.app = current_app._get_current_object()
        self.batch_size = 1000
        self.url_filter = URLFilter()
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handler.stream.reconfigure(encoding='utf-8')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def _process_urls(self, urls, domain):
        """處理和過濾 URL"""
        try:
            # 使用 URL 過濾器處理 URL
            filtered_results = self.url_filter.process_urls(urls)
            
            # 獲取當前域名的 URL
            domain_urls = filtered_results.get(domain, set())
            
            # 生成結果文本
            result_text = self._generate_result_text(domain, urls, domain_urls)
            
            return {
                'total_urls': len(urls),
                'filtered_urls': len(domain_urls),
                'urls': list(domain_urls),
                'result_text': result_text
            }
            
        except Exception as e:
            self.logger.error(f"處理 URL 時出錯: {str(e)}")
            return None

    def _generate_result_text(self, domain: str, original_urls: list, filtered_urls: set) -> str:
        """生成結果文本，包含所有掃描信息"""
        try:
            result_text = f"""
掃描報告
{'='*50}
目標信息:
- 目標 ID: {self.target_id}
- 用戶 ID: {self.user_id}
- 爬蟲 ID: {self.crawler_id}
- 域名: {domain}

掃描統計:
- 總 URL 數: {len(original_urls)}
- 過濾後 URL 數: {len(filtered_urls)}
- 掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

過濾堆疊:
{'-'*50}
"""
            # 添加所有過濾後的 URL 和它們的過濾原因
            for url in sorted(filtered_urls):
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                _, reason = self.url_filter.filter_url(url)
                result_text += f"\nURL: {url}"
                result_text += f"\n保留原因: {reason}"
                if query_params:
                    result_text += "\n參數:"
                    for param, values in query_params.items():
                        result_text += f"\n  - {param}: {values[0] if values else ''}"
                result_text += "\n"

            # 添加過濾統計
            result_text += f"\n{'='*50}\n"
            result_text += "過濾統計詳情:\n"
            result_text += f"{'-'*50}\n"
            
            # 重新過濾所有原始 URL 以獲取統計
            filter_stats = {
                'total': len(original_urls),
                'kept': len(filtered_urls),
                'filtered': len(original_urls) - len(filtered_urls),
                'reasons': {}
            }
            
            for url in original_urls:
                if not url.strip():
                    filter_stats['reasons']['空URL'] = filter_stats['reasons'].get('空URL', 0) + 1
                    continue
                    
                try:
                    _, reason = self.url_filter.filter_url(url)
                    filter_stats['reasons'][reason] = filter_stats['reasons'].get(reason, 0) + 1
                except Exception as e:
                    filter_stats['reasons']['處理錯誤'] = filter_stats['reasons'].get('處理錯誤', 0) + 1

            result_text += f"總 URL: {filter_stats['total']}\n"
            result_text += f"保留 URL: {filter_stats['kept']}\n"
            result_text += f"過濾 URL: {filter_stats['filtered']}\n\n"
            result_text += "過濾原因統計:\n"
            for reason, count in filter_stats['reasons'].items():
                result_text += f"- {reason}: {count}\n"

            return result_text
            
        except Exception as e:
            self.logger.error(f"生成結果文本時出錯: {str(e)}")
            return f"生成結果文本時出錯: {str(e)}"

    def _extract_domain(self, url: str) -> str:
        """從 URL 中提取域名"""
        try:
            # 確保 URL 格式正確
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
                
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # 如果沒有獲取到域名，嘗試從原始 URL 中提取
            if not domain:
                # 移除協議前綴
                domain = url.replace('https://', '').replace('http://', '')
                # 獲取第一部分（域名部分）
                domain = domain.split('/')[0]
            
            if not domain:
                raise ValueError("無法從 URL 中提取域名")
                
            self.logger.info(f"提取到的域名: {domain}")
            return domain
            
        except Exception as e:
            self.logger.error(f"提取域名時出錯: {str(e)}")
            raise

    def scan(self, target_url):
        """執行 ParamSpider 掃描"""
        from models import ParamSpiderResult, db
        
        try:
            with self.app.app_context():
                try:
                    self.logger.debug("開始掃描流程")
                    
                    # 檢查目標 URL
                    if not target_url:
                        raise ValueError("目標 URL 不能為空")
                    
                    self.logger.debug(f"目標 URL: {target_url}")
                    
                    # 在同一個事務中處理刪除和插入
                    with db.session.begin_nested():
                        # 檢查並刪除現有記錄
                        existing_record = ParamSpiderResult.query.filter_by(
                            target_id=self.target_id
                        ).with_for_update().first()  # 添加行鎖
                        
                        if existing_record:
                            self.logger.info(f"發現目標 ID {self.target_id} 的現有記錄")
                            db.session.delete(existing_record)
                            self.logger.info("已刪除現有記錄")
                            db.session.flush()  # 確保刪除操作被執行
                    
                    # 創建新記錄
                    result_record = ParamSpiderResult(
                        target_id=self.target_id,
                        user_id=self.user_id,
                        crawler_id=self.crawler_id,
                        exclude=self.exclude,
                        threads=self.threads,
                        status='running'
                    )
                    db.session.add(result_record)
                    db.session.flush()

                    # 提取並驗證域名
                    try:
                        domain = self._extract_domain(target_url)
                    except Exception as e:
                        raise ValueError(f"無效的目標 URL: {str(e)}")

                    self.logger.info(f"開始掃描域名: {domain}")

                    # 執行 ParamSpider 掃描
                    urls = fetch_and_clean_urls(domain)
                    if urls is None or not urls:
                        self.logger.warning(f"未找到任何 URL，域名: {domain}")
                        urls = []
                    
                    self.logger.info(f"找到原始 URL 數量: {len(urls)}")
                    
                    # 處理和過濾 URL
                    result = self._process_urls(urls, domain)
                    if not result:
                        raise Exception("URL 處理失敗")

                    # 更新掃描結果
                    result_record.result_text = result['result_text']
                    result_record.total_urls = result['total_urls']
                    result_record.filtered_urls = result['filtered_urls']
                    result_record.status = 'completed'
                    result_record.scan_time = datetime.now()
                    
                    db.session.commit()
                    self.logger.info("掃描完成並保存結果")
                    
                    return {
                        'status': 'success',
                        'message': '掃描完成',
                        'data': {
                            'total_urls': result['total_urls'],
                            'filtered_urls': result['filtered_urls'],
                            'result_text': result['result_text']
                        }
                    }
                    
                except Exception as e:
                    db.session.rollback()
                    error_msg = f"掃描過程中出錯: {str(e)}"
                    self.logger.error(error_msg)
                    return {
                        'status': 'error',
                        'message': error_msg
                    }
        except Exception as e:
            error_msg = f"數據庫操作出錯: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            } 