from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from instance.models import db, User
from functools import wraps
from datetime import datetime, UTC

# 創建藍圖
api_route = Blueprint('api', __name__)

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
            
        # 查找具有此 API Key 的用戶
        user = User.query.filter_by(api_key=api_key).first()
        if not user or not user.check_api_key(api_key):
            return jsonify({
                'success': False,
                'message': '無效的 API Key'
            }), 401
            
        return f(*args, **kwargs)
    return decorated_function

def json_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': '請先登錄'
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
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'api_key_expires_at': current_user.api_key_expires_at.isoformat() if current_user.api_key_expires_at else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'API 認證失敗: {str(e)}'
        }), 500

@api_route.route('/key/generate', methods=['POST'])
@json_login_required
def generate_api_key():
    """生成新的 API Key"""
    try:
        # 獲取過期時間（天數）
        data = request.get_json() or {}
        expires_in = data.get('expires_in', 30)
        
        # 生成新的 API Key
        api_key = current_user.generate_api_key(expires_in)
        
        # 保存到數據庫
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'API Key 生成成功',
            'data': {
                'api_key': api_key,
                'expires_at': current_user.api_key_expires_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'生成 API Key 失敗: {str(e)}'
        }), 500

@api_route.route('/key/revoke', methods=['POST'])
@json_login_required
def revoke_api_key():
    """撤銷 API Key"""
    try:
        current_user.revoke_api_key()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'API Key 已撤銷'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'撤銷 API Key 失敗: {str(e)}'
        }), 500

@api_route.route('/key/info', methods=['GET'])
@json_login_required
def get_api_key_info():
    """獲取 API Key 信息"""
    try:
        if not current_user.api_key:
            return jsonify({
                'success': False,
                'message': '尚未生成 API Key'
            }), 404
            
        return jsonify({
            'success': True,
            'data': {
                'api_key': current_user.api_key,
                'created_at': current_user.api_key_created_at.isoformat() if current_user.api_key_created_at else None,
                'expires_at': current_user.api_key_expires_at.isoformat() if current_user.api_key_expires_at else None,
                'is_expired': datetime.now(UTC) > current_user.api_key_expires_at if current_user.api_key_expires_at else True
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'獲取 API Key 信息失敗: {str(e)}'
        }), 500