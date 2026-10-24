"""Opt-in packaged end-to-end verification: --verify-replay OUTPUT INPUT."""
import json
from pathlib import Path
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from export_artifacts import export_replay_gif, export_experiment_bundle


def schedule_verification(window, output, input_path):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    state={'stage':'ordinary'}
    def start():
        window._set_input(input_path)
        window.res_spin.setValue(256); window.steps_spin.setValue(10)
        window.cond1_box.setCurrentText('canny'); window.cond2_box.setCurrentText('palette')
        window._generate()
    def poll():
        if window.worker is not None: return
        try:
            if state['stage']=='ordinary':
                if not window.replay.complete: raise RuntimeError('No completed replay')
                export_replay_gif(window.replay.snapshot_frames(),output/'generation.gif')
                window.tabs.setCurrentIndex(1); window.grab().save(str(output/'replay-ui.png'))
                state['stage']='experiment'; window._start_experiment()
            elif state['stage']=='experiment':
                if len(window.experiment.records)!=3 or any(r.status!='completed' for r in window.experiment.records.values()):
                    raise RuntimeError('Experiment incomplete')
                bundle=export_experiment_bundle(window.experiment.snapshot(),output)
                window.tabs.setCurrentIndex(2); window.grab().save(str(output/'experiment-ui.png'))
                (output/'success.json').write_text(json.dumps(dict(build=window.build_info,bundle=str(bundle))),encoding='utf-8')
                timer.stop(); window.close(); QApplication.instance().quit()
        except Exception as error:
            (output/'failure.txt').write_text(str(error),encoding='utf-8')
            timer.stop(); window.close(); QApplication.instance().exit(1)
    timer=QTimer(window); timer.setInterval(1000); timer.timeout.connect(poll)
    window._verification_timer=timer
    QTimer.singleShot(100,start); QTimer.singleShot(200,timer.start)
