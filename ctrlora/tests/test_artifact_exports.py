import unittest, tempfile, json
from pathlib import Path
from PIL import Image
from generation_records import PreviewFrame, ExperimentRecord
from experiments import build_experiment_tasks
from export_artifacts import export_replay_gif, export_experiment_bundle
class ExportTests(unittest.TestCase):
 def test_exports(self):
  frames=[PreviewFrame(1,2,0,Image.new('RGB',(32,32),'red'),'prediction'),PreviewFrame(2,2,1,Image.new('RGB',(32,32),'blue'),'final')]
  with tempfile.TemporaryDirectory() as d:
   path=export_replay_gif(frames,Path(d)/'demo.gif')
   with Image.open(path) as im:
    im.seek(im.n_frames-1); self.assertEqual(im.convert('RGB').getpixel((0,0)),(0,0,255))
   tasks=build_experiment_tasks('ablation',('canny','palette'),(1,1))
   snap=dict(tasks=tasks,records={tasks[0].task_id:ExperimentRecord(tasks[0],'completed',frames[0].image,(),1,2,None)},input_image=frames[0].image,metadata={})
   bundle=export_experiment_bundle(snap,d)
   data=json.loads((bundle/'metadata.json').read_text(encoding='utf-8'))
   self.assertEqual(data['results'][1]['status'],'not_run')
   self.assertTrue((bundle/'comparison.png').exists())
