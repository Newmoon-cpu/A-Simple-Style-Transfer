# Reassemble reviewed Python source with a completed dependency analysis.
# Use only when runtime dependencies have not changed; run the full spec first.
import ast,os
from pathlib import Path
from PyInstaller.config import CONF
ROOT=Path(SPECPATH).resolve().parent
os.chdir(ROOT)
toc=ast.literal_eval((ROOT/'build-replay/CtrLoRADesktop/Analysis-00.toc').read_text(encoding='utf-8'))
pure=list(toc[14])
for name in ['resource_download','woodcut_adapter','styles','core','ldm.modules.encoders.modules','app.qt_app','app.image_widgets']:
 entry=(name,str(ROOT/(name.replace('.','/')+'.py')),'PYMODULE')
 pure=[x for x in pure if x[0]!=name];pure.append(entry)
known={x[0] for x in pure}
for name in list(known):
 if name.split('.')[0] not in {'cldm','ldm','annotator','app'}:continue
 parts=name.split('.')
 for n in range(1,len(parts)):
  parent='.'.join(parts[:n])
  if parent not in known:pure.append((parent,'-','PYMODULE'));known.add(parent)
pyz=PYZ(pure,name=str(Path(CONF['workpath'])/'PYZ-online-reviewed.pyz'))
exe=EXE(pyz,toc[13],[],exclude_binaries=True,name='CtrLoRADesktop',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False,disable_windowed_traceback=False)
coll=COLLECT(exe,toc[15],toc[18],strip=False,upx=False,name='CtrLoRADesktop')
