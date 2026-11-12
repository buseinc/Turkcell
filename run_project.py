"""Dispatch project scripts to the local Python environment or Ubuntu."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent / 'turkcell_tam_paket_2026-11-10'
if len(sys.argv) < 2:
    raise SystemExit('Usage: calistir.cmd analysis/script.py [args] or simulation/script.py [args]')
script = (root / sys.argv[1]).resolve()
if not script.is_relative_to(root) or not script.is_file() or script.suffix != '.py':
    raise SystemExit('Expected a Python script inside the full project directory')
relative = script.relative_to(root).as_posix()
command = (['wsl', '--distribution', 'Ubuntu-22.04', '--exec', 'python3']
           if relative.startswith('simulation/') else [sys.executable])
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
raise SystemExit(subprocess.call(command + [relative] + sys.argv[2:], cwd=root))
