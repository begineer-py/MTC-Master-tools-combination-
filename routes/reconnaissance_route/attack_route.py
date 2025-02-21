from flask import Blueprint, request, session, flash, redirect, url_for, jsonify, render_template, current_app
from instance.models import Target
from flask_login import login_required, current_user
from utils.permission import check_user_permission 
import logging

# 創建一個藍圖，用於組織攻擊相關的路由
attack_bp = Blueprint('attack', __name__)
logger = logging.getLogger(__name__)

@attack_bp.route('/user/<int:user_id>/attack/<int:target_id>', methods=['GET'])
@login_required
def attack(user_id, target_id):
    # 檢查用戶權限
    permission_result = check_user_permission(current_user.id, target_id)
    if not isinstance(permission_result, Target):
        return permission_result
    if not isinstance(permission_result, Target):
        return redirect(url_for('index.login'))
    target = permission_result
    
    # 渲染攻擊頁面
    current_app.logger.info(f"用戶 {current_user.id} 正在訪問攻擊頁面，目標 ID: {target_id}")
    return render_template('attack.html', target_id=target_id, target=target)


