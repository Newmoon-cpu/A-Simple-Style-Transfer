from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, QPushButton, QSlider, QLabel
from app.image_widgets import ImagePanel
from generation_records import PreviewOptions


class ReplayPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.record = QCheckBox('记录生成过程'); self.record.setChecked(True)
        self.interval = QComboBox(); self.interval.addItems(['2','5','10']); self.interval.setCurrentText('5')
        self.follow_button = QPushButton('跟随最新')
        self.follow_button.clicked.connect(self.follow_latest)
        for widget in (self.record,self.interval,self.follow_button): row.addWidget(widget)
        layout.addLayout(row)
        self.panel = ImagePanel('过程预览','preview.png','尚未记录生成过程')
        layout.addWidget(self.panel,1)
        self.slider = QSlider(Qt.Horizontal); self.slider.valueChanged.connect(self.render)
        self.slider.sliderPressed.connect(self.stop_following)
        layout.addWidget(self.slider)
        row = QHBoxLayout()
        self.play = QPushButton('播放'); self.play.clicked.connect(self.toggle_play)
        self.export = QPushButton('导出 GIF')
        self.detail = QLabel(); row.addWidget(self.play); row.addWidget(self.export); row.addWidget(self.detail,1)
        layout.addLayout(row)
        self.timer = QTimer(self); self.timer.timeout.connect(self.advance)
        self.reset()

    def options(self):
        return PreviewOptions(enabled=self.record.isChecked(), interval=int(self.interval.currentText()))

    def reset(self):
        self.timer.stop(); self.frames=[]; self.follow=True; self.complete=False
        self.panel.clear_image(); self.slider.setRange(0,0)
        self.play.setEnabled(False); self.export.setEnabled(False); self.play.setText('播放')
        self.detail.setText('尚未记录生成过程')

    def append_frame(self, frame):
        self.frames.append(frame); self.slider.setMaximum(len(self.frames)-1)
        if self.follow: self.slider.setValue(len(self.frames)-1)
        self.render(self.slider.value())

    def stop_following(self): self.follow=False

    def follow_latest(self):
        self.follow=True; self.slider.setValue(max(0,len(self.frames)-1))

    def render(self, index):
        if not self.frames: return
        frame=self.frames[index]; self.panel.set_image(frame.image)
        self.detail.setText(('最终结果' if frame.kind=='final' else '预测预览') + f' · {frame.step}/{frame.total_steps} 步')

    def mark_finished(self, success):
        self.complete=success and bool(self.frames) and self.frames[-1].kind=='final'
        self.play.setEnabled(len(self.frames)>1)
        self.export.setEnabled(self.complete)
        if not success: self.detail.setText('未完成 · 已保留本次预览')
        elif not self.frames: self.detail.setText('本次未记录生成过程')

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop(); self.play.setText('播放')
        else:
            self.timer.start(400); self.play.setText('暂停')

    def advance(self):
        index=(self.slider.value()+1)%len(self.frames)
        self.slider.setValue(index)
        self.timer.setInterval(1200 if self.frames[index].kind=='final' else 400)

    def snapshot_frames(self): return tuple(self.frames)
