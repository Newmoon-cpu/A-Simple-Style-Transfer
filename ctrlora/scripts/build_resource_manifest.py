from pathlib import Path
import hashlib,json,requests
r=Path.cwd();resources=[]
def add(rel,url,tags):
 p=r/rel
 with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 resources.append({'path':rel,'url':url,'bytes':p.stat().st_size,'sha256':sha,'tags':tags});print(rel,flush=True)
base='https://huggingface.co/xyfJASON/ctrlora/resolve/main/'
add('ckpts/ctrlora-basecn/ctrlora_sd15_basecn700k.ckpt',base+'ctrlora-basecn/ctrlora_sd15_basecn700k.ckpt',['common'])
for p in (r/'ckpts/ctrlora-loras').rglob('*.ckpt'):
 name=p.name.split('basecn700k_')[1].split('_rank')[0];rel=p.relative_to(r).as_posix();add(rel,base+rel.removeprefix('ckpts/'),[name])
add('ckpts/sd15/v1-5-pruned-emaonly.ckpt','https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt',['v1-5-pruned-emaonly.ckpt','woodcut_style_r16_step0500.safetensors'])
for name,id in [('oilPainting_v10.safetensors',23979),('aziibpixelmix_v10.safetensors',220049),('realisticVisionV60B1.safetensors',245598)]:add('ckpts/sd15/'+name,f'https://civitai.com/api/download/models/{id}',[name])
for p in (r/'annotator/ckpts').iterdir():
 if p.suffix not in ['.pt','.pth'] or p.name=='scannet.pt':continue
 tags={'dpt_large_384.pt':['depth','normal'],'ControlNetHED.pth':['hed'],'upernet_global_small.pth':['seg'],'sk_model.pth':['lineart'],'sk_model2.pth':['lineart']}.get(p.name,['openpose'])
 url='https://huggingface.co/lllyasviel/Annotators/resolve/main/'+p.name
 if p.name=='dpt_large_384.pt':url='https://storage.googleapis.com/sfr-unicontrol-data-research/annotator/ckpts/'+p.name
 add(p.relative_to(r).as_posix(),url,tags)
cache=r/'dist/CtrLoRADesktop/hf-cache/models--openai--clip-vit-large-patch14';rev=(cache/'refs/main').read_text().strip()
for p in (cache/'snapshots'/rev).iterdir():
 if p.is_file():
  rel='hf-cache/models--openai--clip-vit-large-patch14/snapshots/'+rev+'/'+p.name
  # Hash source without copying the cache into the source tree.
  with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
  resources.append({'path':rel,'url':f'https://huggingface.co/openai/clip-vit-large-patch14/resolve/{rev}/{p.name}','bytes':p.stat().st_size,'sha256':sha,'tags':['common']})
p=r/'ckpts/sd15/ChineseInkComicStrip_v10.ckpt'
with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
resp=requests.get('https://civitai.com/api/v1/model-versions/by-hash/'+sha,timeout=40)
if resp.ok:
 id=resp.json()['id'];resources.append({'path':'ckpts/sd15/'+p.name,'url':f'https://civitai.com/api/download/models/{id}','bytes':p.stat().st_size,'sha256':sha,'tags':[p.name]})
else:print('Chinese ink source unresolved:',resp.status_code,flush=True)
for item in resources:
 if 'huggingface.co/' in item['url'] and '?' not in item['url']:item['url']+='?download=true'
(r/'configs/resources.json').write_text(json.dumps({'schema':1,'clip_revision':rev,'resources':resources},ensure_ascii=False,indent=2),encoding='utf-8')
print('Manifest saved',len(resources),flush=True)
