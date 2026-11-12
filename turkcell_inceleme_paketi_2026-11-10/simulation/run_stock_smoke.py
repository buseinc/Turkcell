"""Build and run the installed ns-3.44 LTE+EPC example from WSL.

Only configured build products in NS3 and results in this project are written.
The simulator's source and configuration are not changed.
"""
from pathlib import Path
import json
import os
import subprocess
import time

HERE=Path(__file__).resolve().parent
NS3=Path('/home/umut/ns-allinone-3.44/ns-3.44')
OUT=HERE/'results'/'stock_smoke'


def run_logged(args, cwd, logfile, env=None):
    print('RUN', ' '.join(map(str,args)),flush=True)
    with logfile.open('w') as stream:
        subprocess.run([str(a) for a in args],cwd=cwd,stdout=stream,
                       stderr=subprocess.STDOUT,env=env,check=True)


def pdcp_received(path):
    lines=path.read_text().splitlines()
    header=lines[0].lstrip('% ').split()
    index=header.index('RxBytes')
    return sum(int(float(line.split()[index])) for line in lines[1:]
               if line.strip() and not line.startswith('%'))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert (NS3/'VERSION').read_text().strip()=='3.44'
    started=time.perf_counter()
    run_logged([NS3/'ns3','build','lena-simple-epc','-j','2'],NS3,OUT/'build.log')
    executables=[p for p in (NS3/'build').rglob('ns3.44-lena-simple-epc-default') if p.is_file()]
    if len(executables)!=1:
        raise RuntimeError(f'Expected one example executable; found {executables}')
    env=os.environ.copy()
    env['LD_LIBRARY_PATH']=str(NS3/'build/lib')+':'+env.get('LD_LIBRARY_PATH','')
    run_logged([executables[0]],OUT,OUT/'run.log',env)
    received={name:pdcp_received(OUT/name) for name in ['DlPdcpStats.txt','UlPdcpStats.txt']}
    assert all(v>0 for v in received.values()),received
    report={'ns3_version':'3.44','stack':'classic LTE/EPC','example':'lena-simple-epc',
            'source':str(NS3/'src/lte/examples/lena-simple-epc.cc'),
            'executable':str(executables[0]),'simulation_seconds':1.1,
            'physical_sites':2,'ues':2,'attachment':'manual pairing (stock example)',
            'received_pdcp_bytes':received,'passed':True,
            'build_and_run_wall_seconds':time.perf_counter()-started,
            'meaning':'Software smoke test, not geographical or radio calibration.'}
    (OUT/'result.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
    # Capture exact API/trace units and external compilation files for next step.
    lines=(NS3/'src/lte/model/lte-ue-phy.cc').read_text().splitlines()
    print('UE PHY TRACE IMPLEMENTATION\n'+'\n'.join(lines[540:620]),flush=True)
    print('CMAKE PACKAGES', [str(p) for p in (NS3/'cmake-cache').rglob('*Config.cmake')],flush=True)
    print('COMPILE COMMANDS',list(map(str,NS3.glob('**/compile_commands.json'))),flush=True)


if __name__=='__main__':
    main()
