import base64  # 用於Base64編碼和解碼
import urllib.parse  # 用於URL編碼
import re  # 正則表達式模組
import html  # HTML編碼和解碼
import random  # 隨機數生成
import os

class XSS_encode:  # XSS編碼類別
    def __init__(self,payload,encode_type):  # 初始化方法，接收payload和編碼類型
        self.payload = payload  # 儲存原始payload
        self.encode_type = encode_type  # 儲存編碼類型列表
        self.waf_keywords = []
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            junk_file_path = os.path.join(script_dir, 'WAF_junks.txt')
            with open(junk_file_path, 'r') as f:
                self.waf_keywords = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("WAF_junks.txt not found. The junk encoding will not work.")

    def to_encode(self):  # 主要編碼方法
        self.to_encode_payload = self.payload  # 初始化要編碼的payload
        for encode_type in self.encode_type:  # 遍歷所有編碼類型
            if encode_type == "html":  # HTML編碼
                self.to_encode_payload = self.html_encode(self.to_encode_payload)
            elif encode_type == "base64":  # Base64編碼
                self.to_encode_payload = self.base64_encode(self.to_encode_payload)
            elif encode_type == "url_encode":  # URL編碼
                self.to_encode_payload = self.url_encode(self.to_encode_payload)
            elif encode_type == "url_plus":  # URL Plus編碼
                self.to_encode_payload = self.url_encode_plus(self.to_encode_payload)
            elif encode_type == "unicode_only_char":  # 僅特殊字符Unicode編碼
                self.to_encode_payload = self.unicode_encode_only_char(self.to_encode_payload)
            elif encode_type == "unicode_all":  # 全部字符Unicode編碼
                self.to_encode_payload = self.unicode_encode_all(self.to_encode_payload)
            elif encode_type == "ramdom_junk":
                self.to_encode_payload = self.ramdom_junk_encode(self.to_encode_payload)
        return self.to_encode_payload  # 返回編碼後的結果
    def html_encode(self,to_encode_payload):  # HTML編碼方法
        return html.escape(to_encode_payload)  # 使用html.escape進行HTML編碼
    def base64_encode(self,to_encode_payload):  # Base64編碼方法
        payload_bytes = to_encode_payload.encode('utf-8')  # 將字符串轉換為UTF-8字節
        base64_bytes = base64.b64encode(payload_bytes)  # 進行Base64編碼
        base64_str = base64_bytes.decode('utf-8')  # 將字節轉換回字符串
        return base64_str  # 返回Base64編碼結果
    def url_encode(self,to_encode_payload):  # URL編碼方法
        return urllib.parse.quote(to_encode_payload)  # 使用quote進行URL編碼
    def url_encode_plus(self,to_encode_payload):  # URL Plus編碼方法
        return urllib.parse.quote_plus(to_encode_payload)  # 使用quote_plus進行URL編碼（空格轉為+）
    def unicode_encode_only_char(self,to_encode_payload):  # 僅特殊字符Unicode編碼方法
        encoded_chars_list = []  # 儲存編碼結果的列表
        for char in to_encode_payload:  # 遍歷每個字符
            if "a" <= char.lower() <= "z" or "0" <= char <= "9":  # 如果是字母或數字
                encoded_chars_list.append(char)  # 保持原樣
            else:  # 如果是特殊字符
                encoded_chars_list.append(f'\\u{ord(char):04x}')  # 轉換為Unicode編碼
        return "".join(encoded_chars_list)  # 合併所有字符並返回
    def unicode_encode_all(self,to_encode_payload):  # 全部字符Unicode編碼方法
        encoded_chars_list = []  # 儲存編碼結果的列表
        for char in to_encode_payload:  # 遍歷每個字符
            encoded_chars_list.append(f'\\u{ord(char):04x}')  # 將每個字符轉換為Unicode編碼
        return "".join(encoded_chars_list)  # 合併所有字符並返回
    def ramdom_junk_encode(self,to_encode_payload):  # 隨機垃圾編碼方法
        if not hasattr(self, 'waf_keywords') or not self.waf_keywords:
            return to_encode_payload

        keywords = sorted(self.waf_keywords, key=len, reverse=True)
        pattern = re.compile('|'.join(re.escape(keyword) for keyword in keywords), re.IGNORECASE)

        def replacement(match):
            keyword = match.group(0)
            if len(keyword) <= 1:
                return keyword

            obfuscated = [keyword[0]]
            for char in keyword[1:]:
                junk_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                junk_value = "".join(random.choice(junk_chars) for _ in range(random.randint(2, 8)))
                obfuscated.append(f"/*{junk_value}*/")
                obfuscated.append(char)
            
            return "".join(obfuscated)

        return pattern.sub(replacement, to_encode_payload)

print(XSS_encode("<script>alert(1)</script>",["ramdom_junk"]).to_encode())
