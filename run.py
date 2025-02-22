import os
import sys
import signal

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app

def signal_handler(signum, frame):
    """處理退出信號"""
    print('\n正在關閉應用...')
    sys.exit(0)

if __name__ == '__main__':
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app = create_app()
    with app.app_context():
        from instance.models import db
        db.create_all()
    
    # 禁用重載器並使用線程模式
    app.run(
        port=5000,
        debug=True,
        use_reloader=False,
        threaded=True,
        processes=1
    ) 