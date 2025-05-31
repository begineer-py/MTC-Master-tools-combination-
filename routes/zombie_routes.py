from flask import Blueprint, jsonify, request
from instance.models import db
import logging
from datetime import datetime

zombie_bp = Blueprint('zombie', __name__)

@zombie_bp.route('/zombies', methods=['GET'])
def get_zombies():
    """獲取所有肉雞的資訊"""
    # 此功能已删除，返回空列表
    return jsonify({
        'status': 'success',
        'zombies': []
    })

@zombie_bp.route('/zombie_commands', methods=['POST'])
def execute_zombie_command():
    """執行肉雞命令"""
    # 此功能已删除，返回成功响应但不执行任何操作
    return jsonify({
        'status': 'success',
        'message': '该功能已被移除'
    }) 