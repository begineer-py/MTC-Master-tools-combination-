from flask import Blueprint, request, jsonify, current_app
from utils.permission import check_user_permission
from instance.models import Target
import requests
import json

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
            
        # 检查权限（如果提供了target_id）
        if target_id:
            permission_result = check_user_permission(target_id=target_id)
            if not isinstance(permission_result, Target):
                return permission_result
        
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