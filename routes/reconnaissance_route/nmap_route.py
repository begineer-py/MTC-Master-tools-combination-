from flask import Blueprint, request, jsonify, current_app
from instance.models import Target, nmap_Result, db
from reconnaissance.threads.thread_nmap import start_nmap_scan
import json
import os
from datetime import datetime
import tempfile

# 创建蓝图
nmap_route = Blueprint('nmap', __name__)

@nmap_route.route('/scan/<int:target_id>', methods=['POST'])
def nmap_scan(target_id):
    """启动NMAP扫描"""
    try:
        client_ip = request.remote_addr
        current_app.logger.debug(f"正在访问 nmap 路由，目标 ID: {target_id} {client_ip}")
        
        # 获取目标信息
        target = Target.query.get_or_404(target_id)
        
        # 获取扫描类型
        data = request.get_json() or {}
        scan_type = data.get('scan_type', 'common')  # 默认为common扫描
        
        # 获取目标信息
        target_data = {
            'id': target.id,
            'target_ip': target.domain,  # 使用domain字段
            'target_port': target.target_port,
            'scan_type': scan_type
        }
        
        # 启动扫描
        scan_id = start_nmap_scan(target_id, target_data, current_app._get_current_object())
        
        return jsonify({
            'success': True,
            'message': '扫描已启动',
            'scan_id': scan_id
        })
        
    except Exception as e:
        current_app.logger.error(f"启动NMAP扫描时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动扫描失败: {str(e)}'
        }), 500

@nmap_route.route('/result/<int:target_id>', methods=['GET'])
def get_nmap_result(target_id):
    """获取NMAP扫描结果"""
    try:
        # 获取目标信息
        target = Target.query.get_or_404(target_id)
        
        # 获取扫描类型（默认为common）
        scan_type = request.args.get('scan_type', 'common')
        
        # 查询扫描结果
        nmap_result = nmap_Result.query.filter_by(
            target_id=target_id,
            scan_type=scan_type
        ).first()
        
        if not nmap_result:
            return jsonify({
                'success': False,
                'message': '未找到扫描结果'
            }), 404
        
        # 返回结果
        return jsonify({
            'success': True,
            'result': nmap_result.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取NMAP扫描结果时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取扫描结果失败: {str(e)}'
        }), 500
    

