import os
from flask import Blueprint
from config.config import LogConfig

linksfinder_blueprint = Blueprint('linksfinder_blueprint', __name__)


@linksfinder_blueprint.route('/linksfinder_scan/<int:target_id>')
def linksfinder_scan(target_id):
    logger = LogConfig.get_context_logger()
    logger.info(f"LinksFinder 掃描請求，目標ID: {target_id}")
    pass
