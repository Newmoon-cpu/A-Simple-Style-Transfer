from PyQt5.QtCore import QThread, pyqtSignal


class ExportWorker(QThread):
    done=pyqtSignal(str)
    error=pyqtSignal(str)

    def __init__(self,function,*args):
        super().__init__(); self.function=function; self.args=args

    def run(self):
        try: self.done.emit(str(self.function(*self.args)))
        except Exception as error: self.error.emit(str(error))
