from flask import Blueprint, request, jsonify
from utils.decorators import json_login_required
from instance.models import db
from functools import wraps
from datetime import datetime, UTC
import os

# 創建藍圖
api_route = Blueprint('api', __name__)

# 固定的API密钥 - 可以从环境变量获取或使用固定值
API_KEY = os.environ.get('API_KEY', 'default_api_key_for_development')

def api_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 從請求頭獲取 API Key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                'success': False,
                'message': '缺少 API Key'
            }), 401
            
        # 检查API密钥是否匹配固定值
        if api_key != API_KEY:
            return jsonify({
                'success': False,
                'message': '無效的 API Key'
            }), 401
            
        return f(*args, **kwargs)
    return decorated_function

@api_route.route('/test_auth', methods=['GET'])
@api_auth_required
def test_auth():
    """測試 API 認證"""
    try:
        return jsonify({
            'success': True,
            'message': 'API 認證成功',
            'system': {
                'version': '2.0',
                'api_enabled': True
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'API 認證失敗: {str(e)}'
        }), 500

@api_route.route('/key/info', methods=['GET'])
@json_login_required
def get_api_key_info():
    """獲取 API Key 信息"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'api_key': API_KEY,
                'created_at': datetime.now(UTC).isoformat(),
                'expires_at': None,  # 永不过期
                'is_expired': False
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'獲取 API Key 信息失敗: {str(e)}'
        }), 500

# 以下路由已被移除，返回简化的响应
@api_route.route('/key/generate', methods=['POST'])
@json_login_required
def generate_api_key():
    """生成新的 API Key - 已简化，使用固定API密钥"""
    return jsonify({
        'success': True,
        'message': '系统现在使用固定API密钥，无需生成',
        'data': {
            'api_key': API_KEY,
            'expires_at': None  # 永不过期
        }
    })

@api_route.route('/key/revoke', methods=['POST'])
@json_login_required
def revoke_api_key():
    """撤銷 API Key - 已简化，使用固定API密钥"""
    return jsonify({
        'success': True,
        'message': '系统现在使用固定API密钥，无法撤销'
    })