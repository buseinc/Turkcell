from pathlib import Path

ROOT=Path('/home/umut/ns-allinone-3.44/ns-3.44')
for name in ['src/propagation/model/okumura-hata-propagation-loss-model.cc',
             'src/propagation/model/cost231-propagation-loss-model.cc',
             'src/lte/model/lte-ue-phy.h', 'src/lte/model/lte-ue-phy.cc']:
    path=ROOT/name
    if not path.exists():
        print('ABSENT',name); continue
    lines=path.read_text().splitlines()
    print('\nFILE',name)
    if 'propagation' in name:
        print('\n'.join(lines[:240]))
    else:
        keep=set()
        for i,line in enumerate(lines):
            if any(x in line for x in ['ReportUeMeasurements','m_reportUeMeasurements',
                                       'UeMeasurementsTracedCallback','rsrp_dBm =','rsrq_dB =']):
                keep.update(range(max(0,i-6),min(len(lines),i+12)))
        print('\n'.join(f'{i+1}: {lines[i]}' for i in sorted(keep)))
