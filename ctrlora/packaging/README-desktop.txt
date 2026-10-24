CtrLoRA Desktop

Run CtrLoRADesktop.exe. Python does not need to be installed separately.
Keep the whole folder, including _internal, configs, ckpts, annotator and hf-cache.
Image generation requires a compatible NVIDIA GPU and driver.

Select an input image, a style and one or two conditions, then generate.
The icons at the top right of each image open a preview or save the original image.
The progress panel shows generation stages, actual sampling steps and elapsed time.
The first generation takes longer because models must be loaded.

Replay and comparison (2026-10-23)
- The original result area now has Result / Replay / Experiment tabs.
- Replay records intermediate model predictions, not brush strokes. Final output is appended separately.
- Playback may be paused; individual frames and the complete GIF can be saved.
- Experiment uses two distinct conditions from the left panel. Choose canny + palette for a lightweight demonstration.
- Ablation runs real A-only, B-only and A+B models serially. Weight grid runs 9 combinations.
- Stop means finish the current image and skip remaining tasks.
- Export saves full-resolution results, comparison.png, parameters JSON and CSV in your chosen folder.
- Timings include preprocessing/model loading and should not be used as pure inference speed rankings.
