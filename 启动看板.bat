@echo off
chcp 936 >nul 2>&1
setlocal
title 实验2 数据看板 - 校园消费数据看板
cd /d "%~dp0"

echo ============================================================
echo   实验2 数据看板 . 校园消费数据看板
echo   Streamlit + Pandas + Plotly
echo ============================================================
echo.

rem ---------- 1/3 定位 Python 解释器 ----------
set "PY="
set "VENV=%~dp0..\..\.venv"
for %%I in ("%VENV%") do set "VENV=%%~fI"
if exist "%VENV%\Scripts\python.exe" (
    set "PY=%VENV%\Scripts\python.exe"
    echo [1/3] 解释器：项目虚拟环境 %VENV%
    goto :check_deps
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    echo [1/3] 解释器：系统 Python
    goto :check_deps
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PY=py -3"
    echo [1/3] 解释器：Python 启动器 py -3
    goto :check_deps
)

echo [X] 没有找到 Python。请安装 Python 3.10 及以上版本，
echo     安装时勾选 "Add Python to PATH"，然后重新双击本文件。
echo.
pause
exit /b 1

:check_deps
rem ---------- 2/3 检查依赖 ----------
%PY% -c "import streamlit, pandas, plotly, numpy, openpyxl" >nul 2>&1
if not errorlevel 1 (
    echo [2/3] 依赖已就绪
    goto :run
)

echo [2/3] 缺少依赖，正在安装（首次运行需要几分钟）...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [X] 依赖安装失败。请检查网络后手动执行：
    echo     %PY% -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:run
rem ---------- 3/3 启动看板 ----------
if not exist "data\校园消费数据.csv" (
    echo [提示] 未找到数据文件，正在生成模拟数据 ...
    %PY% generate_data.py
    if errorlevel 1 (
        echo [X] 数据生成失败，请手动执行：%PY% generate_data.py
        echo.
        pause
        exit /b 1
    )
)

echo [3/3] 正在启动看板： http://localhost:8501
echo       浏览器会自动打开；关闭本窗口即停止看板。
echo.
rem showEmailPrompt=false 很关键：否则 Streamlit 首次运行会在终端要邮箱，
rem 而它需要写 %%USERPROFILE%%\.streamlit，权限受限时会直接退出。
%PY% -m streamlit run app.py --server.port 8501 --server.headless=false --server.showEmailPrompt=false --browser.gatherUsageStats=false

set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
    echo 看板已正常退出。
) else (
    echo [X] 看板异常退出，退出码 %RC%。
    echo     常见原因：
    echo       1^) 端口 8501 被占用：关掉已打开的看板窗口，或把本文件的 --server.port 改成 8502
    echo       2^) 依赖损坏：执行  %PY% -m pip install -r requirements.txt
    echo     若你是自己按 Ctrl+C 停下来的，忽略下面的提示。
    echo     否则请把上面的报错信息完整截图发给老师。
)
echo.
echo 按任意键关闭本窗口 ...
pause >nul
endlocal
