@echo off
chcp 65001 >nul
echo ========================================
echo 半格胶片裁切工具
echo ========================================
echo.

cd /d "%~dp0"

if not exist "input" (
    echo [错误] input 文件夹不存在
    pause
    exit /b 1
)

REM 检查input文件夹是否有文件
dir /b "input\*.*" 2>nul | findstr "." >nul
if errorlevel 1 (
    echo [错误] input 文件夹为空，请放入需要裁切的图片
    pause
    exit /b 1
)

echo 开始裁切...
echo.

python main.py input/ -o output/

echo.
echo ========================================
echo 裁切完成！结果保存在 output 文件夹
echo ========================================
pause
