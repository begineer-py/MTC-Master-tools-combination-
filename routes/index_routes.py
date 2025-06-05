from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify, current_app
import os
from instance.models import Target, db
from datetime import datetime
from config.config import log_function_call, LogConfig

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
@log_function_call()
def index():
    """现在直接显示目标列表页面，不再需要重定向"""
    logger = LogConfig.get_context_logger()
    logger.info("用戶訪問首頁")
    
    targets = Target.query.all()
    logger.info(f"查詢到 {len(targets)} 個目標")
    
    return render_template('index.html', targets=targets)

@index_bp.route('/favicon.ico')
def favicon():
    return os.path.join(os.path.dirname(__file__), 'static', 'My_hacker_dream.png')  # 返回图标

@index_bp.route("/reset")
@log_function_call()
def reset():
    """重置会话"""
    logger = LogConfig.get_context_logger()
    logger.info("用戶請求重置會話")
    
    session.clear()
    logger.info("會話已清除")
    
    return redirect(url_for('index.index'))

@index_bp.route("/add_target", methods=['GET', 'POST'])
@log_function_call()
def add_target():
    """添加新目标"""
    logger = LogConfig.get_context_logger()
    
    if request.method == 'POST':
        domain = request.form.get('domain', '').strip()  # 获取domain字段
        target_ip = request.form.get('target_ip', '').strip()
        
        logger.info(f"收到添加目標請求: domain='{domain}', target_ip='{target_ip}'")
        
        # 基本表单验证
        # domain现在是可选的，由target_ip自动提取，但如果用户提供了则优先使用
            
        if not target_ip:
            logger.warning("目標URL為空")
            flash("目標URL不能為空", "danger")
            return render_template('add_target.html')
            
        # 确保URL包含协议
        if not (target_ip.startswith('http://') or target_ip.startswith('https://')):
            logger.warning(f"目標URL格式錯誤: {target_ip}")
            flash("目標URL必須以http://或https://開頭", "danger")
            return render_template('add_target.html')
        
        try:
            # 如果没提供domain，从target_ip中提取
            if not domain:
                domain = target_ip.replace('https://', '').replace('http://', '')
                logger.debug(f"自動提取domain: {domain}")
            
            current_app.logger.info(f"嘗試添加新目標: target_ip={target_ip}, domain={domain}")
            
            # 创建新目标，设置必要的字段
            new_target = Target(
                target_ip=target_ip,
                domain=domain,  # 使用domain字段
                target_port=443 if 'https://' in target_ip else 80,
                target_status='pending'
            )
            
            # 保存到数据库
            db.session.add(new_target)
            db.session.commit()
            
            current_app.logger.info(f"✅ 成功添加目標: ID={new_target.id}, target_ip={target_ip}")
            logger.info(f"目標添加成功: ID={new_target.id}")
            flash("目标添加成功", "success")
            return redirect(url_for('index.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ 添加目標失敗: {str(e)}")
            current_app.logger.error(f"詳細信息: target_ip={target_ip}, domain={domain}")
            logger.error(f"數據庫操作失敗: {str(e)}")
            flash(f"添加目标失败: {str(e)}", "danger")
    
    # GET请求，显示添加目标表单
    logger.debug("顯示添加目標表單")
    return render_template('add_target.html')

@index_bp.route("/delete_target/<int:target_id>", methods=['POST', 'GET'])
@log_function_call()
def delete_target(target_id):
    """删除目标"""
    logger = LogConfig.get_context_logger()
    
    try:
        current_app.logger.info(f"嘗試刪除目標: target_id={target_id}")
        logger.info(f"收到刪除請求: target_id={target_id}")
        
        # 查询目标
        target = Target.query.get_or_404(target_id)
        
        # 获取目标信息用于显示
        target_info = f"{target.target_ip} ({target.domain})"
        logger.debug(f"找到目標: {target_info}")
        
        # 删除目标
        db.session.delete(target)
        db.session.commit()
        
        current_app.logger.info(f"✅ 成功刪除目標: {target_info}")
        logger.info(f"目標刪除成功: {target_info}")
        flash(f"目标 {target_info} 已成功删除", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ 刪除目標失敗: {str(e)}, target_id={target_id}")
        logger.error(f"刪除操作失敗: {str(e)}")
        flash(f"删除目标失败: {str(e)}", "danger")
    
    # 重定向到目标列表页面
    return redirect(url_for('index.index'))

@index_bp.route("/api/delete_target/<int:target_id>", methods=['POST'])
@log_function_call()
def api_delete_target(target_id):
    """删除目标的API接口（用于AJAX请求）"""
    logger = LogConfig.get_context_logger()
    
    try:
        current_app.logger.info(f"API 嘗試刪除目標: target_id={target_id}")
        logger.info(f"API收到刪除請求: target_id={target_id}")
        
        # 查询目标
        target = Target.query.get_or_404(target_id)
        target_info = f"{target.target_ip} ({target.domain})"
        
        # 删除目标
        db.session.delete(target)
        db.session.commit()
        
        current_app.logger.info(f"✅ API 成功刪除目標: {target_info}")
        logger.info(f"API刪除成功: {target_info}")
        return jsonify({"success": True, "message": "目标已成功删除"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ API 刪除目標失敗: {str(e)}, target_id={target_id}")
        logger.error(f"API刪除失敗: {str(e)}")
        return jsonify({"success": False, "message": f"删除目标失败: {str(e)}"}), 500
