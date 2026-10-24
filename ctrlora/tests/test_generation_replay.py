import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import torch
import unittest
from PIL import Image
from PyQt5.QtWidgets import QApplication
from app.replay_widgets import ReplayPanel
from generation_records import PreviewFrame
class ReplayTests(unittest.TestCase):
 def test_lifecycle(self):
  app=QApplication.instance() or QApplication([])
  panel=ReplayPanel(); self.assertFalse(panel.play.isEnabled())
  panel.append_frame(PreviewFrame(1,2,0,Image.new('RGB',(8,8)),'prediction'))
  self.assertFalse(panel.export.isEnabled())
  panel.append_frame(PreviewFrame(2,2,1,Image.new('RGB',(8,8)),'final'))
  panel.mark_finished(True); self.assertTrue(panel.export.isEnabled())
  panel.toggle_play(); self.assertTrue(panel.timer.isActive())
  panel.reset(); self.assertFalse(panel.timer.isActive()); self.assertEqual(panel.frames,[])

class CoreReplayTests(unittest.TestCase):
 def test_decode_schedule_and_failure(self):
  import core, numpy as np
  from unittest.mock import patch
  from contextlib import nullcontext
  from generation_records import PreviewOptions
  class Model:
   def __init__(self,fail=False): self.count=0;self.fail=fail
   def get_learned_conditioning(self,value): return None
   def decode_first_stage(self,value):
    self.count+=1
    if self.fail and self.count==1: raise RuntimeError('preview test failure')
    return torch.zeros((1,3,16,16))
  class Sampler:
   def __init__(self,model): pass
   def sample(self,*a,latent_preview_callback=None,**kw):
    latent=torch.zeros((1,4,2,2))
    for step in range(1,30): latent_preview_callback(latent,step,29)
    return latent,{}
  for enabled,fail,expected in [(False,False,1),(True,False,8),(True,True,2)]:
   model=Model(fail); holder=type('Holder',(),{'model':model})()
   frames=[];warnings=[]
   with patch.object(core,'DDIMSampler',Sampler),patch.object(torch.Tensor,'cuda',lambda self:self),patch.object(torch.cuda,'current_device',return_value=0),patch.object(torch.random,'fork_rng',return_value=nullcontext()):
    result=core.sample(holder,[np.zeros((16,16,3),dtype=np.uint8)],'','',1,28,7,0,42,[1],frame_callback=frames.append,preview_options=PreviewOptions(enabled=enabled),warning_callback=warnings.append)
   self.assertEqual(model.count,expected)
   self.assertEqual(len(result),1)
   if enabled:
    self.assertEqual(frames[-1].kind,'final'); self.assertEqual(frames[-1].total_steps,29)
   else:self.assertEqual(frames,[])
   self.assertEqual(bool(warnings),fail)
