"""核心逻辑层：与 UI 无关的 CtrLoRA 推理引擎。

UI 层（CLI / Gradio / PyQt）只负责展示与交互，全部通过 StyleTransferEngine 调用本模块。
本模块不 import 任何 UI 库。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import compat  # noqa: F401

import config

config.save_memory = True

from share import *  # noqa: F401,F403

import glob

import numpy as np
import torch
import einops
from PIL import Image

from cldm.model import create_model, load_state_dict
from cldm.ddim_hacked import DDIMSampler
from annotator.util import HWC3
from api import CtrLoRA
from conditions import CONDITIONS, extract_condition
from styles import build_prompt


def seed_everything(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def build_model(sd_file, basecn_file, lora_files):
    """lora_files: 1~2 个 LoRA 路径。加载为 fp16。"""
    ctrlora = CtrLoRA(num_loras=len(lora_files))
    model = create_model(ctrlora.config_file)  # CPU

    model.load_state_dict(load_state_dict(sd_file, location='cpu'), strict=False)

    cn_sd = load_state_dict(basecn_file, location='cpu')
    cn_sd = {k: v for k, v in cn_sd.items() if k.startswith('control_model') and not CtrLoRA.check_key(k)}
    model.load_state_dict(cn_sd, strict=False)

    for i, lora_file in enumerate(lora_files):
        lora_sd = load_state_dict(lora_file, location='cpu')
        lora_sd = {k: v for k, v in lora_sd.items() if CtrLoRA.check_key(k)}
        model.control_model.switch_lora(i)
        model.load_state_dict(lora_sd, strict=False)
        model.control_model.copy_weights_to_switchable()

    model = model.half()
    # 修复陈旧 self.dtype（ControlNet/UNet 构造时按 use_fp16=False 固化为 fp32）
    for m in model.modules():
        d = getattr(m, 'dtype', None)
        if isinstance(d, torch.dtype) and d == torch.float32:
            try:
                m.dtype = torch.float16
            except Exception:
                pass
    model = model.cuda()
    ctrlora.model = model
    return ctrlora


def sample(ctrlora, cond_images, prompt, n_prompt, num_samples, ddim_steps,
           scale, eta, seed, weights, progress_callback=None):
    """cond_images: 1~2 个条件图（HWC uint8）。weights: 等长权重列表。返回 PIL 列表。"""
    model = ctrlora.model
    ddim_sampler = DDIMSampler(model)
    num = len(cond_images)

    if num == 2:
        a, b = cond_images
        Ha, Wa = a.shape[:2]
        Hb, Wb = b.shape[:2]
        if Hb > Ha:
            b = b[(Hb - Ha) // 2:(Hb + Ha) // 2]
        else:
            a = a[(Ha - Hb) // 2:(Ha + Hb) // 2]
        if Wb > Wa:
            b = b[:, (Wb - Wa) // 2:(Wb + Wa) // 2]
        else:
            a = a[:, (Wa - Wb) // 2:(Wa + Wb) // 2]
        cond_images = [a, b]

    H, W, C = cond_images[0].shape

    with torch.no_grad():
        controls = []
        for ci in cond_images:
            c = (torch.from_numpy(ci.copy()).float() / 255.0).half().cuda()
            c = torch.stack([c for _ in range(num_samples)], dim=0)
            c = einops.rearrange(c, 'b h w c -> b c h w').clone()
            controls.append(c)

        seed_everything(seed)

        conds = []
        un_conds = []
        for c in controls:
            conds.append({"c_concat": [c],
                          "c_crossattn": [model.get_learned_conditioning([prompt] * num_samples)]})
            un_conds.append({"c_concat": [c],
                             "c_crossattn": [model.get_learned_conditioning([n_prompt] * num_samples)]})

        model.control_scales = [1] * 13
        model.lora_weights = list(weights)

        shape = (4, H // 8, W // 8)
        samples, _ = ddim_sampler.sample(
            ddim_steps, num_samples, shape,
            conds if num > 1 else conds[0], verbose=False, eta=eta,
            unconditional_guidance_scale=scale,
            unconditional_conditioning=un_conds if num > 1 else un_conds[0],
            progress_callback=(lambda done, total: progress_callback('sampling', done, total))
            if progress_callback else None,
        )

        if progress_callback:
            progress_callback('decode', 0, 0)
        x_samples = model.decode_first_stage(samples.half())
        x_samples = (einops.rearrange(x_samples, 'b c h w -> b h w c') * 127.5 + 127.5).float().cpu().numpy().clip(0, 255).astype(np.uint8)

    return [Image.fromarray(x_samples[i]) for i in range(num_samples)]


class StyleTransferEngine:
    """与 UI 无关的推理引擎：模型缓存 + 条件提取 + 采样 + 风格 profile。"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)  # exe 所在目录
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
        self._ctrlora = None
        self._key = None

    # ---- 查询接口（供 UI 填下拉框）----
    def list_styles(self):
        files = glob.glob(os.path.join(self.base_dir, 'ckpts/sd15', '*.ckpt')) + \
            glob.glob(os.path.join(self.base_dir, 'ckpts/sd15', '*.safetensors'))
        return sorted(os.path.basename(p) for p in files)

    def list_conditions(self):
        return list(CONDITIONS.keys())

    def style_profile(self, sd_file):
        return build_prompt(sd_file)  # (prompt, negative, cfg)

    # ---- 核心：生成 ----
    def generate(self, image, sd_file, cond_names, weights, prompt, n_prompt,
                 resolution=448, steps=28, scale=7.0, seed=42, detect_resolution=512,
                 progress_callback=None, preview_callback=None):
        photo = HWC3(np.array(image.convert('RGB')))
        if progress_callback:
            progress_callback('conditions', 0, len(cond_names))
        cond_images = []
        for index, condition in enumerate(cond_names):
            cond_images.append(extract_condition(condition, photo, detect_resolution, resolution))
            if progress_callback:
                progress_callback('conditions', index + 1, len(cond_names))
        previews = [Image.fromarray(ci) for ci in cond_images]
        if preview_callback:
            preview_callback(previews)
        lora_files = [CONDITIONS[c]['lora'] for c in cond_names]
        if progress_callback:
            progress_callback('model', 0, 0)
        ctrlora = self._get_model(sd_file, lora_files)
        if progress_callback:
            progress_callback('sampling', 0, steps)
        results = sample(ctrlora, cond_images, prompt, n_prompt, 1, steps, scale,
                         0.0, seed, weights, progress_callback=progress_callback)
        if progress_callback:
            progress_callback('done', 1, 1)
        return results[0], previews

    def _get_model(self, sd_file, lora_files):
        key = (sd_file, tuple(lora_files))
        if self._ctrlora is not None and self._key == key:
            return self._ctrlora
        if self._ctrlora is not None:
            del self._ctrlora
            self._ctrlora = None
            torch.cuda.empty_cache()
        ctrlora = build_model(
            os.path.join(self.base_dir, 'ckpts/sd15', sd_file),
            os.path.join(self.base_dir, 'ckpts/ctrlora-basecn/ctrlora_sd15_basecn700k.ckpt'),
            lora_files,
        )
        self._ctrlora = ctrlora
        self._key = key
        return ctrlora
