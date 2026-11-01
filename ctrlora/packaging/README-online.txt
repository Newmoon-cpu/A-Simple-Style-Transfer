CtrLoRA Desktop 首次联网版

先双击下载的 CtrLoRADesktop-online-win64.exe 自解压包，解压到可写目录，再双击目录内的 CtrLoRADesktop.exe。无需额外安装解压软件。
选择风格、条件和输入图片，点击生成。第一次会自动下载所选模型和公共依赖，窗口显示下载进度；后续复用本地文件。
默认黑白木刻，建议 Canny、权重1、CFG7、512分辨率。木刻 LoRA 随包提供，不再下载木刻完整底座。
需要 Windows x64、兼容 NVIDIA GPU及驱动。无需安装 Python。首次可能下载数GB，全部风格和条件需要数十GB；请预留至少40GB空间。
下载中断可再次生成，保留.part文件续传；哈希错误不会安装为模型。网络故障会明确报错，请勿关闭证书校验。
Civitai/Hugging Face 可能要求账户授权。可在启动前设置 CIVITAI_TOKEN / HF_TOKEN 环境变量；令牌不会写入清单或发布包。若模型下架或访问受限，无法绕过源站限制。
下载器核对预先固定的大小和SHA256。configs/resources.json 包含来源；不同版本即使同名也不会通过。
需要预下载全部资源时，运行 下载全部模型.bat，完成状态见 download-status.txt。
模型与预处理器分别遵循各自许可证；本包不转授上游模型的分发权。下载使用前请查看来源条款。
木刻LoRA基于SD1.5，遵循底座CreativeML OpenRAIL-M及相关来源条件；不声明CC0。
