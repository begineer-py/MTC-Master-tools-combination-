from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from instance.models import Target
from utils.permission import check_user_permission
from reconnaissance.scanner_flaresolverr.check_cloudflare import check_cloudflare
from reconnaissance.scanner_flaresolverr.start_flaresolverr import start_flaresolverr
from reconnaissance.scanner_flaresolverr.run_cloudflare_pass import CloudflareHarvester
import logging

flaresolverr_route = Blueprint('flaresolverr', __name__)
logger = logging.getLogger(__name__)

@flaresolverr_route.route('/scan/<int:user_id>/<int:target_id>', methods=['POST'])
@login_required
def start_flaresolverr_scan(user_id, target_id, limit=1000):
    try:
        # 檢查用戶權限
        permission_result = check_user_permission(current_user.id, target_id)
        if not isinstance(permission_result, Target):
            return permission_result
        if not isinstance(permission_result, Target):
            return redirect(url_for('index.login'))
        target = permission_result
        
        # 檢查 FlareSolverr 服務    
        flaresolverr_status = start_flaresolverr()
        if not flaresolverr_status:
            logger.error("FlareSolverr 服務啟動失敗")
            return jsonify({
                'success': False,
                'message': 'FlareSolverr 服務啟動失敗，請檢查 Docker 狀態'
            }), 500

        # 檢查是否使用 Cloudflare
        is_cloudflare, message = check_cloudflare(target.target_ip)
        logger.info(f"Cloudflare 檢查結果: {message}")
        
        # 创建并执行爬虫任务
        crawler_pass = CloudflareHarvester(user_id=user_id, target_id=target_id, limit=limit)
        success, message = crawler_pass.process_target(user_id=user_id, target_id=target_id)

        if success:
            return jsonify({
                'success': True,
                'message': '掃描任務已啟動',
                'is_cloudflare': is_cloudflare,
                'details': message
            })
        else:
            logger.error(f"爬蟲任務失敗: {message}")
            return jsonify({
                'success': False,
                'message': f'爬蟲任務失敗: {message}'
            }), 500

    except Exception as e:
        logger.error(f"執行過程出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'執行過程出錯：{str(e)}'
        }), 500 