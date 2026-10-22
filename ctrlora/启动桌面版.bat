@echo off
rem CtrLoRA 桌面版启动器：双击即用，不显示终端窗口
cd /d "%~dp0"
where pythonw.exe >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw.exe app\qt_app.py
) else (
    where python.exe >nul 2>nul
    if %errorlevel%==0 (
        start "" python.exe app\qt_app.py
    ) else (
        echo 未找到 Python，请先安装 Python 3.11 并加入 PATH。
        pause
    )
)
