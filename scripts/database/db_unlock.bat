@echo off
echo ====================================================
echo C2 數據庫自動解鎖工具
echo ====================================================
echo.

REM 獲取Python路徑
where python > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 未找到Python。請確保安裝了Python並添加到PATH環境變量中。
    pause
    exit /b 1
)

REM 設置激活虛擬環境（如果有）
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo 開始解鎖數據庫...
echo.

REM 運行數據庫工具
python instance/tools/db_manager.py --unlock --check

echo.
echo 操作完成。
echo.
echo 要運行更多數據庫維護選項，請使用以下命令：
echo python instance/tools/db_manager.py --help
echo.
echo 要修復數據庫請使用：
echo python instance/tools/db_manager.py --repair
echo.

pause 