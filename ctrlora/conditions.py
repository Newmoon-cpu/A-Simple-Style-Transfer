"""CtrLoRA 条件注入注册表：把「条件名」映射到「预处理器 + LoRA 权重」。

支持的条件（对应论文的 base / novel conditions）：
  canny / depth / openpose(骨架) / seg / hed / normal        —— base conditions
  lineart / palette / pixel / illusion                       —— novel conditions
  deraindrop / llie                                          —— 图像修复类（特殊，输入即退化图）

用法：
  from conditions import CONDITIONS, extract_condition
  info = CONDITIONS['canny']          # {'kind':..., 'lora':...}
  cond_map = extract_condition('canny', img, detect_res, image_res)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import torch

from annotator.util import resize_image, HWC3

_LORA_BASE = 'ckpts/ctrlora-loras/base-conditions/ctrlora_sd15_basecn700k_{}_rank128.ckpt'
_LORA_NOVEL = 'ckpts/ctrlora-loras/novel-conditions/ctrlora_sd15_basecn700k_{}.ckpt'

# 条件名 -> 元信息
CONDITIONS = {
    'canny':    {'kind': 'canny',    'lora': _LORA_BASE.format('canny')},
    'depth':    {'kind': 'depth',    'lora': _LORA_BASE.format('depth')},
    'openpose': {'kind': 'openpose', 'lora': _LORA_BASE.format('openpose')},
    'seg':      {'kind': 'seg',      'lora': _LORA_BASE.format('seg')},
    'hed':      {'kind': 'hed',      'lora': _LORA_BASE.format('hed')},
    'normal':   {'kind': 'normal',   'lora': _LORA_BASE.format('normal')},
    'lineart':  {'kind': 'lineart',  'lora': _LORA_NOVEL.format('lineart_rank128_1kimgs_1ksteps')},
    'palette':  {'kind': 'palette',  'lora': _LORA_NOVEL.format('palette_rank128_100kimgs_100ksteps')},
    'pixel':    {'kind': 'pixel',    'lora': _LORA_NOVEL.format('pixel_rank128_100kimgs_100ksteps')},
    'illusion': {'kind': 'illusion', 'lora': _LORA_NOVEL.format('illusion_rank128_100kimgs_100ksteps')},
    'deraindrop': {'kind': 'none',   'lora': _LORA_NOVEL.format('deraindrop_rank128_861imgs_100ksteps')},
    'llie':     {'kind': 'none',     'lora': _LORA_NOVEL.format('llie_rank128_100kimgs_100ksteps')},
}

_preprocessors = {}


def _get_preprocessor(kind):
    """懒加载预处理器，返回 (preprocessor, params)。"""
    if kind not in _preprocessors:
        if kind == 'canny':
            from annotator.canny import CannyDetector
            p, params = CannyDetector(), dict(low_threshold=100, high_threshold=200)
        elif kind == 'hed':
            from annotator.hed import HEDdetector
            p, params = HEDdetector(), dict()
        elif kind == 'seg':
            from annotator.uniformer import UniformerDetector
            p, params = UniformerDetector(), dict()
        elif kind in ('depth', 'normal'):
            from annotator.midas import MidasDetector
            p, params = MidasDetector(), dict()
        elif kind == 'openpose':
            from annotator.openpose import OpenposeDetector
            p, params = OpenposeDetector(), dict()
        elif kind == 'lineart':
            from annotator.lineart import LineartDetector
            p, params = LineartDetector(), dict(coarse=False)
        elif kind == 'palette':
            from annotator.palette import PaletteDetector
            p, params = PaletteDetector(), dict()
        elif kind == 'pixel':
            from annotator.pixel import Pixelater
            p, params = Pixelater(), dict(n_colors=10, scale=6, down_interpolation=cv2.INTER_LANCZOS4)
        elif kind == 'illusion':
            from annotator.illusion import IllusionConverter
            p, params = IllusionConverter(), dict()
        elif kind == 'none':
            p, params = None, dict()
        else:
            raise ValueError(f'未知条件: {kind}')
        _preprocessors[kind] = (p, params)
    return _preprocessors[kind]


def extract_condition(kind, img, detect_res=512, image_res=448):
    """img: HWC uint8 -> 条件图（HWC uint8，尺寸 image_res）。"""
    img = HWC3(img)
    p, params = _get_preprocessor(kind)
    if p is None:  # 'none'：直接原图（用于 deraindrop/llie 等修复类）
        detected = img
    else:
        with torch.no_grad():
            resized = resize_image(img, detect_res)
            detected = p(resized, **params)
            if kind == 'depth':
                detected = detected[0]
            elif kind == 'normal':
                detected = detected[1]
    detected = HWC3(detected)
    H, W, _ = resize_image(img, image_res).shape
    detected = cv2.resize(detected, (W, H), interpolation=cv2.INTER_LINEAR)
    return HWC3(detected)


def lora_path(condition_name):
    return CONDITIONS[condition_name]['lora']
