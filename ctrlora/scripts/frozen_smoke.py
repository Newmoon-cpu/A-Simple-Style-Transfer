"""Exercise the frozen dependency set and a real generation without Qt input."""
import os
import sys
from pathlib import Path

os.chdir(Path(sys.executable).parent)
os.environ['HF_HUB_OFFLINE'] = '1'

from core import StyleTransferEngine
from PIL import Image, ImageDraw
import torch

engine = StyleTransferEngine()
style = 'ChineseInkComicStrip_v10.ckpt'
prompt, negative, cfg = engine.style_profile(style)
image = Image.new('RGB', (256, 256), '#92b6d5')
draw = ImageDraw.Draw(image)
draw.rectangle((30, 100, 225, 235), fill='#c6ab87', outline='black', width=3)
draw.polygon([(20, 105), (128, 30), (236, 105)], fill='#535965')
draw.rectangle((104, 150, 150, 235), fill='#57483c')

conditions = ['canny', 'palette'] if '--dual' in sys.argv else ['canny']
print('FROZEN_GENERATION_START', style, conditions, flush=True)
result, previews = engine.generate(
    image=image, sd_file=style, cond_names=conditions,
    weights=[1.0] * len(conditions), prompt=prompt, n_prompt=negative,
    resolution=256, steps=10, scale=cfg, seed=42,
)
output = Path('verification')
output.mkdir(exist_ok=True)
image.save(output / 'input.png')
suffix = 'dual' if len(conditions) == 2 else 'single'
result.save(output / f'output-{suffix}.png')
assert result.size == (256, 256)
assert result.convert('RGB').getextrema() != ((0, 0), (0, 0), (0, 0))
print('FROZEN_GENERATION_PASS', result.size, len(previews),
      'peak_cuda_bytes', torch.cuda.max_memory_allocated(), flush=True)
