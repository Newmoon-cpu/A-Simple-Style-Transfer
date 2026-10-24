from PyQt5.QtCore import QThread, pyqtSignal
from experiments import run_experiment


class ExperimentWorker(QThread):
    task_started=pyqtSignal(int,int,object)
    progress=pyqtSignal(str,int,int)
    previews_ready=pyqtSignal(object)
    result_ready=pyqtSignal(object)
    done=pyqtSignal(str)
    error=pyqtSignal(str)

    def __init__(self, engine, params, tasks):
        super().__init__(); self.engine=engine; self.params=params; self.tasks=tasks

    def run(self):
        try:
            status=run_experiment(self.engine,self.params,self.tasks,
                on_started=self.task_started.emit,
                on_progress=lambda i,n,s,d,t:self.progress.emit(s,d,t),
                on_previews=lambda i,p:self.previews_ready.emit(p),
                on_result=self.result_ready.emit,should_stop=self.isInterruptionRequested)
            self.done.emit(status)
        except Exception as error: self.error.emit(str(error))
