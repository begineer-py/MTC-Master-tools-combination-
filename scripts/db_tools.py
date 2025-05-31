#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import argparse
import sqlite3

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def ensure_directories_exist():
    """确保必要的目录存在"""
    required_dirs = [
        os.path.join(project_root, "instance"),
        os.path.join(project_root, "instance/backups"),
        os.path.join(project_root, "logs"),
        os.path.join(project_root, "flask_session")
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"创建目录: {directory}")

def backup_database(db_path):
    """备份数据库文件"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在，无需备份: {db_path}")
        return False
        
    backup_time = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, f"c2_{backup_time}.db")
    try:
        shutil.copy2(db_path, backup_path)
        print(f"数据库备份创建: {backup_path}")
        return True
    except Exception as e:
        print(f"备份数据库时出错: {str(e)}")
        return False

def unlock_database(db_path):
    """解锁数据库文件"""
    # 确保数据库目录存在
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"创建数据库目录: {db_dir}")
    
    # 检查是否存在锁文件
    db_shm_path = f"{db_path}-shm"
    db_wal_path = f"{db_path}-wal"
    
    lock_files = []
    if os.path.exists(db_shm_path):
        lock_files.append(db_shm_path)
    if os.path.exists(db_wal_path):
        lock_files.append(db_wal_path)
    
    if lock_files:
        # 备份数据库
        backup_database(db_path)
        
        # 删除锁文件
        for lock_file in lock_files:
            try:
                os.remove(lock_file)
                print(f"删除锁文件: {lock_file}")
            except Exception as e:
                print(f"无法删除锁文件 {lock_file}: {str(e)}")
    else:
        print("未发现锁文件")
    
    # 确保数据库文件存在
    if not os.path.exists(db_path):
        try:
            # 创建空的数据库文件
            with open(db_path, 'wb') as f:
                pass
            print(f"创建新的数据库文件: {db_path}")
        except Exception as e:
            print(f"无法创建数据库文件: {str(e)}")
            return False
    
    return True

def check_database(db_path):
    """检查数据库完整性"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查数据库完整性
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result and result[0] == 'ok':
            print("数据库完整性检查通过")
            
            # 获取数据库表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"数据库包含 {len(tables)} 个表:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  - {table[0]}: {count} 条记录")
            
            conn.close()
            return True
        else:
            print(f"数据库完整性检查失败: {result[0] if result else 'Unknown error'}")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"数据库检查出错: {str(e)}")
        return False

def optimize_database(db_path):
    """优化数据库性能"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 备份数据库
        backup_database(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 设置优化参数
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=30000000000")
        cursor.execute("PRAGMA cache_size=10000")
        
        # 执行VACUUM操作压缩数据库
        print("开始执行VACUUM操作压缩数据库...")
        cursor.execute("VACUUM")
        
        # 分析数据库以优化查询计划
        print("开始分析数据库以优化查询计划...")
        cursor.execute("ANALYZE")
        
        conn.close()
        print("数据库优化完成")
        return True
        
    except sqlite3.Error as e:
        print(f"数据库优化出错: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='数据库管理工具')
    parser.add_argument('--unlock', action='store_true', help='解锁数据库')
    parser.add_argument('--check', action='store_true', help='检查数据库完整性')
    parser.add_argument('--optimize', action='store_true', help='优化数据库')
    parser.add_argument('--backup', action='store_true', help='备份数据库')
    parser.add_argument('--db-path', type=str, help='数据库文件路径')
    
    args = parser.parse_args()
    
    # 确保必要的目录存在
    ensure_directories_exist()
    
    # 设置默认数据库路径
    db_path = args.db_path or os.path.join(project_root, 'instance', 'c2.db')
    print(f"使用数据库路径: {db_path}")
    
    # 执行操作
    if args.unlock:
        unlock_database(db_path)
    
    if args.check:
        check_database(db_path)
    
    if args.optimize:
        optimize_database(db_path)
    
    if args.backup:
        backup_database(db_path)
    
    # 如果没有指定任何操作，默认执行解锁和检查
    if not (args.unlock or args.check or args.optimize or args.backup):
        print("执行默认操作: 解锁和检查数据库")
        unlock_database(db_path)
        check_database(db_path)

if __name__ == '__main__':
    main() 