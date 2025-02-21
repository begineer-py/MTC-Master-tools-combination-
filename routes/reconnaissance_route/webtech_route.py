from flask import Blueprint, request, jsonify, redirect, url_for, current_app, make_response
from flask_login import login_required, current_user
from instance.models import Target, webtech_Result, db
from utils.permission import check_user_permission
from reconnaissance.threads.thread_webtech import WebTechScanThread
from utils.file_change.file_converter_webtech import ScanResultConverter
import logging
import json
import requests
webtech_route = Blueprint('webtech', __name__)
logger = logging.getLogger(__name__)

@webtech_route.route('/scan/<int:user_id>/<int:target_id>', methods=['GET', 'POST'])
@login_required
def webtech_scan(user_id, target_id):
    try:
        current_app.logger.debug(f"用戶 {current_user.id} 正在訪問 webtech 路由，目標 ID: {target_id} {request.remote_addr}")
        
        # 如果是 GET 請求，檢查是否有現有結果
        if request.method == 'GET':
            result = webtech_Result.query.filter_by(target_id=target_id).order_by(webtech_Result.scan_time.desc()).first()
            if result:
                return jsonify({
                    'status': 'success',
                    'message': '掃描結果獲取成功',
                    'result': result.to_dict()
                }), 200
        
        target = Target.query.filter_by(id=target_id).first()
        if not target:
            return jsonify({
                'status': 'error',
                'message': '找不到指定的目標'
            }), 404
            
        # 创建扫描线程
        scan_thread = WebTechScanThread(
            app=current_app,
            target_ip=target.target_ip_no_https,
            target_id=target_id
        )
        
        # 启动扫描會自動調用run方法
        scan_thread.start()
        current_app.logger.debug("掃描線程已啟動")
        
        # 等待结果
        result, success, code = scan_thread.get_result(timeout=300)
        current_app.logger.debug("掃描已完成")
        
        if success and isinstance(result, dict):
            try:
                # 檢查是否已存在結果
                existing_result = webtech_Result.query.filter_by(
                    target_id=target_id,
                ).first()
                
                if existing_result:
                    # 如果存在，更新結果
                    existing_result.webtech_result = json.dumps(result)
                    existing_result.web_tech = ','.join([tech['name'] for tech in result.get('technologies', [])])
                else:
                    # 如果不存在，創建新記錄
                    new_result = webtech_Result(
                        target_id=target_id,
                        webtech_result=json.dumps(result),
                        web_tech=','.join([tech['name'] for tech in result.get('technologies', [])])
                    )
                    db.session.add(new_result)
                
                db.session.commit()
                current_app.logger.info("成功保存掃描結果到數據庫")
                
                return jsonify({
                    'status': 'success',
                    'message': '掃描完成',
                    'result': result,
                    'code': code
                }), code
            except Exception as db_error:
                db.session.rollback()
                current_app.logger.error(f"保存到數據庫時發生錯誤: {str(db_error)}")
                return jsonify({
                    'status': 'error',
                    'message': '保存掃描結果失敗',
                    'code': 500
                }), 500
        else:
            current_app.logger.error(f"Webtech scan error: {result}")
            return jsonify({
                'status': 'error',
                'message': result if isinstance(result, str) else '掃描失敗',
                'code': code
            }), code
            
    except Exception as e:
        current_app.logger.error(f"Webtech scan error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '掃描失敗',
            'code': 500
        }), 500

@webtech_route.route('/result/<int:user_id>/<int:target_id>', methods=['GET'])
@login_required
def get_latest_webtech_result(user_id, target_id):
    try:
        target = Target.query.filter_by(id=target_id).first()
        if not target:
            return jsonify({
                'status': 'error',
                'message': '找不到指定的目標'
            }), 404
        
        result = webtech_Result.query.filter_by(target_id=target_id).order_by(webtech_Result.scan_time.desc()).first()

        if result:
            return jsonify({
                'status': 'success',
                'message': '掃描結果獲取成功',
                'result': result.to_dict()
            }), 200
        else:
            return redirect(url_for('webtech.webtech_scan', user_id=user_id, target_id=target_id))
    except Exception as e:
        current_app.logger.error(f"獲取掃描結果時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '獲取掃描結果時發生錯誤',
            'code': 500
        }), 500

@webtech_route.route('/download/<int:user_id>/<int:target_id>', methods=['GET'])
@login_required
def download_webtech_result(user_id, target_id):
    try:
        # 記錄請求信息
        current_app.logger.debug(f"接收到下載請求: user_id={user_id}, target_id={target_id}, format={request.args.get('format', 'txt')}")
        
        # 檢查用戶權限
        permission_result = check_user_permission(current_user.id, target_id)
        if not isinstance(permission_result, Target):
            current_app.logger.error(f"權限檢查失敗: {permission_result}")
            return permission_result
        target = permission_result
        
        # 檢查數據庫中的所有結果
        all_results = webtech_Result.query.filter_by(target_id=target_id).all()
        current_app.logger.debug(f"數據庫中找到 {len(all_results)} 條結果記錄")
        for idx, r in enumerate(all_results):
            current_app.logger.debug(f"結果 {idx + 1}:")
            current_app.logger.debug(f"- ID: {r.id}")
            current_app.logger.debug(f"- Target ID: {r.target_id}")
            current_app.logger.debug(f"- Scan Time: {r.scan_time}")
            current_app.logger.debug(f"- Web Tech: {r.web_tech}")
        
        # 獲取最新的掃描結果
        result = webtech_Result.query.filter_by(
            target_id=target_id
        ).order_by(
            webtech_Result.scan_time.desc()
        ).first()
        
        if not result:
            current_app.logger.error(f"找不到掃描結果: target_id={target_id}")
            return jsonify({
                'status': 'error',
                'message': '找不到掃描結果'
            }), 404

        # 檢查結果數據是否為空或無效
        if not result.webtech_result:
            current_app.logger.error("掃描結果數據為空")
            return jsonify({
                'status': 'error',
                'message': '掃描結果數據為空'
            }), 400
            
        # 獲取請求的文件格式
        file_format = request.args.get('format', 'txt')
        current_app.logger.debug(f"請求的文件格式: {file_format}")
        
        try:
            # 嘗試解析 JSON 數據
            result_data = json.loads(result.webtech_result) if isinstance(result.webtech_result, str) else result.webtech_result
            current_app.logger.debug(f"解析後的數據類型: {type(result_data)}")
            current_app.logger.debug(f"解析後的數據內容: {str(result_data)[:200]}...")
            
            converter = ScanResultConverter()
            
            if file_format == 'csv':
                current_app.logger.debug("正在轉換為 CSV 格式")
                data = converter.webtech_to_csv(result_data)
                filename = f'webtech_result_{target_id}.csv'
                content_type = 'text/csv'
            elif file_format == 'json':
                current_app.logger.debug("正在轉換為 JSON 格式")
                data = converter.webtech_to_json(result_data)
                filename = f'webtech_result_{target_id}.json'
                content_type = 'application/json'
            else:  # 默認為 txt
                current_app.logger.debug("正在轉換為 TXT 格式")
                data = converter.webtech_to_txt(result_data)
                filename = f'webtech_result_{target_id}.txt'
                content_type = 'text/plain'
            
            current_app.logger.debug(f"文件轉換完成，準備返回響應，文件名: {filename}")
            
            # 創建響應
            response = make_response(data)
            response.headers['Content-Type'] = content_type
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except json.JSONDecodeError as je:
            current_app.logger.error(f"JSON 解析錯誤: {str(je)}")
            return jsonify({
                'status': 'error',
                'message': 'JSON 數據格式錯誤'
            }), 400
            
        except Exception as e:
            current_app.logger.error(f"轉換文件格式時發生錯誤: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': '文件格式轉換失敗'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"下載掃描結果時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '下載失敗'
        }), 500
