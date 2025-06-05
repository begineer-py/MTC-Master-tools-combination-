from flask import Blueprint, jsonify, render_template, request
from instance.models import (
    Target, 
    crawler_each_url, 
    crawler_each_form, 
    crawler_each_html, 
    crawler_each_js, 
    crawler_each_image,
    crawler_each_security,
    gau_results,
    nmap_Result,
    crtsh_Result,
    webtech_Result,
    if_sql_injection,
    xss_result,
    vulnerability_scanning_result
)
from flask import current_app
import json
import logging

# 设置日志
logger = logging.getLogger(__name__)

result_bp = Blueprint('result', __name__)

@result_bp.route('/form/<int:target_id>')
def get_crawler_form(target_id):
    """获取表单数据"""
    try:
        # 检查权限
        permission_result = check_user_permission(target_id=target_id)
        if not isinstance(permission_result, Target):
            return permission_result

        # 获取与目标相关的所有 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到URL 记录'
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

@result_bp.route('/html/<int:target_id>')
def get_crawler_html(target_id):
    """获取HTML数据"""
    try:
        # 检查权限
        permission_result = check_user_permission(target_id=target_id)
        if not isinstance(permission_result, Target):
            return permission_result

        # 获取与目标相关的所有 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到URL记录'
            }), 404

        html_data = []
        for url in urls:
            htmls = crawler_each_html.query.filter_by(crawler_each_url_id=url.id).all()
            for html in htmls:
                html_data.append({
                    'id': html.id,
                    'url': url.url,
                    'html': html.html,
                    'title': html.title
                })

        return jsonify({
            'status': 'success',
            'data': html_data
        })
    except Exception as e:
        current_app.logger.error(f"获取HTML数据时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取数据失败: {str(e)}'
        }), 500

@result_bp.route('/js/<int:target_id>')
def get_crawler_js(target_id):
    """获取JavaScript数据"""
    try:
        # 检查权限
        permission_result = check_user_permission(target_id=target_id)
        if not isinstance(permission_result, Target):
            return permission_result

        # 获取与目标相关的所有 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到URL记录'
            }), 404

        js_data = []
        for url in urls:
            scripts = crawler_each_js.query.filter_by(crawler_each_url_id=url.id).all()
            for script in scripts:
                js_data.append({
                    'id': script.id,
                    'url': url.url,
                    'js_url': script.js_url,
                    'js_content': script.js_content
                })

        return jsonify({
            'status': 'success',
            'data': js_data
        })
    except Exception as e:
        current_app.logger.error(f"获取JavaScript数据时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取数据失败: {str(e)}'
        }), 500

@result_bp.route('/image/<int:target_id>')
def get_crawler_image(target_id):
    """获取图片数据"""
    try:
        # 检查权限
        permission_result = check_user_permission(target_id=target_id)
        if not isinstance(permission_result, Target):
            return permission_result

        # 获取与目标相关的所有 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到URL记录'
            }), 404

        image_data = []
        for url in urls:
            images = crawler_each_image.query.filter_by(crawler_each_url_id=url.id).all()
            for image in images:
                image_data.append({
                    'id': image.id,
                    'url': url.url,
                    'image_url': image.image_url
                })

        return jsonify({
            'status': 'success',
            'data': image_data
        })
    except Exception as e:
        current_app.logger.error(f"获取图片数据时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取数据失败: {str(e)}'
        }), 500

@result_bp.route('/security/<int:target_id>')
def get_crawler_security(target_id):
    """获取安全相关数据"""
    try:
        # 检查权限
        permission_result = check_user_permission(target_id=target_id)
        if not isinstance(permission_result, Target):
            return permission_result

        # 获取与目标相关的所有 URL 记录
        urls = crawler_each_url.query.filter_by(target_id=target_id).all()
        if not urls:
            return jsonify({
                'status': 'error',
                'message': '未找到URL记录'
            }), 404

        security_data = []
        for url in urls:
            securities = crawler_each_security.query.filter_by(crawler_each_url_id=url.id).all()
            for security in securities:
                security_data.append({
                    'id': security.id,
                    'url': url.url,
                    'security_name': security.security_name,
                    'security_value': security.security_value
                })

        return jsonify({
            'status': 'success',
            'data': security_data
        })
    except Exception as e:
        current_app.logger.error(f"获取安全数据时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取数据失败: {str(e)}'
        }), 500

@result_bp.route('/<int:target_id>')
def get_result(target_id):
    """获取扫描结果页面"""
    try:
        # 检查权限
        permission_result = check_user_permission(target_id=target_id)
        if not isinstance(permission_result, Target):
            return permission_result
            
        target = permission_result
        
        # 获取请求中的结果类型参数
        result_type = request.args.get('type', '')
        
        if result_type == 'gau':
            # 加载gau结果页面
            return render_template(
                'result/gau_result.html',
                target_id=target_id
            )
        else:
            # 默认加载crawler结果页面
            return render_template(
                'result/crawler_result.html',
                target_id=target_id
            )
            
    except Exception as e:
        current_app.logger.error(f"加载结果页面时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'加载结果页面失败: {str(e)}',
            'code': 500
        }), 500



