@echo off
chcp 65001 >nul
title English Listening - 服务启动器

echo ============================================
echo   英语听力应用 - 一键启动
echo ============================================
echo.

REM ---- 后端 8000 ----
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [后端] 已在运行，跳过
) else (
    echo [后端] 启动中...
    start "EL-backend" cmd /k "cd /d d:\english-listening\backend && F:\Miniconda39\envs\python31013\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
)

REM ---- 前端 5173（生产构建 + 预览：手机端只需 4 个请求，快且稳）----
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [前端] 已在运行，跳过
) else (
    echo [前端] 构建并启动中（约 10 秒）...
    start "EL-frontend" cmd /k "cd /d d:\english-listening\frontend && npm run build && npm run preview"
)

echo.
echo 全部服务已启动，本机浏览器访问：
echo.
echo     http://localhost:5173
echo.
echo 手机访问（手机需与电脑连同一个 Wi-Fi），可用地址：
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=* delims= " %%j in ("%%i") do echo     http://%%j:5173
)
echo.
echo   上面可能有多个（VMware / vEthernet 的忽略），选 192.168 或 10. 开头的那个。
echo   也可以试试主机名：http://%COMPUTERNAME%:5173
echo   换了 Wi-Fi 地址就会变，重新看这里或执行 ipconfig 即可。
echo.
echo 提示：
echo   - 两个黑窗口是服务进程，不要关闭
echo   - 改了前端代码，重新双击本脚本即可（会自动重新构建）
echo   - 网站打不开就重新双击本脚本（已在运行的会自动跳过）
echo   - 停止服务请双击 stop.bat
echo   - 开发调试用 npm run dev（带热更新）
echo.
timeout /t 10 >nul 2>&1
