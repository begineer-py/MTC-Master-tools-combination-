from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app

from instance.models import db, web_config, Target
from datetime import datetime
from config.config import LogConfig

target_config_route = Blueprint("target_config_route", __name__)


@target_config_route.route("/add_config/<int:target_id>", methods=['POST'])
def add_config(target_id):
    logger = LogConfig.get_context_logger()
    logger.info(f"添加配置請求，目標ID: {target_id}")

    data = request.get_json()
    database_tech = data.get('database_tech')
    cookie_config = data.get('cookie_config')
    fornt_tech = data.get('fornt_tech')
    back_tech = data.get('back_tech')
    WAF_tech = data.get('WAF_tech')
    captcha_type = data.get('captcha_type')
    login_url = data.get('login_url')
    logout_url = data.get('logout_url')
    server_software = data.get('server_software')
    created_at = datetime.now()

    new_config = web_config(target_id, database_tech, cookie_config, fornt_tech, back_tech,
                            WAF_tech, captcha_type, login_url, logout_url, server_software, created_at)
    db.session.add(new_config)
    db.session.commit()

    logger.info(f"成功添加配置，目標ID: {target_id}")
    return jsonify({'message': '配置添加成功'}), 200


@target_config_route.route("/get_config/<int:target_id>", methods=['GET'])
def get_config(target_id):
    logger = LogConfig.get_context_logger()
    logger.info(f"獲取配置請求，目標ID: {target_id}")

    target = Target.query.filter_by(id=target_id).first()
    if target:
        config = web_config.query.filter_by(target_id=target_id).first()
        if config:
            logger.info(f"成功獲取配置，目標ID: {target_id}")
            return jsonify(config.to_dict()), 200
        else:
            logger.warning(f"配置不存在，目標ID: {target_id}")
            return jsonify({'message': '配置不存在'}), 404
    else:
        logger.error(f"目標不存在，目標ID: {target_id}")
        return jsonify({'message': '目標不存在'}), 404
