import logging
import subprocess
from datetime import datetime
from contextlib import contextmanager
from flask import current_app
from instance.models import db, gau_results
import os

def setup_logging():
    """設置日誌記錄"""
    logger = logging.getLogger('CloudflareHarvester')
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

@contextmanager
def session_scope():
    """提供資料庫會話上下文"""
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        logger.error(f"資料庫操作錯誤: {str(e)}")
        db.session.rollback()
        raise
    finally:
        db.session.close()

class CloudflareHarvester:
    """Cloudflare Harvester API 訪問類"""
    
    def __init__(self, user_id, target_id, limit=1000):
        self.user_id = user_id
        self.target_id = target_id
        self.limit = limit
        self.harvester_path = os.path.join(os.getcwd(), 'tools', 'theHarvester')
        
    def call_harvester_api(self, target_domain):
        """調用 theHarvester
        
        Args:
            target_domain: 目標域名
            
        Returns:
            dict: API 響應結果
        """
        try:
            # 檢查 theHarvester 目錄是否存在
            if not os.path.exists(self.harvester_path):
                # 如果不存在，克隆倉庫
                clone_cmd = f"git clone https://github.com/laramies/theHarvester.git {self.harvester_path}"
                subprocess.run(clone_cmd, shell=True, check=True)
                
                # 安裝依賴
                install_cmd = f"pip install -r {os.path.join(self.harvester_path, 'requirements.txt')}"
                subprocess.run(install_cmd, shell=True, check=True)
            
            # 構建命令
            harvester_script = os.path.join(self.harvester_path, 'theHarvester.py')
            cmd = [
                'python',
                harvester_script,
                '-d', target_domain,
                '-l', str(self.limit),
                '-b', 'all',
                '-f', 'json_results'
            ]
            
            logger.info(f"正在執行 theHarvester: {' '.join(cmd)}")
            
            # 執行命令
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if process.returncode != 0:
                error_msg = f"theHarvester 執行失敗: {process.stderr}"
                logger.error(error_msg)
                return {'status': 'error', 'error': error_msg}
            
            # 讀取結果文件
            result_file = os.path.join(self.harvester_path, 'json_results')
            if os.path.exists(result_file):
                with open(result_file, 'r', encoding='utf-8') as f:
                    result_data = f.read()
                os.remove(result_file)  # 清理結果文件
                
                return {
                    'status': 'success',
                    'result': {
                        'ips': [],
                        'hosts': [],
                        'emails': [],
                        'urls': [],
                        'raw_data': result_data
                    }
                }
            else:
                return {'status': 'error', 'error': '未找到結果文件'}
                
        except subprocess.CalledProcessError as e:
            error_msg = f"命令執行錯誤: {str(e)}"
            logger.error(error_msg)
            return {'status': 'error', 'error': error_msg}
        except Exception as e:
            error_msg = f"執行過程出錯: {str(e)}"
            logger.error(error_msg)
            return {'status': 'error', 'error': error_msg}
        
    def process_target(self, user_id, target_id):
        """處理目標掃描
        
        Args:
            user_id: 用戶ID
            target_id: 目標ID
            
        Returns:
            tuple: (success, message)
        """
        try:
            logger.info("\n" + "#" * 70)
            logger.info("開始目標掃描流程")
            logger.info("#" * 70)
            
            with session_scope() as session:
                # 檢查現有結果
                existing_result = session.query(gau_results).filter_by(
                    target_id=target_id
                ).first()
                
                if existing_result:
                    logger.info(f"找到現有掃描結果，狀態: {existing_result.status}")
                    if existing_result.status == 'running':
                        return True, "掃描正在進行中"
                    
                # 更新或創建新的掃描結果
                if not existing_result:
                    existing_result = gau_results(target_id=target_id)
                    session.add(existing_result)
                
                existing_result.status = 'running'
                existing_result.scan_time = datetime.now()
                session.commit()
                
                try:
                    # 調用 theHarvester
                    scan_result = self.call_harvester_api(
                        target_domain=existing_result.target.target_ip_no_https
                    )
                    
                    if scan_result.get('status') == 'success':
                        # 更新掃描結果
                        existing_result.status = 'completed'
                        result_data = scan_result.get('result', {})
                        existing_result.direct_ips = result_data.get('ips', [])
                        existing_result.subdomains = result_data.get('hosts', [])
                        existing_result.emails = result_data.get('emails', [])
                        existing_result.urls = result_data.get('urls', [])
                        session.commit()
                        
                        logger.info("掃描完成並保存結果")
                        return True, "掃描完成"
                    else:
                        error_msg = scan_result.get('error', '未知錯誤')
                        existing_result.status = 'error'
                        existing_result.error = error_msg
                        session.commit()
                        return False, f"掃描失敗: {error_msg}"
                        
                except Exception as e:
                    error_msg = f"掃描過程出錯: {str(e)}"
                    logger.error(error_msg)
                    existing_result.status = 'error'
                    existing_result.error = error_msg
                    session.commit()
                    return False, error_msg
                    
        except Exception as e:
            error_msg = f"處理目標時出錯: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

def main(user_id, target_id):
    """主函數"""
    try:
        harvester = CloudflareHarvester(user_id, target_id)
        return harvester.process_target(user_id, target_id)
    except Exception as e:
        error_msg = f"執行過程出錯：{str(e)}"
        logger.error(error_msg)
        return False, error_msg


