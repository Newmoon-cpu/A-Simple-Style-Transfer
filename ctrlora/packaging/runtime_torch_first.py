"""Load torch before PyInstaller's Qt runtime hook initializes Qt DLLs."""
import os
import sys

cache = os.path.join(os.path.dirname(sys.executable), 'hf-cache')
if os.path.isdir(cache):
    os.environ['HF_HUB_CACHE'] = cache

import torch
