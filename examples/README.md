# 展示样例与复现参数

本目录是手动筛选的仓库展示素材，不是日常生成缓存目录。现有山水建筑样例替换了早期草莓测试图。

## 输入与输出

| 输入场景 | 双条件水墨重绘 |
| :---: | :---: |
| ![山水建筑输入](input_landscape.jpg) | ![实际生成的水墨结果](output_ink.png) |

`input_landscape.jpg` 是 AI 生成的摄影风格演示素材，包含山、湖、亭台与拱桥，**不是实拍照片**。风格化输出、预测回放及实验结果全部由本仓库的桌面程序和推理引擎实际生成，没有用图片生成工具代替模型输出。

## 使用的设置

| 参数 | 值 |
| --- | --- |
| 风格底座 | `ChineseInkComicStrip_v10.ckpt` |
| 条件 A / B | `canny` / `palette` |
| 条件权重 | `0.65` / `0.35` |
| 分辨率参数 | `448`（实际宽高见参数记录） |
| 请求步数 | `28` |
| CFG / Seed | `6.5` / `42` |
| eta / batch | `0` / `1` |
| 回放 | 每 5 步记录预测帧，包含首步、末步和最终结果 |

完整提示词、负向提示词、实际步数、输出尺寸、资源文件名和实验耗时保存在 [parameters.json](showcase/parameters.json)。资源哈希未核验时标记为 `null`；同种子不保证跨设备、跨软件环境逐像素一致。

复现时，在桌面端加载输入图，选择以上模型和条件，照 JSON 填入正负提示词与采样设置，再生成。对比实验选择“单/双条件对比”，使用同一份左侧设置；每项都是真实生成，单条件不采用双条件权重归零的替代方式。

## 回放与实验

![真实采样预测回放](showcase/generation.gif)

中间帧是模型在采样过程中的最终图像预测；最后一帧为正式结果。播放节奏为导出 GIF 的固定时长，与实际计算耗时无关。

![原图及单/双条件对照](showcase/comparison.png)

拼图包含原图、仅 Canny、仅 palette 和两者联合。结果分别保留到以下文件，图片预览与下载均可使用原尺寸：

- [Canny 单条件输出](verification/output-single.png)
- [palette 单条件输出](showcase/palette-only.png)
- [Canny + palette 双条件输出](verification/output-dual.png)
- [Canny 条件图](verification/condition-1.png) / [palette 条件图](verification/condition-2.png)
- [演示输入 PNG](verification/input.png)

## 桌面截图

- [风格化结果页](showcase/desktop.png)
- [过程回放页](showcase/replay-desktop.png)
- [对比实验页](showcase/experiment-desktop.png)

截图来自实际桌面程序，展示本次真实生成结果。为便于阅读采用 1440×1000 窗口；日常可调整窗口大小或在实验页内滚动查看卡片。

## 文件说明

```text
examples/
├── input_landscape.jpg          # AI 生成的山水建筑输入素材
├── output_ink.png               # 本项目实际生成的水墨结果
├── verification/               # 同次生成的单/双条件结果及条件图
└── showcase/
    ├── desktop.png             # 结果页截图
    ├── replay-desktop.png       # 回放页截图
    ├── experiment-desktop.png   # 实验页截图
    ├── generation.gif          # 实际采样预测回放
    ├── comparison.png          # 原图与三项实验拼图
    └── parameters.json         # 可复现参数与生成记录
```

日常生成与完整实验包请保存到自己选择的本地目录；报告、旧调试截图和资料仍在 Git 忽略的 `docs/` 内。
