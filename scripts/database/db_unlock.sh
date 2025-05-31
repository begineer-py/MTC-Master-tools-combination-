#!/bin/bash

echo "===================================================="
echo "C2 數據庫自動解鎖工具"
echo "===================================================="
echo ""

# 檢查Python是否可用
if ! command -v python &> /dev/null; then
    echo "未找到Python。請確保安裝了Python並添加到PATH環境變量中。"
    exit 1
fi

# 設置激活虛擬環境（如果有）
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "開始解鎖數據庫..."
echo ""

# 運行數據庫工具
python instance/tools/db_manager.py --unlock --check

echo ""
echo "操作完成。"
echo ""
echo "要運行更多數據庫維護選項，請使用以下命令："
echo "python instance/tools/db_manager.py --help"
echo ""
echo "要修復數據庫請使用："
echo "python instance/tools/db_manager.py --repair"
echo ""
echo "要設置自動定時解鎖（僅Linux/macOS）："
echo "python instance/tools/db_manager.py --auto"
echo ""

# 設置腳本權限
chmod +x instance/tools/db_manager.py 