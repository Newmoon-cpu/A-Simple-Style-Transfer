"""Run the real Qt worker, progress signals and image actions in a frozen build."""
import os
import sys
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['HF_HUB_OFFLINE'] = '1'
os.chdir(Path(sys.executable).parent)

from app.qt_app import MainWindow  # Imports torch before Qt.
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont, QFontDatabase
from PIL import Image

app = QApplication([])
# The Windows offscreen plugin does not discover system fonts automatically.
font_path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/msyh.ttc'
font_id = QFontDatabase.addApplicationFont(str(font_path))
if font_id >= 0:
    app.setFont(QFont(QFontDatabase.applicationFontFamilies(font_id)[0], 9))
window = MainWindow()
output = Path('verification')
output.mkdir(exist_ok=True)
if not (output / 'input.png').exists():
    Image.new('RGB', (256, 256), 'skyblue').save(output / 'input.png')
window._set_input(str(output / 'input.png'))
window.cond2_box.setCurrentText('palette')
window.res_spin.setValue(256)
window.steps_spin.setValue(10)
window.show()
events, failures = [], []
QMessageBox.critical = lambda parent, title, text: failures.append(text)
captured = set()


def progress(stage, done, total):
    events.append((stage, done, total))
    print('UI_PROGRESS', stage, done, total, flush=True)
    if stage == 'sampling' and done >= total // 2 and 'sampling' not in captured:
        captured.add('sampling')
        window.grab().save(str(output / 'ui-progress.png'))


def finish():
    try:
        assert not failures, failures
        sampling = [(done, total) for stage, done, total in events if stage == 'sampling' and done > 0]
        assert sampling and sampling[-1][0] == sampling[-1][1]
        assert len(sampling) == sampling[-1][1]
        assert window.generation_progress.bar.value() == 100
        assert window.btn_gen.isEnabled()
        for name, panel in [('input', window.input_label), ('result', window.out_label),
                            ('condition-1', window.prev1), ('condition-2', window.prev2)]:
            assert panel.preview_button.isEnabled() and panel.save_button.isEnabled()
            saved = panel.save_to(output / f'ui-{name}.png')
            with Image.open(saved) as image:
                assert image.size == panel.image.size
            dialog = panel.open_preview()
            dialog.actual_size()
            assert dialog.zoom_factor == 1.0
            dialog.close()
        window.grab().save(str(output / 'ui-complete.png'))
        print('FROZEN_UI_PASS', len(sampling), 'steps; 4 image previews and exports', flush=True)
        window.close()
        app.exit(0)
    except Exception as error:
        import traceback
        traceback.print_exc()
        print('FROZEN_UI_FAIL', error, flush=True)
        app.exit(1)


def start():
    window._generate()
    window.worker.progress.connect(progress)
    window.worker.finished.connect(finish)


QTimer.singleShot(0, start)
QTimer.singleShot(300000, lambda: app.exit(2))
sys.exit(app.exec_())
