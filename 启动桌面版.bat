@echo off
chcp 65001 >nul
setlocal
set "release_dir=%~dp0ctrlora\dist\CtrLoRADesktop"
if exist "%release_dir%\CtrLoRADesktop.exe" (
    start "" /D "%release_dir%" "%release_dir%\CtrLoRADesktop.exe"
) else (
    call "%~dp0ctrlora\启动桌面版.bat"
)
endlocal
