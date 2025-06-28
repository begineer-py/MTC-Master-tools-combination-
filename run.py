import os
import sys
import signal
import time
import traceback
import importlib.util
import subprocess
from sqlalchemy.exc import OperationalError
import argparse
# 嘗試導入 psutil，如果沒有安裝則使用備用方案
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: 未安裝 psutil 模組，將使用系統命令作為備用方案")

# 定義目標端口
TARGET_PORT = 1337
# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def check_and_request_sudo(args):
    """檢查並請求 sudo 權限"""
    # 檢查是否已經是 root 用戶
    if os.geteuid() == 0:
        print("✅ 已獲得 root 權限，將使用高性能 TCP SYN 掃描")
        return True

    # 檢查是否有 --no-sudo 參數（跳過 sudo 請求）
    if args.no_sudo:
        print("⚠️  跳過 sudo 權限請求，將使用 TCP Connect 掃描")
        return False

    # 檢查是否有 --force-sudo 參數（強制要求 sudo）
    force_sudo = args.force_sudo

    # 檢查是否在支持的環境中
    if os.name != 'posix':
        print("⚠️  非 Unix/Linux 環境，無法使用 sudo")
        return False

    # 詢問用戶是否要使用 sudo
    if not force_sudo:
        print("\n🔒 C2 安全測試平台權限提升")
        print("=" * 50)
        print("為了獲得最佳掃描性能，建議以 root 權限運行：")
        print("• TCP SYN 掃描 (更快、更隱蔽)")
        print("• 完整的網絡功能")
        print("• 高級掃描選項")
        print()
        print("如果拒絕，將使用 TCP Connect 掃描 (較慢但無需權限)")
        print()

        try:
            choice = input("是否要求 sudo 權限？[Y/n]: ").strip().lower()
            if choice in ['n', 'no', '否']:
                print("⚠️  繼續以普通用戶權限運行")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\n⚠️  用戶取消，繼續以普通用戶權限運行")
            return False

    # 嘗試獲取 sudo 權限
    try:
        print("\n🔄 正在請求 sudo 權限...")
        # 自動尋找系統Python執行檔
        python_executable = None

        # 常見的系統Python路徑
        common_python_paths = [
            "/usr/bin/python3",
            "/usr/local/bin/python3",
            "/bin/python3",
            "/usr/bin/python",
            "/usr/local/bin/python",
            "/bin/python"
        ]

        # 嘗試找到可用的Python執行檔
        for path in common_python_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                python_executable = path
                break

        # 如果找不到系統Python，使用which命令查找
        if not python_executable:
            try:
                result = subprocess.run(
                    ['which', 'python3'], capture_output=True, text=True)
                if result.returncode == 0:
                    python_executable = result.stdout.strip()
                else:
                    result = subprocess.run(
                        ['which', 'python'], capture_output=True, text=True)
                    if result.returncode == 0:
                        python_executable = result.stdout.strip()
            except Exception:
                pass

        # 最後的備用方案
        if not python_executable:
            python_executable = sys.executable
        script_args = [arg for arg in sys.argv if arg not in ['--force-sudo']]

        # 獲取當前PYTHONPATH
        current_pythonpath = os.environ.get('PYTHONPATH', '')

        # 構建sudo命令，保留環境變數
        sudo_cmd = ['sudo', '-E']
        if current_pythonpath:
            sudo_cmd.extend(['PYTHONPATH=' + current_pythonpath])
        sudo_cmd.extend([python_executable] + script_args)

        print(f"執行命令: {' '.join(sudo_cmd)}")
        print("請輸入您的密碼以獲得管理員權限...")

        # 執行 sudo 命令
        result = subprocess.run(sudo_cmd, check=False)

        # 退出當前進程，因為 sudo 版本已經運行
        sys.exit(result.returncode)

    except KeyboardInterrupt:
        print("\n⚠️  用戶取消 sudo 請求，繼續以普通用戶權限運行")
        return False
    except Exception as e:
        print(f"⚠️  無法獲得 sudo 權限: {str(e)}")
        print("繼續以普通用戶權限運行")
        return False


def force_stop_app():
    """強制停止另一個運行的在同一個端口的應用(不會停止自己)在端口1337"""
    print(f"正在檢查端口 {TARGET_PORT} 的佔用情況...")

    if PSUTIL_AVAILABLE:
        try:
            # 獲取當前運行的進程ID
            current_pid = os.getpid()
            stopped_processes = []

            # 查找佔用目標端口的進程
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    # 檢查進程的網絡連接
                    connections = proc.info['connections']
                    if connections:
                        for conn in connections:
                            if (hasattr(conn, 'laddr') and conn.laddr and
                                conn.laddr.port == TARGET_PORT and
                                    proc.info['pid'] != current_pid):
                                # 找到佔用端口且不是當前進程的程序
                                proc_obj = psutil.Process(proc.info['pid'])
                                proc_obj.terminate()  # 優雅終止
                                stopped_processes.append({
                                    'pid': proc.info['pid'],
                                    'name': proc.info['name']
                                })
                                print(
                                    f"已終止進程: {proc.info['name']} (PID: {proc.info['pid']})")
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                    continue

            # 等待進程終止，如果需要則強制殺死
            if stopped_processes:
                time.sleep(2)  # 等待優雅終止

                for proc_info in stopped_processes:
                    try:
                        proc = psutil.Process(proc_info['pid'])
                        if proc.is_running():
                            proc.kill()  # 強制終止
                            print(
                                f"強制終止進程: {proc_info['name']} (PID: {proc_info['pid']})")
                    except psutil.NoSuchProcess:
                        pass  # 進程已經終止

            if stopped_processes:
                print(f"成功停止 {len(stopped_processes)} 個佔用端口 {TARGET_PORT} 的進程")
                return True
            else:
                print(f"未發現佔用端口 {TARGET_PORT} 的其他進程")
                return False

        except Exception as e:
            print(f"使用 psutil 停止應用時出錯: {str(e)}")
            # 如果 psutil 方法失敗，嘗試系統命令
            psutil_failed = True

    # 備用方案：使用系統命令
    if not PSUTIL_AVAILABLE or 'psutil_failed' in locals():
        print("使用系統命令查找佔用端口的進程...")
        try:
            # 使用 lsof 查找佔用端口的進程
            result = subprocess.run(['lsof', '-ti', f':{TARGET_PORT}'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                current_pid = str(os.getpid())
                stopped_count = 0

                for pid in pids:
                    if pid and pid != current_pid:
                        try:
                            subprocess.run(['kill', '-TERM', pid], check=True)
                            print(f"已終止進程 PID: {pid}")
                            stopped_count += 1
                        except subprocess.CalledProcessError:
                            try:
                                subprocess.run(
                                    ['kill', '-KILL', pid], check=True)
                                print(f"強制終止進程 PID: {pid}")
                                stopped_count += 1
                            except subprocess.CalledProcessError:
                                print(f"無法終止進程 PID: {pid}")

                if stopped_count > 0:
                    print(f"成功停止 {stopped_count} 個佔用端口 {TARGET_PORT} 的進程")
                    return True
                else:
                    print(f"未能停止任何佔用端口 {TARGET_PORT} 的進程")
                    return False
            else:
                print(f"未發現佔用端口 {TARGET_PORT} 的進程")
                return False
        except FileNotFoundError:
            print("錯誤: 系統缺少必要的命令工具 (lsof)")
            # 嘗試使用 netstat 作為最後的備用方案
            try:
                result = subprocess.run(
                    ['netstat', '-tlnp'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if f':{TARGET_PORT}' in line and 'LISTEN' in line:
                            # 嘗試從 netstat 輸出中提取 PID
                            parts = line.split()
                            if len(parts) > 6:
                                pid_info = parts[-1]
                                if '/' in pid_info:
                                    pid = pid_info.split('/')[0]
                                    if pid.isdigit() and pid != str(os.getpid()):
                                        try:
                                            subprocess.run(
                                                ['kill', '-TERM', pid], check=True)
                                            print(f"已終止進程 PID: {pid}")
                                            return True
                                        except subprocess.CalledProcessError:
                                            try:
                                                subprocess.run(
                                                    ['kill', '-KILL', pid], check=True)
                                                print(f"強制終止進程 PID: {pid}")
                                                return True
                                            except subprocess.CalledProcessError:
                                                print(f"無法終止進程 PID: {pid}")
                    print(f"未發現佔用端口 {TARGET_PORT} 的進程")
                    return False
                else:
                    print("無法執行 netstat 命令")
                    return False
            except FileNotFoundError:
                print("錯誤: 系統缺少 netstat 命令")
                return False
        except Exception as e:
            print(f"使用系統命令停止應用時出錯: {str(e)}")
            return False


def print_permission_status():
    """打印當前權限狀態"""
    if os.geteuid() == 0:
        print("🔓 當前權限: Root (管理員)")
        print("🚀 掃描模式: TCP SYN (高性能)")
    else:
        print("👤 當前權限: 普通用戶")
        print("🐌 掃描模式: TCP Connect (標準)")
    print()


def signal_handler(signum, frame):
    """處理退出信號"""
    print('\n正在關閉應用...')
    sys.exit(0)


def load_db_manager():
    """動態加載數據庫管理模塊"""
    db_manager_path = os.path.join(
        project_root, 'instance', 'tools', 'db_manager.py')

    # 如果文件不存在，返回None
    if not os.path.exists(db_manager_path):
        return None

    # 動態加載模塊
    spec = importlib.util.spec_from_file_location(
        "db_manager", db_manager_path)
    if spec is None or spec.loader is None:
        return None

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


def main():
    """主執行函數"""
    parser = argparse.ArgumentParser(
        description="C2 安全測試平台 - 啟動器",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
示例用法:
  python run.py --migrate
  python run.py --reset-db
  sudo python run.py
  python run.py --force-sudo
"""
    )

    # 權限相關
    permission_group = parser.add_argument_group('權限相關')
    permission_group.add_argument(
        '--no-sudo', action='store_true', help='跳過 sudo 權限請求，使用 TCP Connect 掃描')
    permission_group.add_argument(
        '--force-sudo', action='store_true', help='強制要求 sudo 權限，如果失敗則退出')

    # 數據庫相關
    db_group = parser.add_argument_group('數據庫相關')
    db_group.add_argument('--reset-db', action='store_true', help='重置數據庫')
    db_group.add_argument(
        '--reset-only', action='store_true', help='僅重置數據庫，不啟動應用')
    db_group.add_argument('--migrate', action='store_true', help='執行數據庫遷移')
    db_group.add_argument(
        '--migrate-only', action='store_true', help='僅執行遷移，不啟動應用')

    # 其他
    other_group = parser.add_argument_group('其他')
    other_group.add_argument(
        '--force-stop', action='store_true', help='強制停止在同一端口上運行的其他應用實例')

    args = parser.parse_args()

    # 檢查並請求 sudo 權限
    check_and_request_sudo(args)

    # 打印權限狀態
    print_permission_status()

    # 检查是否需要重置数据库
    if args.reset_db:
        reset_database()
        # 如果只需要重置数据库而不启动应用
        if args.reset_only:
            print("数据库重置完成，应用未启动")
            sys.exit(0)

    # 检查是否需要进行数据库迁移
    if args.migrate:
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
        if args.migrate_only:
            sys.exit(0)

    # 检查是否需要强制停止应用
    if args.force_stop:
        force_stop_app()
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
                host='0.0.0.0',
                port=TARGET_PORT,
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


if __name__ == '__main__':
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    main()
