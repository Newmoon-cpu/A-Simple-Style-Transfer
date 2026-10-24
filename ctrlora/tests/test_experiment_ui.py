import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import torch, unittest
from PyQt5.QtWidgets import QApplication
from PIL import Image
from app.experiment_widgets import ExperimentPanel
from experiments import build_experiment_tasks
from generation_records import ExperimentRecord
class ExperimentUITests(unittest.TestCase):
 def test_cards_reset_and_partial(self):
  app=QApplication.instance() or QApplication([])
  panel=ExperimentPanel(); tasks=build_experiment_tasks('ablation',('canny','palette'),(1,1))
  photo=Image.new('RGB',(64,32))
  panel.begin(tasks,photo,{})
  self.assertEqual(panel.grid.count(),4)
  panel.set_result(ExperimentRecord(tasks[0],'completed',photo,(),1,10,None))
  panel.finish('stopped'); self.assertTrue(panel.export.isEnabled())
  self.assertEqual(len(panel.snapshot()['records']),1)
  grid=build_experiment_tasks('weight_grid',('canny','palette'),(1,1))
  panel.begin(grid,photo,{})
  self.assertEqual(panel.grid.count(),9); self.assertEqual(panel.records,{})
