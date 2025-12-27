# c2_core/config/utils.py
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def sanitize_for_db(data: Any) -> Any:
    """
    對準備存入資料庫的數據進行深度消毒。
    主要目標是幹掉 PostgreSQL 不喜歡的 `\u0000` 空字符。
    這東西能處理字串、字典、列表等各種結構。
    """
    if data is None:
        return None

    # 如果是簡單的字串，直接替換
    if isinstance(data, str):
        return data.replace("\x00", "")  # \x00 是 \u0000 的另一種寫法

    # 如果是字典或列表，就用 json 序列化大法來深度清洗
    if isinstance(data, (dict, list)):
        try:
            # 1. 序列化成字串，幹掉非標準類型
            json_string = json.dumps(data, default=str)
            # 2. 在字串層面，幹掉所有空字符
            sanitized_json_string = json_string.replace("\\u0000", "")
            # 3. 重新解析回 Python 物件
            return json.loads(sanitized_json_string)
        except Exception as e:
            logger.error(f"數據消毒時發生錯誤: {e}. 返回原始數據。")
            # 如果消毒失敗，至少返回原始數據，而不是讓程式崩潰
            return data

    # 如果是其他類型 (int, bool 等)，它們是安全的，直接返回
    return data
