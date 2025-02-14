import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from threading import Lock
from flask_login import UserMixin

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
    
    # 關聯定義
    commands = db.relationship('Command_User', backref='user', lazy='dynamic')
    targets = db.relationship('Target', backref='user', lazy='dynamic')

    def set_password(self, password):
        """設置用戶密碼的哈希值"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """檢查用戶輸入的密碼是否正確"""
        return check_password_hash(self.password_hash, password)

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
    api_key = db.Column(db.String(255), nullable=True, unique=True)
    # 關聯定義
    nmap_results = db.relationship('nmap_Result', backref='target', lazy='dynamic')
    crtsh_results = db.relationship('crtsh_Result', backref='target', lazy='dynamic')
    webtech_results = db.relationship('webtech_Result', backref='target', lazy='dynamic')
    crawler_each_urls = db.relationship('crawler_each_url', backref=db.backref('target', lazy='joined'), lazy='dynamic')
    paramspider_results = db.relationship('ParamSpiderResult', backref='target', lazy='dynamic')
    change_urls_into_payloads = db.relationship('change_urls_into_payloads', backref='target', lazy='dynamic')

class nmap_Result(db.Model):
    """掃描結果模型"""
    __tablename__ = 'nmap_result'
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    scan_result = db.Column(db.Text)
    scan_time = db.Column(db.DateTime)
    
    def __init__(self, target_id, scan_result, scan_time):
        self.target_id = target_id
        self.scan_result = scan_result
        self.scan_time = scan_time

class crtsh_Result(db.Model):
    """crtsh掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id', name='fk_crtsh_target'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_crtsh_user'), nullable=False)
    domains = db.Column(db.JSON, nullable=True)  # 存儲域名列表
    total_domains = db.Column(db.Integer, default=0)  # 域名總數
    status = db.Column(db.String(20), nullable=False, default='pending')  # 掃描狀態
    error_message = db.Column(db.Text, nullable=True)  # 錯誤信息
    scan_time = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 掃描時間
    
    def __init__(self, user_id, target_id, domains=None, total_domains=0, status='pending', error_message=None, scan_time=None):
        self.user_id = user_id
        self.target_id = target_id
        self.domains = domains or []
        self.total_domains = total_domains
        self.status = status
        self.error_message = error_message
        self.scan_time = scan_time or datetime.now()

class webtech_Result(db.Model):
    """webtech掃描結果模型"""
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    webtech_result = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    web_tech = db.Column(db.String(255), nullable=False)

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

class ParamSpiderResult(db.Model):
    """ParamSpider 爬取結果模型"""
    __tablename__ = 'paramspider_results'
    
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False, unique=True)
    exclude = db.Column(db.String(255))
    threads = db.Column(db.Integer)
    
    status = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    result_text = db.Column(db.Text)
    total_urls = db.Column(db.Integer, default=0)
    unique_parameters = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    @classmethod
    def get_by_target_id(cls, target_id):
        """通過 target_id 獲取掃描結果"""
        return cls.query.filter_by(target_id=target_id).first()
    def to_dict(self):
        """將結果轉換為字典格式"""
        return {
            'id': self.id,
            'target_id': self.target_id,
            'user_id': self.user_id,
            'crawler_id': self.crawler_id,
            'exclude': self.exclude,
            'threads': self.threads,
            'status': self.status,
            'error_message': self.error_message,
            'result_text': self.result_text,
            'total_urls': self.total_urls,
            'unique_parameters': self.unique_parameters,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class change_urls_into_payloads(db.Model):
    """將urls轉換為payloads"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    payload = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)


