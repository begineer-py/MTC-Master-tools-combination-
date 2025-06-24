from flask import Blueprint, request, session, flash, redirect, url_for, jsonify, render_template, current_app
from instance.models import Target
from config.config import LogConfig

# 创建蓝图，用于处理扫描相关操作
attack_bp = Blueprint('attack', __name__)
logger = LogConfig.get_context_logger()


@attack_bp.route('/attack/<int:target_id>', methods=['GET'])
def attack(target_id):
    logger = LogConfig.get_context_logger()
    try:
        logger.info(f"載入攻擊界面，目標ID: {target_id}")

        # 直接获取目标信息
        target = Target.query.get_or_404(target_id)

        # 加载扫描界面
        current_app.logger.info(f"加载扫描界面，目标ID: {target_id}")
        return render_template('attack.html', target_id=target_id, target=target)

    except Exception as e:
        current_app.logger.error(f"加载扫描界面时出错: {str(e)}")
        logger.error(f"載入攻擊界面時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'加载扫描界面失败: {str(e)}'
        }), 500
