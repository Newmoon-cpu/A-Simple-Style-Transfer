"""Render Qt layout using the images produced by the frozen generation test."""
import os
import sys
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from app.qt_app import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase
from PIL import Image

app = QApplication([])
font_id = QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR']) / 'Fonts/msyh.ttc'))
assert font_id >= 0, 'The offscreen platform needs an explicit system font'
app.setFont(QFont(QFontDatabase.applicationFontFamilies(font_id)[0], 9))
output = root.parent / 'examples/verification'
screenshots = root.parent / 'docs/images'
screenshots.mkdir(parents=True, exist_ok=True)
window = MainWindow()
window._set_input(str(output / 'input.png'))
window.cond2_box.setCurrentText('palette')
window.res_spin.setValue(256)
window.steps_spin.setValue(10)
with Image.open(output / 'output-dual.png') as file:
    result = file.copy()
previews = []
for name in ['condition-1.png', 'condition-2.png']:
    with Image.open(output / name) as file:
        previews.append(file.copy())
window._on_previews(previews)
window._set_busy(True)
window.generation_progress.start()
window.generation_progress.update_progress('sampling', 5, 10)
window.show()
app.processEvents()
window.grab().save(str(screenshots / 'ui-progress.png'))
window._on_done(result, previews)
app.processEvents()
window.grab().save(str(screenshots / 'ui-complete.png'))
dialog = window.out_label.open_preview()
app.processEvents()
dialog.grab().save(str(screenshots / 'ui-preview.png'))
dialog.close()
window.resize(1120, 760)
app.processEvents()
window.grab().save(str(screenshots / 'ui-compact.png'))
print('RENDER_PASS', window.size().width(), window.size().height())
window.close()
