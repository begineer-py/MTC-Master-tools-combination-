from flask import Blueprint, jsonify, request, current_app, send_file
from flask_login import login_required, current_user
from utils.permission import check_user_permission
from instance.models import db, Target, gau_results
from reconnaissance.threads.thread_gau import start_gau_scan
import os
import json
from datetime import datetime
import time
from functools import lru_cache

# 创建蓝图
gau_blueprint = Blueprint('gau', __name__, url_prefix='')

# 结果缓存
_result_cache = {}
_cache_timestamp = {}
_cache_lock = False

# 缓存清理函数
def _clean_expired_cache():
    """清理过期缓存"""
    now = time.time()
    expired_keys = []
    for key, timestamp in _cache_timestamp.items():
        # 缓存超过30秒过期
        if now - timestamp > 30:
            expired_keys.append(key)
    
    for key in expired_keys:
        if key in _result_cache:
            del _result_cache[key]
        if key in _cache_timestamp:
            del _cache_timestamp[key]

@gau_blueprint.route('/scan/<int:user_id>/<int:target_id>', methods=['POST'])
@login_required
def gau_scan(user_id, target_id):
    """
    启动 Gau 扫描
    
    请求体参数:
    {
        "threads": number,        // 可选，默认 10，线程数量
        "verbose": boolean,       // 可选，默认 false，是否显示详细信息
        "providers": string,      // 可选，默认 "wayback,commoncrawl,otx,urlscan"，数据提供者
        "blacklist": string       // 可选，默认 "ttf,woff,svg,png,jpg,gif,jpeg,ico"，排除的文件类型
    }
    """
    # 使用权限检查函数
    result = check_user_permission(user_id, target_id)
    if not isinstance(result, Target):
        return result  # 返回错误响应
    
    target = result  # 获取目标对象
    data = request.get_json() or {}
    options = data
    
    # 自动从目标获取域名
    domain = target.target_ip_no_https
    
    # 启动扫描
    try:
        # 检查是否已有进行中的扫描
        existing_scan = gau_results.query.filter_by(
            target_id=target_id,
            status='scanning'
        ).first()
        
        if existing_scan:
            current_app.logger.info(f"已有进行中的 Gau 扫描，目标 ID: {target_id}")
            return jsonify({
                'success': True,
                'message': '已有进行中的扫描',
                'result': existing_scan.to_dict()
            })
        
        # 启动新扫描
        target_id = start_gau_scan(target_id, user_id, domain, options)
        
        return jsonify({
            'success': True,
            'message': '扫描已启动',
            'target_id': target_id
        })
    except Exception as e:
        current_app.logger.error(f"启动 Gau 扫描时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动扫描失败: {str(e)}'
        }), 500

@gau_blueprint.route('/result/<int:user_id>/<int:target_id>', methods=['GET'])
@login_required
def gau_get_result(user_id, target_id):
    """获取 Gau 扫描结果"""
    # 使用权限检查函数
    result = check_user_permission(user_id, target_id)
    if not isinstance(result, Target):
        return result  # 返回错误响应
    
    try:
        # 检查是否只需要元数据
        metadata_only = request.args.get('metadata', '') == 'only'
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        category = request.args.get('category', 'all')
        search = request.args.get('search', '')
        
        # 限制每页最大数量
        if per_page > 1000:
            per_page = 1000
        
        # 生成缓存键
        cache_key = f"{user_id}_{target_id}_{metadata_only}_{page}_{per_page}_{category}_{search}"
        
        # 检查缓存是否有效
        if not _cache_lock and cache_key in _result_cache:
            # 清理过期缓存
            _clean_expired_cache()
            return _result_cache[cache_key]
        
        # 查询最新的扫描结果
        scan_result = gau_results.query.filter_by(
            target_id=target_id
        ).order_by(gau_results.scan_time.desc()).first()
        
        if not scan_result:
            response = jsonify({
                'success': True,
                'message': '未找到扫描结果',
                'result': None
            })
            return response
        
        # 如果只需要元数据，则不返回URL列表
        if metadata_only:
            result_dict = {
                'id': scan_result.id,
                'target_id': scan_result.target_id,
                'domain': scan_result.domain,
                'total_urls': scan_result.total_urls,
                'status': scan_result.status,
                'error_message': scan_result.error_message,
                'scan_time': scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S') if scan_result.scan_time else None
            }
            
            response = jsonify({
                'success': True,
                'message': '获取扫描结果成功',
                'result': result_dict
            })
            
            # 缓存结果
            _result_cache[cache_key] = response
            _cache_timestamp[cache_key] = time.time()
            
            return response
        
        # 获取完整结果
        urls = scan_result.urls or []
        
        # 对URL进行分类
        categories = {
            'all': len(urls),
            'js': 0,
            'api': 0,
            'image': 0,
            'css': 0,
            'doc': 0,
            'other': 0
        }
        
        # 过滤URL
        filtered_urls = []
        
        # 根据类别和搜索词过滤URL
        for url in urls:
            # 分类URL
            if '.js' in url or '/js/' in url:
                categories['js'] += 1
                if category != 'all' and category != 'js':
                    continue
            elif '/api/' in url or '/rest/' in url or '/v1/' in url or '/v2/' in url:
                categories['api'] += 1
                if category != 'all' and category != 'api':
                    continue
            elif any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']):
                categories['image'] += 1
                if category != 'all' and category != 'image':
                    continue
            elif any(ext in url for ext in ['.css', '.scss', '.less']):
                categories['css'] += 1
                if category != 'all' and category != 'css':
                    continue
            elif any(ext in url for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']):
                categories['doc'] += 1
                if category != 'all' and category != 'doc':
                    continue
            else:
                categories['other'] += 1
                if category != 'all' and category != 'other':
                    continue
            
            # 搜索过滤
            if search and search.lower() not in url.lower():
                continue
            
            filtered_urls.append(url)
        
        # 计算分页
        total_items = len(filtered_urls)
        total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
        
        # 确保页码有效
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        # 获取当前页的URL
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_items)
        current_page_urls = filtered_urls[start_idx:end_idx]
        
        # 构建结果
        result_dict = {
            'id': scan_result.id,
            'target_id': scan_result.target_id,
            'domain': scan_result.domain,
            'urls': current_page_urls,
            'total_urls': scan_result.total_urls,
            'status': scan_result.status,
            'error_message': scan_result.error_message,
            'scan_time': scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S') if scan_result.scan_time else None,
            'categories': categories,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': total_items,
                'total_pages': total_pages
            }
        }
        
        response = jsonify({
            'success': True,
            'message': '获取扫描结果成功',
            'result': result_dict
        })
        
        # 缓存结果
        _result_cache[cache_key] = response
        _cache_timestamp[cache_key] = time.time()
        
        return response
    except Exception as e:
        current_app.logger.error(f"获取 Gau 扫描结果时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取扫描结果失败: {str(e)}'
        }), 500

@gau_blueprint.route('/file/<user_id>/<target_id>', methods=['GET'])
@login_required
def get_gau_file(user_id, target_id):
    """获取Gau扫描结果文件"""
    try:
        # 检查用户权限
        if not current_user.is_admin and str(current_user.id) != str(user_id):
            return jsonify({'success': False, 'message': '无权访问此资源'}), 403
        
        # 查询扫描结果
        result = gau_results.query.filter_by(target_id=target_id).first()
        if not result:
            return jsonify({'success': False, 'message': '未找到扫描结果'}), 404
        
        # 获取目标信息
        target = Target.query.get(target_id)
        if not target:
            return jsonify({'success': False, 'message': '未找到目标信息'}), 404
        
        # 检查是否有URL结果
        if not result.urls or len(result.urls) == 0:
            return jsonify({'success': False, 'message': '扫描结果中没有URL'}), 404
        
        # 创建临时文件
        temp_file_path = os.path.join(current_app.config['TEMP_FOLDER'], f"gau_results_{target.domain}_{target_id}.txt")
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
        # 将URL写入文件，按类别分组
        with open(temp_file_path, 'w', encoding='utf-8', errors='replace') as f:
            # 写入文件头部信息
            f.write(f"# Gau扫描结果 - {target.domain}\n")
            f.write(f"# 扫描时间: {result.scan_time}\n")
            f.write(f"# 总URL数: {len(result.urls)}\n")
            f.write("#" + "-" * 50 + "\n\n")
            
            # 对URL进行分类
            js_urls = []
            api_urls = []
            image_urls = []
            css_urls = []
            doc_urls = []
            other_urls = []
            
            for url in result.urls:
                if '.js' in url or '/js/' in url:
                    js_urls.append(url)
                elif '/api/' in url or '/rest/' in url or '/v1/' in url or '/v2/' in url:
                    api_urls.append(url)
                elif any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']):
                    image_urls.append(url)
                elif any(ext in url.lower() for ext in ['.css', '.scss', '.less']):
                    css_urls.append(url)
                elif any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']):
                    doc_urls.append(url)
                else:
                    other_urls.append(url)
            
            # 写入JavaScript文件
            if js_urls:
                f.write("## JavaScript文件\n")
                for url in js_urls:
                    f.write(f"{url}\n")
                f.write("\n")
            
            # 写入API端点
            if api_urls:
                f.write("## API端点\n")
                for url in api_urls:
                    f.write(f"{url}\n")
                f.write("\n")
            
            # 写入其他URL
            if other_urls:
                f.write("## 其他URL\n")
                for url in other_urls:
                    f.write(f"{url}\n")
                f.write("\n")
            
            # 写入文档文件
            if doc_urls:
                f.write("## 文档文件\n")
                for url in doc_urls:
                    f.write(f"{url}\n")
                f.write("\n")
            
            # 写入CSS文件
            if css_urls:
                f.write("## CSS文件\n")
                for url in css_urls:
                    f.write(f"{url}\n")
                f.write("\n")
            
            # 写入图片文件
            if image_urls:
                f.write("## 图片文件\n")
                for url in image_urls:
                    f.write(f"{url}\n")
        
        # 返回文件
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=f"gau_results_{target.domain}_{target_id}.txt",
            mimetype='text/plain'
        )
    
    except Exception as e:
        current_app.logger.error(f"获取Gau扫描结果文件时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'获取文件时出错: {str(e)}'}), 500



