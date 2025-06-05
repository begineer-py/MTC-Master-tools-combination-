from flask import Blueprint, request, jsonify, current_app, render_template
from instance.models import Target
import requests
import json
import sys
import os

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.flaresolverr_set.start_flaresolverr import flaresolverr_manager

# 创建蓝图
flaresolverr_bp = Blueprint('flaresolverr', __name__)

@flaresolverr_bp.route('/solve', methods=['POST'])
def flaresolverr_solve():
    """使用FlareSolverr解决Cloudflare验证码"""
    try:
        # 获取目标ID和URL
        data = request.get_json()
        target_id = data.get('target_id')
        url = data.get('url')
        
        if not url:
            return jsonify({
                'success': False,
                'message': '缺少URL参数'
            }), 400
            
        # 调用FlareSolverr
        flaresolverr_url = 'http://localhost:8191/v1'
        
        # 发送请求
        response = requests.post(
            flaresolverr_url,
            json={
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            },
            timeout=65  # 略高于FlareSolverr超时时间
        )
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'FlareSolverr服务返回错误代码: {response.status_code}'
            }), 500
            
        result = response.json()
        
        # 检查FlareSolverr结果
        if result.get('status') != 'ok':
            return jsonify({
                'success': False,
                'message': f'FlareSolverr解析失败: {result.get("message", "未知错误")}'
            }), 500
            
        # 获取解决后的内容
        solution = {
            'success': True,
            'html': result.get('solution', {}).get('response', ''),
            'cookies': result.get('solution', {}).get('cookies', []),
            'userAgent': result.get('solution', {}).get('userAgent', '')
        }
        
        return jsonify(solution)
        
    except requests.RequestException as e:
        current_app.logger.error(f"FlareSolverr请求错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'请求FlareSolverr服务失败: {str(e)}'
        }), 500
        
    except Exception as e:
        current_app.logger.error(f"FlareSolverr解析错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'处理请求时出错: {str(e)}'
        }), 500

@flaresolverr_bp.route('/start', methods=['POST'])
def start_flaresolverr():
    """啟動 FlareSolverr 服務"""
    try:
        result = flaresolverr_manager.start_flaresolverr()
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error(f"啟動 FlareSolverr 錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'啟動服務時出錯: {str(e)}'
        }), 500

@flaresolverr_bp.route('/stop', methods=['POST'])
def stop_flaresolverr():
    """停止 FlareSolverr 服務"""
    try:
        result = flaresolverr_manager.stop_flaresolverr()
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error(f"停止 FlareSolverr 錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'停止服務時出錯: {str(e)}'
        }), 500

@flaresolverr_bp.route('/restart', methods=['POST'])
def restart_flaresolverr():
    """重啟 FlareSolverr 服務"""
    try:
        result = flaresolverr_manager.restart_flaresolverr()
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error(f"重啟 FlareSolverr 錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重啟服務時出錯: {str(e)}'
        }), 500

@flaresolverr_bp.route('/status', methods=['GET'])
def get_flaresolverr_status():
    """獲取 FlareSolverr 狀態"""
    try:
        result = flaresolverr_manager.get_status()
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error(f"獲取 FlareSolverr 狀態錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'獲取狀態時出錯: {str(e)}'
        }), 500

@flaresolverr_bp.route('/auto-start', methods=['POST'])
def auto_start_flaresolverr():
    """自動啟動 FlareSolverr（如果未運行）"""
    try:
        # 檢查是否已經運行
        status_result = flaresolverr_manager.get_status()
        if status_result['success'] and status_result['status']['running']:
            return jsonify({
                'success': True,
                'message': 'FlareSolverr 已經在運行',
                'status': 'already_running'
            })
        
        # 啟動服務
        result = flaresolverr_manager.start_flaresolverr()
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error(f"自動啟動 FlareSolverr 錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'自動啟動服務時出錯: {str(e)}'
        }), 500

@flaresolverr_bp.route('/dashboard', methods=['GET'])
def flaresolverr_dashboard():
    """FlareSolverr 管理界面"""
    return render_template("flaresolverr_htmls/flaresolverr.html")

@flaresolverr_bp.route('/help', methods=['GET'])
def flaresolverr_help():
    """FlareSolverr 使用說明"""
    help_info = {
        'success': True,
        'service_info': {
            'name': 'FlareSolverr',
            'description': 'Cloudflare 驗證碼解決方案',
            'version': '3.3.21',
            'default_port': 8191
        },
        'api_endpoints': {
            '/api/flaresolverr/start': {
                'method': 'POST',
                'description': '啟動 FlareSolverr 服務'
            },
            '/api/flaresolverr/stop': {
                'method': 'POST', 
                'description': '停止 FlareSolverr 服務'
            },
            '/api/flaresolverr/restart': {
                'method': 'POST',
                'description': '重啟 FlareSolverr 服務'
            },
            '/api/flaresolverr/status': {
                'method': 'GET',
                'description': '獲取服務狀態'
            },
            '/api/flaresolverr/solve': {
                'method': 'POST',
                'description': '解決 Cloudflare 驗證碼',
                'parameters': {
                    'url': '要解析的 URL',
                    'target_id': '目標 ID（可選）'
                }
            },
            '/api/flaresolverr/dashboard': {
                'method': 'GET',
                'description': '管理界面'
            }
        },
        'usage_examples': {
            'solve_request': {
                'url': '/api/flaresolverr/solve',
                'method': 'POST',
                'body': {
                    'url': 'https://example.com',
                    'target_id': 1
                }
            }
        },
        'features': [
            '自動啟動和停止服務',
            '實時狀態監控',
            '自動重啟機制',
            '進程資源監控',
            'Web 管理界面',
            'Cloudflare 驗證碼解決'
        ]
    }
    
    return jsonify(help_info) 