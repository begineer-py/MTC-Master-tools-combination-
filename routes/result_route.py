from flask import Blueprint, jsonify, render_template
from instance.models import (
    Target, 
    crawler_each_url, 
    crawler_each_form, 
    crawler_each_html, 
    crawler_each_js, 
    crawler_each_image,
    crawler_each_security
)
from utils.permission import check_user_permission
from flask_login import login_required, current_user

result_bp = Blueprint('result_bp', __name__)

@result_bp.route('/form/<int:user_id>/<int:target_id>')
@login_required
def get_crawler_form(user_id, target_id):
    """獲取爬蟲表單結果"""
    try:
        # 檢查權限
        permission_result = check_user_permission(user_id, target_id)
        if not isinstance(permission_result, Target):
            return permission_result
            
        # 首先获取所有相关的 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到 URL 數據'
            }), 404

        forms_data = []
        for url in urls:
            forms = crawler_each_form.query.filter_by(crawler_each_url_id=url.id).all()
            for form in forms:
                forms_data.append({
                    'id': form.id,
                    'url': url.url,
                    'form': form.form
                })
            
        return jsonify({
            'status': 'success',
            'data': forms_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'獲取表單數據時出錯：{str(e)}'
        }), 500

@result_bp.route('/html/<int:user_id>/<int:target_id>')
@login_required
def get_crawler_html(user_id, target_id):
    """獲取爬蟲 HTML 結果"""
    try:
        # 檢查權限
        permission_result = check_user_permission(user_id, target_id)
        if not isinstance(permission_result, Target):
            return permission_result
            
        # 获取所有相关的 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到 URL 數據'
            }), 404
            
        html_data = []
        for url in urls:
            htmls = crawler_each_html.query.filter_by(crawler_each_url_id=url.id).all()
            for html in htmls:
                html_data.append({
                    'id': html.id,
                    'url': url.url,
                    'html': html.html
                })
            
        return jsonify({
            'status': 'success',
            'data': html_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'獲取 HTML 數據時出錯：{str(e)}'
        }), 500

@result_bp.route('/js/<int:user_id>/<int:target_id>')
@login_required
def get_crawler_js(user_id, target_id):
    """獲取爬蟲 JS 結果"""
    try:
        # 檢查權限
        permission_result = check_user_permission(user_id, target_id)
        if not isinstance(permission_result, Target):
            return permission_result
            
        # 获取所有相关的 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到 URL 數據'
            }), 404
            
        js_data = []
        for url in urls:
            js_files = crawler_each_js.query.filter_by(crawler_each_url_id=url.id).all()
            for js in js_files:
                js_data.append({
                    'id': js.id,
                    'url': url.url,
                    'js': js.js
                })
            
        return jsonify({
            'status': 'success',
            'data': js_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'獲取 JS 數據時出錯：{str(e)}'
        }), 500

@result_bp.route('/image/<int:user_id>/<int:target_id>')
@login_required
def get_crawler_image(user_id, target_id):
    """獲取爬蟲圖片結果"""
    try:
        # 檢查權限
        permission_result = check_user_permission(user_id, target_id)
        if not isinstance(permission_result, Target):
            return permission_result
            
        # 获取所有相关的 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到 URL 數據'
            }), 404
            
        image_data = []
        for url in urls:
            images = crawler_each_image.query.filter_by(crawler_each_url_id=url.id).all()
            for image in images:
                image_data.append({
                    'id': image.id,
                    'url': url.url,
                    'image_url': image.image_url,
                    'image': image.image
                })
            
        return jsonify({
            'status': 'success',
            'data': image_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'獲取圖片數據時出錯：{str(e)}'
        }), 500

@result_bp.route('/security/<int:user_id>/<int:target_id>')
@login_required
def get_crawler_security(user_id, target_id):
    """獲取爬蟲安全信息結果"""
    try:
        # 檢查權限
        permission_result = check_user_permission(user_id, target_id)
        if not isinstance(permission_result, Target):
            return permission_result
            
        # 获取所有相关的 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到 URL 數據'
            }), 404
            
        security_data = []
        for url in urls:
            securities = crawler_each_security.query.filter_by(crawler_each_url_id=url.id).all()
            for security in securities:
                security_data.append({
                    'id': security.id,
                    'url': url.url,
                    'security': security.security
                })
            
        return jsonify({
            'status': 'success',
            'data': security_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'獲取安全信息時出錯：{str(e)}'
        }), 500

