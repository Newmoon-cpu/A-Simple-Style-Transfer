"""Image actions and generation progress for the PyQt desktop interface."""
import time
from pathlib import Path

from PIL import Image
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QToolButton, QGridLayout, QHBoxLayout, QVBoxLayout,
    QDialog, QScrollArea, QFileDialog, QMessageBox, QStyle, QSizePolicy,
    QProgressBar,
)


def pil_to_pixmap(image):
    rgb = image.convert('RGB')
    data = rgb.tobytes('raw', 'RGB')
    qimage = QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format_RGB888)
    return QPixmap.fromImage(qimage.copy())


def save_image_file(image, path, selected_filter=''):
    path = Path(path)
    if not path.suffix:
        suffix = '.jpg' if 'JPEG' in selected_filter else '.webp' if 'WebP' in selected_filter else '.png'
        path = path.with_suffix(suffix)
    output = image
    if path.suffix.lower() in {'.jpg', '.jpeg'}:
        if image.mode == 'RGBA':
            output = Image.new('RGB', image.size, 'white')
            output.paste(image, mask=image.getchannel('A'))
        else:
            output = image.convert('RGB')
    output.save(path)
    return str(path)


class ImagePreviewDialog(QDialog):
    def __init__(self, image, title, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.image = image.copy()
        self._pixmap = pil_to_pixmap(self.image)
        self.zoom_factor = 1.0
        self._fit_mode = True
        self.setWindowTitle(f'{title} · {image.width} × {image.height}')
        self.resize(1000, 760)
        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.zoom_label = QLabel()
        toolbar.addWidget(QLabel(f'{image.width} × {image.height} px'))
        toolbar.addStretch()
        for text, tip, action in [
            ('−', '缩小', lambda: self.set_zoom(self.zoom_factor / 1.25)),
            ('+', '放大', lambda: self.set_zoom(self.zoom_factor * 1.25)),
            ('1:1', '查看原始尺寸', self.actual_size),
            ('适应窗口', '等比适应窗口', self.fit_image),
        ]:
            button = QToolButton()
            button.setText(text)
            button.setToolTip(tip)
            button.clicked.connect(action)
            toolbar.addWidget(button)
        toolbar.addWidget(self.zoom_label)
        root.addLayout(toolbar)
        self.scroll = QScrollArea()
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.setStyleSheet('QScrollArea {background: #172033; border: none; border-radius: 8px;}')
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.scroll.setWidget(self.label)
        root.addWidget(self.scroll)

    def _render(self):
        size = QSize(max(1, round(self.image.width * self.zoom_factor)),
                     max(1, round(self.image.height * self.zoom_factor)))
        pixmap = self._pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.size())
        self.zoom_label.setText(f'{self.zoom_factor:.0%}')

    def set_zoom(self, factor):
        self._fit_mode = False
        self.zoom_factor = max(0.02, min(8.0, factor))
        self._render()

    def actual_size(self):
        self.set_zoom(1.0)

    def fit_image(self):
        self._fit_mode = True
        viewport = self.scroll.viewport().size()
        self.zoom_factor = min(1.0, max(0.001, (viewport.width() - 24) / self.image.width),
                               max(0.001, (viewport.height() - 24) / self.image.height))
        self._render()

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scroll') and self._fit_mode:
            self.fit_image()


class ImagePanel(QWidget):
    def __init__(self, title, filename, placeholder='暂无图片', parent=None):
        super().__init__(parent)
        self.title = title
        self.filename = filename
        self.placeholder = placeholder
        self.image = None
        self._pixmap = None
        self._preview = None
        self.setMinimumSize(220, 160)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel(placeholder)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setStyleSheet(
            'QLabel {background: #eef2f7; color: #7c879b; border: 1px solid #e0e6ef; border-radius: 10px;}')
        layout.addWidget(self.image_label, 0, 0)
        toolbar = QWidget()
        buttons = QHBoxLayout(toolbar)
        buttons.setContentsMargins(8, 8, 8, 8)
        buttons.setSpacing(6)
        self.preview_button = self._button(QStyle.SP_TitleBarMaxButton, '放大预览', self.open_preview)
        self.save_button = self._button(QStyle.SP_DialogSaveButton, '下载 / 保存原图', self.save_image)
        buttons.addWidget(self.preview_button)
        buttons.addWidget(self.save_button)
        layout.addWidget(toolbar, 0, 0, Qt.AlignTop | Qt.AlignRight)
        self.clear_image()

    def _button(self, icon, tooltip, action):
        button = QToolButton()
        button.setIcon(self.style().standardIcon(icon))
        button.setIconSize(QSize(17, 17))
        button.setFixedSize(32, 30)
        button.setToolTip(tooltip)
        button.setAccessibleName(f'{self.title}：{tooltip}')
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet('''
            QToolButton {background: rgba(255,255,255,235); border: 1px solid #d6deea; border-radius: 7px;}
            QToolButton:hover {background: #dbeafe; border-color: #93b4f5;}
            QToolButton:disabled {background: #edf0f5; border-color: #e0e6ef;}
        ''')
        button.clicked.connect(action)
        return button

    def set_image(self, image):
        self.image = image.copy()
        self._pixmap = pil_to_pixmap(self.image)
        self.preview_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.image_label.setToolTip(f'{self.title} · {image.width} × {image.height} px')
        self._refresh()

    def clear_image(self):
        self.image = None
        self._pixmap = None
        self.image_label.clear()
        self.image_label.setText(self.placeholder)
        self.image_label.setToolTip('')
        self.preview_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def _refresh(self):
        if self._pixmap is not None:
            size = self.image_label.size() - QSize(16, 16)
            self.image_label.setPixmap(self._pixmap.scaled(
                QSize(max(1, size.width()), max(1, size.height())),
                Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh()

    def open_preview(self):
        if self.image is None:
            return None
        self._preview = ImagePreviewDialog(self.image, self.title, self)
        self._preview.show()
        return self._preview

    def save_to(self, path, selected_filter=''):
        if self.image is None:
            raise ValueError('没有可保存的图片')
        return save_image_file(self.image, path, selected_filter)

    def save_image(self):
        if self.image is None:
            return
        directory = Path.home() / 'Pictures'
        if not directory.exists():
            directory = Path.home()
        path, selected = QFileDialog.getSaveFileName(
            self, f'保存{self.title}', str(directory / self.filename),
            'PNG 图片 (*.png);;JPEG 图片 (*.jpg *.jpeg);;WebP 图片 (*.webp)')
        if path:
            try:
                self.save_to(path, selected)
            except Exception as error:
                QMessageBox.critical(self, '保存失败', str(error))


class GenerationProgress(QWidget):
    STAGES = [('conditions', '条件提取'), ('model', '模型加载'),
              ('sampling', '逐步绘制'), ('decode', '图像解码')]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.started_at = None
        self.labels = []
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        stages = QHBoxLayout()
        for index, (_, title) in enumerate(self.STAGES):
            if index:
                arrow = QLabel('›')
                arrow.setStyleSheet('color: #a4afc0;')
                stages.addWidget(arrow)
            label = QLabel(f'{index + 1}  {title}')
            label.setAlignment(Qt.AlignCenter)
            stages.addWidget(label, 1)
            self.labels.append(label)
        root.addLayout(stages)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFixedHeight(20)
        self.bar.setFormat('%p%')
        self.bar.setStyleSheet('''
            QProgressBar {background: #e9eef6; border: none; border-radius: 6px; text-align: center; color: #172b4d;}
            QProgressBar::chunk {background: #78a9ff; border-radius: 6px;}
        ''')
        root.addWidget(self.bar)
        info = QHBoxLayout()
        self.status = QLabel('准备就绪')
        self.detail = QLabel('选择图片后开始生成')
        self.detail.setStyleSheet('color: #69768b;')
        info.addWidget(self.status)
        info.addStretch()
        info.addWidget(self.detail)
        root.addLayout(info)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.elapsed = QLabel('已耗时 00:00')
        self.elapsed.setStyleSheet('color: #69768b; font-size: 11px;')
        root.addWidget(self.elapsed)
        self._mark_stage(-1)

    def _mark_stage(self, active, failed=False):
        for index, label in enumerate(self.labels):
            color, background = '#7c879b', '#edf1f6'
            if index < active:
                color, background = '#16764a', '#e5f5ec'
            elif index == active:
                color, background = ('#b42318', '#feeceb') if failed else ('#1d4ed8', '#e4edff')
            label.setStyleSheet(f'color: {color}; background: {background}; padding: 7px 5px; border-radius: 6px;')
        self._active = active

    def start(self):
        self.started_at = time.monotonic()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFormat('%p%')
        self.status.setText('正在准备')
        self.detail.setText('首次加载模型可能需要较长时间')
        self.detail.setToolTip('')
        self._mark_stage(0)
        self._tick()
        self.timer.start(250)

    def reset(self):
        self.timer.stop()
        self.started_at = None
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.status.setText('准备就绪')
        self.detail.setText('选择图片后开始生成')
        self.detail.setToolTip('')
        self._mark_stage(-1)
        self._tick()

    def update_progress(self, stage, completed, total):
        if stage == 'done':
            self.finish()
            return
        names = [item[0] for item in self.STAGES]
        if stage not in names:
            return
        self._mark_stage(names.index(stage))
        self.status.setText(f'正在{self.STAGES[self._active][1]}')
        if stage == 'sampling':
            self.bar.setRange(0, 100)
            percent = min(100, max(0, int(100 * completed / total))) if total else 0
            self.bar.setValue(percent)
            self.bar.setFormat('%p%')
            self.detail.setText(f'采样步数 {completed} / {total}')
        else:
            self.bar.setRange(0, 0)
            self.detail.setText({
                'conditions': f'已提取 {completed} / {total} 个条件',
                'model': '加载或复用模型，请稍候',
                'decode': '采样完成，正在还原最终图像',
            }[stage])

    def _tick(self):
        seconds = int(time.monotonic() - self.started_at) if self.started_at is not None else 0
        self.elapsed.setText(f'已耗时 {seconds // 60:02d}:{seconds % 60:02d}')

    def finish(self):
        self.timer.stop()
        self._tick()
        self._mark_stage(len(self.STAGES))
        self.bar.setRange(0, 100)
        self.bar.setValue(100)
        self.status.setText('绘制完成')
        self.detail.setText('可使用图片右上角图标预览或保存')

    def fail(self, message):
        self.timer.stop()
        self._tick()
        if self.bar.maximum() == 0:
            self.bar.setRange(0, 100)
            self.bar.setValue(0)
        self._mark_stage(max(0, self._active), failed=True)
        self.status.setText('生成失败')
        self.detail.setText('请调整参数后重试')
        self.detail.setToolTip(message)
