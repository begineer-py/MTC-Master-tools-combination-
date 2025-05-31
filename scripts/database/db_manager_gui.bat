@echo off
echo ====================================================
echo C2 數據庫管理工具 (GUI)
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

REM 檢查tkinter是否安裝
python -c "import tkinter" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 未安裝tkinter模塊，請先安裝Python的tkinter模塊。
    echo 您可以嘗試重新安裝Python時勾選tcl/tk和IDLE選項。
    pause
    exit /b 1
)

echo 正在啟動數據庫管理工具GUI...
echo.

REM 運行GUI工具
python instance/tools/db_gui.py

echo.
exit /b 0 