import os
from flask import Blueprint, request, jsonify, current_app, render_template
from config.config import LogConfig
from flask_cors import CORS


linksfinder_blueprint = Blueprint('linksfinder_blueprint', __name__)
CORS(linksfinder_blueprint, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
     allow_headers="*", supports_credentials=True, expose_headers="*")


@linksfinder_blueprint.route('/linksfinder_scan/<int:target_id>')
def linksfinder_scan(target_id):
    logger = LogConfig.get_context_logger()
    logger.info(f"LinksFinder 掃描請求，目標ID: {target_id}")
    pass
