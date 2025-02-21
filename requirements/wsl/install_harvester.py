import subprocess
import logging
import os
import time
from datetime import datetime

class KaliInstaller:
    """Kali Linux 工具安装器"""
    
    def __init__(self):
        self._setup_logger()
        
    def _setup_logger(self):
        """设置日志记录器"""
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, f'install_harvester_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        self.logger = logging.getLogger('KaliInstaller')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def start_kali(self):
        """启动 Kali Linux"""
        try:
            self.logger.info("检查 Kali Linux 状态...")
            result = subprocess.run(['wsl', '--list', '--running'], capture_output=True, text=True)
            output = result.stdout
            
            if 'kali-linux' not in output:
                self.logger.info("启动 Kali Linux...")
                subprocess.run(['wsl', '--distribution', 'kali-linux', '--user', 'root', '--exec', 'echo', 'Kali Linux is starting...'])
                time.sleep(5)  # 等待系统启动
                return True
            else:
                self.logger.info("Kali Linux 已经在运行")
                return True
            
        except Exception as e:
            self.logger.error(f"启动 Kali Linux 失败: {str(e)}")
            return False
        
    def run_wsl_command(self, command):
        """在 WSL 中运行命令"""
        try:
            self.logger.info(f"执行命令: {command}")
            process = subprocess.Popen(
                ['wsl', '--distribution', 'kali-linux', '--user', 'root', '--exec', 'bash', '-c', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate()
            stdout = stdout.decode('utf-8', errors='ignore')
            stderr = stderr.decode('utf-8', errors='ignore')
            
            if process.returncode != 0:
                self.logger.error(f"命令执行失败: {stderr}")
            else:
                self.logger.info("命令执行成功")
                
            return stdout, stderr, process.returncode
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {str(e)}")
            return '', str(e), 1
            
    def install_packages(self):
        """安装必要的包"""
        try:
            self.logger.info("更新包列表...")
            self.run_wsl_command('apt-get update')
            
            self.logger.info("安装 theHarvester...")
            self.run_wsl_command('apt-get install -y theharvester')
            
            return True
            
        except Exception as e:
            self.logger.error(f"安装包失败: {str(e)}")
            return False
            
    def install(self):
        """执行完整的安装过程"""
        try:
            self.logger.info("开始安装 theHarvester...")
            
            if not self.start_kali():
                raise Exception("无法启动 Kali Linux")
                
            if not self.install_packages():
                raise Exception("安装包失败")
                
            self.logger.info("安装完成！")
            self.logger.info("使用说明:")
            self.logger.info("1. 在 WSL 中运行 theHarvester")
            self.logger.info("2. 基本命令格式: theharvester -d <domain> -l <limit> -b <source>")
            self.logger.info("3. 示例: theharvester -d example.com -l 100 -b all")
            
            return True
            
        except Exception as e:
            self.logger.error(f"安装过程失败: {str(e)}")
            return False

if __name__ == '__main__':
    installer = KaliInstaller()
    installer.install() 