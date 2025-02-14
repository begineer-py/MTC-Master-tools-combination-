import sys
import os

# 添加項目根目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

import logging
from flask import Flask
from .cloudflare_bypass import CloudflareBypass
from models import db, crawler_each_url, crawler_each_form, FormParameter, Target

def setup_logging():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

def create_test_app():
    """創建測試用的 Flask 應用"""
    app = Flask(__name__)
    
    # 使用絕對路徑
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance', 'c2.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True  # 啟用 SQL 語句日誌
    
    # 確保 instance 目錄存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    db.init_app(app)
    
    return app

def analyze_parameters(url_id):
    """分析特定 URL 的所有參數"""
    try:
        # 獲取 URL 記錄
        url_record = crawler_each_url.query.get(url_id)
        if not url_record:
            logger.error(f"未找到 URL ID: {url_id}")
            return
        
        logger.info(f"\n{'='*50}")
        logger.info(f"分析 URL: {url_record.url}")
        logger.info(f"{'='*50}")
        
        # 獲取所有相關的表單
        forms = crawler_each_form.query.filter_by(crawler_each_url_id=url_id).all()
        
        if not forms:
            logger.info("未找到任何表單")
            return
        
        for form in forms:
            logger.info(f"\n表單 ID: {form.id}")
            logger.info(f"方法: {form.form_method}")
            logger.info(f"動作: {form.form_action}")
            
            # 獲取該表單的所有參數
            parameters = FormParameter.query.filter_by(form_id=form.id).all()
            
            if not parameters:
                logger.info("此表單沒有參數")
                continue
            
            logger.info("\n參數列表:")
            for param in parameters:
                logger.info(f"""
                參數名稱: {param.name}
                參數來源: {param.parameter_source}
                參數類型: {param.param_type}
                是否必填: {param.required}
                默認值: {param.default_value}
                佔位符: {param.placeholder}
                {'-'*30}""")
                
    except Exception as e:
        logger.error(f"分析參數時出錯: {str(e)}")

def test_parameter_extraction(url, target_id=1):
    """測試參數提取功能"""
    try:
        app = create_test_app()
        with app.app_context():
            logger.info(f"開始測試 URL: {url}")
            
            # 檢查數據庫連接
            try:
                db.session.execute(db.text("SELECT 1"))
                logger.info("數據庫連接正常")
            except Exception as e:
                logger.error(f"數據庫連接測試失敗: {str(e)}")
                return False
            
            # 檢查目標是否存在
            target = Target.query.get(target_id)
            if not target:
                logger.info("創建測試目標")
                target = Target(
                    id=target_id,
                    target_ip='https://example.com',
                    target_ip_no_https='example.com',
                    target_port=443,
                    target_username='test',
                    target_password='test',
                    user_id=1
                )
                db.session.add(target)
                try:
                    db.session.commit()
                    logger.info("創建測試目標成功")
                except Exception as e:
                    logger.error(f"創建測試目標失敗: {str(e)}")
                    db.session.rollback()
                    return False
            
            # 刪除之前的測試記錄
            try:
                old_url_records = crawler_each_url.query.filter_by(
                    target_id=target_id,
                    url=url
                ).all()
                
                for record in old_url_records:
                    # 刪除相關的表單參數
                    forms = crawler_each_form.query.filter_by(crawler_each_url_id=record.id).all()
                    for form in forms:
                        FormParameter.query.filter_by(form_id=form.id).delete()
                        db.session.delete(form)
                    db.session.delete(record)
                
                db.session.commit()
                logger.info("成功清理舊記錄")
            except Exception as e:
                logger.error(f"清理舊記錄時出錯: {str(e)}")
                db.session.rollback()
                return False
            
            # 創建 CloudflareBypass 實例
            bypass = CloudflareBypass(app=app)
            
            # 執行請求
            success = bypass.make_request(url, target_id)
            
            if success:
                logger.info("請求成功，開始分析參數")
                
                # 獲取最新創建的 URL 記錄
                url_record = crawler_each_url.query.filter_by(
                    target_id=target_id,
                    url=url
                ).order_by(crawler_each_url.id.desc()).first()
                
                if url_record:
                    analyze_parameters(url_record.id)
                    return True
                else:
                    logger.error("未找到 URL 記錄")
                    return False
            else:
                logger.error("請求失敗")
                return False
                
    except Exception as e:
        logger.error(f"測試過程出錯: {str(e)}")
        if 'db' in locals() and hasattr(db, 'session'):
            db.session.rollback()
        return False

def main():
    """主函數"""
    if len(sys.argv) < 2:
        print("使用方法: python test_parameter_extraction.py <URL> [target_id]")
        sys.exit(1)
        
    url = sys.argv[1]
    target_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    test_parameter_extraction(url, target_id)

if __name__ == "__main__":
    main() 