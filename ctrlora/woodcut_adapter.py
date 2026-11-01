"""Apply the released rank16/alpha16 SD1.5 woodcut adapter in memory."""
import re
import hashlib
import torch
from safetensors.torch import load_file
NAME='woodcut_style_r16_step0500.safetensors'
BASE='v1-5-pruned-emaonly.ckpt'
def ldm_attention_key(module):
    match=re.fullmatch(r'down_blocks\.(\d+)\.attentions\.(\d+)\.(.+)',module)
    if match:
        block,attention,tail=match.groups();block=int(block);attention=int(attention)
        if block>2 or attention>1:raise ValueError(module)
        return f'model.diffusion_model.input_blocks.{block*3+attention+1}.1.{tail}.weight'
    match=re.fullmatch(r'up_blocks\.(\d+)\.attentions\.(\d+)\.(.+)',module)
    if match:
        block,attention,tail=match.groups();block=int(block);attention=int(attention)
        if block not in [1,2,3] or attention>2:raise ValueError(module)
        return f'model.diffusion_model.output_blocks.{block*3+attention}.1.{tail}.weight'
    prefix='mid_block.attentions.0.'
    if module.startswith(prefix):return 'model.diffusion_model.middle_block.1.'+module[len(prefix):]+'.weight'
    raise ValueError(f'Unsupported SD1.5 attention location: {module}')

def apply_woodcut(model,path):
 with open(path,'rb') as f:
  if hashlib.file_digest(f,'sha256').hexdigest()!='e71cacd939951eb9369bdca1cd99db40838ad92eb7b81bf161a489966fb39360':raise ValueError('Woodcut adapter checksum mismatch')
 weights=load_file(str(path),device='cpu');state=model.state_dict();updates=[]
 for key,a in weights.items():
  if not key.endswith('.lora.down.weight'):continue
  module=key.removeprefix('unet.').removesuffix('.lora.down.weight')
  target=ldm_attention_key(module);b=weights[key.replace('.lora.down.weight','.lora.up.weight')]
  if a.shape[0]!=16:raise ValueError('Unexpected woodcut rank')
  delta=b.float()@a.float()
  if target not in state or state[target].shape!=delta.shape or not torch.isfinite(delta).all():raise ValueError('Invalid woodcut mapping')
  updates.append((target,delta))
 if len(updates)!=128 or len(weights)!=256:raise ValueError('Incomplete woodcut adapter')
 with torch.no_grad():
  for target,delta in updates:state[target].copy_(state[target].float()+delta)
 return len(updates)
