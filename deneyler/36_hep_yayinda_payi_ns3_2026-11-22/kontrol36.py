"""Windows: checks of deneyler/36 KURALLAR.md (with the correction). Usage: py kontrol36.py 1|2. Writes kontrol<n>.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
RES = HERE/'simulation/results'
D33 = HERE.parent/'33_kesinti_ns3_2026-11-20'
D34 = HERE.parent/'34_yol_hareketi_2026-11-21'
sys.path.insert(0, str(HERE.parent/'35_bolge_secimi_2026-11-21'))
import sinamalar as sn  # noqa: E402
import alan  # noqa: E402
hm = alan.hm
F = 0.03


def k1():
    out = {}
    for f in ['radio_samples.csv', 'ues.csv', 'prb_usage.csv', 'voice.csv', 'DlRxPhyStats.txt', 'sectors.csv']:
        a = (RES/'R1_f0'/f).read_bytes().replace(b'\r\n', b'\n')
        b = (D34/'simulation/results/R1_regresyon'/f).read_bytes().replace(b'\r\n', b'\n')
        out[f] = a == b
    return {'files_equal': out, 'pass': all(out.values())}


def run_data(name):
    f = RES/name
    sec = pd.read_csv(f/'sectors.csv')
    sites = pd.read_csv(D33/'inputs/sites_S0TA_42.csv').set_index('site')
    sec['x_m'], sec['y_m'] = sec.site.map(sites.x_m), sec.site.map(sites.y_m)
    final = pd.read_csv(f/'ues.csv').set_index('ue_id').synthetic_cell_id
    rs = pd.read_csv(f/'radio_samples.csv')
    rs = rs[(rs.time_s >= 1.0) & (rs.synthetic_cell_id.to_numpy() == final.reindex(rs.ue_id).to_numpy())]
    sinr = rs.groupby('ue_id').sinr_db.apply(lambda x: 10*np.log10(np.mean(10**(x/10))))
    prb = pd.read_csv(f/'prb_usage.csv').set_index('synthetic_cell_id').dl_prb_utilization
    return sec, final, sinr, prb


def k2():
    ues = pd.read_csv(D33/'inputs/ues_V25_701.csv')
    res = {}
    for name, f in [('R2b_f0', 0.0), ('R2b_f003', F)]:
        sec, final, sinr, prb = run_data(name)
        net = alan.Network34(sec, ues, 42)
        r = net.rsrp(net.draw_los())
        col = {v: i for i, v in enumerate(sec.synthetic_cell_id)}
        u = sinr.index.to_numpy()
        cell = np.array([col[final[x]] for x in u])
        load = prb.reindex(sec.synthetic_cell_id).fillna(0).to_numpy()
        model = sn.sinr_on(r[u], cell, load, f)
        d = pd.DataFrame({'site': sec.site.to_numpy()[cell], 'sector': sec.sector.to_numpy()[cell],
                          'ns3': sinr.to_numpy(), 'fast': model})
        ev = sec[sec.role == 'Evaluation'].site.unique()
        site = d.groupby(['site', 'sector'])[['ns3', 'fast']].mean().groupby('site').mean().reindex(ev).dropna()
        res[name] = {'site_mae_db': float((site.ns3 - site.fast).abs().mean()),
                     'eval_mean_ns3': float(d[d.site.isin(ev)].ns3.mean()), 'eval_mean_fast': float(d[d.site.isin(ev)].fast.mean()),
                     'users': int(len(d)), 'eval_prb': float(prb.reindex(sec[sec.role == 'Evaluation'].synthetic_cell_id).mean())}
    drop_ns3 = res['R2b_f0']['eval_mean_ns3'] - res['R2b_f003']['eval_mean_ns3']
    drop_fast = res['R2b_f0']['eval_mean_fast'] - res['R2b_f003']['eval_mean_fast']
    res['drop_ns3_db'], res['drop_fast_db'] = float(drop_ns3), float(drop_fast)
    res['pass_a'] = bool(res['R2b_f003']['site_mae_db'] <= 1.5)
    res['pass_b'] = bool(abs(drop_ns3 - drop_fast) <= 0.5)
    res['pass'] = res['pass_a'] and res['pass_b']
    return res


if __name__ == '__main__':
    n = sys.argv[1]
    out = {'1': k1, '2': k2}[n]()
    (HERE/f'kontrol{n}.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(json.dumps(out, indent=1))
