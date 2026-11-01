"""Verified, resumable model downloads. No tokens are stored in the manifest."""
import hashlib,json,os,time,shutil
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
_HTTP = requests.Session()
_HTTP.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504])))

def safe_target(root,relative):
 root=Path(root).resolve();p=(root/relative).resolve()
 if not p.is_relative_to(root):raise ValueError('Resource path escapes installation')
 return p

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def install_resource(root,item,progress=None):
 target=safe_target(root,item['path']);target.parent.mkdir(parents=True,exist_ok=True)
 if target.is_file() and target.stat().st_size==item['bytes'] and digest(target)==item['sha256']:return
 part=target.with_name(target.name+'.part');offset=part.stat().st_size if part.exists() else 0
 if offset>=item['bytes']:
  if offset==item['bytes'] and digest(part)==item['sha256']:os.replace(part,target);return
  part.unlink();offset=0
 headers={'Range':f'bytes={offset}-'} if offset else {}
 token=os.environ.get('HF_TOKEN') if 'huggingface.co/' in item['url'] else os.environ.get('CIVITAI_TOKEN') if 'civitai.com/' in item['url'] else None
 if token:headers['Authorization']='Bearer '+token
 with _HTTP.get(item['url'],headers=headers,stream=True,timeout=(30,120)) as response:
  response.raise_for_status()
  if response.status_code==206:
   if not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):raise ValueError('Invalid resume range')
  elif response.status_code==200:offset=0
  else:raise ValueError('Unexpected download response')
  with part.open('ab' if offset else 'wb') as f:
   done=offset
   for chunk in response.iter_content(1024*1024):
    if not chunk:continue
    f.write(chunk);done+=len(chunk)
    if done>item['bytes']:raise ValueError('Downloaded resource exceeds expected size')
    if progress:progress(item['path'],done,item['bytes'])
 if part.stat().st_size!=item['bytes'] or digest(part)!=item['sha256']:
  part.unlink(missing_ok=True);raise ValueError('Resource size or SHA-256 mismatch; file was not installed')
 os.replace(part,target)

def prepare(root,style=None,conditions=None,progress=None,all_resources=False):
 root=Path(root);manifest=json.loads((root/'configs/resources.json').read_text(encoding='utf-8'))
 selected=[]
 for item in manifest['resources']:
  tags=item['tags']
  if all_resources or 'common' in tags or (style and style in tags) or set(conditions or []).intersection(tags):selected.append(item)
 needed=sum(x['bytes'] for x in selected if not safe_target(root,x['path']).is_file())
 if shutil.disk_usage(root).free < needed + 512*1024*1024:raise OSError('Insufficient free disk space for selected models')
 for item in selected:
  for attempt in range(3):
   candidate = dict(item)
   if attempt % 2 and candidate['url'].endswith('?download=true'):candidate['url']=candidate['url'].removesuffix('?download=true')
   try:install_resource(root,candidate,progress);break
   except Exception as error:
    if attempt==2:raise RuntimeError(f"Cannot prepare {item['path']}. Check network, disk space and source authorization. {type(error).__name__}") from error
    time.sleep(2*(attempt+1))
 clip=root/'hf-cache/models--openai--clip-vit-large-patch14/refs/main';clip.parent.mkdir(parents=True,exist_ok=True);clip.write_text(manifest['clip_revision'],encoding='utf-8')
 return len(selected)
