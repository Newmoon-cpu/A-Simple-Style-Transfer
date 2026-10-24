import unittest
from generation_records import PreviewOptions, build_preview_steps
from experiments import build_experiment_tasks, run_experiment
from PIL import Image

class ExperimentTests(unittest.TestCase):
    def test_frame_plan(self):
        self.assertEqual(build_preview_steps(29, PreviewOptions()), (1,5,10,15,20,25,29))
        self.assertLessEqual(len(build_preview_steps(1000, PreviewOptions(interval=2))),23)
        with self.assertRaises(ValueError): build_preview_steps(0, PreviewOptions())
    def test_tasks(self):
        tasks=build_experiment_tasks('ablation', ('canny','palette'), (1,.5))
        self.assertEqual([len(t.cond_names) for t in tasks],[1,1,2])
        self.assertEqual(tasks[1].weights,(.5,))
        grid=build_experiment_tasks('weight_grid', ('canny','palette'), (1,1))
        self.assertEqual(len(grid),9)
        self.assertEqual(grid[1].weights,(.5,1.))
        for conditions in [('canny','none'),('canny','canny')]:
            with self.assertRaises(ValueError): build_experiment_tasks('ablation',conditions,(1,1))
    def test_stop_and_failure(self):
        tasks=build_experiment_tasks('ablation',('canny','palette'),(1,1))
        calls=[]; records=[]
        class Engine:
            def generate(self, **kw):
                calls.append(kw)
                kw['progress_callback']('sampling',10,10)
                return Image.new('RGB',(8,8)),[]
        params=dict(image=Image.new('RGB',(8,8)),seed=42)
        status=run_experiment(Engine(),params,tasks,on_started=lambda *a:None,
            on_progress=lambda *a:None,on_previews=lambda *a:None,on_result=records.append,
            should_stop=lambda:len(calls)>0)
        self.assertEqual(status,'stopped'); self.assertEqual(len(calls),1)
        self.assertEqual(records[0].actual_steps,10)
        self.assertNotIn('cond_names',params)

    def test_failure_preserves_completed(self):
        tasks=build_experiment_tasks('ablation',('canny','palette'),(1,1))
        calls=[];records=[]
        class Engine:
            def generate(self,**kw):
                calls.append(kw)
                if len(calls)==2: raise RuntimeError('expected test failure')
                return Image.new('RGB',(8,8)),[]
        status=run_experiment(Engine(),dict(image=Image.new('RGB',(8,8))),tasks,
            on_started=lambda *a:None,on_progress=lambda *a:None,on_previews=lambda *a:None,
            on_result=records.append,should_stop=lambda:False)
        self.assertEqual(status,'failed');self.assertEqual(len(calls),2)
        self.assertEqual([r.status for r in records],['completed','failed'])
