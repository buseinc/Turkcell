"""Windows: score the ns-3 runs K0-K3 with the predeclared radio criteria (prepare.py) and compare with the
fast model on the same users (20 LOS draws, 5-95 % range). Writes analiz.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
sys.path.insert(0, str(DEN/'32_kesinti_hazirligi_2026-11-20'))
import senaryo as sc  # noqa: E402
import hizli_model as hm  # noqa: E402  (path added by senaryo)

RES = HERE/'simulation/results'
SINR_CQI0 = -6.7
PRB_FULL = 0.95


def db_mean(x):
    return 10*np.log10(np.mean(10**(np.asarray(x)/10)))


def ns3(name, plan, ues_in):
    f = RES/name
    u = pd.read_csv(f/'ues.csv')
    sec = pd.read_csv(f/'sectors.csv')
    prb = pd.read_csv(f/'prb_usage.csv').merge(sec[['synthetic_cell_id', 'site', 'role']], on='synthetic_cell_id')
    rs = pd.read_csv(f/'radio_samples.csv')
    g = rs.groupby('ue_id')
    per = pd.DataFrame({'sinr': g.sinr_db.apply(db_mean), 'rsrp': g.rsrp_dbm.apply(db_mean)})
    u = u.join(per, on='ue_id').merge(ues_in[['ue_id', 'home_site']], on='ue_id')
    no_srv = (u.rrc_connected != 1) | u.sinr.isna() | (u.sinr < SINR_CQI0)
    weak = u.rsrp < sc.REFSENS_RE_DBM
    off = plan['scenarios'][name]['off']
    out = {}
    for label, m in [('all', np.ones(len(u), bool)), ('around_off', u.home_site.isin(off).to_numpy())]:
        if m.sum() == 0:
            continue
        out[label] = {'users': int(m.sum()), 'no_service': float(no_srv[m].mean()), 'weak': float(weak[m].mean()),
                      'not_connected': int((u.rrc_connected[m] != 1).sum())}
    ev = prb[prb.role == 'Evaluation']
    out['eval_prb'] = float(ev.dl_prb_utilization.mean())
    out['eval_cells_full'] = int((ev.dl_prb_utilization >= PRB_FULL).sum())
    out['eval_cells'] = int(len(ev))
    out['max_cell_prb'] = float(prb.dl_prb_utilization.max())
    out['sinr_median_db'] = float(u.sinr.median())
    # secondary, not a service criterion (ns-3 has no outer-loop link adaptation): delivered share of sent bytes
    out['delivered_share_secondary'] = float(u.dl_bytes.sum() / (len(u)*512*(4.0 - 0.3)*1000/plan['udp_interval_ms']))
    # cell PRB per site, for the sites next to the removed ones
    out['prb_by_site'] = prb.groupby('site').dl_prb_utilization.mean().round(3).to_dict()
    return out


def fast(plan, ues_in, b):
    net = b.network(ues_in)
    n = len(ues_in)
    pk, iv = np.full(n, 512.0), np.full(n, plan['udp_interval_ms'])
    res = {}
    for k, v in plan['scenarios'].items():
        mask_on = b.cells_on(v['off'])
        around = ues_in.home_site.isin(v['off']).to_numpy()
        rows = []
        for i in range(20):
            los = net.draw_los(np.random.default_rng(1000 + i))
            r = hm.solve(net, los, pk, iv, cell_on=mask_on)
            o = {'all_' + a: c for a, c in sc.outcome(b, ues_in, r).items()}
            if around.any():
                o.update({'around_' + a: c for a, c in sc.outcome(b, ues_in, r, around).items()})
            rows.append(o)
        d = pd.DataFrame(rows)
        res[k] = {c: [float(d[c].quantile(.05)), float(d[c].median()), float(d[c].quantile(.95))] for c in d.columns}
    return res


def main():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    ues_in = pd.read_csv(HERE/'inputs/ues_quake_42.csv')
    out = {'ns3': {k: ns3(k, plan, ues_in) for k in plan['scenarios']}}
    b = sc.Builder(42, plan['quake'])
    out['fast_model_5_50_95'] = fast(plan, ues_in, b)
    k0 = out['ns3']['K0']['eval_prb']
    out['k0_load_accepted'] = bool(0.15 <= k0 <= 0.35)
    (HERE/'analiz.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    for k, v in out['ns3'].items():
        f = out['fast_model_5_50_95'][k]
        line = f"{k}: ns3 no_srv {v['all']['no_service']:.3f} weak {v['all']['weak']:.3f} prb {v['eval_prb']:.3f} full {v['eval_cells_full']}"
        line += f" | fast no_srv {f['all_no_service']} prb {f['all_eval_prb']}"
        if 'around_off' in v:
            line += f"\n   around: ns3 no_srv {v['around_off']['no_service']:.3f} weak {v['around_off']['weak']:.3f} n {v['around_off']['users']}"
            line += f" | fast no_srv {f['around_no_service']} weak {f['around_weak']}"
        print(line)
    print('K0 load accepted', out['k0_load_accepted'])


if __name__ == '__main__':
    main()
