from flask import Blueprint, jsonify, request, current_app, send_file
from utils.decorators import login_required
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
        # 缓存超过60秒过期 (从30秒增加到60秒)
        if now - timestamp > 60:
            expired_keys.append(key)
    
    for key in expired_keys:
        if key in _result_cache:
            del _result_cache[key]
        if key in _cache_timestamp:
            del _cache_timestamp[key]

@gau_blueprint.route('/scan/<int:target_id>', methods=['POST'])
def gau_scan(target_id):
    """
    启动 Gau 扫描
    
    请求体参数:
    {
        "threads": number,        // 可选，默认 50，线程数量
        "verbose": boolean,       // 可选，默认 false，是否显示详细信息
        "providers": string,      // 可选，默认 "wayback,commoncrawl,otx,urlscan"，数据提供者
        "blacklist": string       // 可选，默认 "ttf,woff,svg,png,jpg,gif,jpeg,ico"，排除的文件类型
    }
    """
    # 使用权限检查函数
    result = check_user_permission(target_id=target_id)
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
        
        # 启动新扫描，直接使用target_id
        scan_target_id = start_gau_scan(target_id, domain, options)
        
        return jsonify({
            'success': True,
            'message': '扫描已启动',
            'target_id': scan_target_id
        })
    except Exception as e:
        current_app.logger.error(f"启动 Gau 扫描时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动扫描失败: {str(e)}'
        }), 500

# 使用LRU缓存加速常用查询
@lru_cache(maxsize=32)
def _get_scan_result_cached(target_id):
    """获取缓存的扫描结果"""
    return gau_results.query.filter_by(
        target_id=target_id
    ).order_by(gau_results.scan_time.desc()).first()

@gau_blueprint.route('/result/<int:target_id>', methods=['GET'])
def gau_get_result(target_id):
    """获取 Gau 扫描结果"""
    # 使用权限检查函数
    result = check_user_permission(target_id=target_id)
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
        
        # 查询最新的扫描结果 (使用缓存)
        scan_result = _get_scan_result_cached(target_id)
        
        if not scan_result:
            response = jsonify({
                'success': True,
                'message': '未找到扫描结果',
                'result': None
            })
            return response
        
        # 安全生成缓存键，确保类型正确
        try:
            # 避免使用布尔值作为字符串的一部分
            metadata_str = "metadata_only" if metadata_only else "full_data"
            cache_key = f"{target_id}_{metadata_str}_{page}_{per_page}_{category}_{search}"
            
            # 检查缓存是否有效
            if not _cache_lock and cache_key in _result_cache:
                # 清理过期缓存
                _clean_expired_cache()
                return _result_cache[cache_key]
        except Exception as e:
            current_app.logger.warning(f"生成缓存键时出错: {str(e)}")
            # 出错时不使用缓存
            cache_key = None
        
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
            
            # 缓存结果 (如果缓存键有效)
            if cache_key:
                _result_cache[cache_key] = response
                _cache_timestamp[cache_key] = time.time()
            
            return response
        
        # 获取完整结果
        urls = scan_result.urls or []
        
        # 对URL进行分类 - 优化为单次遍历
        categories = {
            'all': 0,
            'js': 0,
            'api': 0,
            'image': 0,
            'css': 0,
            'doc': 0,
            'other': 0
        }
        
        # 过滤URL
        filtered_urls = []
        
        # 单次遍历优化：根据类别和搜索词过滤URL
        for url in urls:
            # 确保URL是字符串
            if not isinstance(url, str):
                continue
                
            # 分类URL并同时过滤
            url_category = 'other'  # 默认分类
            
            if '.js' in url or '/js/' in url:
                url_category = 'js'
            elif '/api/' in url or '/rest/' in url or '/v1/' in url or '/v2/' in url:
                url_category = 'api'
            elif any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']):
                url_category = 'image'
            elif any(ext in url for ext in ['.css', '.scss', '.less']):
                url_category = 'css'
            elif any(ext in url for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']):
                url_category = 'doc'
            
            # 更新分类计数
            categories[url_category] += 1
            categories['all'] += 1
            
            # 检查是否满足当前选择的类别
            if category != 'all' and category != url_category:
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
        
        # 缓存结果 (如果缓存键有效)
        if cache_key:
            _result_cache[cache_key] = response
            _cache_timestamp[cache_key] = time.time()
        
        return response
    except Exception as e:
        current_app.logger.error(f"获取 Gau 扫描结果时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取扫描结果失败: {str(e)}'
        }), 500

@gau_blueprint.route('/file/<int:target_id>', methods=['GET'])
def get_gau_file(target_id):
    """获取Gau扫描结果文件"""
    try:
        # 检查权限
        permission_result = check_user_permission(target_id=target_id)
        if not isinstance(permission_result, Target):
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
        
        # 检查是否存在缓存文件
        cache_file_path = os.path.join(current_app.config['TEMP_FOLDER'], f"gau_results_{target.domain}_{target_id}.txt")
        if os.path.exists(cache_file_path) and os.path.getmtime(cache_file_path) > (time.time() - 3600):  # 缓存1小时
            # 返回缓存文件
            return send_file(
                cache_file_path,
                as_attachment=True,
                download_name=f"gau_results_{target.domain}_{target_id}.txt",
                mimetype='text/plain'
            )
        
        # 确保临时目录存在
        os.makedirs(os.path.dirname(os.path.join(current_app.config['TEMP_FOLDER'], f"temp.txt")), exist_ok=True)
        
        # 创建临时文件
        temp_file_path = os.path.join(current_app.config['TEMP_FOLDER'], f"gau_results_{target.domain}_{target_id}.txt")
        
        # 使用更高效的方式写入文件
        with open(temp_file_path, 'w', encoding='utf-8', errors='replace', buffering=1024*1024) as f:  # 1MB缓冲区
            # 写入文件头部信息
            f.write(f"# Gau扫描结果 - {target.domain}\n")
            f.write(f"# 扫描时间: {result.scan_time}\n")
            f.write(f"# 总URL数: {len(result.urls)}\n")
            f.write("#" + "-" * 50 + "\n\n")
            
            # 使用单次遍历分类URL
            js_urls = []
            api_urls = []
            image_urls = []
            css_urls = []
            doc_urls = []
            other_urls = []
            
            # 预分配内存
            urls = result.urls
            url_count = len(urls)
            
            # 计算大概的内存分配
            estimated_js = int(url_count * 0.15)  # 假设15%是JS
            estimated_api = int(url_count * 0.10)  # 假设10%是API
            estimated_other = int(url_count * 0.50)  # 假设50%是其他
            
            # 预分配
            js_urls = [None] * estimated_js
            api_urls = [None] * estimated_api
            other_urls = [None] * estimated_other
            image_urls = []
            css_urls = []
            doc_urls = []
            
            # 实际填充的计数
            js_count = 0
            api_count = 0
            other_count = 0
            
            for url in urls:
                # 确保URL是字符串
                if not isinstance(url, str):
                    continue
                    
                if '.js' in url or '/js/' in url:
                    if js_count < estimated_js:
                        js_urls[js_count] = url
                        js_count += 1
                    else:
                        js_urls.append(url)
                elif '/api/' in url or '/rest/' in url or '/v1/' in url or '/v2/' in url:
                    if api_count < estimated_api:
                        api_urls[api_count] = url
                        api_count += 1
                    else:
                        api_urls.append(url)
                elif any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']):
                    image_urls.append(url)
                elif any(ext in url.lower() for ext in ['.css', '.scss', '.less']):
                    css_urls.append(url)
                elif any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']):
                    doc_urls.append(url)
                else:
                    if other_count < estimated_other:
                        other_urls[other_count] = url
                        other_count += 1
                    else:
                        other_urls.append(url)
            
            # 裁剪预分配数组
            js_urls = js_urls[:js_count]
            api_urls = api_urls[:api_count]
            other_urls = other_urls[:other_count]
            
            # 写入JavaScript文件
            if js_urls:
                f.write("## JavaScript文件\n")
                f.write("\n".join(js_urls))
                f.write("\n\n")
            
            # 写入API端点
            if api_urls:
                f.write("## API端点\n")
                f.write("\n".join(api_urls))
                f.write("\n\n")
            
            # 写入其他URL
            if other_urls:
                f.write("## 其他URL\n")
                f.write("\n".join(other_urls))
                f.write("\n\n")
            
            # 写入文档文件
            if doc_urls:
                f.write("## 文档文件\n")
                f.write("\n".join(doc_urls))
                f.write("\n\n")
            
            # 写入CSS文件
            if css_urls:
                f.write("## CSS文件\n")
                f.write("\n".join(css_urls))
                f.write("\n\n")
            
            # 写入图片文件
            if image_urls:
                f.write("## 图片文件\n")
                f.write("\n".join(image_urls))
        
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



