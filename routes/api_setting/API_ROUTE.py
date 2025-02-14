from flask import Blueprint, request, jsonify
from routes.api_setting.api_set import API_SET
from flask_login import login_required

api_route = Blueprint('api_route', __name__, url_prefix='/api')

@api_route.route('/check_api', methods=['POST'])
@login_required
def check_api():
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400
            
        user_id = data.get('user_id')
        target_id = data.get('target_id')
        api_key = data.get('api_key')
        
        if not all([user_id, target_id, api_key]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
            
        api_set = API_SET(user_id, target_id, api_key)
        result, message = api_set.check_api()
        
        return jsonify({
            'success': result,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服务器错误：{str(e)}'
        }), 500

@api_route.route('/get_api_key', methods=['POST'])
@login_required
def get_api_key():
    data = request.json
    user_id = data.get('user_id')
    target_id = data.get('target_id')
    api_set = API_SET(user_id, target_id, None)
    return jsonify(api_set.get_api_key())

@api_route.route('/make_api_key', methods=['POST'])
@login_required
def make_api_key():
    data = request.json
    user_id = data.get('user_id')
    target_id = data.get('target_id')
    api_set = API_SET(user_id, target_id, None)
    return jsonify(api_set.make_api_key())

@api_route.route('/delete_api_key', methods=['POST'])
@login_required
def delete_api_key():
    data = request.json
    user_id = data.get('user_id')
    target_id = data.get('target_id')
    api_set = API_SET(user_id, target_id, None)
    return jsonify(api_set.delete_api_key())