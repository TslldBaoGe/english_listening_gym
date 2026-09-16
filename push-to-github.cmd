@echo off
cd /d "D:\english-listening"
echo ============================================
echo   Pushing english_listening_gym to GitHub
echo ============================================
echo.
git remote set-url origin git@github.com:TslldBaoGe/english_listening_gym.git
echo.
echo Pushing to GitHub...
git push -u origin master
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   Push successful! 
    echo ============================================
) else (
    echo.
    echo Push failed. Check error message above.
)
pause