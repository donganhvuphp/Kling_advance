@echo off
chcp 65001 >nul
echo ========================================
echo   KLING VIDEO GENERATOR
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Môi trường ảo chưa được tạo!
    echo Vui lòng chạy setup.bat trước
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Không thể kích hoạt môi trường ảo!
    pause
    exit /b 1
)

echo [INFO] Đang khởi động ứng dụng...
echo.

REM Run the application
python gui_app.py
if errorlevel 1 (
    echo.
    echo [ERROR] Ứng dụng đã gặp lỗi!
    pause
    exit /b 1
)