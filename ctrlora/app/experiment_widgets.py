from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QScrollArea, QGridLayout
from app.image_widgets import ImagePanel


class ExperimentPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout=QVBoxLayout(self); row=QHBoxLayout()
        self.mode=QComboBox(); self.mode.addItem('单/双条件对比（3次）','ablation'); self.mode.addItem('权重扫描（9次）','weight_grid')
        self.start=QPushButton('开始实验'); self.stop=QPushButton('停止后续任务'); self.export=QPushButton('导出实验')
        for widget in (self.mode,self.start,self.stop,self.export): row.addWidget(widget)
        layout.addLayout(row)
        self.status=QLabel('串行生成，沿用左侧参数；请选择两个不同条件'); layout.addWidget(self.status)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        content=QWidget(); self.grid=QGridLayout(content); scroll.setWidget(content); layout.addWidget(scroll,1)
        self.reset()

    def reset(self):
        while self.grid.count():
            item=self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.tasks=(); self.records={}; self.cards={}; self.metadata={}; self.input_image=None
        self.stop.setEnabled(False); self.export.setEnabled(False)

    def begin(self,tasks,input_image,metadata):
        self.reset(); self.tasks=tasks; self.input_image=input_image.copy(); self.metadata=metadata
        self.metadata['created_at']=datetime.now().astimezone().isoformat()
        columns=2 if len(tasks)==3 else 3
        offset=0
        if len(tasks)==3:
            panel=ImagePanel('原图','input.png'); panel.setMinimumSize(180,130); panel.set_image(input_image)
            title=QLabel('原图'); title.setFixedHeight(20)
            panel.layout().addWidget(title,1,0)
            panel.layout().setRowStretch(0,1)
            self.grid.addWidget(panel,0,0); offset=1
        for index,task in enumerate(tasks,offset):
            panel=ImagePanel(task.label,task.task_id+'.png','未运行'); panel.setMinimumSize(180,130)
            title=QLabel(task.label); title.setFixedHeight(20)
            panel.layout().addWidget(title,1,0)
            panel.layout().setRowStretch(0,1)
            self.cards[task.task_id]=panel; self.grid.addWidget(panel,index//columns,index%columns)
        self.stop.setEnabled(True)

    def set_active(self,index,total,task):
        self.status.setText(f'任务 {index}/{total} · {task.label}')

    def set_result(self,record):
        self.records[record.task.task_id]=record
        if record.image is not None: self.cards[record.task.task_id].set_image(record.image)
        else:
            card=self.cards[record.task.task_id]
            card.image_label.setText('失败：'+(record.error or '未知错误'))
            card.setToolTip(record.error or '失败')

    def finish(self,status):
        self.stop.setEnabled(False); self.export.setEnabled(bool(self.records))
        text={'completed':'实验完成','stopped':'已停止后续任务','failed':'实验失败，已保留完成项'}
        self.status.setText(text.get(status,status))

    def snapshot(self):
        return dict(tasks=self.tasks,records=dict(self.records),input_image=self.input_image,
                    metadata=dict(self.metadata))
