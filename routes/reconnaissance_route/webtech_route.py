from flask import Blueprint, request, jsonify, current_app, render_template

from instance.models import Target, webtech_Result, db
from reconnaissance.threads.thread_webtech import WebTechScanThread
import os
import json
from config.config import LogConfig

# 创建蓝图
webtech_route = Blueprint('webtech_route', __name__)


@webtech_route.route('/start/<int:target_id>', methods=['POST'])
def webtech_start(target_id):
    """启动 WebTech 扫描"""
    logger = LogConfig.get_context_logger()
    client_ip = request.remote_addr
    current_app.logger.debug(
        f"正在访问 webtech 路由，目标 ID: {target_id} {request.remote_addr}")
    logger.info(f"收到 WebTech 掃描請求，目標ID: {target_id}, 客戶端IP: {client_ip}")

    try:
        # 获取目标信息
        target = Target.query.get_or_404(target_id)

        # 获取目标信息
        target_data = {
            'id': target.id,
            'target_ip': target.target_ip,
            'domain': target.domain,
            'deep_scan': target.deep_scan
        }

        # 启动扫描
        target_id = WebTechScanThread.start_webtech_scan(
            target_id, target_data)
        logger.info(f"WebTech 掃描已啟動，目標ID: {target_id}")

        return jsonify({'success': True, 'message': '扫描已启动', 'target_id': target_id})
    except Exception as e:
        current_app.logger.error(f"启动 WebTech 扫描时出错: {str(e)}")
        logger.error(f"啟動 WebTech 掃描時出錯: {str(e)}")
        return jsonify({'success': False, 'message': f'启动扫描失败: {str(e)}'}), 500


@webtech_route.route('/result/<int:target_id>', methods=['GET'])
def webtech_result(target_id):
    """获取 WebTech 扫描结果"""
    logger = LogConfig.get_context_logger()
    try:
        logger.info(f"獲取 WebTech 掃描結果，目標ID: {target_id}")

        # 获取目标信息
        target = Target.query.get_or_404(target_id)

        # 查询扫描结果
        webtech_result = webtech_Result.query.filter_by(
            target_id=target_id).first()

        if not webtech_result:
            logger.warning(f"未找到 WebTech 掃描結果，目標ID: {target_id}")
            return jsonify({
                'success': False,
                'message': '未找到扫描结果'
            }), 404

        # 使用to_dict()方法获取结果字典
        result_dict = webtech_result.to_dict()

        # 添加目标信息
        result_dict['target'] = {
            'id': target.id,
            'target_ip': target.target_ip,
            'domain': target.domain
        }

        logger.info(f"成功獲取 WebTech 掃描結果，目標ID: {target_id}")

        return jsonify({
            'success': True,
            'result': result_dict
        })

    except Exception as e:
        current_app.logger.error(f"获取 WebTech 扫描结果时出错: {str(e)}")
        logger.error(f"獲取 WebTech 掃描結果時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取扫描结果失败: {str(e)}'
        }), 500


@webtech_route.route('/check/<int:target_id>', methods=['GET'])
def check_cloudflare(target_id):
    """检查目标是否使用了Cloudflare"""
    logger = LogConfig.get_context_logger()
    try:
        logger.info(f"檢查 Cloudflare 使用情況，目標ID: {target_id}")

        # 检查权限
        target = Target.query.filter_by(id=target_id).first()  # 获取目标对象

        # 获取WebTech扫描结果
        webtech_result = webtech_Result.query.filter_by(
            target_id=target_id).first()

        if not webtech_result:
            logger.warning(
                f"未找到 WebTech 掃描結果進行 Cloudflare 檢查，目標ID: {target_id}")
            return jsonify({
                'success': False,
                'message': '未找到WebTech扫描结果，请先进行扫描'
            }), 404

        cloudflare_status = webtech_result.if_cloudflare
        logger.info(
            f"Cloudflare 檢查完成，目標ID: {target_id}, 使用 Cloudflare: {cloudflare_status}")

        return jsonify({
            'success': True,
            'is_cloudflare': cloudflare_status,
            'web_tech': webtech_result.web_tech
        })

    except Exception as e:
        current_app.logger.error(f"检查Cloudflare时出错: {str(e)}")
        logger.error(f"檢查 Cloudflare 時出錯: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'检查失败: {str(e)}'
        }), 500
