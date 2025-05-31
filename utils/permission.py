from flask import jsonify, current_app, request
from instance.models import db, Target

def check_user_permission(target_id=None):
    """
    检查目标权限，支持单独的目标ID检查。

    Args:
        target_id: 目标ID

    Returns:
        Target 或 Response: 如果找到目标返回目标对象，否则返回错误响应
    """
    try:
        # 如果没有指定目标ID，直接返回True
        if target_id is None:
            return True

        # 查询目标是否存在
        target = Target.query.filter_by(id=target_id).first()
        if not target:
            return jsonify({
                'success': False,
                'message': '未找到指定目标',
                'code': 404
            }), 404

        return target

    except Exception as e:
        current_app.logger.error(f"检查目标权限时出现错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'权限检查错误: {str(e)}',
            'code': 500
        }), 500 