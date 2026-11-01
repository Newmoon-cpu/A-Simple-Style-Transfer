@echo off
chcp 65001 >nul
cd /d "%~dp0"
start /wait "" CtrLoRADesktop.exe --download-models
type download-status.txt
pause
