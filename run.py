import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from instance.models import db
        db.create_all()
    app.run(port=5000, debug=True) 