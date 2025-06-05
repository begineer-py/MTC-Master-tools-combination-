from flask import Blueprint, jsonify, request, current_app, send_file, render_template
from instance.models import db, Target, gau_results
from reconnaissance.threads.thread_gau import start_gau_scan
import os
import json
from datetime import datetime
import time
from functools import lru_cache
from sqlalchemy import text

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

def _check_database_health():
    """檢查數據庫健康狀態並嘗試修復"""
    try:
        # 簡單的數據庫連接測試
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        return True
    except Exception as e:
        current_app.logger.warning(f"數據庫健康檢查失敗: {str(e)}")
        try:
            # 嘗試回滾並重新連接
            db.session.rollback()
            db.session.close()
            # 重新測試
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            current_app.logger.info("數據庫連接已修復")
            return True
        except Exception as e2:
            current_app.logger.error(f"數據庫修復失敗: {str(e2)}")
            return False

@gau_blueprint.route('/scan/<int:target_id>', methods=['POST', 'GET'])
def gau_scan(target_id):
    """启动 Gau 扫描"""

    target = Target.query.get_or_404(target_id)
    
    try:
        # 获取扫描参数
        data = request.get_json() or {}
        threads = data.get('threads', 3)
        providers = data.get('providers', ['wayback', 'commoncrawl', 'otx'])
        exclude_extensions = data.get('exclude_extensions', [])
        blacklist = data.get('blacklist', '')  # 新增：直接接收 blacklist 參數
        
        verbose = data.get('verbose', False)
        
        current_app.logger.info(f"Scan parameters: threads={threads}, providers={providers}, exclude_extensions={exclude_extensions}, blacklist={blacklist}")
        
        # 使用 domain 字段而不是 target_ip_no_https
        domain = target.domain
        if not domain:
            # 如果 domain 为空，尝试从 target_ip 中提取
            domain = target.target_ip.replace('https://', '').replace('http://', '').split('/')[0]
        
        # 檢查數據庫健康狀態
        if not _check_database_health():
            return jsonify({
                'success': False,
                'message': '數據庫連接異常，請稍後重試'
            }), 503
        
        # 使用重試機制處理數據庫操作
        max_retries = 3
        retry_delay = 0.5  # 500ms
        
        for attempt in range(max_retries):
            try:
                # 检查是否已存在扫描结果
                existing_result = gau_results.query.filter_by(target_id=target_id).first()
                
                if existing_result:
                    # 删除旧结果
                    db.session.delete(existing_result)
                    current_app.logger.info(f"已删除旧的扫描结果: target_id={target_id}")
                
                # 创建新的扫描记录
                new_result = gau_results(
                    target_id=target_id,
                    domain=domain,
                    status='scanning'
                )
                
                db.session.add(new_result)
                db.session.commit()
                current_app.logger.info(f"创建新的扫描记录: target_id={target_id}, domain={domain}")
                break  # 成功則跳出重試循環
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning(f"數據庫操作失敗 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt == max_retries - 1:
                    # 最後一次嘗試失敗
                    current_app.logger.error(f"创建扫描记录失败，已重試 {max_retries} 次: {str(e)}")
                    return jsonify({
                        'success': False,
                        'message': f'数据库繁忙，请稍后重试: {str(e)}'
                    }), 503  # Service Unavailable
                else:
                    # 等待後重試
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指數退避
        
        # 启动后台扫描任务
        # 處理排除文件類型
        final_blacklist = ''
        if blacklist:
            # 如果直接提供了 blacklist 字符串，使用它
            final_blacklist = blacklist
        elif exclude_extensions:
            # 如果提供了 exclude_extensions 列表，轉換為字符串
            if isinstance(exclude_extensions, list):
                final_blacklist = ','.join(exclude_extensions)
            else:
                final_blacklist = str(exclude_extensions)
        else:
            # 默認排除的文件類型
            final_blacklist = 'ttf,woff,svg,png,jpg,gif,jpeg,ico'
        
        options = {
            'threads': threads,
            'providers': ','.join(providers) if isinstance(providers, list) else str(providers),
            'blacklist': final_blacklist,
            'verbose': verbose
        }
        
        current_app.logger.info(f"Final scan options: {options}")
        
        scan_id = start_gau_scan(target_id, domain, options)
        
        return jsonify({
            'success': True,
            'message': 'Gau 扫描已启动',
            'scan_id': scan_id,
            'target_id': target_id,
            'domain': domain,
            'estimated_time': '1-3分钟'
        })
        
    except Exception as e:
        current_app.logger.error(f"启动 Gau 扫描时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动扫描失败: {str(e)}'
        }), 500

# 移除 LRU 緩存，改用簡單查詢
def _get_scan_result_cached(target_id):
    """获取扫描结果"""
    try:
        return gau_results.query.filter_by(
            target_id=target_id
        ).order_by(gau_results.scan_time.desc()).first()
    except Exception as e:
        current_app.logger.error(f"查询扫描结果时出错: {str(e)}")
        return None

@gau_blueprint.route('/result/<int:target_id>', methods=['GET'])
def gau_get_result(target_id):
    """获取 Gau 扫描结果"""
    current_app.logger.info(f"DEBUG: gau_get_result called with target_id={target_id}")
    
    target = Target.query.get_or_404(target_id)
    
    try:
        # 检查是否只需要元数据
        metadata_only = request.args.get('metadata', '') == 'only'
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
        current_app.logger.info(f"DEBUG: Query parameters - page={page}, per_page={per_page}, category={category}")
        
        # 获取扫描结果
        scan_result = gau_results.query.filter_by(target_id=target_id).first()
        
        current_app.logger.info(f"DEBUG: scan_result found: {scan_result is not None}")
        
        if not scan_result:
            response_data = {
                'success': True,  # 改為 True，因為查詢成功，只是沒有結果
                'message': '未找到扫描结果',
                'result': {
                    'status': 'not_started',
                    'total_urls': 0,
                    'urls': [],
                    'categories': {
                        'all': 0,
                        'js': 0,
                        'api': 0,
                        'image': 0,
                        'css': 0,
                        'doc': 0,
                        'other': 0
                    },
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': 0,
                        'pages': 0,
                        'total_pages': 0
                    }
                }
            }
            current_app.logger.info(f"DEBUG: Returning no result response: {response_data}")
            return jsonify(response_data)
        
        # 如果只需要元数据
        if metadata_only:
            return jsonify({
                'success': True,
                'result': {
                    'status': scan_result.status,
                    'total_urls': scan_result.total_urls,
                    'domain': scan_result.domain,
                    'scan_time': scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S') if scan_result.scan_time else None,
                    'error_message': scan_result.error_message
                }
            })
        
        # 获取 URL 列表
        urls = scan_result.urls or []
        
        # 分类统计
        categories = _categorize_urls(urls)
        
        # 过滤 URL
        filtered_urls = urls
        if category and category != 'all' and category in categories:
            filtered_urls = [url for url in urls if _get_url_category(url) == category]
        
        if search:
            filtered_urls = [url for url in filtered_urls if search.lower() in url.lower()]
        
        # 分页处理
        total = len(filtered_urls)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_urls = filtered_urls[start:end]
        
        return jsonify({
            'success': True,
            'result': {
                'status': scan_result.status,
                'total_urls': scan_result.total_urls,
                'domain': scan_result.domain,
                'scan_time': scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S') if scan_result.scan_time else None,
                'error_message': scan_result.error_message,
                'urls': paginated_urls,
                'categories': categories,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page,
                    'total_pages': (total + per_page - 1) // per_page  # 添加 total_pages 以保持兼容性
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取 Gau 扫描结果时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取结果失败: {str(e)}'
        }), 500

@gau_blueprint.route('/status/<int:target_id>', methods=['GET'])
def get_scan_status(target_id):
    """获取掃描状态"""
    try:
        # 檢查是否有結果
        gau_result = gau_results.query.filter_by(target_id=target_id).order_by(gau_results.scan_time.desc()).first()
        
        if gau_result:
            if gau_result.status == 'completed':
                return jsonify({
                    'success': True,
                    'status': 'completed',
                    'message': '掃描已完成，結果可用'
                })
            elif gau_result.status == 'failed':
                return jsonify({
                    'success': True,
                    'status': 'error',
                    'message': f'掃描失敗: {gau_result.error_message}'
                })
            elif gau_result.status == 'scanning':
                return jsonify({
                    'success': True,
                    'status': 'scanning',
                    'message': '掃描正在進行中...'
                })
            else:
                return jsonify({
                    'success': True,
                    'status': 'scanning',
                    'message': '掃描正在進行中...'
                })
        else:
            return jsonify({
                'success': True,
                'status': 'not_started',
                'message': '尚未開始掃描'
            })
            
    except Exception as e:
        current_app.logger.error(f"获取掃描状态時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500

@gau_blueprint.route('/history/<int:target_id>', methods=['GET'])
def get_scan_history(target_id):
    """获取掃描历史"""
    try:
        # 获取所有掃描结果
        results = gau_results.query.filter_by(target_id=target_id).order_by(gau_results.scan_time.desc()).all()
        
        history = []
        for result in results:
            history.append({
                'scan_time': result.scan_time.timestamp() if result.scan_time else None,
                'status': result.status,
                'url_count': result.total_urls or 0,
                'total_urls': result.total_urls or 0,
                'error_message': result.error_message
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        current_app.logger.error(f"获取掃描历史時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取历史失败: {str(e)}'
        }), 500

@gau_blueprint.route('/dashboard', methods=['GET'])
def gau_dashboard():
    """Gau URL 掃描器現代化界面"""
    try:
        current_app.logger.info("正在載入 Gau 掃描器界面")
        
        # 獲取 URL 參數
        target_id = request.args.get('target_id', '')
        
        # 使用分離的模板文件
        return render_template('gau_htmls/dashboard.html', target_id=target_id)
        
    except Exception as e:
        current_app.logger.error(f"載入 Gau 掃描器界面時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'載入界面失敗: {str(e)}'
        }), 500

@gau_blueprint.route('/help', methods=['GET'])
def gau_help():
    """Gau API 使用說明"""
    try:
        # 獲取當前文件的目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        help_file_path = os.path.join(current_dir, 'Gau_help.json')
        
        # 讀取 JSON 文件
        with open(help_file_path, 'r', encoding='utf-8') as f:
            help_info = json.load(f)
        
        return jsonify(help_info)
        
    except FileNotFoundError:
        current_app.logger.error(f"幫助文件未找到: {help_file_path}")
        return jsonify({
            'error': '幫助文檔未找到',
            'message': 'Gau 幫助文件遺失'
        }), 404
    except json.JSONDecodeError as e:
        current_app.logger.error(f"幫助文件中的 JSON 格式無效: {str(e)}")
        return jsonify({
            'error': '幫助文檔格式無效',
            'message': '幫助文件包含無效的 JSON 格式'
        }), 500
    except Exception as e:
        current_app.logger.error(f"載入幫助文檔時出錯: {str(e)}")
        return jsonify({
            'error': '載入幫助文檔失敗',
            'message': str(e)
        }), 500

@gau_blueprint.route('/file/<int:target_id>', methods=['GET'])
def get_gau_file(target_id):
    """获取Gau扫描结果文件"""
    try:
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
        
        current_app.logger.info(f"開始生成文件，URL 總數: {len(result.urls)}")
        
        try:
            # 使用簡單高效的方式寫入文件
            with open(temp_file_path, 'w', encoding='utf-8', errors='replace') as f:
                # 写入文件头部信息
                f.write(f"# Gau扫描结果 - {target.domain}\n")
                f.write(f"# 扫描时间: {result.scan_time}\n")
                f.write(f"# 总URL数: {len(result.urls)}\n")
                f.write("#" + "-" * 50 + "\n\n")
                
                # 分類 URL
                js_urls = []
                api_urls = []
                image_urls = []
                css_urls = []
                doc_urls = []
                other_urls = []
                
                # 一次性分類所有 URL
                for url in result.urls:
                    url_lower = url.lower()
                    if any(ext in url_lower for ext in ['.js', 'javascript']):
                        js_urls.append(url)
                    elif any(ext in url_lower for ext in ['/api/', '/v1/', '/v2/', '.json', '.xml']):
                        api_urls.append(url)
                    elif any(ext in url_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp']):
                        image_urls.append(url)
                    elif any(ext in url_lower for ext in ['.css', '.scss', '.sass']):
                        css_urls.append(url)
                    elif any(ext in url_lower for ext in ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']):
                        doc_urls.append(url)
                    else:
                        other_urls.append(url)
                
                # 寫入分類的 URL
                categories = [
                    ("JavaScript 文件", js_urls),
                    ("API 端點", api_urls),
                    ("圖片文件", image_urls),
                    ("CSS 文件", css_urls),
                    ("文檔文件", doc_urls),
                    ("其他 URL", other_urls)
                ]
                
                for category_name, category_urls in categories:
                    if category_urls:
                        f.write(f"\n# {category_name} ({len(category_urls)} 个)\n")
                        f.write("#" + "-" * 30 + "\n")
                        for url in category_urls:
                            f.write(f"{url}\n")
                
                current_app.logger.info(f"文件生成完成: {temp_file_path}")
                
        except Exception as e:
            current_app.logger.error(f"文件生成錯誤: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'文件生成失敗: {str(e)}',
                'code': 500
            }), 500
        
        # 返回文件
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=f"gau_results_{target.domain}_{target_id}.txt",
            mimetype='text/plain'
        )
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'code': 500
        }), 500

# 輔助函數
def _categorize_urls(urls):
    """對 URL 進行分類統計"""
    categories = {
        'all': len(urls),
        'js': 0,
        'api': 0,
        'image': 0,
        'css': 0,
        'doc': 0,
        'other': 0
    }
    
    for url in urls:
        category = _get_url_category(url)
        if category in categories:
            categories[category] += 1
    
    return categories

def _get_url_category(url):
    """獲取 URL 的分類"""
    url_lower = url.lower()
    
    if any(ext in url_lower for ext in ['.js', 'javascript']):
        return 'js'
    elif any(ext in url_lower for ext in ['/api/', '/v1/', '/v2/', '.json', '.xml']):
        return 'api'
    elif any(ext in url_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp']):
        return 'image'
    elif any(ext in url_lower for ext in ['.css', '.scss', '.sass']):
        return 'css'
    elif any(ext in url_lower for ext in ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']):
        return 'doc'
    else:
        return 'other'



