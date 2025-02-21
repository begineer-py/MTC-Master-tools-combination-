from flask import make_response
import json
from datetime import datetime
import csv
from io import StringIO
import sys

class ScanResultConverter:
    """掃描結果文件轉換器"""
    
    @staticmethod
    def webtech_to_txt(result_data):
        """將 webtech 掃描結果轉換為 txt 格式"""
        try:
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
                
            output = []
            output.append("Web 技術掃描結果報告")
            output.append("=" * 50)
            output.append(f"掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            output.append("-" * 50)
            
            # 添加技術信息
            if 'technologies' in result_data:
                output.append("\n檢測到的技術:")
                for tech in result_data['technologies']:
                    output.append(f"\n技術名稱: {tech.get('name', 'N/A')}")
                    output.append(f"版本: {tech.get('version', 'N/A')}")
                    output.append(f"置信度: {tech.get('confidence', 'N/A')}%")
                    if 'categories' in tech:
                        output.append(f"類別: {', '.join(tech['categories'])}")
                    output.append("-" * 30)
            
            # 添加安全特徵
            if 'security_features' in result_data:
                output.append("\n安全特徵:")
                security = result_data['security_features']
                output.append(f"WAF: {security.get('waf', 'N/A')}")
                output.append(f"SSL信息: {security.get('ssl_info', 'N/A')}")
                if 'security_headers' in security:
                    output.append("安全標頭:")
                    for header in security['security_headers']:
                        output.append(f"- {header}")
            
            return "\n".join(output)
        except Exception as e:
            sys.stderr.write(f"轉換 webtech 結果到 TXT 時發生錯誤: {str(e)}\n")
            raise
    
    @staticmethod
    def webtech_to_csv(result_data):
        """將 webtech 掃描結果轉換為 CSV 格式"""
        try:
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
                
            output = StringIO()
            writer = csv.writer(output)
            
            # 寫入標題
            writer.writerow(['技術名稱', '版本', '置信度', '類別'])
            
            # 寫入技術數據
            if 'technologies' in result_data:
                for tech in result_data['technologies']:
                    writer.writerow([
                        tech.get('name', 'N/A'),
                        tech.get('version', 'N/A'),
                        tech.get('confidence', 'N/A'),
                        ','.join(tech.get('categories', []))
                    ])
            
            return output.getvalue()
        except Exception as e:
            sys.stderr.write(f"轉換 webtech 結果到 CSV 時發生錯誤: {str(e)}\n")
            raise
    
    @staticmethod
    def webtech_to_json(result_data):
        """將 webtech 掃描結果轉換為格式化的 JSON"""
        try:
            sys.stdout.write(f"開始轉換 JSON，輸入數據類型: {type(result_data)}\n")
            
            # 如果是字符串，嘗試解析為 JSON
            if isinstance(result_data, str):
                sys.stdout.write("輸入是字符串，嘗試解析為 JSON\n")
                result_data = json.loads(result_data)
                sys.stdout.write("JSON 解析成功\n")
            
            # 確保數據是字典類型
            if not isinstance(result_data, dict):
                sys.stderr.write(f"數據不是字典類型: {type(result_data)}\n")
                result_data = {"error": "無效的數據格式"}
            
            # 轉換為格式化的 JSON 字符串
            formatted_json = json.dumps(result_data, indent=2, ensure_ascii=False)
            sys.stdout.write("JSON 格式化成功\n")
            
            return formatted_json
            
        except json.JSONDecodeError as e:
            sys.stderr.write(f"JSON 解析錯誤: {str(e)}\n")
            raise
        except Exception as e:
            sys.stderr.write(f"轉換 webtech 結果到 JSON 時發生錯誤: {str(e)}\n")
            raise
    
    @staticmethod
    def create_file_response(data, filename, file_type):
        """創建文件下載響應"""
        try:
            sys.stdout.write(f"創建文件響應: filename={filename}, file_type={file_type}\n")
            response = make_response(data)
            
            # 設置適當的 Content-Type
            content_types = {
                'txt': 'text/plain',
                'csv': 'text/csv',
                'json': 'application/json'
            }
            content_type = content_types.get(file_type, 'text/plain')
            sys.stdout.write(f"設置 Content-Type: {content_type}\n")
            response.headers['Content-Type'] = content_type
            
            # 設置文件名
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            sys.stdout.write("響應頭設置完成\n")
            
            return response
        except Exception as e:
            sys.stderr.write(f"創建文件響應時發生錯誤: {str(e)}\n")
            raise 