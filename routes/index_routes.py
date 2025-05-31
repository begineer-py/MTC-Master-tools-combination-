from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
import os
from instance.models import Target, db
from datetime import datetime

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index():
    """现在直接显示目标列表页面，不再需要重定向"""
    targets = Target.query.all()
    return render_template('index.html', targets=targets)

@index_bp.route('/favicon.ico')
def favicon():
    return os.path.join(os.path.dirname(__file__), 'static', 'My_hacker_dream.png')  # 返回图标

@index_bp.route("/reset")
def reset():
    """重置会话"""
    session.clear()
    return redirect(url_for('index.index'))

@index_bp.route("/add_target", methods=['GET', 'POST'])
def add_target():
    """添加新目标"""
    if request.method == 'POST':
        domain = request.form.get('domain', '').strip()  # 获取domain字段
        target_ip = request.form.get('target_ip', '').strip()
        
        # 基本表单验证
        # domain现在是可选的，由target_ip自动提取，但如果用户提供了则优先使用
            
        if not target_ip:
            flash("目标URL不能为空", "danger")
            return render_template('add_target.html')
            
        # 确保URL包含协议
        if not (target_ip.startswith('http://') or target_ip.startswith('https://')):
            flash("目标URL必须以http://或https://开头", "danger")
            return render_template('add_target.html')
        
        try:
            # 如果没提供domain，从target_ip中提取
            if not domain:
                domain = target_ip.replace('https://', '').replace('http://', '')
            
            # 创建新目标，设置必要的字段
            new_target = Target(
                target_ip=target_ip,
                domain=domain,  # 使用domain字段
                target_port=443 if 'https://' in target_ip else 80,
                target_username='',  # 用户名为空
                target_password='',  # 密码为空
                target_status='pending',
                # date=datetime.now()  # 不再设置date字段
            )
            
            # 保存到数据库
            db.session.add(new_target)
            db.session.commit()
            
            flash("目标添加成功", "success")
            return redirect(url_for('index.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"添加目标失败: {str(e)}", "danger")
    
    # GET请求，显示添加目标表单
    return render_template('add_target.html')

@index_bp.route("/delete_target/<int:target_id>", methods=['POST', 'GET'])
def delete_target(target_id):
    """删除目标"""
    try:
        # 查询目标
        target = Target.query.get_or_404(target_id)
        
        # 获取目标信息用于显示
        target_info = f"{target.target_ip} ({target.domain})"
        
        # 删除目标
        db.session.delete(target)
        db.session.commit()
        
        flash(f"目标 {target_info} 已成功删除", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"删除目标失败: {str(e)}", "danger")
    
    # 重定向到目标列表页面
    return redirect(url_for('index.index'))

@index_bp.route("/api/delete_target/<int:target_id>", methods=['POST'])
def api_delete_target(target_id):
    """删除目标的API接口（用于AJAX请求）"""
    try:
        # 查询目标
        target = Target.query.get_or_404(target_id)
        
        # 删除目标
        db.session.delete(target)
        db.session.commit()
        
        return jsonify({"success": True, "message": "目标已成功删除"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"删除目标失败: {str(e)}"}), 500
