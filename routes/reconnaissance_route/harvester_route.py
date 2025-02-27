from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required
from instance.models import Target, HarvesterResult
from utils.permission import check_user_permission
from reconnaissance.threads.thread_harvester import HarvesterScanThread
import logging
from flask import current_app
import json
from datetime import datetime
from io import BytesIO
from reconnaissance.theHarvester.harvester_integration import create_harvester_integration

harvester_route = Blueprint('harvester', __name__)
logger = logging.getLogger(__name__)

@harvester_route.route('/scan/<int:user_id>/<int:target_id>', methods=['POST'])
@login_required
def harvester_scan(user_id, target_id):
    """启动 theHarvester 扫描"""
    # 检查用户权限
    permission_result = check_user_permission(user_id, target_id)
    if not isinstance(permission_result, Target):
        return permission_result
    target = permission_result
    
    try:
        # 获取请求参数
        data = request.get_json() or {}
        sources = data.get('sources', 'all')
        limit = data.get('limit', 1000)
        
        # 创建并启动扫描线程
        scan_thread = HarvesterScanThread(
            target_domain=target.target_ip_no_https,
            target_id=target_id,
            app=current_app,
            sources=sources,
            limit=limit
        )
        logger.info(f"开始扫描目标: {target.target_ip_no_https}")
        scan_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': '掃描已啟動'
        })
        
    except Exception as e:
        logger.error(f"启动扫描失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'启动扫描失败: {str(e)}'
        }), 500

@harvester_route.route('/result/<int:user_id>/<int:target_id>', methods=['GET'])
@login_required
def get_harvester_result(user_id, target_id):
    """获取 theHarvester 扫描结果"""
    # 检查用户权限
    permission_result = check_user_permission(user_id, target_id)
    if not isinstance(permission_result, Target):
        return permission_result
    
    try:
        # 获取最新结果
        result = HarvesterResult.query.filter_by(
            target_id=target_id
        ).order_by(
            HarvesterResult.scan_time.desc()
        ).first()
        
        if result:
            return jsonify({
                'status': 'success',
                'data': result.to_dict()
            })
        
        return jsonify({
            'status': 'error',
            'message': '未找到扫描结果'
        }), 404
        
    except Exception as e:
        logger.error(f"获取结果失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取结果失败: {str(e)}'
        }), 500

@harvester_route.route('/download/<int:user_id>/<int:target_id>', methods=['GET'])
@login_required
def download_harvester_result(user_id, target_id):
    """下载 theHarvester 扫描结果"""
    # 检查用户权限
    permission_result = check_user_permission(user_id, target_id)
    if not isinstance(permission_result, Target):
        return permission_result
    
    try:
        # 获取最新结果
        result = HarvesterResult.query.filter_by(
            target_id=target_id
        ).order_by(
            HarvesterResult.scan_time.desc()
        ).first()
        
        if not result:
            return jsonify({
                'status': 'error',
                'message': '未找到扫描结果'
            }), 404
        
        # 创建结果字典
        result_dict = result.to_dict()
        
        # 获取下载格式
        format_type = request.args.get('format', 'json')
        
        if format_type == 'json':
            # JSON 格式
            result_json = json.dumps(result_dict, indent=2, ensure_ascii=False)
            mem_file = BytesIO()
            mem_file.write(result_json.encode('utf-8'))
            mem_file.seek(0)
            
            filename = f'harvester_result_{target_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            return send_file(
                mem_file,
                mimetype='application/json',
                as_attachment=True,
                download_name=filename
            )
        else:
            # 文本格式
            output_parser = create_harvester_integration().output_parser
            temp_file = output_parser.save_to_file(result_dict)
            
            if temp_file:
                return send_file(
                    temp_file,
                    mimetype='text/plain',
                    as_attachment=True,
                    download_name=f'harvester_result_{target_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                )
            
            return jsonify({
                'status': 'error',
                'message': '生成文本文件失敗'
            }), 500
        
    except Exception as e:
        logger.error(f"下载结果失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'下载结果失败: {str(e)}'
        }), 500 