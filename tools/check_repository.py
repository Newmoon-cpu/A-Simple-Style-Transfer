"""Read-only checks for upload candidates and maintained documentation links."""
import ast
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
errors = []


def git(*arguments):
    return subprocess.check_output(['git', '-C', str(ROOT), *arguments])


candidates = sorted({name.decode('utf-8') for name in
                     git('ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0') if name})
existing = [ROOT / name for name in candidates if (ROOT / name).is_file()]
for path in existing:
    relative = path.relative_to(ROOT)
    if path.stat().st_size > 50 * 1024 * 1024:
        errors.append(f'Upload candidate exceeds project limit of 50 MiB: {relative}')
    if path.suffix.lower() in {'.exe', '.dll', '.pyd', '.pyc', '.ckpt', '.safetensors', '.pth', '.pt'}:
        errors.append(f'Local runtime or cache included in upload candidates: {relative}')
    if any(part in {'__pycache__', '.obsidian', 'build', 'dist'} for part in relative.parts):
        errors.append(f'Generated directory included in upload candidates: {relative}')

required = [
    'README.md', 'requirements.txt', 'ctrlora/core.py', 'ctrlora/app/qt_app.py',
    'ctrlora/app/image_widgets.py', 'ctrlora/packaging/CtrLoRADesktop.spec',
    'ctrlora/packaging/runtime_torch_first.py',
]
for name in required:
    if not (ROOT / name).is_file() or name not in candidates:
        errors.append(f'Required source missing or ignored: {name}')

documents = [ROOT / 'README.md', ROOT / 'ctrlora/README.md',
             ROOT / 'ctrlora/packaging/README.md', ROOT / 'examples/README.md']
documents.extend(path for path in (ROOT / 'docs').rglob('*.md')
                 if path.relative_to(ROOT).as_posix() in candidates)
link_count = 0
for document in documents:
    text = document.read_text(encoding='utf-8-sig')
    links = re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', text)
    links += re.findall(r'(?:src|href)=["\']([^"\']+)["\']', text)
    for link in links:
        parsed = urlsplit(link.strip('<>'))
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        link_count += 1
        target = document.parent / unquote(parsed.path)
        if not target.exists():
            errors.append(f'Broken local link in {document.relative_to(ROOT)}: {link}')

python_count = 0
for path in existing:
    if path.suffix not in {'.py', '.spec'}:
        continue
    if 'annotator' in path.relative_to(ROOT).parts:
        continue
    try:
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        python_count += 1
    except (SyntaxError, UnicodeError) as error:
        errors.append(f'Cannot parse {path.relative_to(ROOT)}: {error}')

total_size = sum(path.stat().st_size for path in existing)
print(f'Git upload candidates: {len(existing)} files, {total_size / 1024**2:.2f} MiB')
print(f'Checked {link_count} local documentation links and {python_count} Python/spec files')
if errors:
    for error in errors:
        print('ERROR:', error)
    sys.exit(1)
print('PASS: repository layout, upload candidates and maintained links')
