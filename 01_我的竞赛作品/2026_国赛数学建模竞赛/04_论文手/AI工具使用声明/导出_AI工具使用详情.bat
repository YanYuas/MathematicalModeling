@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================================
echo  导出「AI 工具使用详情.pdf」——一键脚本
echo  作用：把 AI工具使用详情.md 转成可打印 HTML，并在浏览器打开
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 python。请先安装 Python 3 并加入 PATH。
  pause
  exit /b 1
)

python "_ai_detail_to_html.py"
if errorlevel 1 (
  echo.
  echo [错误] 生成 HTML 失败，请查看上方输出。
  pause
  exit /b 1
)

echo.
echo [打开] 正在用默认浏览器打开 AI工具使用详情.html ...
start "" "AI工具使用详情.html"

echo.
echo ============================================================
echo  请在浏览器中按 Ctrl+P，然后：
echo    1) 目标打印机选择「另存为 PDF」
echo    2) 文件名填：AI 工具使用详情.pdf   （文件名必须逐字一致）
echo    3) 保存到：06_交付物\  （支撑材料目录）
echo ============================================================
echo.
pause
endlocal
