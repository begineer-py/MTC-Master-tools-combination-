import os 
import requests
import json
import sys
from instance.models import Target, db
from flask import Blueprint, request, jsonify

api_route = Blueprint('api_route', __name__)

class API_SET:
    def __init__(self, target_id, api_key):
        self.error_message = ""
        self.target_id = target_id
        self.api_key = api_key
    
    def check_api(self):
        try:
            target = Target.query.filter_by(id=self.target_id).first()
            if not target:
                return False, "目標不存在"
            if not target.api_key:
                return False, "API Key 未生成"
            if target.api_key == self.api_key:
                return True, "API Key 驗證成功"
            return False, "API Key 無效"
        except Exception as e:
            return False, f"API 錯誤: {e}"
    
    def get_api_key(self):
        try:
            target = Target.query.filter_by(id=self.target_id).first()
            if not target:
                return {
                    'success': False,
                    'message': '目標不存在'
                }
            if not target.api_key:
                return {
                    'success': False,
                    'message': 'API Key 未生成'
                }
            return {
                'success': True,
                'api_key': target.api_key
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'獲取 API Key 錯誤: {str(e)}'
            }
    
    def make_api_key(self):
        try:
            target = Target.query.filter_by(id=self.target_id).first()
            if not target:
                return {
                    'success': False,
                    'message': '目標不存在'
                }
            api_key = os.urandom(64).hex()
            target.api_key = api_key
            db.session.commit()
            return {
                'success': True,
                'api_key': api_key
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'生成 API Key 錯誤: {str(e)}'
            }
    
    def delete_api_key(self):
        try:
            target = Target.query.filter_by(id=self.target_id).first()
            if not target:
                return {
                    'success': False,
                    'message': '目標不存在'
                }
            target.api_key = None
            db.session.commit()
            return {
                'success': True,
                'message': 'API Key 已刪除'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'刪除 API Key 錯誤: {str(e)}'
            }

@api_route.route('/test_auth', methods=['GET'])
def test_auth():
    """測試 API 認證"""
    try:
        # 簡化認證信息
        auth_info = {
            'system_version': '2.0',
            'api_enabled': True
        }
        
        return jsonify({
            'status': 'success',
            'message': 'API 認證成功',
            'auth_info': auth_info
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'認證測試失敗: {str(e)}'
        }), 500

@api_route.route('/check_api', methods=['POST'])
def check_api():
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': '無效的請求數據'
            }), 400
            
        target_id = data.get('target_id')
        api_key = data.get('api_key')
        
        if not all([target_id, api_key]):
            return jsonify({
                'success': False,
                'message': '缺少必要參數'
            }), 400
            
        # 檢查目標是否存在
        target = Target.query.filter_by(id=target_id).first()
        if not target:
            return jsonify({
                'success': False,
                'message': '目標不存在'
            }), 404
            
        # 檢查 API Key 是否匹配
        if target.api_key != api_key:
            return jsonify({
                'success': False,
                'message': 'API Key 無效'
            }), 401
            
        return jsonify({
            'success': True,
            'message': 'API Key 驗證成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服務器錯誤：{str(e)}'
        }), 500

@api_route.route('/get_api_key', methods=['POST'])
def get_api_key():
    try:
        data = request.json
        target_id = data.get('target_id')
        
        if not target_id:
            return jsonify({
                'success': False,
                'message': '缺少必要參數'
            }), 400
            
        target = Target.query.filter_by(id=target_id).first()
        if not target:
            return jsonify({
                'success': False,
                'message': '目標不存在'
            }), 404
            
        return jsonify({
            'success': True,
            'api_key': target.api_key
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'獲取 API Key 失敗：{str(e)}'
        }), 500

@api_route.route('/make_api_key', methods=['POST'])
def make_api_key():
    try:
        data = request.json
        target_id = data.get('target_id')
        
        if not target_id:
            return jsonify({
                'success': False,
                'message': '缺少必要參數'
            }), 400
            
        target = Target.query.filter_by(id=target_id).first()
        if not target:
            return jsonify({
                'success': False,
                'message': '目標不存在'
            }), 404
            
        # 生成新的 API Key
        api_key = os.urandom(64).hex()
        target.api_key = api_key
        db.session.commit()
        
        return jsonify({
            'success': True,
            'api_key': api_key
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成 API Key 失敗：{str(e)}'
        }), 500

@api_route.route('/delete_api_key', methods=['POST'])
def delete_api_key():
    try:
        data = request.json
        target_id = data.get('target_id')
        
        if not target_id:
            return jsonify({
                'success': False,
                'message': '缺少必要參數'
            }), 400
            
        target = Target.query.filter_by(id=target_id).first()
        if not target:
            return jsonify({
                'success': False,
                'message': '目標不存在'
            }), 404
            
        # 删除 API Key
        target.api_key = None
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'API Key 已刪除'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'刪除 API Key 失敗：{str(e)}'
        }), 500

