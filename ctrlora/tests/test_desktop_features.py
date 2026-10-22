import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch  # Must precede Qt on Windows.
from PIL import Image
import core
from cldm.ddim_hacked import DDIMSampler
from PyQt5.QtWidgets import QApplication
from app.image_widgets import ImagePanel, GenerationProgress
from app.qt_app import MainWindow


class DesktopFeaturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_image_actions_and_full_resolution_export(self):
        panel = ImagePanel('结果', 'output.png')
        self.assertFalse(panel.preview_button.isEnabled())
        panel.set_image(Image.new('RGB', (1024, 256), 'red'))
        panel.resize(400, 300)
        panel.show()
        self.app.processEvents()
        self.assertTrue(panel.save_button.isEnabled())
        pixmap = panel.image_label.pixmap()
        self.assertAlmostEqual(pixmap.width() / pixmap.height(), 4, places=1)
        with tempfile.TemporaryDirectory() as directory:
            path = panel.save_to(Path(directory) / 'result')
            with Image.open(path) as saved:
                self.assertEqual(saved.size, (1024, 256))
                self.assertEqual(saved.getpixel((500, 100)), (255, 0, 0))
        dialog = panel.open_preview()
        self.assertEqual(dialog.image.size, (1024, 256))
        dialog.actual_size()
        self.assertEqual(dialog.zoom_factor, 1.0)
        dialog.close()
        panel.clear_image()
        self.assertFalse(panel.preview_button.isEnabled())
        self.assertFalse(panel.save_button.isEnabled())
        panel.close()

    def test_jpeg_export_handles_transparency(self):
        panel = ImagePanel('图片', 'input.png')
        panel.set_image(Image.new('RGBA', (60, 120), (100, 20, 40, 128)))
        with tempfile.TemporaryDirectory() as directory:
            path = panel.save_to(Path(directory) / 'image.jpg')
            with Image.open(path) as image:
                self.assertEqual(image.mode, 'RGB')
                self.assertEqual(image.size, (60, 120))

    def test_save_cancel_leaves_original_image_untouched(self):
        panel = ImagePanel('图片', 'input.png')
        panel.set_image(Image.new('RGB', (80, 40), 'green'))
        with patch('app.image_widgets.QFileDialog.getSaveFileName', return_value=('', '')), \
             patch.object(panel, 'save_to') as save:
            panel.save_image()
            save.assert_not_called()
        self.assertEqual(panel.image.size, (80, 40))

    def test_single_condition_clears_old_second_preview_and_busy_close_is_safe(self):
        window = MainWindow()
        image = Image.new('RGB', (64, 128), 'red')
        window._on_done(image, [image, image])
        self.assertIsNotNone(window.prev2.image)
        window._on_done(image, [image])
        self.assertIsNone(window.prev2.image)
        self.assertFalse(window.prev2.save_button.isEnabled())
        window.worker = type('RunningWorker', (), {'isRunning': lambda self: True})()
        event = type('CloseEvent', (), {'ignore': lambda self: setattr(self, 'ignored', True)})()
        with patch('app.qt_app.QMessageBox.information'):
            window.closeEvent(event)
        self.assertTrue(event.ignored)
        window.worker = None
        window.close()

    def test_progress_unknown_stages_steps_failure_and_retry(self):
        widget = GenerationProgress()
        widget.start()
        widget.update_progress('model', 0, 0)
        self.assertEqual(widget.bar.maximum(), 0)
        widget.update_progress('sampling', 3, 10)
        self.assertEqual(widget.bar.value(), 30)
        self.assertIn('3 / 10', widget.detail.text())
        widget.fail('model unavailable')
        self.assertFalse(widget.timer.isActive())
        self.assertIn('失败', widget.status.text())
        widget.start()
        self.assertEqual(widget.bar.value(), 0)
        widget.update_progress('sampling', 10, 10)
        widget.update_progress('decode', 0, 0)
        self.assertIn('解码', widget.status.text())
        widget.finish()
        self.assertEqual(widget.bar.value(), 100)
        self.assertFalse(widget.timer.isActive())
        widget.reset()
        self.assertEqual(widget.bar.value(), 0)
        self.assertIn('准备', widget.status.text())

    def test_sampler_reports_actual_number_of_steps(self):
        sampler = DDIMSampler.__new__(DDIMSampler)
        sampler.model = type('Model', (), {'betas': torch.zeros(1)})()
        sampler.ddim_timesteps = np.array([1, 201, 401, 601, 801])
        sampler.p_sample_ddim = lambda image, *args, **kwargs: (image, image)
        events = []
        legacy_events = []
        sampler.ddim_sampling(None, (1, 4, 2, 2),
                              callback=legacy_events.append,
                              progress_callback=lambda done, total: events.append((done, total)))
        self.assertEqual(events, [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)])
        self.assertEqual(legacy_events, list(range(5)))

    def test_engine_emits_previews_and_stages_without_changing_return(self):
        engine = core.StyleTransferEngine()
        events, previews_ready = [], []
        output = Image.new('RGB', (64, 64), 'blue')
        def fake_sample(*args, progress_callback=None, **kwargs):
            progress_callback('sampling', 1, 2)
            progress_callback('sampling', 2, 2)
            progress_callback('decode', 0, 0)
            return [output]
        with patch.object(core, 'extract_condition', return_value=np.zeros((64, 64, 3), dtype=np.uint8)), \
             patch.object(engine, '_get_model', return_value=object()), \
             patch.object(core, 'sample', side_effect=fake_sample):
            result, previews = engine.generate(output, 'style', ['canny'], [1], '', '',
                progress_callback=lambda *event: events.append(event),
                preview_callback=previews_ready.append)
        self.assertIs(result, output)
        self.assertEqual(len(previews), 1)
        self.assertEqual(len(previews_ready[0]), 1)
        self.assertEqual([event[0] for event in events],
                         ['conditions', 'conditions', 'model', 'sampling', 'sampling', 'sampling', 'decode', 'done'])


if __name__ == '__main__':
    unittest.main()
