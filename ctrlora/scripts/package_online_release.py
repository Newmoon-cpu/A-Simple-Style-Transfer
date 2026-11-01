"""Maintainer utility: package a built desktop with only the project woodcut adapter."""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--built',default='dist-online/CtrLoRADesktop');a=p.parse_args()
 built=ROOT/a.built;stage=ROOT/'release-staging/CtrLoRADesktop';stage.mkdir(parents=True,exist_ok=True)
 shutil.copytree(built,stage,dirs_exist_ok=True)
 shutil.copytree(ROOT/'configs',stage/'configs',dirs_exist_ok=True)
 (stage/'hf-cache').mkdir(exist_ok=True)
 (stage/'ckpts/style-loras').mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/'ckpts/style-loras/woodcut_style_r16_step0500.safetensors',stage/'ckpts/style-loras')
 shutil.copy2(ROOT/'LICENSE',stage/'LICENSE-CtrLoRA.txt')
 shutil.copy2(ROOT/'packaging/WOODCUT-MODEL-CARD.md',stage/'WOODCUT-MODEL-CARD.md')
 shutil.copy2(ROOT/'packaging/README-online.txt',stage/'使用说明.txt')
 shutil.copy2(ROOT/'packaging/下载全部模型.bat',stage/'下载全部模型.bat')
 weights=list(stage.rglob('*.ckpt'))+list(stage.rglob('*.safetensors'))
 assert len(weights)==1 and weights[0].name=='woodcut_style_r16_step0500.safetensors','Unexpected bundled model'
 output=ROOT/'release-staging/CtrLoRADesktop-online-win64.zip'
 with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
  z.write(stage/'hf-cache','CtrLoRADesktop/hf-cache/')
  for file in stage.rglob('*'):
   if file.is_file():z.write(file,str(file.relative_to(stage.parent)))
 with zipfile.ZipFile(output) as z:assert z.testzip() is None
 assert output.stat().st_size<2*1024**3,'Single GitHub asset would exceed 2GiB'
 with output.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 (output.parent/'SHA256SUMS.txt').write_text(sha+'  '+output.name+'\n',encoding='utf-8')
 print(json.dumps({'zip':str(output),'bytes':output.stat().st_size,'sha256':sha,'model_count':len(weights)},indent=2))
if __name__=='__main__':main()
