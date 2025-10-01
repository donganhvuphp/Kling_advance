@echo off
chcp 65001 >nul
echo ========================================
echo   KLING VIDEO GENERATOR - SETUP
echo ========================================
echo.

REM Check Python installation (try 'python' first, then 'py')
set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python không được tìm thấy!
        echo Vui lòng cài đặt Python 3.8+ từ https://www.python.org/downloads/
        echo Nhớ check "Add Python to PATH" khi cài đặt!
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
)

echo [✓] Python đã được cài đặt
%PYTHON_CMD% --version
echo.

REM Create virtual environment if not exists
if not exist "venv" (
    echo [INFO] Đang tạo môi trường ảo Python...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Không thể tạo môi trường ảo!
        pause
        exit /b 1
    )
    echo [✓] Đã tạo môi trường ảo
) else (
    echo [✓] Môi trường ảo đã tồn tại
)
echo.

REM Activate virtual environment
echo [INFO] Kích hoạt môi trường ảo...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Không thể kích hoạt môi trường ảo!
    pause
    exit /b 1
)
echo [✓] Đã kích hoạt môi trường ảo
echo.

REM Upgrade pip
echo [INFO] Cập nhật pip...
python -m pip install --upgrade pip --quiet
echo [✓] Đã cập nhật pip
echo.

REM Install requirements
echo [INFO] Đang cài đặt thư viện cần thiết...
echo - playwright
echo - PyQt6
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Cài đặt thư viện thất bại!
    pause
    exit /b 1
)
echo [✓] Đã cài đặt thư viện
echo.

REM Install Playwright browsers
echo [INFO] Đang cài đặt trình duyệt Chromium cho Playwright...
echo (Quá trình này có thể mất vài phút...)
python -m playwright install chromium
if errorlevel 1 (
    echo [ERROR] Cài đặt Chromium thất bại!
    pause
    exit /b 1
)
echo [✓] Đã cài đặt Chromium
echo.

echo ========================================
echo   CÀI ĐẶT HOÀN TẤT!
echo ========================================
echo.
echo Bây giờ bạn có thể chạy start.bat để khởi động ứng dụng
echo.
pause