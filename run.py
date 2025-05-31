import os
import sys
import signal
import time
import traceback
import importlib.util
from sqlalchemy.exc import OperationalError

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 确保必要的目录存在
required_dirs = [
    "instance",
    "instance/backups",
    "instance/tools",
    "logs",
    "flask_session"
]

for directory in required_dirs:
    os.makedirs(directory, exist_ok=True)

def signal_handler(signum, frame):
    """處理退出信號"""
    print('\n正在關閉應用...')
    sys.exit(0)

def load_db_manager():
    """動態加載數據庫管理模塊"""
    db_manager_path = os.path.join(project_root, 'instance', 'tools', 'db_manager.py')
    
    # 如果文件不存在，返回None
    if not os.path.exists(db_manager_path):
        return None
        
    # 動態加載模塊
    spec = importlib.util.spec_from_file_location("db_manager", db_manager_path)
    db_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_manager)
    
    return db_manager

def unlock_database():
    """解鎖數據庫"""
    # 嘗試使用數據庫管理模塊
    db_manager = load_db_manager()
    
    if db_manager:
        db_path = os.path.join(project_root, 'instance', 'c2.db')
        print(f"使用數據庫管理模塊解鎖數據庫: {db_path}")
        
        # 調用數據庫管理模塊的解鎖函數
        db_manager.unlock_database(db_path)
        return True
    
    # 如果無法加載模塊，使用簡單的解鎖方法
    try:
        db_path = os.path.join(project_root, 'instance', 'c2.db')
        db_shm_path = f"{db_path}-shm"
        db_wal_path = f"{db_path}-wal"
        
        # 檢查並刪除鎖文件
        for lock_file in [db_shm_path, db_wal_path]:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"已刪除鎖文件: {lock_file}")
                
        return True
    except Exception as e:
        print(f"解鎖數據庫時出錯: {str(e)}")
        return False

def reset_database():
    """重置数据库（删除并重建）"""
    print("正在重置数据库...")
    try:
        db_path = os.path.join(project_root, 'instance', 'c2.db')
        # 首先解锁数据库
        unlock_database()
        
        # 删除数据库文件
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"已删除数据库文件: {db_path}")
        
        # 删除相关的WAL和SHM文件
        for ext in ['-shm', '-wal']:
            file_path = f"{db_path}{ext}"
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"已删除数据库文件: {file_path}")
        
        # 创建应用并初始化数据库
        from app import create_app
        app = create_app()
        with app.app_context():
            from instance.models import db
            db.create_all()
            print("数据库已重建成功")
        
        return True
    except Exception as e:
        print(f"重置数据库失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 检查是否需要重置数据库
    if '--reset-db' in sys.argv:
        reset_database()
        # 如果只需要重置数据库而不启动应用
        if '--reset-only' in sys.argv:
            print("数据库重置完成，应用未启动")
            sys.exit(0)
    
    # 检查是否需要进行数据库迁移
    if '--migrate' in sys.argv:
        from app import create_app
        from instance.models import db
        from flask_migrate import Migrate, upgrade, migrate
        
        app = create_app()
        migrate_instance = Migrate(app, db)
        
        with app.app_context():
            migrate()
            upgrade()
            
        print("数据库迁移已完成")
        
        # 如果只需要迁移数据库而不启动应用
        if '--migrate-only' in sys.argv:
            sys.exit(0)
    
    # 设置最大重试次数
    max_app_retries = 3
    current_retry = 0
    
    while current_retry < max_app_retries:
        try:
            # 运行前先解锁数据库
            unlock_database()
            
            # 尝试创建应用
            from app import create_app
            
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
            
            # 如果运行成功退出循环
            break
            
        except OperationalError as e:
            current_retry += 1
            print(f"数据库错误 (尝试 {current_retry}/{max_app_retries}): {str(e)}")
            
            if current_retry < max_app_retries:
                # 尝试解锁数据库
                print("尝试解锁数据库...")
                unlock_database()
                
                print(f"等待 5 秒后重试...")
                time.sleep(5)
            else:
                print("已达到最大重试次数，退出应用。")
                traceback.print_exc()
                sys.exit(1)
                
        except Exception as e:
            print(f"应用启动失败: {str(e)}")
            traceback.print_exc()
            sys.exit(1) 