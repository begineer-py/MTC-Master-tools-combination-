from flask import Blueprint, request, session, flash, redirect, url_for, jsonify, render_template, current_app
from instance.models import Target
import logging

# 创建蓝图，用于处理扫描相关操作
attack_bp = Blueprint('attack', __name__)
logger = logging.getLogger(__name__)

@attack_bp.route('/attack/<int:target_id>', methods=['GET'])
def attack(target_id):
    try:
        # 直接获取目标信息
        target = Target.query.get_or_404(target_id)
        
        # 加载扫描界面
        current_app.logger.info(f"加载扫描界面，目标ID: {target_id}")
        return render_template('attack.html', target_id=target_id, target=target)
        
    except Exception as e:
        current_app.logger.error(f"加载扫描界面时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'加载扫描界面失败: {str(e)}'
        }), 500


