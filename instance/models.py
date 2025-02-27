import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from threading import Lock
from flask_login import UserMixin
import json
import secrets

db = SQLAlchemy()
migrate = Migrate()
db_lock = Lock()

class payload(db.Model):
    """負載模型"""
    id = db.Column(db.Integer, primary_key=True)
    payload = db.Column(db.String(255), nullable=False)

class User(db.Model, UserMixin):
    """用戶模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    registered_on = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    client_ip = db.Column(db.String(39))
    is_admin = db.Column(db.Boolean, default=False)
    
    # API Key 相關字段
    api_key = db.Column(db.String(64), unique=True, nullable=True)
    api_key_created_at = db.Column(db.DateTime, nullable=True)
    api_key_expires_at = db.Column(db.DateTime, nullable=True)
    is_api_authenticated = db.Column(db.Boolean, default=False)
    
    # 關聯定義
    commands = db.relationship('Command_User', backref='user', lazy='dynamic')
    targets = db.relationship('Target', backref='user', lazy='dynamic')

    def set_password(self, password):
        """設置密碼"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """檢查密碼"""
        return check_password_hash(self.password_hash, password)
        
    def generate_api_key(self, expires_in=30):
        """生成新的 API Key
        
        Args:
            expires_in: API Key 的有效期（天數）
            
        Returns:
            str: 生成的 API Key
        """
        self.api_key = secrets.token_hex(32)
        self.api_key_created_at = datetime.now(UTC)
        self.api_key_expires_at = self.api_key_created_at + timedelta(days=expires_in)
        return self.api_key
        
    def revoke_api_key(self):
        """撤銷當前的 API Key"""
        self.api_key = None
        self.api_key_created_at = None
        self.api_key_expires_at = None
        self.is_api_authenticated = False
        
    def check_api_key(self, api_key):
        """檢查 API Key 是否有效
        
        Args:
            api_key: 要檢查的 API Key
            
        Returns:
            bool: API Key 是否有效
        """
        if not self.api_key or not api_key:
            return False
            
        if self.api_key != api_key:
            return False
            
        if not self.api_key_expires_at:
            return False
            
        if datetime.now(UTC) > self.api_key_expires_at:
            return False
            
        return True

    def set_api_auth(self, api_key):
        """設置 API 認證狀態"""
        self.is_api_authenticated = self.check_api_key(api_key)
        return self.is_api_authenticated

    @property
    def is_active(self):
        """用戶是否活躍"""
        return True

    @property
    def is_authenticated(self):
        """用戶是否已認證"""
        return True if self.is_api_authenticated else super().is_authenticated

class ZOMBIE(db.Model):
    """肉雞模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    session_id = db.Column(db.String(32))
    ip_address = db.Column(db.String(39))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    commands = db.relationship('Command_ZOMBIE', backref='zombie', lazy='dynamic')

class Command_ZOMBIE(db.Model):
    """肉雞命令模型"""
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('zombie.id'), nullable=True)
    is_run = db.Column(db.Boolean, default=False)
    result = db.Column(db.Text, nullable=True)

class Command_User(db.Model):
    """用戶命令模型"""
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_run = db.Column(db.Boolean, default=False)
    result = db.Column(db.Text, nullable=True)

class Target(db.Model):
    """目標模型"""
    __tablename__ = 'target'
    id = db.Column(db.Integer, primary_key=True)
    target_ip = db.Column(db.String(255), nullable=False)
    target_ip_no_https = db.Column(db.String(255), nullable=False)
    target_port = db.Column(db.Integer, nullable=False)
    target_username = db.Column(db.String(255), nullable=False)
    target_password = db.Column(db.String(255), nullable=False)
    target_status = db.Column(db.String(50), default='pending')
    deep_scan = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 關聯定義
    nmap_results = db.relationship('nmap_Result', backref='target', lazy='dynamic')
    crtsh_results = db.relationship('crtsh_Result', backref='target', lazy='dynamic')
    webtech_results = db.relationship('webtech_Result', backref='target', lazy='dynamic')
    crawler_each_urls = db.relationship('crawler_each_url', backref=db.backref('target', lazy='joined'), lazy='dynamic')
    harvester_results = db.relationship('HarvesterResult', backref='target', lazy='dynamic')

class nmap_Result(db.Model):
    """掃描結果模型"""
    __tablename__ = 'nmap_result'
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id', name='fk_nmap_target'), nullable=False, unique=True)
    scan_result = db.Column(db.Text)
    scan_time = db.Column(db.DateTime)
    scan_type = db.Column(db.String(10), default='common')  # 'common' 或 'full'
    
    def __init__(self, target_id, scan_result, scan_time, scan_type='common'):
        self.target_id = target_id
        self.scan_result = scan_result
        self.scan_time = scan_time
        self.scan_type = scan_type
        
    def to_dict(self):
        """將結果轉換為字典格式"""
        return {
            'id': self.id,
            'target_id': self.target_id,
            'scan_result': json.loads(self.scan_result) if self.scan_result else None,
            'scan_time': self.scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.scan_time else None,
            'scan_type': self.scan_type
        }

class crtsh_Result(db.Model):
    """crtsh掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id', name='fk_crtsh_target'), nullable=False)
    domains = db.Column(db.JSON, nullable=True)  # 存儲域名列表
    total_domains = db.Column(db.Integer, default=0)  # 域名總數
    status = db.Column(db.String(20), nullable=False, default='pending')  # 掃描狀態
    error_message = db.Column(db.Text, nullable=True)  # 錯誤信息
    scan_time = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 掃描時間
    
    def __init__(self, target_id, domains=None, total_domains=0, status='pending', error_message=None, scan_time=None):
        self.target_id = target_id
        self.domains = domains or []
        self.total_domains = total_domains
        self.status = status
        self.error_message = error_message
        self.scan_time = scan_time or datetime.now()

    def to_dict(self):
        """將結果轉換為字典格式"""
        return {
            'id': self.id,
            'target_id': self.target_id,
            'domains': self.domains or [],
            'total_domains': self.total_domains,
            'status': self.status,
            'error_message': self.error_message,
            'scan_time': self.scan_time.timestamp() if self.scan_time else None
        }

class webtech_Result(db.Model):
    """webtech掃描結果模型"""
    __tablename__ = 'webtech_result'
    
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id', name='fk_webtech_target'), nullable=False)
    webtech_result = db.Column(db.Text, nullable=False)
    web_tech = db.Column(db.String(255), nullable=False, default='沒有掃描到')
    web_base_on = db.Column(db.Text, nullable=False, default='沒有掃描到')
    if_cloudflare = db.Column(db.Boolean, default=False)
    scan_time = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 掃描時間
    
    def to_dict(self):
        """將結果轉換為字典格式"""
        return {
            'id': self.id,
            'target_id': self.target_id,
            'webtech_result': json.loads(self.webtech_result) if self.webtech_result else None,
            'web_tech': self.web_tech,
            'web_base_on': self.web_base_on,
            'if_cloudflare': self.if_cloudflare,
            'scan_time': self.scan_time.timestamp() if self.scan_time else None
        }
    
    def __init__(self, target_id, webtech_result, web_tech='沒有掃描到', web_base_on='沒有掃描到', if_cloudflare=False):
        self.target_id = target_id
        self.webtech_result = webtech_result
        self.web_tech = web_tech
        self.web_base_on = web_base_on
        self.if_cloudflare = if_cloudflare
        self.scan_time = datetime.now()

class crawler_each_url(db.Model):
    """crawler每個url掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    status_code = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    # 關聯定義
    crawler_each_js = db.relationship('crawler_each_js', backref='url', lazy='dynamic', cascade='all, delete-orphan')
    crawler_each_form = db.relationship('crawler_each_form', backref='url', lazy='dynamic', cascade='all, delete-orphan')
    crawler_each_image = db.relationship('crawler_each_image', backref='url', lazy='dynamic', cascade='all, delete-orphan')
    crawler_each_html = db.relationship('crawler_each_html', backref='url', lazy='dynamic', cascade='all, delete-orphan')
    crawler_each_security = db.relationship('crawler_each_security', backref='url', lazy='dynamic', cascade='all, delete-orphan')

class crawler_each_js(db.Model):
    """crawler_each_url每個js掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    js = db.Column(db.Text, nullable=False)
    js_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    crawler_each_url_id = db.Column(db.Integer, db.ForeignKey('crawler_each_url.id'), nullable=False)

class crawler_each_form(db.Model):
    """crawler_each_url每個form掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    form = db.Column(db.Text, nullable=False)
    form_method = db.Column(db.String(10))
    form_action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    crawler_each_url_id = db.Column(db.Integer, db.ForeignKey('crawler_each_url.id'), nullable=False)
    
    # 關聯定義
    parameters = db.relationship('FormParameter', backref='form', lazy='dynamic', cascade='all, delete-orphan')

class FormParameter(db.Model):
    """表單參數模型"""
    __tablename__ = 'form_parameter'
    
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('crawler_each_form.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    param_type = db.Column(db.String(50))  # input, select, textarea 等
    parameter_source = db.Column(db.String(50))  # 'GET', 'POST', 'URL', 'COOKIE' 等
    required = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.String(255))
    placeholder = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class crawler_each_image(db.Model):
    """每個圖片掃描結果模型,在crawler_each_url中"""
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    image_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    crawler_each_url_id = db.Column(db.Integer, db.ForeignKey('crawler_each_url.id'), nullable=False)

class crawler_each_html(db.Model):
    """每個html掃描結果模型,在crawler_each_url中"""
    id = db.Column(db.Integer, primary_key=True)
    html = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    crawler_each_url_id = db.Column(db.Integer, db.ForeignKey('crawler_each_url.id'), nullable=False)

class crawler_each_security(db.Model):
    """每個安全掃描結果模型,在crawler_each_url中"""
    id = db.Column(db.Integer, primary_key=True)
    security = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    crawler_each_url_id = db.Column(db.Integer, db.ForeignKey('crawler_each_url.id'), nullable=False)

class if_sql_injection(db.Model):
    """sql注入掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    sql_injection = db.Column(db.Text, nullable=False)
    crawler_each_url_id = db.Column(db.Integer, db.ForeignKey('crawler_each_url.id'), nullable=False)
    if_sql_injection = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    scan_time = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 掃描時間
    # 關聯定義
    url = db.relationship('crawler_each_url', backref=db.backref('sql_injections', lazy='dynamic'))

class HarvesterResult(db.Model):
    """theHarvester 扫描结果模型"""
    __tablename__ = 'harvester_results'
    
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    
    # 基本信息
    scan_time = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, error
    error = db.Column(db.Text)
    
    # IP 相关信息
    direct_ips = db.Column(db.JSON)  # 直接关联的 IP 地址
    ip_ranges = db.Column(db.JSON)   # IP 地址段
    cdn_ips = db.Column(db.JSON)     # CDN IP 地址
    
    # DNS 信息
    dns_records = db.Column(db.JSON)  # DNS 记录
    reverse_dns = db.Column(db.JSON)  # 反向 DNS 记录
    asn_info = db.Column(db.JSON)     # ASN 信息
    
    # 域名信息
    subdomains = db.Column(db.JSON)   # 子域名列表
    hosts = db.Column(db.JSON)        # 主机信息
    
    # 其他发现
    urls = db.Column(db.JSON)         # 发现的 URL
    emails = db.Column(db.JSON)       # 电子邮件地址
    social_media = db.Column(db.JSON) # 社交媒体信息
    
    # 扫描配置
    scan_sources = db.Column(db.String(255))  # 使用的数据源
    limit = db.Column(db.Integer)             # 结果限制数
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'target_id': self.target_id,
            'scan_time': self.scan_time.isoformat() if self.scan_time else None,
            'status': self.status,
            'error': self.error,
            
            # IP 相关信息
            'ip_data': {
                'direct_ips': self.direct_ips or [],
                'ip_ranges': self.ip_ranges or [],
                'cdn_ips': self.cdn_ips or []
            },
            
            # DNS 信息
            'dns_data': {
                'dns_records': self.dns_records or [],
                'reverse_dns': self.reverse_dns or [],
                'asn_info': self.asn_info or []
            },
            
            # 域名信息
            'domain_data': {
                'subdomains': self.subdomains or [],
                'hosts': self.hosts or []
            },
            
            # 其他发现
            'discovery_data': {
                'urls': self.urls or [],
                'emails': self.emails or [],
                'social_media': self.social_media or []
            },
            
            # 扫描配置
            'scan_config': {
                'sources': self.scan_sources,
                'limit': self.limit
            }
        }
class vulnerability_scanning_result(db.Model):
    """漏洞掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    crawler_each_url_id = db.Column(db.Integer, db.ForeignKey('crawler_each_url.id'), nullable=False,unique=True)
    vulnerability_scanning_result = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __init__(self, crawler_each_url_id, vulnerability_scanning_result,xss_result):
        self.crawler_each_url_id = crawler_each_url_id
        self.vulnerability_scanning_result = vulnerability_scanning_result
        self.xss_result = xss_result.to_dict()
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'crawler_each_url_id': self.crawler_each_url_id,
            'vulnerability_scanning_result': self.vulnerability_scanning_result,
            'xss_result': self.xss_result
        }
    #子表漏洞模塊
    xss_result = db.relationship('xss_result', backref='vulnerability_scanning_result', lazy='dynamic')
class xss_result(db.Model):
    """xss掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    xss_result = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    vulnerability_scanning_result_id = db.Column(db.Integer, db.ForeignKey('vulnerability_scanning_result.id'), nullable=False,unique=True)
    if_xss = db.Column(db.Boolean, default=False)
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'xss_result': self.xss_result
        }
    
