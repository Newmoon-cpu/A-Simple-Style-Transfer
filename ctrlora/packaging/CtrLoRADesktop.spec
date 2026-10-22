# -*- mode: python ; coding: utf-8 -*-
# CtrLoRA 桌面版打包 spec
# 关键：不用 --collect-all torch（会卡死），靠 PyInstaller 自带 torch hook 收集 DLL，
#       只手动 collect_submodules cldm/ldm/annotator 处理动态导入。
import os
import sys
from pathlib import Path
from PyInstaller import isolated
from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, collect_data_files

PROJECT_DIR = Path(SPECPATH).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))
os.chdir(PROJECT_DIR)

# PyInstaller's Windows DLL discovery otherwise imports Qt before torch.
# Preload torch only in that discovery subprocess to avoid a loader deadlock.
_original_call = isolated.Python.call

def _preload_torch():
    import torch

def _torch_first_call(self, function, *args, **kwargs):
    if function.__name__ == 'setup' and function.__module__ == 'PyInstaller.building.build_main':
        _original_call(self, _preload_torch)
    return _original_call(self, function, *args, **kwargs)

isolated.Python.call = _torch_first_call

hiddenimports = []
for pkg in ['cldm', 'ldm', 'annotator']:
    hiddenimports += collect_submodules(pkg)

# torch 的 DLL（c10.dll、cudnn、cublas 等）——作为 torch hook 之外的补充
binaries = collect_dynamic_libs('torch')

a = Analysis(
    [str(PROJECT_DIR / 'app/qt_app.py')],
    pathex=[str(PROJECT_DIR)],
    binaries=binaries,
    datas=collect_data_files('open_clip'),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(PROJECT_DIR / 'packaging/runtime_torch_first.py')],
    excludes=['tensorflow', 'detectron2', 'matplotlib', 'tkinter', 'PyQt6', 'PySide6'],
    noarchive=False,
)

# Preserve namespace parents for dynamically imported model modules.
_known_modules = {entry[0] for entry in a.pure}
for _name in list(_known_modules):
    if _name.split('.')[0] not in {'cldm', 'ldm', 'annotator', 'app'}:
        continue
    _parts = _name.split('.')
    for _length in range(1, len(_parts)):
        _parent = '.'.join(_parts[:_length])
        if _parent not in _known_modules:
            a.pure.append((_parent, '-', 'PYMODULE'))
            _known_modules.add(_parent)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CtrLoRADesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='CtrLoRADesktop',
)
