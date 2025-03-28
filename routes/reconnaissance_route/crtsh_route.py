from flask import Blueprint, request, jsonify, redirect, url_for, current_app, make_response
from flask_login import login_required
from instance.models import Target, db, crtsh_Result
from utils.permission import check_user_permission
from reconnaissance.threads.thread_crtsh import crtsh_scan_target
from datetime import datetime
import logging
import time

crtsh_route = Blueprint('crtsh', __name__)
logger = logging.getLogger(__name__)

@crtsh_route.route('/scan/<int:user_id>/<int:target_id>', methods=['POST','GET'])
@login_required
def crtsh_scan(user_id, target_id):
    client_ip = request.remote_addr
    current_app.logger.debug(f"用戶 {user_id} 正在訪問 crtsh 路由，目標 ID: {target_id} {client_ip}")
    
    # 檢查用戶權限
    permission_result = check_user_permission(user_id, target_id)
    if not isinstance(permission_result, Target):
        return permission_result
    if not isinstance(permission_result, Target):
        return redirect(url_for('index.login'))
    target = permission_result
    
    try:
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
        domains, success, message = crtsh_scan_target(target.target_ip_no_https, target_id)
        
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
                'error_message': message if not success else None
            },
            'code': 200 if success else 400
        }
        
        return jsonify(response_data), 200 if success else 400
        
    except Exception as e:
        current_app.logger.error(f"crtsh 掃描過程中發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'掃描過程中發生錯誤: {str(e)}',
            'code': 500
        }), 500 
@crtsh_route.route('/result/<int:user_id>/<int:target_id>', methods=['GET'])
@login_required
def get_latest_crtsh_result(user_id, target_id):
    """獲取最新的 crtsh 掃描結果"""
    try:
        result = crtsh_Result.query.filter_by(
            target_id=target_id,
        ).order_by(
            crtsh_Result.scan_time.desc()
        ).first()

        if result:
            return jsonify({
                'status': 'success',
                'message': '掃描結果獲取成功',
                'result': result.to_dict()
            }), 200
        else:
            # 如果沒有掃描結果，返回302重定向到掃描頁面
            return redirect(url_for('crtsh.crtsh_scan', user_id=user_id, target_id=target_id))
        
    except Exception as e:
        current_app.logger.error(f"獲取 crtsh 掃描結果時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'獲取掃描結果時發生錯誤: {str(e)}',
            'code': 500
        }), 500
@crtsh_route.route('/download/<int:user_id>/<int:target_id>', methods=['GET'])
@login_required
def download_crtsh_result(user_id, target_id):
    """下載 crtsh 掃描結果"""
    try:
        # 檢查用戶權限
        permission_result = check_user_permission(user_id, target_id)
        if not isinstance(permission_result, Target):
            return permission_result
        if not isinstance(permission_result, Target):
            return redirect(url_for('index.login'))
        target = permission_result
        
        # 從資料庫中獲取最新的掃描結果
        result = crtsh_Result.query.filter_by(
            target_id=target_id,
        ).order_by(
            crtsh_Result.scan_time.desc()
        ).first()
        
        if not result:
            return jsonify({
                'status': 'error',
                'message': '找不到掃描結果',
                'code': 404
            }), 404
            
        # 檢查域名列表是否存在
        if not result.domains:
            return jsonify({
                'status': 'error',
                'message': '掃描結果為空',
                'code': 404
            }), 404
            
        # 將域名列表轉換為文本格式
        domains_text = '\n'.join(result.domains)
        
        # 創建響應
        filename = f'crtsh_result_{target_id}.txt'
        response = make_response(domains_text)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"下載 crtsh 掃描結果時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'下載失敗: {str(e)}',
            'code': 500
        }), 500
        

