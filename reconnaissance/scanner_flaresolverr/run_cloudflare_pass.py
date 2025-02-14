import logging
import sys
import requests
from instance.models import db, ParamSpiderResult, Target
from reconnaissance.threads.thread_flaresolverr import FlareSolverrThreadPool
from reconnaissance.threads.thread_paramspider import ParamSpiderThread, ParamSpiderThreadPool
from flask import current_app
from contextlib import contextmanager
import time

def setup_logging():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    handler.stream.reconfigure(encoding='utf-8')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

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

class CrawlerPass:
    def __init__(self, user_id, target_id, limit=1000):
        self.user_id = user_id
        self.target_id = target_id
        self.limit = limit
        self.app = current_app._get_current_object()
        self.thread_pool = FlareSolverrThreadPool(num_threads=5)
        self.paramspider_pool = ParamSpiderThreadPool(num_threads=5)

    def process_target(self, user_id, target_id):
        """處理目標 URL"""
        try:
            logger.info("\n" + "#" * 70)
            logger.info("開始目標掃描流程")
            logger.info("#" * 70 + "\n")
            
            # 使用应用上下文和会话管理
            with self.app.app_context():
                with session_scope() as session:
                    # 獲取目標信息
                    target = session.query(Target).get(self.target_id)
                    if not target:
                        logger.error(f"目標不存在: {self.target_id} ")
                        return False, "目標不存在"
                    
                    # 檢查是否已有 ParamSpider 結果
                    existing_results = self._get_paramspider_results(session)
                    
                    # 如果沒有現有結果，執行 ParamSpider 掃描
                    if not existing_results:
                        logger.info("[*] 未找到現有的 ParamSpider 結果，開始新的掃描")
                        logger.info("=" * 50)
                        
                        # 調用 ParamSpider API
                        try:
                            api_url = f"http://localhost:5000/user/{user_id}/paramspider/{target_id}"
                            headers = {'Content-Type': 'application/json'}
                            
                            logger.info(f"正在調用 ParamSpider API: {api_url}")
                            response = requests.post(api_url, headers=headers)
                            
                            if response.status_code == 200:
                                result = response.json()
                                if result.get('success'):
                                    logger.info("ParamSpider 掃描已成功啟動")
                                else:
                                    error_msg = result.get('message', '未知錯誤')
                                    logger.error(f"ParamSpider API 調用失敗: {error_msg}")
                                    return False, f"ParamSpider API 調用失敗: {error_msg}"
                            else:
                                logger.error(f"ParamSpider API 請求失敗，狀態碼: {response.status_code}")
                                return False, f"ParamSpider API 請求失敗，狀態碼: {response.status_code}"
                                
                            # 等待結果生成（可以添加輪詢機制）
                            max_retries = 10
                            retry_count = 0
                            while retry_count < max_retries:
                                paramspider_results = self._get_paramspider_results(session)
                                if paramspider_results:
                                    break
                                logger.info(f"等待 ParamSpider 結果... ({retry_count + 1}/{max_retries})")
                                time.sleep(5)  # 等待5秒後重試
                                retry_count += 1
                            
                            if not paramspider_results:
                                logger.error("等待 ParamSpider 結果超時")
                                return False, "等待 ParamSpider 結果超時"
                                
                        except requests.exceptions.RequestException as e:
                            logger.error(f"調用 ParamSpider API 時發生錯誤: {str(e)}")
                            return False, f"調用 ParamSpider API 時發生錯誤: {str(e)}"
                    else:
                        logger.info("[*] 找到現有的 ParamSpider 結果，直接使用")
                        paramspider_results = existing_results
                    
                    # 使用 FlareSolverr 處理 URL
                    logger.info("\n[*] 開始處理 ParamSpider 發現的 URL")
                    logger.info("\n" + "=" * 70)
                    
                    if paramspider_results:
                        logger.info(f"[*] 原始結果行數: {len(paramspider_results)}")
                        
                        # 限制處理的 URL 數量
                        urls_to_process = paramspider_results[:self.limit]
                        logger.info(f"[*] 將處理 {len(urls_to_process)} 個 URL")
                        logger.info("-" * 70)
                        
                        # 將所有 URL 添加到 FlareSolverr 線程池
                        for url in urls_to_process:
                            self.thread_pool.add_url(url)
                        
                        # 啟動 FlareSolverr 線程池並等待完成
                        self.thread_pool.start_threads(self.target_id)
                        self.thread_pool.wait_completion()
                    else:
                        logger.warning("[!] 未找到任何 URL 需要處理")
                    
                    logger.info("\n" + "#" * 70)
                    logger.info("目標掃描流程完成")
                    logger.info("#" * 70)
                    
                    return True, "掃描完成"
            
        except Exception as e:
            error_message = f"處理目標時出錯：{str(e)}"
            logger.error(error_message)
            return False, error_message

    def _get_paramspider_results(self, session):
        """獲取 ParamSpider 掃描結果"""
        try:
            # 使用传入的session进行查询
            result = session.query(ParamSpiderResult).filter_by(target_id=self.target_id).first()
            if not result:
                logger.info("未找到 ParamSpider 結果")
                return []
            
            result_text = result.result_text
            if not result_text:
                logger.info("ParamSpider 結果文本為空")
                return []
            
            # 將結果文本分割成行並過濾
            urls = []
            for line in result_text.splitlines():
                line = line.strip()
                if line.startswith('URL: '):
                    # 提取 URL 並去除 FUZZ 參數
                    url = line[5:].strip()  # 去除 "URL: " 前綴
                    # 去除 FUZZ 參數但保留參數名
                    url = url.replace('=FUZZ', '=').replace('?FUZZ', '?')
                    # 去除末尾的 = 符號
                    url = url.rstrip('=')
                    # 去除末尾的 ? 符號
                    url = url.rstrip('?')
                    urls.append(url)
            
            logger.info(f"從 ParamSpider 結果中提取了 {len(urls)} 個有效 URL")
            return urls
            
        except Exception as e:
            logger.error(f"獲取 ParamSpider 結果時出錯：{str(e)}")
            return []

def main(user_id, target_id):
    """主函數"""
    try:
        crawler = CrawlerPass(user_id, target_id)
        return crawler.process_target(user_id, target_id)
    except Exception as e:
        error_msg = f"執行過程出錯：{str(e)}"
        logger.error(error_msg)
        return False, error_msg


