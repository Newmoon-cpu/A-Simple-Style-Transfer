"""CtrLoRA 通用条件注入风格重绘 —— Gradio 网页界面（fp16，1~2 条件 + 多风格）。

启动：python app/gradio_style_transfer.py  →  http://127.0.0.1:7860
切换风格底座时，prompt/负向/CFG 会自动切换为该风格推荐的参数。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import compat  # noqa: F401

import config

config.save_memory = True

from share import *  # noqa: F401,F403

import glob
import numpy as np
import torch
import gradio as gr
from PIL import Image

from annotator.util import HWC3
from conditions import CONDITIONS, extract_condition
from run_style_transfer import build_model, sample
from styles import build_prompt, DEFAULT_CONTENT

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SD_FILES = [os.path.basename(p) for p in sorted(
    glob.glob(os.path.join(BASE, 'ckpts/sd15', '*.ckpt')) +
    glob.glob(os.path.join(BASE, 'ckpts/sd15', '*.safetensors')))]

COND_NAMES = list(CONDITIONS.keys())

_state = {'key': None, 'ctrlora': None}


def _get_model(sd_file, cond_names):
    key = (sd_file, tuple(cond_names))
    if _state['ctrlora'] is not None and _state['key'] == key:
        return _state['ctrlora']
    if _state['ctrlora'] is not None:
        del _state['ctrlora']
        _state['ctrlora'] = None
        torch.cuda.empty_cache()
    lora_files = [CONDITIONS[c]['lora'] for c in cond_names]
    ctrlora = build_model(
        os.path.join(BASE, 'ckpts/sd15', sd_file),
        os.path.join(BASE, 'ckpts/ctrlora-basecn/ctrlora_sd15_basecn700k.ckpt'),
        lora_files,
    )
    _state['ctrlora'] = ctrlora
    _state['key'] = key
    return ctrlora


def run(input_image, sd_file, cond1, cond2, weight1, weight2, prompt, n_prompt,
        resolution, steps, scale, seed):
    if input_image is None:
        raise gr.Error('请先上传照片')
    cond_names = [cond1]
    if cond2 != 'none':
        cond_names.append(cond2)
    weights = [weight1, weight2][:len(cond_names)]

    photo = HWC3(np.array(input_image.convert('RGB')))

    cond_images = [extract_condition(c, photo, 512, resolution) for c in cond_names]
    ctrlora = _get_model(sd_file, cond_names)
    results = sample(ctrlora, cond_images, prompt, n_prompt, 1, steps, scale,
                     0.0, int(seed), weights)

    previews = [Image.fromarray(ci) for ci in cond_images]
    while len(previews) < 2:
        previews.append(None)
    return results[0], previews[0], previews[1]


def on_style_change(sd_file):
    prompt, negative, cfg = build_prompt(sd_file)
    return prompt, negative, cfg


def _default_sd():
    for pref in ['ChineseInkComicStrip_v10.ckpt', 'realisticVisionV60B1.safetensors',
                 'oilPainting_v10.safetensors', 'aziibpixelmix_v10.safetensors']:
        if pref in SD_FILES:
            return pref
    return SD_FILES[0] if SD_FILES else None


_dsd = _default_sd()
_default_prompt, _default_neg, _default_cfg = build_prompt(_dsd)

with gr.Blocks(title='CtrLoRA 通用条件注入风格重绘') as demo:
    gr.Markdown('# 🎨 CtrLoRA 条件注入风格重绘（8G · fp16 · 多条件 + 多风格）\n'
                '上传照片 → 选风格底座（会自动切 prompt/负向）→ 选 1~2 个条件 → 生成。')

    with gr.Row():
        with gr.Column(scale=1):
            input_image = gr.Image(label='① 输入照片', type='pil')
            sd_file = gr.Dropdown(label='② 风格底座', choices=SD_FILES, value=_dsd)

            gr.Markdown('### ③ 条件注入（最多 2 个联合）')
            with gr.Row():
                cond1 = gr.Dropdown(label='条件 1', choices=COND_NAMES, value='canny')
                weight1 = gr.Slider(0.0, 1.5, value=1.0, step=0.05, label='权重 1')
            with gr.Row():
                cond2 = gr.Dropdown(label='条件 2（none=不启用）', choices=['none'] + COND_NAMES, value='none')
                weight2 = gr.Slider(0.0, 1.5, value=1.0, step=0.05, label='权重 2')

            gr.Markdown('### ④ 采样参数（切换底座会自动更新）')
            prompt = gr.Textbox(label='Prompt', value=_default_prompt)
            n_prompt = gr.Textbox(label='Negative Prompt', value=_default_neg)
            with gr.Row():
                resolution = gr.Slider(256, 512, value=448, step=64, label='分辨率')
                steps = gr.Slider(10, 40, value=28, step=1, label='步数')
            with gr.Row():
                scale = gr.Slider(1.0, 15.0, value=_default_cfg, step=0.5, label='CFG')
                seed = gr.Number(value=42, label='种子', precision=0)
            run_btn = gr.Button('生成', variant='primary')

        with gr.Column(scale=1):
            output = gr.Image(label='风格化结果', type='pil')
            with gr.Row():
                preview1 = gr.Image(label='条件 1 图', type='pil')
                preview2 = gr.Image(label='条件 2 图', type='pil')

    sd_file.change(on_style_change, sd_file, [prompt, n_prompt, scale])
    run_btn.click(run,
                  [input_image, sd_file, cond1, cond2, weight1, weight2,
                   prompt, n_prompt, resolution, steps, scale, seed],
                  [output, preview1, preview2])

if __name__ == '__main__':
    demo.launch(server_name='127.0.0.1', server_port=7860, show_error=True)
