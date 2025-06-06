import os
import subprocess
import shutil
import time
from datetime import datetime
import sqlite3
import logging
from pathlib import Path
from flask import Flask
from models import db

# 設置日誌
def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'db_migration.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def backup_database():
    """備份數據庫"""
    try:
        db_path = Path('instance/c2.db')
        if not db_path.exists():
            logger.warning("數據庫文件不存在，跳過備份")
            return True
            
        backup_dir = Path('instance/backups')
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'c2_{timestamp}.db'
        
        shutil.copy2(db_path, backup_path)
        logger.info(f"數據庫已備份到: {backup_path}")
        
        # 清理舊備份（保留最近10個）
        backups = sorted(backup_dir.glob('c2_*.db'))
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                old_backup.unlink()
                logger.info(f"已刪除舊備份: {old_backup}")
                
        return True
    except Exception as e:
        logger.error(f"備份數據庫時出錯: {str(e)}")
        return False

def run_command(command, retry_count=3, ignore_errors=False):
    """運行命令行命令，支持重試"""
    for attempt in range(retry_count):
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0 or ignore_errors:
                logger.info(f"命令執行成功: {command}")
                logger.debug(f"輸出: {result.stdout}")
                return True, result.stdout
            else:
                logger.warning(f"命令執行失敗 (嘗試 {attempt + 1}/{retry_count})")
                logger.warning(f"錯誤信息: {result.stderr}")
                
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # 指數退避
                    continue
                    
                return False, result.stderr
                
        except Exception as e:
            logger.error(f"執行命令時出錯: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
                continue
            return False, str(e)

def check_database_connection():
    """檢查數據庫連接"""
    try:
        db_path = Path('instance/c2.db')
        if not db_path.exists():
            logger.info("數據庫文件不存在，將在遷移時創建")
            return True
            
        conn = sqlite3.connect('instance/c2.db')
        conn.close()
        logger.info("數據庫連接測試成功")
        return True
    except Exception as e:
        logger.error(f"數據庫連接測試失敗: {str(e)}")
        return False

def restore_latest_backup():
    """恢復最新的備份"""
    try:
        backup_dir = Path('instance/backups')
        if not backup_dir.exists():
            logger.warning("沒有找到備份目錄")
            return False
            
        backups = sorted(backup_dir.glob('c2_*.db'))
        if not backups:
            logger.warning("沒有找到可用的備份")
            return False
            
        latest_backup = backups[-1]
        shutil.copy2(latest_backup, 'instance/c2.db')
        logger.info(f"已恢復最新備份: {latest_backup}")
        return True
    except Exception as e:
        logger.error(f"恢復備份時出錯: {str(e)}")
        return False

def force_upgrade_database():
    """強制更新數據庫"""
    try:
        logger.info("嘗試強制更新數據庫")
        
        # 刪除 alembic_version 表
        conn = sqlite3.connect('instance/c2.db')
        cursor = conn.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS alembic_version")
            conn.commit()
            logger.info("成功刪除 alembic_version 表")
        except Exception as e:
            logger.warning(f"刪除 alembic_version 表時出錯: {str(e)}")
        finally:
            conn.close()
        
        # 強制執行升級
        success, output = run_command('flask db stamp head')
        if not success:
            logger.error("強制更新失敗")
            return False
            
        logger.info("強制更新成功")
        return True
        
    except Exception as e:
        logger.error(f"強制更新過程出錯: {str(e)}")
        return False

def check_migration_status():
    """檢查遷移狀態"""
    try:
        result = subprocess.run(
            'flask db current',
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0
    except Exception:
        return False

def migrate_database():
    """自動遷移數據庫"""
    logger.info("開始數據庫遷移流程")
    
    # 檢查數據庫連接
    if not check_database_connection():
        logger.error("數據庫連接檢查失敗，嘗試恢復備份")
        if restore_latest_backup():
            logger.info("成功恢復備份，繼續遷移流程")
        else:
            logger.error("無法恢復備份，終止遷移")
            return False
    
    # 備份當前數據庫
    if not backup_database():
        logger.error("數據庫備份失敗，終止遷移")
        return False
    
    try:
        # 檢查並創建遷移目錄
        if not os.path.exists('migrations'):
            logger.info("初始化遷移目錄")
            success, output = run_command('flask db init')
            if not success:
                raise Exception(f"初始化遷移失敗: {output}")
        
        # 檢查當前數據庫版本
        success, current_version = run_command('flask db current', ignore_errors=True)
        if not success or "head" not in current_version.lower():
            logger.warning("數據庫版本不是最新的，執行強制更新")
            
            # 刪除現有的遷移腳本
            success, _ = run_command('flask db stamp head', ignore_errors=True)
            if not success:
                logger.warning("重置版本標記失敗，嘗試強制更新")
                if not force_upgrade_database():
                    raise Exception("強制更新數據庫失敗")
            
            # 重新初始化遷移
            success, _ = run_command('flask db migrate -m "Reset migration"')
            if not success:
                raise Exception("重新初始化遷移失敗")
            
            # 應用遷移
            success, _ = run_command('flask db upgrade')
            if not success:
                raise Exception("應用初始遷移失敗")
        
        # 創建新的遷移腳本
        logger.info("創建遷移腳本")
        success, output = run_command('flask db migrate -m "Auto migration"')
        if not success:
            raise Exception(f"創建遷移腳本失敗: {output}")
        
        # 應用遷移
        logger.info("應用遷移")
        success, output = run_command('flask db upgrade')
        if not success:
            raise Exception(f"應用遷移失敗: {output}")
        
        logger.info("數據庫遷移完成")
        return True
        
    except Exception as e:
        logger.error(f"遷移過程出錯: {str(e)}")
        logger.info("嘗試恢復最新備份")
        
        if restore_latest_backup():
            logger.info("成功恢復到最新備份")
        else:
            logger.error("恢復備份失敗，請手動檢查數據庫狀態")
        
        return False

def update_database():
    """简单迁移：将target_ip_no_https换成domain"""
    try:
        # 连接数据库
        conn = sqlite3.connect('instance/c2.db')
        cursor = conn.cursor()
        
        # 备份当前数据库
        backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'instance/backups/c2_{backup_time}.db'
        os.makedirs('instance/backups', exist_ok=True)
        shutil.copy2('instance/c2.db', backup_path)
        print(f"数据库已备份到: {backup_path}")
            
        print("开始将target_ip_no_https换成domain的迁移...")
        
        # 1. 检查target表是否已经有domain列
        cursor.execute("PRAGMA table_info(target)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 如果已经有domain列，则跳过创建
        if 'domain' not in column_names:
            # 2. 添加domain列
            print("添加domain列...")
            cursor.execute("ALTER TABLE target ADD COLUMN domain VARCHAR(255)")
        else:
            print("domain列已存在，跳过创建")
        
        # 3. 将target_ip_no_https的数据复制到domain
        if 'target_ip_no_https' in column_names:
            print("将target_ip_no_https数据复制到domain...")
            cursor.execute("UPDATE target SET domain = target_ip_no_https WHERE domain IS NULL OR domain = ''")
        
        # 4. 更新引用target_ip_no_https的相关表（这里以gau_results为例）
        # 检查gau_results表中是否有需要更新的字段
        try:
            cursor.execute("SELECT * FROM gau_results LIMIT 1")
            # 如果表存在，检查数据
            cursor.execute("UPDATE gau_results SET domain = (SELECT target_ip_no_https FROM target WHERE target.id = gau_results.target_id) WHERE domain IS NULL OR domain = ''")
            print("更新gau_results表中的domain引用...")
        except sqlite3.OperationalError:
            print("gau_results表不存在或无需更新")
        
        # 5. 提交更改
        conn.commit()
        print("数据库迁移成功完成！")
        
        # 6. 关闭连接
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"数据库更新失败: {str(e)}")
        # 尝试回滚
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    update_database()
