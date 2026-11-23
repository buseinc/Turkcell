"""Windows: score the Edremit ns-3 runs E0-E2 with the KURALLAR.md criteria (as deneyler/33 analiz.py) and put
them next to Sindirgi (deneyler/33 analiz.json). Writes analiz.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
RES = HERE/'simulation/results'
D33 = HERE.parent/'33_kesinti_ns3_2026-11-20'
REFSENS = -91.0 - 10*np.log10(1200)


def db_mean(x):
    return 10*np.log10(np.mean(10**(np.asarray(x)/10)))


def score(name, off, ues_in):
    f = RES/name
    u = pd.read_csv(f/'ues.csv').merge(ues_in[['ue_id', 'kind', 'home_site']], on='ue_id')
    sec = pd.read_csv(f/'sectors.csv')
    prb = pd.read_csv(f/'prb_usage.csv').merge(sec[['synthetic_cell_id', 'site', 'role']], on='synthetic_cell_id')
    rs = pd.read_csv(f/'radio_samples.csv')
    g = rs.groupby('ue_id')
    u = u.join(pd.DataFrame({'sinr': g.sinr_db.apply(db_mean), 'rsrp': g.rsrp_dbm.apply(db_mean)}), on='ue_id')
    u = u[u.kind == 'quake']
    nos = (u.rrc_connected != 1) | u.sinr.isna() | (u.sinr < -6.7)
    weak = u.rsrp < REFSENS
    out = {'all': {'users': int(len(u)), 'no_service': float(nos.mean()), 'weak': float(weak.mean())}}
    m = u.home_site.isin(off).to_numpy()
    if m.any():
        out['around_off'] = {'users': int(m.sum()), 'no_service': float(nos[m].mean()), 'weak': float(weak[m].mean()),
                             'not_connected': int((u.rrc_connected[m] != 1).sum()), 'sinr_median': float(u.sinr[m].median())}
    ev = prb[prb.role == 'Evaluation']
    out['eval_prb'] = float(ev.dl_prb_utilization.mean())
    out['eval_cells_full'] = int((ev.dl_prb_utilization >= 0.95).sum())
    out['max_prb_eval'] = float(ev.dl_prb_utilization.max())
    out['cells_full_any'] = prb[prb.dl_prb_utilization >= 0.95][['site', 'role']].to_dict('records')
    return out


def main():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    ues_in = pd.read_csv(HERE/'inputs/ues_quake.csv')
    out = {k: score(k, v['off'], ues_in) for k, v in plan['scenarios'].items()}
    # the same users with their sites ON (E0) - baseline for the around-off numbers
    e0 = score('E0', [], ues_in)
    for k, v in plan['scenarios'].items():
        if v['off']:
            base = score('E0', v['off'], ues_in)
            out[k]['around_off_when_on'] = base.get('around_off')
    s33 = json.loads((D33/'analiz.json').read_text(encoding='utf-8'))['ns3']
    out['sindirgi_deney33'] = {k: {'around_off_no_service': v.get('around_off', {}).get('no_service'),
                                   'all_no_service': v['all']['no_service'], 'eval_prb': v['eval_prb']} for k, v in s33.items()}
    (HERE/'analiz.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    for k in plan['scenarios']:
        print(k, json.dumps({kk: vv for kk, vv in out[k].items() if kk != 'cells_full_any'}, ensure_ascii=False))
    print('Sindirgi', out['sindirgi_deney33'])


if __name__ == '__main__':
    main()
