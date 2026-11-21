"""Windows: L25 check 2 (prepare.py rule). For voice users with mean reported SINR > 3 dB at light load
(deneyler/29 V25 inputs), share of DL transport blocks received in error (ns-3 DlRxPhyStats.txt).
CQI in ns-3 targets 10 % BLER on the first transmission, so first transmissions (rv 0) are the main number.
Usage: py l25_kontrol.py [L25|L25_smoke]. Writes l25_kontrol.json (full run only)."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
name = sys.argv[1] if len(sys.argv) > 1 else 'L25'
F = HERE/'simulation/results'/name
D29 = HERE.parent/'29_ihtiyaca_gore_zamanlayici_2026-11-19/simulation/results/V25_draw701'


def db_mean(x):
    return 10*np.log10(np.mean(10**(np.asarray(x)/10)))


u = pd.read_csv(F/'ues.csv')
inp = pd.read_csv(HERE/'inputs/ues_V25_701.csv')[['ue_id', 'voice']]
rs = pd.read_csv(F/'radio_samples.csv')
sinr = rs.groupby('ue_id').sinr_db.apply(db_mean).rename('sinr')
u = u.merge(inp, on='ue_id').join(sinr, on='ue_id')
tb = pd.read_csv(F/'DlRxPhyStats.txt', sep='\t')
tb.columns = [c.lstrip('% ').strip() for c in tb.columns]
tb = tb.merge(u[['imsi', 'ue_id', 'voice', 'sinr']], left_on='IMSI', right_on='imsi')
v = pd.read_csv(F/'voice.csv')
out = {'run': name, 'tbs': int(len(tb))}
if name == 'L25':
    out['check1_voice_csv_equal_to_29'] = (F/'voice.csv').read_bytes() == (D29/'voice.csv').read_bytes()
bins = [-99, 0, 3, 10, 99]
labels = ['<0', '0-3', '3-10', '>10']
rows = []
for kind, m in [('voice', tb.voice == 1), ('other', tb.voice != 1)]:
    t = tb[m].assign(band=pd.cut(tb[m].sinr, bins, labels=labels))
    for b, g in t.groupby('band', observed=True):
        f = g[g.rv == 0]
        rows.append({'users': kind, 'sinr_band_db': b, 'ues': int(g.ue_id.nunique()), 'tbs_first': int(len(f)),
                     'err_first_tx': float(1 - f.correct.mean()) if len(f) else None,
                     'err_all_tx': float(1 - g.correct.mean()), 'mean_mcs_first': float(f.mcs.mean()) if len(f) else None})
out['by_band'] = rows
good = tb[(tb.voice == 1) & (tb.sinr > 3) & (tb.rv == 0)]
out['check2_err_first_tx_voice_sinr_gt3'] = float(1 - good.correct.mean())
out['check2_tbs'] = int(len(good))
out['check2_ues'] = int(good.ue_id.nunique())
# packets: users that fail the ITU 98 % on-time rule among the same users
vv = v.merge(u[['ue_id', 'sinr', 'voice']], on='ue_id')
vv = vv[(vv.voice == 1) & (vv.sent > 0)]
out['fail_itu_voice_sinr_gt3'] = float(((vv.on_time/vv.sent) < 0.98)[vv.sinr > 3].mean())
print(json.dumps(out, indent=1, default=str))
if name == 'L25':
    (HERE/'l25_kontrol.json').write_text(json.dumps(out, indent=1, default=str), encoding='utf-8')
