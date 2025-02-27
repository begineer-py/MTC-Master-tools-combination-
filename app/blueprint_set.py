import os 
from flask import Blueprint
from routes.zombie_routes import zombie_bp
from routes.user_dashboard_routes import user_bp
from routes.index_routes import index_bp
from routes.admin_routes import admin_bp
from routes.reconnaissance_route.attack_route import attack_bp
from routes.result_route import result_bp
from routes.attack_vulnerability_route import attack_vulnerability_route
from routes.api_setting.API_ROUTE import api_route
from routes.reconnaissance_route.nmap_route import nmap_route
from routes.reconnaissance_route.crtsh_route import crtsh_route
from routes.reconnaissance_route.webtech_route import webtech_route
from routes.reconnaissance_route.flaresolverr_route import flaresolverr_route
from routes.reconnaissance_route.harvester_route import harvester_route

def register_blueprints(app):
    """註冊所有藍圖"""
    # 定義藍圖和對應的 URL 前綴
    blueprints = [
        (zombie_bp, '/api/zombie'),
        (user_bp, '/user'),
        (index_bp, '/'),
        (admin_bp, '/admin'),
        (attack_bp, None),  # None 表示沒有前綴
        (result_bp, '/result'),
        (attack_vulnerability_route, '/attack/vulnerability'),
        (api_route, '/api'),
        (nmap_route, '/api/nmap'),
        (crtsh_route, '/api/crtsh'),
        (webtech_route, '/api/webtech'),
        (flaresolverr_route, '/api/flaresolverr'),
        (harvester_route, '/api/harvester')
    ]
    
    # 註冊藍圖
    for blueprint, url_prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)

