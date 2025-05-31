import os
from flask import Blueprint

linksfinder_blueprint = Blueprint('linksfinder_blueprint', __name__)

@linksfinder_blueprint.route('/linksfinder_scan/<int:target_id>')
def linksfinder_scan(target_id):
    pass    
