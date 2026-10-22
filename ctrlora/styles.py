"""风格底座 → 采样参数 Profile（prompt / 负向 / 推荐 CFG）。

每个风格化 SD1.5 底座有各自的触发词与推荐参数，换底座时应同步切换，
否则风格不激活或颜色失真（例如用油画底座却写水墨触发词）。
"""

STYLE_PROFILES = {
    # 水墨（触发词为该模型 trainedWords）
    'ChineseInkComicStrip_v10.ckpt': {
        'prompt': 'Chinese ink painting, traditional media, liujiyou, {content}',
        'negative': 'photo, photograph, photorealistic, 3d, render, worst quality, low quality',
        'cfg': 7.0,
    },
    # 油画（无特定触发词，用风格词强化）
    'oilPainting_v10.safetensors': {
        'prompt': 'oil painting, {content}',
        'negative': 'photo, photograph, photorealistic, 3d, render, worst quality, low quality',
        'cfg': 7.0,
    },
    # 像素（trainedWords: pixel art, pixel world）
    'aziibpixelmix_v10.safetensors': {
        'prompt': 'pixel art, pixel world, {content}',
        'negative': 'highres, realistic, photo, photograph, blurry, worst quality, low quality',
        'cfg': 7.0,
    },
    # 写实（Realistic Vision 用摄影词）
    'realisticVisionV60B1.safetensors': {
        'prompt': 'RAW photo, 8k uhd, dslr, film grain, {content}',
        'negative': 'anime, cartoon, painting, drawing, 3d, cgi, render, worst quality, low quality',
        'cfg': 5.0,
    },
    # SD1.5 原版
    'v1-5-pruned-emaonly.ckpt': {
        'prompt': '{content}',
        'negative': 'worst quality, low quality',
        'cfg': 7.5,
    },
}

DEFAULT_CONTENT = 'a landscape, masterpiece, best quality'


def get_profile(sd_file):
    """按文件名取 profile，找不到则回退到通用。"""
    name = sd_file.split('/')[-1].split('\\')[-1]
    return STYLE_PROFILES.get(name, {
        'prompt': '{content}',
        'negative': 'worst quality, low quality',
        'cfg': 7.5,
    })


def build_prompt(sd_file, content=DEFAULT_CONTENT):
    prof = get_profile(sd_file)
    return prof['prompt'].format(content=content), prof['negative'], prof['cfg']
