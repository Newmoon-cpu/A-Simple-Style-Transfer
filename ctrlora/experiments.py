"""UI-independent, serial comparison runner."""
import math
import time
from generation_records import ExperimentTask, ExperimentRecord

CONDITION_NAMES = frozenset('canny depth openpose seg hed normal lineart palette pixel illusion deraindrop llie'.split())


def build_experiment_tasks(mode, cond_names, weights):
    if len(cond_names) != 2 or len(set(cond_names)) != 2 or any(c not in CONDITION_NAMES for c in cond_names):
        raise ValueError('请选择两个不同且有效的条件，例如 canny 和 palette')
    if len(weights) != 2 or any(not math.isfinite(w) or not 0 <= w <= 1.5 for w in weights):
        raise ValueError('权重必须在 0 到 1.5 之间')
    a, b = cond_names
    wa, wb = weights
    if mode == 'ablation':
        return (ExperimentTask('only_a', f'仅 {a} ({wa:g})', (a,), (wa,)),
                ExperimentTask('only_b', f'仅 {b} ({wb:g})', (b,), (wb,)),
                ExperimentTask('both', f'{a} {wa:g} + {b} {wb:g}', (a,b), (wa,wb)))
    if mode == 'weight_grid':
        return tuple(ExperimentTask(f'grid_a{int(x*100):03}_b{int(y*100):03}',
            f'{a} {x:g} + {b} {y:g}', (a,b), (x,y))
            for x in (.5,1.,1.5) for y in (.5,1.,1.5))
    raise ValueError('未知实验方案')


def _synchronize():
    import sys
    torch = sys.modules.get('torch')
    if torch is not None and torch.cuda.is_available():
        torch.cuda.synchronize()


def run_experiment(engine, base_params, tasks, *, on_started, on_progress,
                   on_previews, on_result, should_stop):
    for index, task in enumerate(tasks, 1):
        if should_stop():
            return 'stopped'
        on_started(index, len(tasks), task)
        actual = None
        def progress(stage, done, total):
            nonlocal actual
            if stage == 'sampling' and total > 0:
                actual = total
            on_progress(index, len(tasks), stage, done, total)
        _synchronize()
        start = time.perf_counter()
        try:
            image, previews = engine.generate(**dict(base_params,
                cond_names=list(task.cond_names), weights=list(task.weights)),
                progress_callback=progress, preview_callback=lambda p: on_previews(index,p))
            _synchronize()
            record = ExperimentRecord(task,'completed',image,tuple(previews),time.perf_counter()-start,actual,None)
        except Exception as error:
            import traceback
            traceback.print_exc()
            record = ExperimentRecord(task,'failed',None,(),time.perf_counter()-start,actual,str(error))
        on_result(record)
        if record.status == 'failed':
            return 'failed'
    return 'completed'
