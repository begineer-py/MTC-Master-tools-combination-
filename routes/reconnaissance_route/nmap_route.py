from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from instance.models import Target
from utils.permission import check_user_permission
from reconnaissance.threads.thread_nmap import nmap_ScanThread
import queue
from instance.models import nmap_Result
import requests
import json

nmap_route = Blueprint('nmap', __name__)

@nmap_route.route('/scan/<int:user_id>/<int:target_id>', methods=['POST'])
@login_required
def nmap_scan(user_id, target_id):
    # 檢查用戶權限
    target = Target.query.filter_by(id=target_id).first()
    if not target:
        return jsonify({
            'status': 'error',
            'message': '找不到指定的目標'
        }), 404
    
    client_ip = request.remote_addr
    current_app.logger.debug(f"用戶 {current_user.id} 正在訪問 nmap 路由，目標 ID: {target_id} {client_ip}")
    
    try:
        # 獲取掃描類型
        data = request.get_json()
        scan_type = data.get('scan_type', 'common') if data else 'common'
        
        # 創建並啟動掃描線程
        scan_thread = nmap_ScanThread(
            target_ip=target.target_ip_no_https,
            user_id=current_user.id,
            target_id=target_id,
            app=current_app,
            scan_type=scan_type
        )
        scan_thread.start()
        current_app.logger.debug(f"掃描線程已啟動，類型: {scan_type}")
        
        # 等待結果（最多等待6000秒）
        try:
            scan_result, success, code = scan_thread.get_result(timeout=6000)
            if not success:
                raise Exception(scan_result if isinstance(scan_result, str) else "掃描失敗")
            
            if not scan_result or not isinstance(scan_result, dict):
                raise Exception("無效的掃描結果")
            
            current_app.logger.debug(f"掃描已完成")
            return jsonify({
                'status': 'success',
                'message': '掃描完成',
                'result': scan_result,
                'code': code
            }), 200
            
        except queue.Empty:
            current_app.logger.error("掃描超時")
            return jsonify({
                'status': 'error',
                'message': '掃描超時，請稍後重試',
                'code': 408
            }), 408
        
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"Nmap scan error: {error_msg}")
        return jsonify({
            'status': 'error',
            'message': f'掃描過程中發生錯誤: {error_msg}',
            'code': 500
        }), 500

@nmap_route.route('/result/<int:user_id>/<int:target_id>', methods=['GET', 'POST'])
@login_required
def nmap_get_result(user_id, target_id):
    try:
        # 檢查用戶權限
        target = Target.query.filter_by(id=target_id).first()
        if not target:
            return jsonify({
                'status': 'error',
                'message': '找不到指定的目標'
            }), 404
        
        # 檢查是否已存在掃描結果
        existing_result = nmap_Result.query.filter_by(
            target_id=target_id,
        ).order_by(
            nmap_Result.scan_time.desc()
        ).first()
        
        if existing_result:
            return jsonify({
                'status': 'success',
                'data': existing_result.to_dict()
            })
        
        # 如果沒有結果，自動開始新的掃描
        response = requests.post(
            url_for('nmap.nmap_scan', user_id=user_id, target_id=target_id, _external=True),
            json={'scan_type': 'common'}
        )
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': '掃描完成'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '未找到掃描結果,自動掃描中'
            }), 302
        
    except Exception as e:
        current_app.logger.error(f"Error getting Nmap result: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'獲取掃描結果時發生錯誤: {str(e)}'
        }), 500
    

