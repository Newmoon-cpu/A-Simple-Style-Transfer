"""CPU-only records shared by inference, UI and export."""
from dataclasses import dataclass
from PIL import Image


@dataclass(frozen=True)
class PreviewOptions:
    enabled: bool = False
    interval: int = 5
    max_frames: int = 24
    max_side: int = 512


@dataclass(frozen=True)
class PreviewFrame:
    step: int
    total_steps: int
    elapsed_s: float
    image: Image.Image
    kind: str


@dataclass(frozen=True)
class ExperimentTask:
    task_id: str
    label: str
    cond_names: tuple
    weights: tuple


@dataclass(frozen=True)
class ExperimentRecord:
    task: ExperimentTask
    status: str
    image: object
    previews: tuple
    elapsed_s: float
    actual_steps: object
    error: object


def build_preview_steps(total_steps, options):
    if total_steps < 1 or options.interval < 1 or options.max_frames < 3 or options.max_side < 1:
        raise ValueError('Invalid preview settings')
    steps = sorted({1, total_steps, *range(options.interval, total_steps+1, options.interval)})
    limit = options.max_frames - 1
    if len(steps) > limit:
        steps = [steps[round(i*(len(steps)-1)/(limit-1))] for i in range(limit)]
    return tuple(steps)
