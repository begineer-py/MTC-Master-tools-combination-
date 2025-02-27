import json
import logging
from datetime import datetime
from instance.models import db, HarvesterResult
import time

class HarvesterDBUpdater:
    """處理 theHarvester 結果的數據庫更新"""
    
    def __init__(self):
        self.logger = logging.getLogger('HarvesterDBUpdater')
        self.logger.setLevel(logging.INFO)
        
    def update_db_result(self, target_id, scan_data=None, error=None):
        """更新數據庫中的掃描結果，包含重試機制
        
        Args:
            target_id: 目標ID
            scan_data: 掃描結果數據（可選）
            error: 錯誤信息（可選）
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 開始新的事務
                db.session.begin_nested()
                
                # 查找現有結果或創建新結果
                result = HarvesterResult.query.filter_by(target_id=target_id).with_for_update().first()
                if not result:
                    result = HarvesterResult(target_id=target_id)
                    db.session.add(result)
                
                # 更新結果
                result.scan_time = datetime.now()
                
                if scan_data is not None:
                    result.status = 'completed'
                    # 確保列表數據被正確序列化
                    result.urls = json.dumps(scan_data['urls'])
                    result.emails = json.dumps(scan_data['emails'])
                    result.hosts = json.dumps(scan_data['hosts'])
                    result.direct_ips = json.dumps(scan_data['ips'])
                    result.asn_info = json.dumps(scan_data['asns'])
                    result.social_media = json.dumps(scan_data.get('linkedin', []))
                    result.dns_records = json.dumps(scan_data['dns_records'])
                    result.ip_ranges = json.dumps(scan_data['ip_ranges'])
                    result.reverse_dns = json.dumps(scan_data['reverse_dns'])
                    result.error = None
                else:
                    result.status = 'error'
                    result.error = error
                
                # 提交事務
                db.session.commit()
                self.logger.info(f"成功更新數據庫結果 (target_id: {target_id})")
                break  # 成功後退出循環
                
            except Exception as e:
                db.session.rollback()
                retry_count += 1
                if retry_count >= max_retries:
                    self.logger.error(f"更新數據庫結果失敗（重試{retry_count}次後）: {str(e)}")
                    raise
                else:
                    self.logger.warning(f"更新數據庫失敗，正在重試（第{retry_count}次）: {str(e)}")
                    time.sleep(1)  # 等待1秒後重試
