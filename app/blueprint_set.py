import os 
from flask import Blueprint

def create_blueprints(app):
    from routes.zombie_routes import zombie_bp
    from routes.user_dashboard_routes import user_bp
    from routes.index_routes import index_bp

