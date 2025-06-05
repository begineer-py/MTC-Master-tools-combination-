from flask import Blueprint, request, jsonify, current_app, render_template
from instance.models import Target, nmap_Result, db
from reconnaissance.threads.thread_nmap import start_nmap_scan, active_scans
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
            'message': '掃描已啟動',
            'scan_id': scan_id,
            'target_id': target_id,
            'scan_type': scan_type,
            'estimated_time': '30-120秒（19個端口）' if scan_type == 'common' else '2-8分鐘（114個端口）'
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
                'message': '未找到扫描结果',
                'status': 'not_found'
            }), 404
        
        # 返回结果
        result_dict = nmap_result.to_dict()
        
        # 添加額外的統計信息
        if result_dict.get('ports'):
            port_stats = {
                'total': len(result_dict['ports']),
                'open': len([p for p in result_dict['ports'] if p.get('state') == 'open']),
                'filtered': len([p for p in result_dict['ports'] if p.get('state') == 'filtered']),
                'closed': len([p for p in result_dict['ports'] if p.get('state') == 'closed'])
            }
            result_dict['port_statistics'] = port_stats
        
        return jsonify({
            'success': True,
            'result': result_dict,
            'target_info': {
                'id': target.id,
                'domain': target.domain,
                'target_port': target.target_port
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取NMAP扫描结果时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取扫描结果失败: {str(e)}'
        }), 500

@nmap_route.route('/status/<int:target_id>', methods=['GET'])
def get_scan_status(target_id):
    """获取扫描状态"""
    try:
        scan_type = request.args.get('scan_type', 'common')
        scan_key = f"{target_id}_{scan_type}"
        
        # 检查是否有活动扫描
        if scan_key in active_scans:
            scan_thread = active_scans[scan_key]
            if scan_thread.is_alive():
                return jsonify({
                    'success': True,
                    'status': 'scanning',
                    'message': '掃描正在進行中...'
                })
            else:
                # 掃描已完成，清理線程
                del active_scans[scan_key]
                return jsonify({
                    'success': True,
                    'status': 'completed',
                    'message': '掃描已完成'
                })
        
        # 檢查是否有結果
        nmap_result = nmap_Result.query.filter_by(
            target_id=target_id,
            scan_type=scan_type
        ).first()
        
        if nmap_result:
            return jsonify({
                'success': True,
                'status': 'completed',
                'message': '掃描已完成，結果可用'
            })
        else:
            return jsonify({
                'success': True,
                'status': 'not_started',
                'message': '尚未開始掃描'
            })
            
    except Exception as e:
        current_app.logger.error(f"获取扫描状态时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500

@nmap_route.route('/history/<int:target_id>', methods=['GET'])
def get_scan_history(target_id):
    """获取扫描历史"""
    try:
        # 获取所有扫描结果
        results = nmap_Result.query.filter_by(target_id=target_id).order_by(nmap_Result.scan_time.desc()).all()
        
        history = []
        for result in results:
            result_dict = result.to_dict()
            history.append({
                'scan_type': result.scan_type,
                'scan_time': result_dict['scan_time'],
                'host_status': result_dict['host_status'],
                'port_count': len(result_dict.get('ports', [])),
                'open_ports': len([p for p in result_dict.get('ports', []) if p.get('state') == 'open'])
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        current_app.logger.error(f"获取扫描历史时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取历史失败: {str(e)}'
        }), 500

@nmap_route.route('/dashboard', methods=['GET'])
def nmap_dashboard():
    """Nmap 掃描器現代化界面"""
    try:
        current_app.logger.info("正在載入 Nmap 掃描器界面")
        
        # 獲取 URL 參數
        target_id = request.args.get('target_id', '')
        
        # 使用分離的模板文件
        return render_template('nmap_htmls/dashboard.html', target_id=target_id)
        
    except Exception as e:
        current_app.logger.error(f"載入 Nmap 掃描器界面時出錯: {str(e)}")
        return f"載入界面失敗: {str(e)}", 500

@nmap_route.route('/help', methods=['GET'])
def nmap_help():
    """Nmap 掃描器幫助信息"""
    with open(os.path.join(os.path.dirname(__file__), 'nmap_help.json'), 'r', encoding='utf-8') as f:
        help_content = json.load(f)
    
    return jsonify(help_content)
    

