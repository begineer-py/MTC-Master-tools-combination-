import os 
import requests
import json
import sys
from instance.models import Target,db
class API_SET:
    def __init__(self,user_id,target_id,api_key):
        self.error_message = ""
        self.user_id = user_id
        self.target_id = target_id
        self.api_key = api_key
    def check_api(self):
        try:
            target = Target.query.filter_by(user_id=self.user_id, id=self.target_id).first()
            if not target:
                return False, "目标不存在"
            if not target.api_key:
                return False, "API Key 未生成"
            if target.api_key == self.api_key:
                return True, "API Key 验证成功"
            return False, "API Key 无效"
        except Exception as e:
            return False, f"API 错误: {e}"
    def get_api_key(self):
        try:
            target = Target.query.filter_by(user_id=self.user_id,id=self.target_id).first()
            if target:
                return target.api_key
            else:
                return False
        except Exception as e:
            sys.stderr.write(f"提取API錯誤: {e}")        
            error_message = f"提取API錯誤: {e}"        
            return False,error_message
    def make_api_key(self):
        try:
            api_key = os.urandom(64).hex()
            target = Target.query.filter_by(user_id=self.user_id,id=self.target_id).first()
            target.api_key = api_key
            db.session.commit()
            return api_key  
        except Exception as e:
            sys.stderr.write(f"生成API錯誤: {e}")        
            error_message = f"生成API錯誤: {e}"        
            return False,error_message
    def delete_api_key(self):
        try:
            target = Target.query.filter_by(user_id=self.user_id,id=self.target_id).first()
            target.api_key = None
            db.session.commit()
            return True
        except Exception as e:
            sys.stderr.write(f"刪除API錯誤: {e}")
            error_message = f"刪除API錯誤: {e}"        
            return False,error_message

