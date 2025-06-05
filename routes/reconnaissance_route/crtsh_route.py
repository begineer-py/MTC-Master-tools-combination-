from flask import Blueprint, request, jsonify, redirect, url_for, current_app, make_response, render_template
from instance.models import Target, db, crtsh_Result
from reconnaissance.threads.thread_crtsh import crtsh_scan_target
from datetime import datetime
import logging
import time

crtsh_route = Blueprint('crtsh', __name__)
logger = logging.getLogger(__name__)

@crtsh_route.route('/scan/<int:target_id>', methods=['POST','GET'])
def crtsh_scan(target_id):
    client_ip = request.remote_addr
    current_app.logger.debug(f"用戶正在訪問 crtsh 路由，目標 ID: {target_id} {client_ip}")
    
    try:
        # 获取目标信息
        target = Target.query.get_or_404(target_id)
        
        # 檢查是否已存在掃描結果
        existing_result = crtsh_Result.query.filter_by(
            target_id=target_id,
        ).first()
        
        if existing_result:
            # 如果存在舊的結果，先刪除
            try:
                db.session.delete(existing_result)
                db.session.commit()
                current_app.logger.info(f"已刪除舊的掃描結果: target_id={target_id}")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"刪除舊結果時發生錯誤: {str(e)}")
                
        # 執行掃描
        domains, success, message = crtsh_scan_target(target.domain, target_id)
        
        # 記錄域名數量
        current_app.logger.info(f"掃描完成，找到 {len(domains)} 個域名")
        
        # 驗證掃描結果
        if not isinstance(domains, list):
            current_app.logger.error("掃描結果格式無效：domains 不是列表類型")
            return jsonify({
                'status': 'error',
                'message': '掃描結果格式無效',
                'result': {
                    'domains': [],
                    'total': 0,
                    'scan_time': None,
                    'error_message': '返回的域名列表格式無效'
                },
                'code': 400
            }), 400
        
        # 創建新的掃描結果記錄
        scan_time = datetime.now()
        result = crtsh_Result(
            target_id=target_id,
            domains=domains,  # 這裡直接存儲域名列表
            total_domains=len(domains),  # 記錄總數
            status='success' if success else 'failed',
            error_message=None if success else message,
            scan_time=scan_time  # 記錄掃描時間
        )
        
        # 使用重試機制保存到數據庫
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                db.session.add(result)
                db.session.commit()
                current_app.logger.info(f"成功保存掃描結果到數據庫，包含 {len(domains)} 個域名")
                break
            except Exception as e:
                db.session.rollback()
                retry_count += 1
                if retry_count == max_retries:
                    current_app.logger.error(f"保存到數據庫失敗，已重試 {max_retries} 次: {str(e)}")
                    raise
                current_app.logger.warning(f"保存到數據庫時發生錯誤，正在重試 ({retry_count}/{max_retries}): {str(e)}")
                time.sleep(1)  # 等待1秒後重試
        
        # 返回響應
        response_data = {
            'success': True if success else False,
            'message': '掃描完成' if success else message,
            'result': {
                'domains': domains,
                'total': len(domains),
                'scan_time': scan_time.timestamp(),
                'error_message': None if success else message
            },
            'code': 200 if success else 500
        }
        
        return jsonify(response_data), 200 if success else 500
    
    except Exception as e:
        # 記錄異常
        current_app.logger.exception(f"執行 crt.sh 掃描時發生錯誤: {str(e)}")
        
        # 返回錯誤響應
        return jsonify({
            'success': False,
            'message': f'執行掃描時發生錯誤: {str(e)}',
            'result': {
                'domains': [],
                'total': 0,
                'scan_time': None,
                'error_message': str(e)
            },
            'code': 500
        }), 500

@crtsh_route.route('/result/<int:target_id>', methods=['GET'])
def get_latest_crtsh_result(target_id):
    """獲取最新的 crt.sh 掃描結果"""
    try:
        # 获取目标信息
        target = Target.query.get_or_404(target_id)
        
        # 查詢數據庫獲取最新結果
        result = crtsh_Result.query.filter_by(target_id=target_id).order_by(crtsh_Result.scan_time.desc()).first()
        
        if not result:
            return jsonify({
                'success': False,
                'message': '未找到掃描結果',
                'status': 'not_found'
            }), 404
        
        # 返回結果
        result_dict = result.to_dict()
        
        # 添加額外的統計信息
        if result_dict.get('domains'):
            domain_stats = {
                'total': len(result_dict['domains']),
                'unique_subdomains': len(set(result_dict['domains'])),
                'wildcard_domains': len([d for d in result_dict['domains'] if d.startswith('*.')]),
                'main_domain_count': len([d for d in result_dict['domains'] if not d.startswith('*.')])
            }
            result_dict['domain_statistics'] = domain_stats
        
        return jsonify({
            'success': True,
            'result': result_dict,
            'target_info': {
                'id': target.id,
                'domain': target.domain,
                'target_port': target.target_port
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取 crt.sh 掃描結果時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取掃描結果失败: {str(e)}'
        }), 500

@crtsh_route.route('/status/<int:target_id>', methods=['GET'])
def get_scan_status(target_id):
    """获取掃描状态"""
    try:
        # 檢查是否有結果
        crtsh_result = crtsh_Result.query.filter_by(target_id=target_id).order_by(crtsh_Result.scan_time.desc()).first()
        
        if crtsh_result:
            if crtsh_result.status == 'success':
                return jsonify({
                    'success': True,
                    'status': 'completed',
                    'message': '掃描已完成，結果可用'
                })
            elif crtsh_result.status == 'failed':
                return jsonify({
                    'success': True,
                    'status': 'error',
                    'message': f'掃描失敗: {crtsh_result.error_message}'
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

@crtsh_route.route('/history/<int:target_id>', methods=['GET'])
def get_scan_history(target_id):
    """获取掃描历史"""
    try:
        # 获取所有掃描结果
        results = crtsh_Result.query.filter_by(target_id=target_id).order_by(crtsh_Result.scan_time.desc()).all()
        
        history = []
        for result in results:
            result_dict = result.to_dict()
            history.append({
                'scan_time': result_dict['scan_time'],
                'status': result.status,
                'domain_count': len(result_dict.get('domains', [])),
                'total_domains': result.total_domains,
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

@crtsh_route.route('/dashboard', methods=['GET'])
def crtsh_dashboard():
    """crt.sh 掃描器現代化界面"""
    try:
        current_app.logger.info("正在載入 crt.sh 掃描器界面")
        
        # 獲取 URL 參數
        target_id = request.args.get('target_id', '')
        
        # 使用分離的模板文件
        return render_template('crtsh_htmls/dashboard.html', target_id=target_id)
        
    except Exception as e:
        current_app.logger.error(f"載入 crt.sh 掃描器界面時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'載入界面失敗: {str(e)}'
        }), 500

@crtsh_route.route('/help', methods=['GET'])
def crtsh_help():
    """crt.sh API 使用說明"""
    help_info = {
        'title': 'crt.sh 子域名掃描器 API',
        'description': '使用 crt.sh 服務進行子域名發現和證書透明度日誌查詢',
        'endpoints': [
            {
                'method': 'POST',
                'path': '/api/crtsh/scan/<target_id>',
                'description': '啟動 crt.sh 掃描',
                'parameters': {
                    'target_id': '目標 ID（路徑參數）'
                },
                'response': {
                    'success': '是否成功',
                    'message': '響應消息',
                    'result': {
                        'domains': '發現的域名列表',
                        'total': '域名總數',
                        'scan_time': '掃描時間戳',
                        'error_message': '錯誤信息（如有）'
                    }
                }
            },
            {
                'method': 'GET',
                'path': '/api/crtsh/result/<target_id>',
                'description': '獲取掃描結果',
                'response': {
                    'success': '是否成功',
                    'result': '掃描結果詳情',
                    'target_info': '目標信息'
                }
            },
            {
                'method': 'GET',
                'path': '/api/crtsh/status/<target_id>',
                'description': '獲取掃描狀態',
                'response': {
                    'success': '是否成功',
                    'status': '掃描狀態（not_started/scanning/completed/error）',
                    'message': '狀態描述'
                }
            },
            {
                'method': 'GET',
                'path': '/api/crtsh/history/<target_id>',
                'description': '獲取掃描歷史',
                'response': {
                    'success': '是否成功',
                    'history': '歷史記錄列表'
                }
            },
            {
                'method': 'GET',
                'path': '/api/crtsh/dashboard',
                'description': '訪問 crt.sh 掃描器界面',
                'parameters': {
                    'target_id': '目標 ID（可選查詢參數）'
                }
            }
        ],
        'usage_example': {
            'scan': 'POST /api/crtsh/scan/1',
            'get_result': 'GET /api/crtsh/result/1',
            'check_status': 'GET /api/crtsh/status/1',
            'view_dashboard': 'GET /api/crtsh/dashboard?target_id=1'
        },
        'features': [
            '證書透明度日誌查詢',
            '子域名自動發現',
            '實時掃描狀態更新',
            '歷史記錄管理',
            '結果導出功能',
            '現代化 Web 界面'
        ]
    }
    
    return jsonify(help_info)

@crtsh_route.route('/download/<int:target_id>', methods=['GET'])
def download_crtsh_result(target_id):
    """下載 crt.sh 掃描結果為文本文件"""
    try:
        # 獲取目標信息
        target = Target.query.get_or_404(target_id)
        
        # 查詢數據庫獲取最新結果
        result = crtsh_Result.query.filter_by(target_id=target_id).order_by(crtsh_Result.scan_time.desc()).first()
        
        if not result or not result.domains:
            return jsonify({
                'status': 'error',
                'message': '沒有可用的掃描結果',
                'code': 404
            }), 404
        
        # 生成文本內容
        domains = result.domains
        content = f"# crt.sh 子域名掃描結果\n"
        content += f"# 目標: {target.domain}\n"
        content += f"# 掃描時間: {result.scan_time}\n"
        content += f"# 總域名數: {len(domains)}\n\n"
        
        # 添加每個域名
        for i, domain in enumerate(domains, 1):
            content += f"{i}. {domain}\n"
        
        # 創建響應對象
        response = make_response(content)
        response.headers["Content-Disposition"] = f"attachment; filename=crtsh_results_{target.domain}_{int(time.time())}.txt"
        response.headers["Content-Type"] = "text/plain"
        
        return response
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'code': 500
        }), 500
        

