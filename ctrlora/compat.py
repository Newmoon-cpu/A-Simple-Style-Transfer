"""CtrLoRA 在 torch 2.x + pytorch-lightning 2.x 下的兼容性补丁。

老版 ldm 代码依赖 `pytorch_lightning.utilities.distributed.rank_zero_only`，
该路径在 pytorch-lightning 2.x 已被移除。此模块在导入 cldm 前调用，
把 `rank_zero_only` 注入到旧导入路径。
"""
import sys
import types

_ALREADY_SHIM = False


def apply():
    global _ALREADY_SHIM
    if _ALREADY_SHIM:
        return
    _ALREADY_SHIM = True

    # 若旧路径仍可用则无需处理
    try:
        from pytorch_lightning.utilities.distributed import rank_zero_only  # noqa: F401
        return
    except ImportError:
        pass

    # 从新位置取 rank_zero_only
    try:
        from pytorch_lightning.utilities.rank_zero import rank_zero_only as _rzo
    except ImportError:
        from lightning_utilities.core.rank_zero import rank_zero_only as _rzo

    import pytorch_lightning.utilities as _pu

    _dist = types.ModuleType("pytorch_lightning.utilities.distributed")
    _dist.rank_zero_only = _rzo
    sys.modules["pytorch_lightning.utilities.distributed"] = _dist
    setattr(_pu, "distributed", _dist)


apply()
