"""CtrLoRA 通用条件注入风格重绘 —— PyQt5 桌面版（横版布局）。

逻辑层：core.StyleTransferEngine（不依赖 UI）
UI 层：本文件（只负责展示与交互）

运行：python app/qt_app.py
打包：见 build_exe.bat
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 打包成 exe 后，把工作目录切到 exe 所在目录，使外部的 configs/ckpts/annotator 相对路径可用
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

from PIL import Image, ImageOps

# 必须先导入 core（内部 import torch），再导入 PyQt5：
# Windows 下若先 import Qt，其 DLL 会干扰 torch 的 c10.dll 加载导致 WinError 1114。
from core import StyleTransferEngine

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QLineEdit, QFileDialog, QHBoxLayout, QVBoxLayout,
    QGridLayout, QGroupBox, QSplitter, QMessageBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from app.image_widgets import ImagePanel, GenerationProgress


class GenerateWorker(QThread):
    done = pyqtSignal(object, object)   # (result PIL, previews [PIL,...])
    error = pyqtSignal(str)
    progress = pyqtSignal(str, int, int)
    previews_ready = pyqtSignal(object)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def run(self):
        try:
            result, previews = self.engine.generate(
                **self.params, progress_callback=self.progress.emit,
                preview_callback=self.previews_ready.emit)
            self.done.emit(result, previews)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = StyleTransferEngine()
        self.worker = None
        self._input_img = None

        self.setWindowTitle('CtrLoRA 条件注入风格重绘（桌面版）')
        self.resize(1360, 860)
        self.setMinimumSize(1120, 760)

        self._build_ui()
        self._populate()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        splitter = QSplitter(Qt.Horizontal)

        # ===== 左栏：输入与参数 =====
        left = QWidget()
        lv = QVBoxLayout(left)

        g_input = QGroupBox('① 输入照片')
        gi = QVBoxLayout(g_input)
        self.input_label = ImagePanel('输入照片', 'input.png', '选择图片或将图片拖入此处')
        self.input_label.setMinimumSize(320, 200)
        self.input_label.setAcceptDrops(True)
        self.input_label.dragEnterEvent = self._drag_enter
        self.input_label.dropEvent = self._drop
        self.btn_load = QPushButton('选择图片…')
        self.btn_load.clicked.connect(self._load_image)
        gi.addWidget(self.input_label)
        gi.addWidget(self.btn_load)
        lv.addWidget(g_input)

        g_style = QGroupBox('② 风格底座')
        gs = QVBoxLayout(g_style)
        self.style_box = QComboBox()
        self.style_box.currentTextChanged.connect(self._on_style_change)
        gs.addWidget(self.style_box)
        lv.addWidget(g_style)

        g_cond = QGroupBox('③ 条件注入（最多 2 个联合）')
        gc = QGridLayout(g_cond)
        self.cond1_box = QComboBox()
        self.weight1 = QDoubleSpinBox()
        self.weight1.setRange(0.0, 1.5); self.weight1.setSingleStep(0.05); self.weight1.setValue(1.0)
        self.cond2_box = QComboBox()
        self.weight2 = QDoubleSpinBox()
        self.weight2.setRange(0.0, 1.5); self.weight2.setSingleStep(0.05); self.weight2.setValue(1.0)
        gc.addWidget(QLabel('条件 1'), 0, 0); gc.addWidget(self.cond1_box, 0, 1)
        gc.addWidget(QLabel('权重 1'), 0, 2); gc.addWidget(self.weight1, 0, 3)
        gc.addWidget(QLabel('条件 2'), 1, 0); gc.addWidget(self.cond2_box, 1, 1)
        gc.addWidget(QLabel('权重 2'), 1, 2); gc.addWidget(self.weight2, 1, 3)
        lv.addWidget(g_cond)

        g_param = QGroupBox('④ 采样参数（切换底座自动更新 prompt/负向/CFG）')
        gp = QGridLayout(g_param)
        gp.addWidget(QLabel('Prompt'), 0, 0)
        self.prompt_edit = QLineEdit()
        gp.addWidget(self.prompt_edit, 0, 1, 1, 3)
        gp.addWidget(QLabel('负向'), 1, 0)
        self.neg_edit = QLineEdit()
        gp.addWidget(self.neg_edit, 1, 1, 1, 3)
        self.res_spin = QSpinBox(); self.res_spin.setRange(256, 512); self.res_spin.setSingleStep(64); self.res_spin.setValue(448)
        self.steps_spin = QSpinBox(); self.steps_spin.setRange(10, 40); self.steps_spin.setValue(28)
        self.scale_spin = QDoubleSpinBox(); self.scale_spin.setRange(1.0, 15.0); self.scale_spin.setSingleStep(0.5); self.scale_spin.setValue(7.0)
        self.seed_spin = QSpinBox(); self.seed_spin.setRange(0, 999999); self.seed_spin.setValue(42)
        gp.addWidget(QLabel('分辨率'), 2, 0); gp.addWidget(self.res_spin, 2, 1)
        gp.addWidget(QLabel('步数'), 2, 2); gp.addWidget(self.steps_spin, 2, 3)
        gp.addWidget(QLabel('CFG'), 3, 0); gp.addWidget(self.scale_spin, 3, 1)
        gp.addWidget(QLabel('种子'), 3, 2); gp.addWidget(self.seed_spin, 3, 3)
        lv.addWidget(g_param)
        self.parameter_groups = [g_style, g_cond, g_param]

        self.btn_gen = QPushButton('🎨 生成')
        self.btn_gen.setMinimumHeight(40)
        self.btn_gen.clicked.connect(self._generate)
        lv.addWidget(self.btn_gen)
        lv.addStretch()

        # ===== 右栏：结果与条件预览 =====
        right = QWidget()
        rv = QVBoxLayout(right)

        g_out = QGroupBox('风格化结果')
        go = QVBoxLayout(g_out)
        self.out_label = ImagePanel('风格化结果', 'styled.png', '绘制完成后，结果将显示在这里')
        self.out_label.setMinimumSize(500, 300)
        go.addWidget(self.out_label)
        rv.addWidget(g_out, 3)

        g_prev = QGroupBox('条件图预览')
        gpre = QHBoxLayout(g_prev)
        self.prev1 = ImagePanel('条件图 1', 'condition-1.png', '条件图 1')
        self.prev2 = ImagePanel('条件图 2', 'condition-2.png', '条件图 2（可选）')
        gpre.addWidget(self.prev1)
        gpre.addWidget(self.prev2)
        rv.addWidget(g_prev, 2)

        g_progress = QGroupBox('生成过程')
        progress_layout = QVBoxLayout(g_progress)
        self.generation_progress = GenerationProgress()
        progress_layout.addWidget(self.generation_progress)
        rv.addWidget(g_progress)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 5)
        root.addWidget(splitter)
        self.setStyleSheet('''
            QMainWindow {background: #f5f7fb;}
            QGroupBox {font-weight: 600; color: #263650; border: 1px solid #dce3ed;
                       border-radius: 9px; margin-top: 12px; padding-top: 10px;}
            QGroupBox::title {subcontrol-origin: margin; left: 12px; padding: 0 5px;}
            QPushButton {padding: 6px 12px;}
        ''')

    def _populate(self):
        self.style_box.addItems(self.engine.list_styles())
        conds = self.engine.list_conditions()
        self.cond1_box.addItems(conds)
        self.cond2_box.addItems(['none'] + conds)
        self.cond1_box.setCurrentText('canny')
        self.cond2_box.setCurrentText('none')
        # 默认选水墨（若存在）
        styles = [self.style_box.itemText(i) for i in range(self.style_box.count())]
        for pref in ['ChineseInkComicStrip_v10.ckpt', 'realisticVisionV60B1.safetensors']:
            if pref in styles:
                self.style_box.setCurrentText(pref)
                break
        self._on_style_change(self.style_box.currentText())

    def _on_style_change(self, sd_file):
        if not sd_file:
            return
        prompt, negative, cfg = self.engine.style_profile(sd_file)
        self.prompt_edit.setText(prompt)
        self.neg_edit.setText(negative)
        self.scale_spin.setValue(cfg)

    # ---- 图片加载 / 拖拽 ----
    def _load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择图片', '', 'Images (*.png *.jpg *.jpeg *.bmp *.webp)')
        if path:
            self._set_input(path)

    def _drag_enter(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def _drop(self, e):
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                self._set_input(p)
                break

    def _set_input(self, path):
        if self.worker is not None and self.worker.isRunning():
            return
        try:
            with Image.open(path) as source:
                img = ImageOps.exif_transpose(source).convert('RGB')
        except Exception as error:
            QMessageBox.warning(self, '无法打开图片', str(error))
            return
        self._input_img = img
        self.input_label.filename = os.path.splitext(os.path.basename(path))[0] + '.png'
        self.input_label.set_image(img)
        self.input_label.setToolTip(path)
        self.out_label.clear_image()
        self.prev1.clear_image()
        self.prev2.clear_image()
        self.generation_progress.reset()

    # ---- 生成 ----
    def _generate(self):
        if self._input_img is None:
            QMessageBox.warning(self, '提示', '请先选择输入照片')
            return
        if self.worker is not None and self.worker.isRunning():
            return
        cond_names = [self.cond1_box.currentText()]
        if self.cond2_box.currentText() != 'none':
            cond_names.append(self.cond2_box.currentText())
        params = dict(
            image=self._input_img,
            sd_file=self.style_box.currentText(),
            cond_names=cond_names,
            weights=[self.weight1.value(), self.weight2.value()][:len(cond_names)],
            prompt=self.prompt_edit.text(),
            n_prompt=self.neg_edit.text(),
            resolution=self.res_spin.value(),
            steps=self.steps_spin.value(),
            scale=self.scale_spin.value(),
            seed=self.seed_spin.value(),
        )
        self._set_busy(True)
        self.out_label.clear_image()
        self.prev1.clear_image()
        self.prev2.clear_image()
        self.generation_progress.start()
        self.worker = GenerateWorker(self.engine, params)
        self.worker.done.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.progress.connect(self.generation_progress.update_progress)
        self.worker.previews_ready.connect(self._on_previews)
        self.worker.start()

    def _on_done(self, result, previews):
        self._set_busy(False)
        self.out_label.set_image(result)
        self._on_previews(previews)
        self.generation_progress.finish()

    def _on_previews(self, previews):
        self.prev1.clear_image()
        self.prev2.clear_image()
        if previews and previews[0] is not None:
            self.prev1.set_image(previews[0])
        if len(previews) > 1 and previews[1] is not None:
            self.prev2.set_image(previews[1])

    def _set_busy(self, busy):
        self.btn_gen.setEnabled(not busy)
        self.btn_gen.setText('正在绘制…' if busy else '🎨 生成')
        self.btn_load.setEnabled(not busy)
        for group in self.parameter_groups:
            group.setEnabled(not busy)

    def _on_error(self, msg):
        self._set_busy(False)
        self.generation_progress.fail(msg)
        QMessageBox.critical(self, '生成失败', msg)

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, '正在绘制', '请等待本次生成结束后再关闭窗口。')
            event.ignore()
            return
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
