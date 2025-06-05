import threading
import os
import json
import subprocess
import time
import io
from datetime import datetime, timedelta
from queue import Queue, Empty
from instance.models import db, gau_results, Target
from flask import current_app
from sqlalchemy import exc
from urllib.parse import urlparse
import platform

class GauScanThread(threading.Thread):
    """Gau扫描线程类"""
    
    def __init__(self, target_id, domain, options=None, app=None):
        """
        初始化Gau扫描线程
        
        参数:
            target_id: 目标ID
            domain: 要扫描的域名
            options: 扫描配置选项
            app: Flask应用实例
        """
        super().__init__()
        self.target_id = target_id
        self.domain = domain
        self.options = options or {}
        self.app = app
        self.daemon = True  # 设置为守护线程
        
        # 保存到活动扫描字典，用于跟踪
        active_scans[f"{target_id}"] = self
        
        self.result = Queue()
        self.batch_size = 10000  # 每批处理的URL数量，从1000增加到10000
        self.update_interval = 60  # 更新数据库的间隔（秒），从30增加到60
        self.log_interval = 50000  # 日志记录间隔，从10000增加到50000
        self.last_update_time = 0  # 上次更新时间
        self.url_set = set()  # 使用集合存储URL，自动去重
        self.last_log_count = 0  # 上次记录日志时的URL数量
        self.memory_mode = True  # 使用内存模式加快处理速度
    
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
            # 确保输出目录存在
            output_folder = getattr(current_app.config, 'OUTPUT_FOLDER', None)
            if not output_folder:
                # 如果配置中没有 OUTPUT_FOLDER，使用默认路径
                base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                output_folder = os.path.join(base_dir, 'output')
            
            output_dir = os.path.join(output_folder, 'gau')
            os.makedirs(output_dir, exist_ok=True)
            
            # 设置输出文件路径
            output_file = os.path.join(output_dir, f"gau_{self.target_id}_{int(time.time())}.txt")
            
            # 获取正确的 gau 执行文件路径
            tools_folder = getattr(current_app.config, 'TOOLS_FOLDER', None)
            if not tools_folder:
                # 如果配置中没有 TOOLS_FOLDER，使用默认路径
                base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                tools_folder = os.path.join(base_dir, 'tools')
                gau_path = os.path.join(tools_folder, 'gau_linux', 'gau')
            
            # 检查 gau 执行文件是否存在
            if not os.path.exists(gau_path):
                error_msg = f"Gau 执行文件不存在: {gau_path}"
                current_app.logger.error(error_msg)
                scan_result.status = 'failed'
                scan_result.error_message = error_msg
                db.session.commit()
                return False
            
            # 构建命令
            cmd = [
                gau_path,
                self.domain,
                '--o', output_file  # 直接輸出到文件
            ]
            
            # 添加線程參數 - 使用更保守的設置
            if self.options.get('threads'):
                cmd.extend(['--threads', str(self.options.get('threads'))])
            else:
                # 默認使用5個線程，進一步降低並發
                cmd.extend(['--threads', '5'])
            
            # 添加超時設置
            cmd.extend(['--timeout', '20'])  # 20秒超時
            
            # 添加重試次數限制
            cmd.extend(['--retries', '2'])  # 最多重試2次
            
            # 限制日期範圍，只獲取最近2年的數據
            current_date = datetime.now()
            two_years_ago = current_date - timedelta(days=730)
            cmd.extend(['--from', two_years_ago.strftime('%Y%m')])
            
            # 默認只使用 wayback provider，更穩定
            if self.options.get('providers'):
                cmd.extend(['--providers', self.options.get('providers')])
            else:
                cmd.extend(['--providers', 'wayback'])
            
            # 添加去重參數，減少重複URL
            cmd.append('--fp')  # 移除相同端點的不同參數
            
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
            
            # 检查输出文件是否存在
            if not os.path.exists(output_file):
                current_app.logger.warning(f"输出文件不存在: {output_file}")
                scan_result.status = 'completed'
                scan_result.total_urls = 0
                db.session.commit()
                return True
            
            # 获取文件大小以决定处理方式
            file_size = os.path.getsize(output_file)
            current_app.logger.info(f"输出文件大小: {file_size} 字节")
            
            # 如果文件较小（小于100MB），使用内存模式处理
            if file_size < 100 * 1024 * 1024 and self.memory_mode:
                try:
                    with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                    
                    url_buffer = []
                    for line in lines:
                        url = self._clean_url(line.strip())
                        if url and url not in self.url_set:
                            self.url_set.add(url)
                            url_buffer.append(url)
                        
                        processed_count += 1
                    
                    # 一次性更新所有URL
                    self._update_scan_result(scan_result, url_buffer, processed_count, final_update=True)
                    
                    # 更新最终结果
                    scan_result.status = 'completed'
                    scan_result.total_urls = len(self.url_set)
                    db.session.commit()
                    
                    current_app.logger.info(f"Gau扫描处理完成，目标ID: {self.target_id}，总URL数: {scan_result.total_urls}")
                    
                except Exception as e:
                    current_app.logger.error(f"内存模式处理文件失败: {str(e)}，切换到流式处理模式")
                    self.memory_mode = False
            
            # 如果不使用内存模式或内存模式处理失败，使用流式处理
            if not self.memory_mode:
                # 分批读取文件并处理
                with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                    url_buffer = []
                    buffer_size = 20000  # 更大的缓冲区
                    
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

def start_gau_scan(target_id, domain, options=None):
    """
    启动Gau扫描
    
    参数:
        target_id: 目标ID
        domain: 域名
        options: 扫描选项
    
    返回:
        target_id: 目标ID
    """
    # 初始化选项
    if options is None:
        options = {}
    
    # 检查是否已有该目标的扫描正在进行
    scan_key = f"{target_id}"
    if scan_key in active_scans and active_scans[scan_key].is_alive():
        current_app.logger.info(f"已有Gau扫描正在进行，目标ID: {target_id}")
        return target_id
    
    # 创建并启动新的扫描线程
    scan_thread = GauScanThread(target_id, domain, options, current_app._get_current_object())
    scan_thread.start()
    
    # 记录活动扫描
    active_scans[scan_key] = scan_thread
    
    current_app.logger.info(f"已启动Gau扫描，目标ID: {target_id}")
    return target_id 