# CtrLoRA 源码目录

本目录包含桌面、网页和命令行程序，以及上游模型与预处理器代码。

- 使用、依赖和仓库结构：[项目 README](../README.md)
- 打包方法：[packaging/README](packaging/README.md)
- 上游 README 与训练资料：[CtrLoRA 官方仓库](https://github.com/xyfJASON/ctrlora)

源码运行命令以本目录为工作目录，例如 `python app/qt_app.py`。保留 `configs`、`ckpts`、`annotator` 等目录的相对关系；本地权重与 `dist` 发布包不加入源码提交。

## 当前桌面功能

`app/qt_app.py` 的右侧结果区提供“风格化结果 / 过程回放 / 对比实验”三个页签。回放使用采样阶段的实际预测帧；实验通过 `experiments.py` 串行执行真实单条件、双条件或权重扫描任务，导出由 `export_artifacts.py` 负责。

界面使用方法与真实生成展示见 [项目 README](../README.md)；样例的模型、提示词、条件权重和采样设置见 [examples](../examples/README.md)。文档中的桌面回放/实验交互不等于网页和 CLI 已具有同样的界面。
