"""CtrLoRA 通用条件注入风格重绘（零训练，1~2 个条件 + 任意风格底座，fp16 适配 8G）。

用法示例：
  # 单条件：线稿约束 + 水墨底座
  python run_style_transfer.py --input in.jpg --condition1 lineart \
      --sd-file ckpts/sd15/ChineseInkComicStrip_v10.ckpt

  # 双条件：Canny 边缘 + 深度，写实底座
  python run_style_transfer.py --input in.jpg --condition1 canny --condition2 depth \
      --sd-file ckpts/sd15/realisticVisionV60B1.safetensors

条件名（见 conditions.py）：canny / depth / openpose / seg / hed / normal /
  lineart / palette / pixel / illusion / deraindrop / llie
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import compat  # noqa: F401

import config

config.save_memory = True

from share import *  # noqa: F401,F403

import argparse

import numpy as np
import torch
import einops
from PIL import Image

from cldm.model import create_model, load_state_dict
from cldm.ddim_hacked import DDIMSampler
from annotator.util import resize_image, HWC3
from api import CtrLoRA
from conditions import CONDITIONS, extract_condition


def seed_everything(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def build_model(sd_file, basecn_file, lora_files):
    """lora_files: 1~2 个 LoRA 路径。加载 fp16。"""
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
           scale, eta, seed, weights):
    """cond_images: 1~2 个条件图（HWC uint8）。weights: 与条件等长的权重。"""
    model = ctrlora.model
    ddim_sampler = DDIMSampler(model)
    num = len(cond_images)

    # 多条件统一尺寸（center crop 到最小）
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
        )

        x_samples = model.decode_first_stage(samples.half())
        x_samples = (einops.rearrange(x_samples, 'b c h w -> b h w c') * 127.5 + 127.5).float().cpu().numpy().clip(0, 255).astype(np.uint8)

    return [Image.fromarray(x_samples[i]) for i in range(num_samples)]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='输入照片路径')
    p.add_argument('--output', default='results/output.png')
    p.add_argument('--sd-file', default='ckpts/sd15/v1-5-pruned-emaonly.ckpt')
    p.add_argument('--basecn-file', default='ckpts/ctrlora-basecn/ctrlora_sd15_basecn700k.ckpt')
    p.add_argument('--condition1', default='palette', choices=list(CONDITIONS.keys()))
    p.add_argument('--condition2', default='lineart', help='第二个条件，填 none 表示只用单条件')
    p.add_argument('--weight1', type=float, default=1.0)
    p.add_argument('--weight2', type=float, default=1.0)
    p.add_argument('--prompt', default='best quality, masterpiece')
    p.add_argument('--n-prompt', default='worst quality, low quality')
    p.add_argument('--resolution', type=int, default=448)
    p.add_argument('--detect-resolution', type=int, default=512)
    p.add_argument('--ddim-steps', type=int, default=20)
    p.add_argument('--scale', type=float, default=7.5)
    p.add_argument('--eta', type=float, default=0.0)
    p.add_argument('--num-samples', type=int, default=1)
    p.add_argument('--seed', type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()
    assert os.path.exists(args.input), f'输入不存在: {args.input}'

    photo = np.array(Image.open(args.input).convert('RGB'))
    photo = HWC3(photo)

    # 组装条件列表
    cond_names = [args.condition1]
    if args.condition2.lower() != 'none':
        cond_names.append(args.condition2)

    cond_images = [extract_condition(c, photo, args.detect_resolution, args.resolution)
                   for c in cond_names]
    lora_files = [CONDITIONS[c]['lora'] for c in cond_names]
    weights = [args.weight1, args.weight2][:len(cond_names)]

    print(f'条件: {cond_names}，权重 {weights}，分辨率 {args.resolution} ...')
    ctrlora = build_model(args.sd_file, args.basecn_file, lora_files)
    results = sample(ctrlora, cond_images, args.prompt, args.n_prompt,
                     args.num_samples, args.ddim_steps, args.scale, args.eta,
                     args.seed, weights)

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    if len(results) == 1:
        results[0].save(args.output)
        print(f'已保存: {args.output}')
    else:
        base, ext = os.path.splitext(args.output)
        for i, r in enumerate(results):
            out = f'{base}_{i}{ext}'
            r.save(out)
            print(f'已保存: {out}')


if __name__ == '__main__':
    main()
