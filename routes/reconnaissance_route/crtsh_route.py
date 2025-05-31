from flask import Blueprint, request, jsonify, redirect, url_for, current_app, make_response
from instance.models import Target, db, crtsh_Result
from utils.permission import check_user_permission
from reconnaissance.threads.thread_crtsh import crtsh_scan_target
from datetime import datetime
import logging
import time

crtsh_route = Blueprint('crtsh', __name__)
logger = logging.getLogger(__name__)

@crtsh_route.route('/scan/<int:target_id>', methods=['POST','GET'])
def crtsh_scan(target_id):
    client_ip = request.remote_addr
    current_app.logger.debug(f"用戶正在訪問 crtsh 路由，目標 ID: {target_id} {client_ip}")
    
    try:
        # 获取目标信息
        target = Target.query.get_or_404(target_id)
        
        # 檢查是否已存在掃描結果
        existing_result = crtsh_Result.query.filter_by(
            target_id=target_id,
        ).first()
        
        if existing_result:
            # 如果存在舊的結果，先刪除
            try:
                db.session.delete(existing_result)
                db.session.commit()
                current_app.logger.info(f"已刪除舊的掃描結果: target_id={target_id}")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"刪除舊結果時發生錯誤: {str(e)}")
                
        # 執行掃描
        domains, success, message = crtsh_scan_target(target.domain, target_id)
        
        # 記錄域名數量
        current_app.logger.info(f"掃描完成，找到 {len(domains)} 個域名")
        
        # 驗證掃描結果
        if not isinstance(domains, list):
            current_app.logger.error("掃描結果格式無效：domains 不是列表類型")
            return jsonify({
                'status': 'error',
                'message': '掃描結果格式無效',
                'result': {
                    'domains': [],
                    'total': 0,
                    'scan_time': None,
                    'error_message': '返回的域名列表格式無效'
                },
                'code': 400
            }), 400
        
        # 創建新的掃描結果記錄
        scan_time = datetime.now()
        result = crtsh_Result(
            target_id=target_id,
            domains=domains,  # 這裡直接存儲域名列表
            total_domains=len(domains),  # 記錄總數
            status='success' if success else 'failed',
            error_message=None if success else message,
            scan_time=scan_time  # 記錄掃描時間
        )
        
        # 使用重試機制保存到數據庫
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                db.session.add(result)
                db.session.commit()
                current_app.logger.info(f"成功保存掃描結果到數據庫，包含 {len(domains)} 個域名")
                break
            except Exception as e:
                db.session.rollback()
                retry_count += 1
                if retry_count == max_retries:
                    current_app.logger.error(f"保存到數據庫失敗，已重試 {max_retries} 次: {str(e)}")
                    raise
                current_app.logger.warning(f"保存到數據庫時發生錯誤，正在重試 ({retry_count}/{max_retries}): {str(e)}")
                time.sleep(1)  # 等待1秒後重試
        
        # 返回響應
        response_data = {
            'status': 'success' if success else 'error',
            'message': '掃描完成' if success else message,
            'result': {
                'domains': domains,
                'total': len(domains),
                'scan_time': scan_time.timestamp(),
                'error_message': None if success else message
            },
            'code': 200 if success else 500
        }
        
        return jsonify(response_data), 200 if success else 500
    
    except Exception as e:
        # 記錄異常
        current_app.logger.exception(f"執行 crt.sh 掃描時發生錯誤: {str(e)}")
        
        # 返回錯誤響應
        return jsonify({
            'status': 'error',
            'message': f'執行掃描時發生錯誤: {str(e)}',
            'result': {
                'domains': [],
                'total': 0,
                'scan_time': None,
                'error_message': str(e)
            },
            'code': 500
        }), 500

@crtsh_route.route('/result/<int:target_id>', methods=['GET'])
def get_latest_crtsh_result(target_id):
    """獲取最新的 crt.sh 掃描結果"""
    try:
        # 获取目标信息
        target = Target.query.get_or_404(target_id)
        
        # 查詢數據庫獲取最新結果
        result = crtsh_Result.query.filter_by(target_id=target_id).order_by(crtsh_Result.scan_time.desc()).first()
        
        if not result:
            # 如果沒有結果，重定向到掃描頁面
            return redirect(url_for('crtsh.crtsh_scan', target_id=target_id))
        
        # 返回結果
        return jsonify({
            'status': 'success',
            'message': '獲取結果成功',
            'result': result.to_dict(),
            'code': 200
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'code': 500
        }), 500

@crtsh_route.route('/download/<int:target_id>', methods=['GET'])
def download_crtsh_result(target_id):
    """下載 crt.sh 掃描結果為文本文件"""
    try:
        # 獲取目標信息
        target = Target.query.get_or_404(target_id)
        
        # 查詢數據庫獲取最新結果
        result = crtsh_Result.query.filter_by(target_id=target_id).order_by(crtsh_Result.scan_time.desc()).first()
        
        if not result or not result.domains:
            return jsonify({
                'status': 'error',
                'message': '沒有可用的掃描結果',
                'code': 404
            }), 404
        
        # 生成文本內容
        domains = result.domains
        content = f"# crt.sh 子域名掃描結果\n"
        content += f"# 目標: {target.domain}\n"
        content += f"# 掃描時間: {result.scan_time}\n"
        content += f"# 總域名數: {len(domains)}\n\n"
        
        # 添加每個域名
        for i, domain in enumerate(domains, 1):
            content += f"{i}. {domain}\n"
        
        # 創建響應對象
        response = make_response(content)
        response.headers["Content-Disposition"] = f"attachment; filename=crtsh_results_{target.domain}_{int(time.time())}.txt"
        response.headers["Content-Type"] = "text/plain"
        
        return response
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'code': 500
        }), 500
        

