# 自训练木刻风格适配器

文件 woodcut_style_r16_step0500.safetensors 是本项目基于原版 SD1.5 训练的 rank16 alpha16 UNet attention LoRA。默认风格前缀为 woodcut_style, black and white woodcut print。

训练图共150张，仅120张参与梯度训练；训练主实验1500步，按固定验证样图初选500步用于发布。模型保留纸边、伪文字和人物细节变形等局限。四组对比未证明风格质量明显胜过提示词基线，真实人工盲评未开展。

底座来源 https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5 ，使用与分发遵循 CreativeML OpenRAIL-M 以及相关来源条款，不声明CC0。开放训练图来自 Cleveland 和 Met，详细逐图来源保留在项目训练记录。

SHA256 e71cacd939951eb9369bdca1cd99db40838ad92eb7b81bf161a489966fb39360

本文件不能直接替换 CtrLoRA 条件控制权重。发布程序会将其应用到SD1.5生成UNet，条件分支仍使用各自预训练权重。
