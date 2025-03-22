import os
from flask import Blueprint

linksfinder_blueprint = Blueprint('linksfinder_blueprint', __name__)

@linksfinder_blueprint.route('/linksfinder_scan')
def linksfinder_scan(user_id,target_id):
    pass    
