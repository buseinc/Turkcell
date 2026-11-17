"""WSL: exercise the actual C++ spectrum model on controlled links."""
from pathlib import Path
import json
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
sys.path.insert(0,str(SIM))
from ns3_paths import ns3_root


def main():
    root = ns3_root()
    commands = json.loads((root/'cmake-cache/compile_commands.json').read_text())
    entry = next(v for v in commands if v['file'].endswith('/utils/perf/perf-io.cc'))
    command = entry.get('arguments') or shlex.split(entry['command'])
    obj = SIM/'build/test_building_vertical.o'
    binary = SIM/'build/test_building_vertical'
    command[command.index('-c')+1] = str(SIM/'test_building_vertical.cc')
    command[command.index('-o')+1] = str(obj)
    with (HERE/'logs/model_test_compile.log').open('w') as log:
        subprocess.run(command,cwd=entry['directory'],stdout=log,stderr=subprocess.STDOUT,check=True)
    lib = root/'build/lib'
    modules = ['spectrum','mobility','antenna','propagation','network','core']
    link = [command[0],str(obj),'-o',str(binary),'-L'+str(lib),'-Wl,-rpath,'+str(lib)]
    link += ['-l:libns3.44-'+m+'-default.so' for m in modules]
    subprocess.run(link,check=True)
    completed = subprocess.run([str(binary)],capture_output=True,text=True,check=True)
    result = json.loads(completed.stdout)
    (HERE/'model_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(completed.stdout)


if __name__=='__main__':
    main()
