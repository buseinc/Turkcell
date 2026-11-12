"""Inspect the existing WSL ns-3 installation without changing it."""
from pathlib import Path
import json
import platform
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
NS3=Path('/home/umut/ns-allinone-3.44/ns-3.44')


def excerpt(path, needles, radius=4):
    lines=(NS3/path).read_text().splitlines()
    keep=set()
    for i,line in enumerate(lines):
        if any(n in line for n in needles):
            keep.update(range(max(0,i-radius),min(len(lines),i+radius+1)))
    return '\n'.join(f'{i+1}: {lines[i]}' for i in sorted(keep))


def main():
    info={'platform':platform.platform(),'ns3_root':str(NS3),
          'ns3_version':(NS3/'VERSION').read_text().strip(),
          'tools':{},'cmake_configs':[], 'pkgconfig_files':[]}
    for name,args in [('g++',['--version']),('cmake',['--version']),
                      ('ninja',['--version']),('python3',['--version']),
                      ('pkg-config',['--version'])]:
        path=shutil.which(name)
        info['tools'][name]={'path':path}
        if path:
            p=subprocess.run([path]+args,capture_output=True,text=True,check=False)
            info['tools'][name]['version']=p.stdout.splitlines()[0] if p.stdout else p.stderr.strip()
    info['cmake_configs']=[str(p) for folder in [NS3/'build',NS3/'cmake-cache']
                           for p in folder.rglob('*Config.cmake')]
    info['pkgconfig_files']=[str(p) for p in (NS3/'build').rglob('*lte.pc')]
    info['lte_library_present']=any((NS3/'build/lib').glob('libns3.44-lte-default.so'))
    cache=NS3/'cmake-cache/CMakeCache.txt'
    info['build_options']=[l for l in cache.read_text().splitlines()
                           if any(key in l for key in ['NS3_EXAMPLES:','NS3_TESTS:','CMAKE_BUILD_TYPE:'])]
    (HERE/'environment.json').write_text(json.dumps(info,indent=2))
    print(json.dumps(info,indent=2))
    for name,needles in [
        ('src/antenna/model/cosine-antenna-model.cc',['HorizontalBeamwidth','VerticalBeamwidth','MaxGain','Orientation']),
        ('src/lte/helper/lte-helper.h',['SetPathlossModel','Attach(NetDeviceContainer','SetEnbAntennaModel']),
        ('src/lte/model/lte-ue-phy.h',['RsrpSinrTracedCallback','ReportCurrentCellRsrpSinr']),
        ('src/lte/model/lte-ue-phy.cc',['m_reportCurrentCellRsrpSinrTrace(','rsrpSum','ReportCurrentCellRsrpSinr']),
    ]:
        print('\nSOURCE',name)
        print(excerpt(name,needles))


if __name__=='__main__':
    main()
