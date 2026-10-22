"""Check that bundled project modules have importable parent packages."""
import sys
from PyInstaller.archive.readers import ZlibArchiveReader

archive = ZlibArchiveReader(sys.argv[1])
missing = set()
for name in archive.toc:
    if name.split('.')[0] not in {'ldm', 'cldm', 'annotator', 'app'}:
        continue
    parts = name.split('.')
    for length in range(1, len(parts)):
        parent = '.'.join(parts[:length])
        if parent not in archive.toc:
            missing.add(parent)
assert not missing, f'Missing parent packages: {sorted(missing)}'
print('PASS: project module parent packages are present')
