#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import argparse
import sqlite3

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def ensure_directories_exist():
    """確保必要的目錄存在"""
    required_dirs = [
        os.path.join(project_root, "instance"),
        os.path.join(project_root, "instance/backups"),
        os.path.join(project_root, "instance/tools"),
        os.path.join(project_root, "logs"),
        os.path.join(project_root, "flask_session")
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"創建目錄: {directory}")

def backup_database(db_path):
    """備份數據庫文件"""
    if not os.path.exists(db_path):
        print(f"數據庫文件不存在，無需備份: {db_path}")
        return False
        
    backup_time = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, f"c2_{backup_time}.db")
    try:
        shutil.copy2(db_path, backup_path)
        print(f"數據庫備份創建: {backup_path}")
        return True
    except Exception as e:
        print(f"備份數據庫時出錯: {str(e)}")
        return False

def unlock_database(db_path):
    """解鎖數據庫文件"""
    # 確保數據庫目錄存在
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"創建數據庫目錄: {db_dir}")
    
    # 檢查是否存在鎖文件
    db_shm_path = f"{db_path}-shm"
    db_wal_path = f"{db_path}-wal"
    
    lock_files = []
    if os.path.exists(db_shm_path):
        lock_files.append(db_shm_path)
    if os.path.exists(db_wal_path):
        lock_files.append(db_wal_path)
    
    if lock_files:
        # 備份數據庫
        backup_database(db_path)
        
        # 刪除鎖文件
        for lock_file in lock_files:
            try:
                os.remove(lock_file)
                print(f"刪除鎖文件: {lock_file}")
            except Exception as e:
                print(f"無法刪除鎖文件 {lock_file}: {str(e)}")
    else:
        print("未發現鎖文件")
    
    # 確保數據庫文件存在
    if not os.path.exists(db_path):
        try:
            # 創建空的數據庫文件
            with open(db_path, 'wb') as f:
                pass
            print(f"創建新的數據庫文件: {db_path}")
        except Exception as e:
            print(f"無法創建數據庫文件: {str(e)}")
            return False
    
    return True

def check_database(db_path):
    """檢查數據庫完整性"""
    if not os.path.exists(db_path):
        print(f"數據庫文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查數據庫完整性
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result and result[0] == 'ok':
            print("數據庫完整性檢查通過")
            
            # 獲取數據庫表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"數據庫包含 {len(tables)} 個表:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  - {table[0]}: {count} 條記錄")
            
            conn.close()
            return True
        else:
            print(f"數據庫完整性檢查失敗: {result[0] if result else 'Unknown error'}")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"數據庫檢查出錯: {str(e)}")
        return False

def optimize_database(db_path):
    """優化數據庫性能"""
    if not os.path.exists(db_path):
        print(f"數據庫文件不存在: {db_path}")
        return False
    
    try:
        # 備份數據庫
        backup_database(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 設置優化參數
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=30000000000")
        cursor.execute("PRAGMA cache_size=10000")
        
        # 執行VACUUM操作壓縮數據庫
        print("開始執行VACUUM操作壓縮數據庫...")
        cursor.execute("VACUUM")
        
        # 分析數據庫以優化查詢計劃
        print("開始分析數據庫以優化查詢計劃...")
        cursor.execute("ANALYZE")
        
        conn.close()
        print("數據庫優化完成")
        return True
        
    except sqlite3.Error as e:
        print(f"數據庫優化出錯: {str(e)}")
        return False

def repair_database(db_path):
    """修復損壞的數據庫"""
    # 檢查數據庫是否存在
    if not os.path.exists(db_path):
        print(f"數據庫文件不存在: {db_path}")
        return False
    
    # 首先嘗試解鎖數據庫
    unlock_database(db_path)
    
    try:
        # 創建備份
        backup_database(db_path)
        
        # 嘗試打開數據庫連接以檢查是否可以訪問
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查數據庫完整性
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()
        
        if integrity_result and integrity_result[0] == 'ok':
            print("數據庫完整性良好，無需修復")
            conn.close()
            return True
        
        print(f"數據庫完整性檢查結果: {integrity_result[0] if integrity_result else 'Unknown error'}")
        
        # 嘗試修復數據庫
        print("嘗試修復損壞的數據庫...")
        
        # 關閉原連接
        conn.close()
        
        # 創建一個新的臨時數據庫
        temp_db_path = f"{db_path}_temp"
        temp_conn = sqlite3.connect(temp_db_path)
        temp_cursor = temp_conn.cursor()
        
        # 從原數據庫導出結構和數據
        original_conn = sqlite3.connect(db_path)
        original_cursor = original_conn.cursor()
        
        # 獲取所有的表
        original_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        tables = original_cursor.fetchall()
        
        for table_name, table_sql in tables:
            if table_name.startswith('sqlite_'):
                continue  # 跳過sqlite內部表
            
            print(f"正在修復表: {table_name}")
            
            # 在新數據庫中創建表
            try:
                temp_cursor.execute(table_sql)
                temp_conn.commit()
            except sqlite3.Error as e:
                print(f"無法創建表 {table_name}: {str(e)}")
                continue
                
            # 嘗試從原表中複製數據
            try:
                original_cursor.execute(f"SELECT * FROM {table_name}")
                rows = original_cursor.fetchall()
                
                if rows:
                    # 獲取列名
                    column_info = original_cursor.description
                    column_count = len(column_info)
                    
                    # 創建插入語句
                    placeholders = ", ".join(["?" for _ in range(column_count)])
                    insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                    
                    # 插入數據
                    for row in rows:
                        try:
                            temp_cursor.execute(insert_sql, row)
                        except sqlite3.Error as row_err:
                            print(f"插入數據行時出錯，已跳過: {str(row_err)}")
                    
                    temp_conn.commit()
                    print(f"成功從表 {table_name} 恢復 {len(rows)} 行數據")
                
            except sqlite3.Error as copy_err:
                print(f"從原表 {table_name} 複製數據時出錯: {str(copy_err)}")
        
        # 獲取所有的索引
        try:
            original_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
            indexes = original_cursor.fetchall()
            
            for index_name, index_sql in indexes:
                if index_name.startswith('sqlite_'):
                    continue
                
                try:
                    temp_cursor.execute(index_sql)
                    temp_conn.commit()
                    print(f"重建索引: {index_name}")
                except sqlite3.Error as idx_err:
                    print(f"重建索引 {index_name} 時出錯: {str(idx_err)}")
        except sqlite3.Error as idx_list_err:
            print(f"獲取索引列表時出錯: {str(idx_list_err)}")
        
        # 關閉連接
        original_conn.close()
        temp_conn.close()
        
        # 備份原數據庫
        repair_backup_path = f"{db_path}_damaged_{time.strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.move(db_path, repair_backup_path)
            print(f"已將損壞的數據庫備份到: {repair_backup_path}")
        except Exception as mv_err:
            print(f"備份損壞的數據庫時出錯: {str(mv_err)}")
            return False
        
        # 將臨時數據庫移動到原位置
        try:
            shutil.move(temp_db_path, db_path)
            print(f"已將修復的數據庫移動到原位置: {db_path}")
        except Exception as replace_err:
            print(f"替換數據庫文件時出錯: {str(replace_err)}")
            # 嘗試恢復原數據庫
            try:
                shutil.move(repair_backup_path, db_path)
                print(f"由於出錯，已恢復原數據庫")
            except Exception:
                print(f"無法恢復原數據庫，請手動檢查: {repair_backup_path}")
            return False
        
        # 優化新數據庫
        optimize_database(db_path)
        
        print("數據庫修復完成")
        return True
        
    except sqlite3.Error as e:
        print(f"修復數據庫時出錯: {str(e)}")
        return False

def auto_unlock_cron():
    """設置自動解鎖定時任務（僅支持Linux/macOS）"""
    if sys.platform.startswith('win'):
        print("Windows系統不支持cron任務，請使用Windows計劃任務")
        print("命令示例: schtasks /create /sc minute /mo 30 /tn \"C2數據庫自動解鎖\" /tr \"python instance/tools/db_manager.py --unlock\"")
        return False
    
    try:
        # 獲取當前腳本的絕對路徑
        script_path = os.path.abspath(__file__)
        python_path = sys.executable
        
        # 生成cron任務內容 - 每30分鐘執行一次
        cron_job = f"*/30 * * * * {python_path} {script_path} --unlock --quiet\n"
        
        # 臨時文件路徑
        temp_cron_file = "/tmp/db_unlock_cron"
        
        # 導出當前的cron任務
        os.system(f"crontab -l > {temp_cron_file} 2>/dev/null || touch {temp_cron_file}")
        
        # 檢查是否已經存在相同的任務
        with open(temp_cron_file, 'r') as f:
            current_cron = f.read()
            if script_path in current_cron:
                print("自動解鎖任務已經存在於cron中")
                os.remove(temp_cron_file)
                return True
        
        # 添加新任務
        with open(temp_cron_file, 'a') as f:
            f.write(cron_job)
        
        # 應用新的cron設置
        os.system(f"crontab {temp_cron_file}")
        os.remove(temp_cron_file)
        
        print("已添加數據庫自動解鎖cron任務 (每30分鐘執行一次)")
        return True
    
    except Exception as e:
        print(f"設置cron任務時出錯: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='數據庫管理工具')
    parser.add_argument('--unlock', action='store_true', help='解鎖數據庫')
    parser.add_argument('--check', action='store_true', help='檢查數據庫完整性')
    parser.add_argument('--optimize', action='store_true', help='優化數據庫')
    parser.add_argument('--repair', action='store_true', help='修復損壞的數據庫')
    parser.add_argument('--backup', action='store_true', help='備份數據庫')
    parser.add_argument('--auto', action='store_true', help='設置自動解鎖任務')
    parser.add_argument('--quiet', action='store_true', help='安靜模式，減少輸出')
    parser.add_argument('--db-path', type=str, help='數據庫文件路徑')
    
    args = parser.parse_args()
    
    # 確保必要的目錄存在
    ensure_directories_exist()
    
    # 設置默認數據庫路徑
    db_path = args.db_path or os.path.join(project_root, 'instance', 'c2.db')
    if not args.quiet:
        print(f"使用數據庫路徑: {db_path}")
    
    # 執行操作
    if args.unlock:
        unlock_database(db_path)
    
    if args.check:
        check_database(db_path)
    
    if args.optimize:
        optimize_database(db_path)
    
    if args.repair:
        repair_database(db_path)
    
    if args.backup:
        backup_database(db_path)
    
    if args.auto:
        auto_unlock_cron()
    
    # 如果沒有指定任何操作，默認執行解鎖和檢查
    if not (args.unlock or args.check or args.optimize or args.backup or args.repair or args.auto):
        if not args.quiet:
            print("執行默認操作: 解鎖和檢查數據庫")
        unlock_database(db_path)
        check_database(db_path)

if __name__ == '__main__':
    main() 