@echo off
chcp 65001 >nul
title English Listening - 停止服务

echo 正在停止服务...

REM 杀掉占用端口的进程（后端 8000 / 前端 5173）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1

REM 关闭启动器打开的窗口
taskkill /FI "WINDOWTITLE eq EL-backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq EL-frontend*" /F >nul 2>&1

echo 服务已全部停止。
timeout /t 2 >nul 2>&1
