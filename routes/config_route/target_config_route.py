from flask import Blueprint, request, jsonify
from instance.models import db, web_config, Target
from datetime import datetime
target_config_route = Blueprint("target_config_route", __name__)

@target_config_route.route("/add_config/<int:target_id>", methods=['POST'])
def add_config(target_id):
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
    new_config = web_config(target_id, database_tech, cookie_config,fornt_tech,back_tech,WAF_tech,captcha_type,login_url,logout_url,server_software,created_at)
    db.session.add(new_config)
    db.session.commit()
    return jsonify({'message': '配置添加成功'}), 200
@target_config_route.route("/get_config/<int:target_id>", methods=['GET'])
def get_config(target_id):
    target = Target.query.filter_by(id=target_id).first()
    if target:
        config = web_config.query.filter_by(target_id=target_id).first()
        if config:
            return jsonify(config.to_dict()), 200
        else:
            return jsonify({'message': '配置不存在'}), 404
    else:
        return jsonify({'message': '目標不存在'}), 404