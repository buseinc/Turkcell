"""WSL: build a private copy of libns3.44-lte with transmitter EVM (experiment 26).

The installed ns-3.44 is not modified. ns-3 was built with -fno-semantic-interposition, so overriding a
library function from the executable does not work; instead two library sources are patched and relinked.
Every change is guarded by g_lteEvm2 > 0 (default 0: identical to the original code paths).

EVM (3GPP TS 36.104 Table 6.5.2-1, 64QAM 8 %) is distortion of the wanted signal, SINR_eff = 1/(1/SINR + EVM^2):
1. src/lte/model/lte-interference.cc, ConditionallyEvaluateChunk: the SINR given to the SINR chunk processors
   (data decoding / error model, control SINR, UL) becomes rx / (interf + EVM^2 * rx). The interference given
   to the interference chunk processors is unchanged, so RSRQ and interference reports are unchanged.
2. src/lte/model/lte-ue-phy.cc, GenerateMixedCqiReport: the mixed SINR (RS power / PDSCH interference) used
   for CQI and for the reported RSRP/SINR trace gets the same formula per RB. (The scenario uses mixed CQI;
   then the control SINR of 1 is not used for CQI, so EVM is counted once.)
The library is linked from ns-3's own 126 other lte object files plus the two patched objects, with ns-3's
own link libraries and the same soname, into build/lte_private/.
"""
from pathlib import Path
import json
import re
import shlex
import subprocess

from ns3_paths import ns3_root

HERE = Path(__file__).resolve().parent
OUT = HERE/'build/lte_private'
NS3 = ns3_root()
CACHE = NS3/'cmake-cache'

INTERF_OLD = '''        SpectrumValue sinr = (*m_rxSignal) / interf;
'''
INTERF_NEW = '''        SpectrumValue sinr = (*m_rxSignal) / interf;
        if (g_lteEvm2 > 0)
        {
            // experiment 26: transmitter EVM distortion of the wanted signal
            sinr = (*m_rxSignal) / (interf + (*m_rxSignal) * g_lteEvm2);
        }
'''
UEPHY_OLD = '''    /*
     * some RBs are not used in PDSCH and their SINR is very high
'''
UEPHY_NEW = '''    if (g_lteEvm2 > 0)
    {
        // experiment 26: transmitter EVM, SINR_eff = 1 / (1/SINR + EVM^2) per RB
        for (auto it = mixedSinr.ValuesBegin(); it != mixedSinr.ValuesEnd(); ++it)
        {
            *it = 1.0 / (1.0 / (*it) + g_lteEvm2);
        }
    }

''' + UEPHY_OLD
NS_OPEN = 'namespace ns3\n{\n'
PATCHES = {
    'lte-interference': [(INTERF_OLD, INTERF_NEW),
                         (NS_OPEN, NS_OPEN + '\ndouble g_lteEvm2 = 0.0; // experiment 26, set by the scenario\n')],
    'lte-ue-phy': [(UEPHY_OLD, UEPHY_NEW),
                   (NS_OPEN, NS_OPEN + '\nextern double g_lteEvm2; // experiment 26, defined in lte-interference.cc\n')],
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    commands = json.loads((CACHE/'compile_commands.json').read_text())
    patched_objs = {}
    for name, edits in PATCHES.items():
        src = (NS3/f'src/lte/model/{name}.cc').read_text()
        for old, new in edits:
            assert src.count(old) == 1, (name, old)
            src = src.replace(old, new)
        patched = OUT/f'{name}-evm.cc'
        patched.write_text(src)
        entry = next(c for c in commands if c['file'].endswith(f'/src/lte/model/{name}.cc'))
        cmd = entry.get('arguments') or shlex.split(entry['command'])
        cmd[cmd.index('-c')+1] = str(patched)
        cmd.insert(1, '-I' + str(NS3/'src/lte/model'))  # the originals include headers by relative path
        obj = OUT/f'{name}-evm.o'
        cmd[cmd.index('-o')+1] = str(obj)
        subprocess.run(cmd, cwd=entry['directory'], check=True)
        patched_objs[f'{name}.cc.o'] = str(obj)

    ninja = (CACHE/'build.ninja').read_text()
    m = re.search(r'^build \S*libns3\.44-lte-default\.so: CXX_SHARED_LIBRARY_LINKER__lte_default (.*?)(?:\s\|\||\s\||\n)', ninja, re.M)
    objs = [o for o in m.group(1).split() if o.endswith('.o')]
    block = ninja[m.end():ninja.index('\n\n', m.end())]
    var = dict(re.findall(r'^\s+(\w+) = (.*)$', block, re.M))
    for k in patched_objs:
        assert sum(o.endswith('/' + k) for o in objs) == 1, k
    keep = [str(CACHE/o) for o in objs if not any(o.endswith('/' + k) for k in patched_objs)]
    lib = OUT/'libns3.44-lte-default.so'
    link = ['/usr/bin/c++', '-fPIC', *shlex.split(var.get('LANGUAGE_COMPILE_FLAGS', '')), *shlex.split(var.get('LINK_FLAGS', '')),
            '-shared', '-Wl,-soname,libns3.44-lte-default.so', '-o', str(lib), *keep, *patched_objs.values(),
            *shlex.split(var.get('LINK_PATH', '')), *shlex.split(var['LINK_LIBRARIES'])]
    subprocess.run(link, check=True)
    (OUT/'manifest.json').write_text(json.dumps({'objects_from_ns3': len(keep), 'patched': patched_objs,
                                                  'ns3_root': str(NS3)}, indent=2))
    print('built', lib, len(keep), '+', len(patched_objs), 'objects')


if __name__ == '__main__':
    main()
