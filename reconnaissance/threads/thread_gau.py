import threading
import os
import json
import subprocess
import time
import io
from datetime import datetime
from queue import Queue, Empty
from instance.models import db, gau_results, Target
from flask import current_app
from sqlalchemy import exc
from urllib.parse import urlparse

class GauScanThread(threading.Thread):
    """Gau扫描线程类"""
    
    def __init__(self, target_id, user_id, domain, options=None, app=None):
        """
        初始化Gau扫描线程
        
        参数:
            target_id: 目标ID
            user_id: 用户ID
            domain: 要扫描的域名
            options: 扫描选项字典
            app: Flask应用实例
        """
        threading.Thread.__init__(self)
        self.target_id = target_id
        self.user_id = user_id
        self.domain = domain
        self.options = options or {}
        self.app = app
        self.result = Queue()
        self.daemon = True  # 设置为守护线程，主线程结束时自动结束
        self.batch_size = 1000  # 每批处理的URL数量，从500增加到1000
        self.update_interval = 30  # 更新数据库的间隔（秒），从10增加到30
        self.log_interval = 10000  # 日志记录间隔，每处理10000个URL记录一次
        self.last_update_time = 0  # 上次更新时间
        self.url_set = set()  # 使用集合存储URL，自动去重
        self.last_log_count = 0  # 上次记录日志时的URL数量
    
    def run(self):
        """线程执行函数"""
        with self.app.app_context():
            try:
                # 创建或更新扫描结果记录
                scan_result = self._create_or_update_scan_result('scanning')
                
                # 执行Gau扫描
                success = self._execute_gau_scan(scan_result)
                
                # 构建返回结果
                result_data = {
                    'id': scan_result.id,
                    'target_id': scan_result.target_id,
                    'domain': scan_result.domain,
                    'total_urls': scan_result.total_urls,
                    'status': scan_result.status,
                    'scan_time': scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S') if scan_result.scan_time else None
                }
                
                self.result.put((result_data, success, 200 if success else 500))
                
            except Exception as e:
                error_msg = f"Gau扫描过程中发生错误: {str(e)}"
                current_app.logger.error(error_msg)
                self.result.put(({'error': error_msg}, False, 500))
    
    def _create_or_update_scan_result(self, status):
        """创建或更新扫描结果记录"""
        # 检查是否已存在扫描结果
        scan_result = None
        
        # 首先尝试查找正在扫描的结果
        scan_result = gau_results.query.filter_by(
            target_id=self.target_id,
            status='scanning'
        ).first()
        
        if not scan_result:
            # 如果没有正在扫描的结果，查找是否有已完成的结果
            scan_result = gau_results.query.filter_by(
                target_id=self.target_id
            ).first()
            
            if scan_result:
                # 如果存在已完成的结果，重置它
                scan_result.status = status
                scan_result.urls = []
                scan_result.total_urls = 0
                scan_result.error_message = None
                scan_result.scan_time = datetime.now()
                
                # 初始化URL集合
                self.url_set = set()
                
                # 保存更改
                try:
                    db.session.commit()
                    current_app.logger.info(f"重置现有Gau扫描结果，目标ID: {self.target_id}")
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"重置Gau扫描结果时出错: {str(e)}")
                    # 创建新记录
                    scan_result = None
        
        if not scan_result:
            # 创建新的扫描结果记录
            scan_result = gau_results(
                target_id=self.target_id,
                domain=self.domain,
                status=status,
                urls=[]  # 初始化为空列表
            )
            db.session.add(scan_result)
            
            try:
                db.session.commit()
                current_app.logger.info(f"创建新的Gau扫描结果，目标ID: {self.target_id}")
            except exc.IntegrityError:
                # 如果发生完整性错误（例如唯一约束冲突），回滚并重试
                db.session.rollback()
                current_app.logger.warning(f"创建Gau扫描结果时发生完整性错误，尝试重新查询")
                
                # 再次尝试查找并更新
                scan_result = gau_results.query.filter_by(target_id=self.target_id).first()
                if scan_result:
                    scan_result.status = status
                    scan_result.urls = []
                    scan_result.total_urls = 0
                    scan_result.error_message = None
                    scan_result.scan_time = datetime.now()
                    db.session.commit()
        
        # 初始化URL集合
        if scan_result.urls:
            self.url_set = set(scan_result.urls)
        else:
            self.url_set = set()
            
        return scan_result
    
    def _update_scan_result(self, scan_result, new_urls, processed_count, final_update=False):
        """更新扫描结果"""
        try:
            # 获取当前URL列表
            current_urls = scan_result.urls or []
            current_count = len(current_urls)
            
            # 添加新URL
            current_urls.extend(new_urls)
            
            # 更新扫描结果
            scan_result.urls = current_urls
            scan_result.total_urls = len(current_urls)
            
            # 如果是最终更新或URL数量增加了一定比例，才提交更改
            if final_update or (len(current_urls) - current_count) > 5000 or processed_count % 50000 == 0:
                # 提交更改
                db.session.commit()
                
                # 只在最终更新或处理了一定数量的URL时记录日志
                if final_update or processed_count % 10000 == 0:
                    current_app.logger.info(f"已更新Gau扫描结果，目标ID: {self.target_id}，当前URL总数: {scan_result.total_urls}")
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新Gau扫描结果时出错: {str(e)}")
            
            # 重试
            try:
                db.session.refresh(scan_result)
                
                # 获取当前URL列表
                current_urls = scan_result.urls or []
                
                # 添加新URL（避免重复）
                for url in new_urls:
                    if url not in current_urls:
                        current_urls.append(url)
                
                # 更新扫描结果
                scan_result.urls = current_urls
                scan_result.total_urls = len(current_urls)
                
                # 提交更改
                if final_update:
                    db.session.commit()
                    current_app.logger.info(f"重试成功：已更新Gau扫描结果，目标ID: {self.target_id}，当前URL总数: {scan_result.total_urls}")
            
            except Exception as retry_error:
                db.session.rollback()
                current_app.logger.error(f"重试更新Gau扫描结果时出错: {str(retry_error)}")
    
    def _execute_gau_scan(self, scan_result):
        """执行Gau扫描"""
        try:
            # 创建输出目录
            output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'gau')
            os.makedirs(output_dir, exist_ok=True)
            
            # 设置输出文件路径
            output_file = os.path.join(output_dir, f"gau_{self.target_id}_{int(time.time())}.txt")
            
            # 构建命令
            cmd = [
                os.path.join(current_app.config['TOOLS_FOLDER'], 'gau_2.2.3_windows_amd64', 'gau.exe'),
                self.domain,
                '--o', output_file  # 直接输出到文件
            ]
            
            # 添加线程参数
            if self.options.get('threads'):
                cmd.extend(['--threads', str(self.options.get('threads'))])
            
            if self.options.get('providers'):
                cmd.extend(['--providers', self.options.get('providers')])
            
            if self.options.get('blacklist'):
                cmd.extend(['--blacklist', self.options.get('blacklist')])
            
            if self.options.get('verbose', False):
                cmd.append('--verbose')
            
            # 记录执行的命令
            command_str = ' '.join(cmd)
            current_app.logger.info(f"执行命令: {command_str}")
            
            # 更新扫描状态为扫描中
            scan_result.status = 'scanning'
            db.session.commit()
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'  # 处理编码错误
            )
            
            # 初始化URL集合和计数器
            self.url_set = set()
            processed_count = 0
            
            # 监控进程执行
            start_time = time.time()
            last_log_time = start_time
            
            # 等待进程完成
            stdout, stderr = process.communicate()
            
            # 检查进程是否成功完成
            if process.returncode != 0:
                current_app.logger.error(f"Gau扫描失败，错误信息: {stderr}")
                scan_result.status = 'failed'
                scan_result.error_message = f"扫描失败: {stderr}"
                db.session.commit()
                return False
            
            # 从文件中读取URL并处理
            current_app.logger.info(f"Gau扫描完成，正在处理结果...")
            
            # 分批读取文件并处理
            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                url_buffer = []
                buffer_size = 10000  # 更大的缓冲区
                
                for line in f:
                    url = self._clean_url(line.strip())
                    if url and url not in self.url_set:
                        self.url_set.add(url)
                        url_buffer.append(url)
                    
                    processed_count += 1
                    
                    # 每处理一定数量的URL，更新一次数据库
                    if len(url_buffer) >= buffer_size:
                        self._update_scan_result(scan_result, url_buffer, processed_count)
                        url_buffer = []
                        
                        # 每处理100,000个URL记录一次日志
                        if processed_count % 100000 == 0:
                            current_app.logger.info(f"已处理 {processed_count} 个URL，当前去重后URL数量：{len(self.url_set)}")
            
            # 处理剩余的URL
            if url_buffer:
                self._update_scan_result(scan_result, url_buffer, processed_count)
            
            # 更新最终结果
            scan_result.status = 'completed'
            scan_result.total_urls = len(self.url_set)
            db.session.commit()
            
            current_app.logger.info(f"Gau扫描完成，目标ID: {self.target_id}，总URL数: {scan_result.total_urls}")
            
            # 尝试删除临时文件以节省空间
            try:
                os.remove(output_file)
                current_app.logger.info(f"已删除临时文件: {output_file}")
            except Exception as e:
                current_app.logger.warning(f"删除临时文件失败: {str(e)}")
            
            return True
        
        except Exception as e:
            current_app.logger.error(f"执行Gau扫描时出错: {str(e)}")
            scan_result.status = 'failed'
            scan_result.error_message = f"扫描出错: {str(e)}"
            db.session.commit()
            return False
    
    def _clean_url(self, url):
        """清理和验证URL"""
        if not url:
            return None
        
        # 移除URL中的引号和其他无关字符
        url = url.strip('"\'')
        
        # 如果URL包含逗号和其他数据（如JSON片段），只保留URL部分
        if ',' in url:
            url = url.split(',')[0]
        
        # 移除URL中的换行符和多余空格
        url = url.replace('\n', '').replace('\r', '').strip()
        
        # 验证URL格式
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return None
            
            # 确保URL使用有效的协议
            if parsed.scheme not in ['http', 'https']:
                return None
            
            return url
        except:
            return None
    
    def _save_to_database(self, scan_result):
        """保存扫描结果到数据库"""
        try:
            # 使用重试机制保存到数据库
            max_retries = 3
            retry_delay = 1  # 秒
            
            for attempt in range(max_retries):
                try:
                    db.session.commit()
                    break
                except exc.IntegrityError as e:
                    # 处理完整性错误（例如唯一约束冲突）
                    db.session.rollback()
                    current_app.logger.warning(f"保存Gau扫描结果时发生完整性错误: {str(e)}")
                    # 不重试，直接返回
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        db.session.rollback()
                        current_app.logger.warning(f"保存Gau扫描结果时发生错误，尝试重试 {attempt + 1}/{max_retries}: {str(e)}")
                        time.sleep(retry_delay)
                    else:
                        raise e
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"保存Gau扫描结果到数据库时出错: {str(e)}")
            raise e
    
    def get_result(self, timeout=600):  # 默认超时时间设为10分钟
        """获取扫描结果，带超时机制"""
        try:
            return self.result.get(timeout=timeout)
        except Empty:
            return {'error': 'Gau扫描超时'}, False, 408  # 408 是超时状态码

# 全局线程字典，用于跟踪正在运行的扫描
active_scans = {}

def start_gau_scan(target_id, user_id, domain, options=None):
    """
    启动Gau扫描
    
    参数:
        target_id: 目标ID
        user_id: 用户ID
        domain: 要扫描的域名
        options: 扫描选项字典
    
    返回:
        target_id: 目标ID
    """
    # 检查是否已有该目标的扫描正在进行
    scan_key = f"{user_id}_{target_id}"
    if scan_key in active_scans and active_scans[scan_key].is_alive():
        current_app.logger.info(f"已有Gau扫描正在进行，目标ID: {target_id}")
        return target_id
    
    # 创建并启动新的扫描线程
    scan_thread = GauScanThread(target_id, user_id, domain, options, current_app._get_current_object())
    scan_thread.start()
    
    # 记录活动扫描
    active_scans[scan_key] = scan_thread
    
    current_app.logger.info(f"已启动Gau扫描，目标ID: {target_id}")
    return target_id 