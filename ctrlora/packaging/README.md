# Desktop packaging

Run `build_exe.bat` from the `ctrlora` source directory. It invokes
`packaging/CtrLoRADesktop.spec`, then copies external configuration and weights.

The spec resolves its source paths from its own location and preloads torch
before Qt during Windows DLL discovery and at runtime. Keep the runtime hook
next to the spec.

Install build dependencies with `python -m pip install -r packaging/requirements-build.txt`
from `ctrlora/`, then run `build_exe.bat`. Prepare model files in `ckpts/` and
`annotator/ckpts/` first. The build copies these resources and
`packaging/README-desktop.txt` into the release directory.

The complete output is `dist/CtrLoRADesktop/`. Keep that folder together;
the executable alone is not a complete application. The output and model
weights are intentionally excluded from the source repository.
