"""WSL: compile cqi_table.cc against the installed ns-3.44 (same flags as the scenario) and run it."""
from pathlib import Path
import json
import os
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / '09_kpi_yuk_profili_2026-11-12/simulation'))
from ns3_paths import ns3_root  # noqa: E402

NS3 = ns3_root()
commands = json.loads((NS3 / 'cmake-cache/compile_commands.json').read_text())
entry = next(v for v in commands if v['file'].endswith('/src/lte/examples/lena-simple-epc.cc'))
cmd = entry.get('arguments') or shlex.split(entry['command'])
build = HERE / 'build'
build.mkdir(exist_ok=True)
obj = build / 'cqi_table.o'
cmd[cmd.index('-c') + 1] = str(HERE / 'cqi_table.cc')
cmd[cmd.index('-o') + 1] = str(obj)
subprocess.run(cmd, cwd=entry['directory'], check=True)
lib = NS3 / 'build/lib'
modules = ['spectrum', 'lte', 'applications', 'point-to-point', 'internet', 'mobility', 'antenna', 'propagation', 'network', 'core']
binary = build / 'cqi_table'
subprocess.run([cmd[0], str(obj), '-o', str(binary), '-L' + str(lib), '-Wl,-rpath,' + str(lib)]
               + ['-l:libns3.44-' + m + '-default.so' for m in modules], check=True)
env = os.environ.copy()
env['LD_LIBRARY_PATH'] = str(lib) + ':' + env.get('LD_LIBRARY_PATH', '')
subprocess.run([str(binary), '--output=' + str(HERE.parent / 'cqi_table.csv')], env=env, check=True)
