import base64
import urllib.parse
import re
import html
import random
class XSS_encode:
    def __init__(self,payload,encode_type):
        self.payload = payload
        self.encode_type = encode_type
    def to_encode(self):
        self.to_encode_payload = self.payload
        for encode_type in self.encode_type:
            if encode_type == "html":
                self.to_encode_payload = self.html_encode(self.to_encode_payload)
            elif encode_type == "base64":
                self.to_encode_payload = self.base64_encode(self.to_encode_payload)
            elif encode_type == "url_encode":
                self.to_encode_payload = self.url_encode(self.to_encode_payload)
            elif encode_type == "url_plus":
                self.to_encode_payload = self.url_encode_plus(self.to_encode_payload)
            elif encode_type == "unicode_only_char":
                self.to_encode_payload = self.unicode_encode_only_char(self.to_encode_payload)
            elif encode_type == "unicode_all":
                self.to_encode_payload = self.unicode_encode_all(self.to_encode_payload)
        return self.to_encode_payload
    def html_encode(self,to_encode_payload):
        return html.escape(to_encode_payload)
    def base64_encode(self,to_encode_payload):
        payload_bytes = to_encode_payload.encode('utf-8')
        base64_bytes = base64.b64encode(payload_bytes)
        base64_str = base64_bytes.decode('utf-8')
        return base64_str
    def url_encode(self,to_encode_payload):
        return urllib.parse.quote(to_encode_payload)
    def url_encode_plus(self,to_encode_payload):
        return urllib.parse.quote_plus(to_encode_payload)
    def unicode_encode_only_char(self,to_encode_payload):
        encoded_chars_list = []
        for char in to_encode_payload:
            if "a" <= char.lower() <= "z" or "0" <= char <= "9":
                encoded_chars_list.append(char)
            else:
                encoded_chars_list.append(f'\\u{ord(char):04x}')
        return "".join(encoded_chars_list)
    def unicode_encode_all(self,to_encode_payload):
        encoded_chars_list = []
        for char in to_encode_payload:
            encoded_chars_list.append(f'\\u{ord(char):04x}')
        return "".join(encoded_chars_list)
    def ramdom_junk_encode(self,to_encode_payload):
        
print(XSS_encode("hello",["html","url_encode","unicode_all","base64"]).to_encode())
