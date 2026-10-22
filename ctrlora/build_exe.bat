@echo off
chcp 65001 >nul
rem 打包桌面版为 exe（onedir 模式，输出到 dist\CtrLoRADesktop\）
rem Large model files are copied beside the executable, not embedded in it.
cd /d "%~dp0"

python -m PyInstaller --noconfirm packaging\CtrLoRADesktop.spec
if errorlevel 1 exit /b 1

rem Copy real files so the release can be moved to another directory or computer.
robocopy configs dist\CtrLoRADesktop\configs /E /NFL /NDL /NJH /NJS /NP
if errorlevel 8 exit /b 1
if exist "%USERPROFILE%\.cache\huggingface\hub\models--openai--clip-vit-large-patch14" (
    robocopy "%USERPROFILE%\.cache\huggingface\hub\models--openai--clip-vit-large-patch14" dist\CtrLoRADesktop\hf-cache\models--openai--clip-vit-large-patch14 /E /NFL /NDL /NJH /NJS /NP
    if errorlevel 8 exit /b 1
)
robocopy ckpts dist\CtrLoRADesktop\ckpts /E /NFL /NDL /NJH /NJS /NP
if errorlevel 8 exit /b 1
robocopy annotator dist\CtrLoRADesktop\annotator /E /NFL /NDL /NJH /NJS /NP /XD __pycache__
if errorlevel 8 exit /b 1

copy /Y LICENSE dist\CtrLoRADesktop\LICENSE-CtrLoRA.txt >nul
if errorlevel 1 exit /b 1
copy /Y "packaging\README-desktop.txt" "dist\CtrLoRADesktop\使用说明.txt" >nul
if errorlevel 1 exit /b 1

echo.
echo 打包完成，exe 在 dist\CtrLoRADesktop\CtrLoRADesktop.exe
echo 请保留整个 CtrLoRADesktop 文件夹，不能单独移动 exe。
pause
