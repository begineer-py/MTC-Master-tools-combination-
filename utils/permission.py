from flask import jsonify, current_app, request
from flask_login import current_user
from instance.models import db, Target, User

def check_user_permission(user_id, target_id=None):
    """
    檢查用戶對目標的訪問權限
    
    Args:
        user_id: 用戶ID
        target_id: 目標ID (可選)
        
    Returns:
        Target/User 或 Response: 如果有權限返回目標/用戶對象，否則返回錯誤響應
    """
    try:
        # 檢查 API Key 認證
        api_key = request.headers.get('X-API-Key')
        if api_key:
            user = User.query.filter_by(api_key=api_key).first()
            if user and user.check_api_key(api_key):
                if target_id is None:
                    return user
                if user.is_admin or user.id == user_id:
                    target = Target.query.filter_by(id=target_id).first()
                    if target and (user.is_admin or target.user_id == user.id):
                        return target
                    return jsonify({
                        'success': False,
                        'message': '找不到指定的目標或無權訪問'
                    }), 404
            return jsonify({
                'success': False,
                'message': 'API Key 無效'
            }), 401

        # 檢查一般用戶認證
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': '請先登錄'
            }), 401
            
        # 如果是管理員,允許訪問任何目標
        if current_user.is_admin:
            if target_id is None:
                return current_user
            target = Target.query.filter_by(id=target_id).first()
            return target if target else (jsonify({
                'success': False,
                'message': '找不到指定的目標'
            }), 404)
            
        # 非管理員需要檢查用戶ID匹配
        if current_user.id != user_id:
            return jsonify({
                'success': False,
                'message': '無權訪問',
                'code': 403
            }), 403
        
        # 如果沒有指定目標ID，直接返回用戶對象
        if target_id is None:
            return current_user
            
        # 檢查目標所屬用戶
        target = Target.query.filter_by(id=target_id).first()
        if not target or target.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '找不到指定的目標或無權訪問',
                'code': 404
            }), 404
            
        return target

    except Exception as e:
        current_app.logger.error(f"權限檢查過程中發生錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': '權限驗證失敗',
            'code': 500
        }), 500 