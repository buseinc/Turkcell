"""Windows: voice capacity limit with the fast model (the step deneyler/29 could not finish in ns-3).

Same design as deneyler/29 stress steps (draw 701, azimuth 42, AMR 44 B every 20 ms, 3N voice users per
evaluation site placed from Experia TA, background = the 72 calibrated load users), N extended past 200.
Voice users are generated exactly as deneyler/29 prepare.voice_ues (same seed rule), in memory.
A cell is counted as overloaded when the PRB its users need exceeds the whole band (demand >= 1).
LOS states: 20 independent draws per step. Known bias (dogrulama.json): at N = 200 the fast model gives
0.81 mean PRB where ns-3 gave 0.72, so the limit found here is on the safe (low) side.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

import hizli_model as hm

HERE = Path(__file__).resolve().parent
D29 = HERE.parent/'29_ihtiyaca_gore_zamanlayici_2026-11-19'
STEPS = [100, 200, 250, 300, 350, 400, 500]
DRAWS = 20


def voice_users(n, plan, sites, load):
    corr = plan['correction']
    k0 = corr['model_fit_a_b'][0] - corr['experia_fit_a_b'][0]
    k1 = corr['model_fit_a_b'][1] - corr['experia_fit_a_b'][1]
    exp = pd.read_csv(HERE.parents[1]/'deneyler/13_hucre_imzasi_2026-11-15/experia_cells.csv.gz').dropna(subset=['AVG(TAAVG)'])
    exp['d'] = (exp['AVG(TAAVG)']*4.88).clip(100.0, 15000.0)
    rng = np.random.default_rng(701*1000 + n)
    rows = []
    for s in plan['eval_sites']:
        pool = exp.loc[exp.site == s, 'd'].to_numpy()
        for _ in range(3*n):
            d = float(pool[rng.integers(len(pool))])
            a = rng.uniform(0, 2*np.pi)
            rows.append({'x_m': sites.loc[s, 'x_m'] + d*np.cos(a), 'y_m': sites.loc[s, 'y_m'] + d*np.sin(a), 'z_m': 1.5,
                         'extra_loss_db': k0 + k1*np.log10(d), 'udp_interval_ms': 20.0, 'packet_size_bytes': 44.0,
                         'kind': 'voice', 'site': s})
    v = pd.DataFrame(rows)
    # round as the deneyler/29 CSV writer does, so positions (and the shadow hash) are identical
    v['x_m'] = v.x_m.map(lambda x: float(f'{x:.9f}'))
    v['y_m'] = v.y_m.map(lambda x: float(f'{x:.9f}'))
    v['extra_loss_db'] = v.extra_loss_db.map(lambda x: float(f'{x:.6f}'))
    bg = load.assign(packet_size_bytes=512.0)
    return pd.concat([v, bg[['x_m', 'y_m', 'z_m', 'extra_loss_db', 'udp_interval_ms', 'packet_size_bytes', 'kind']]], ignore_index=True)


def main():
    plan = json.loads((D29/'plan.json').read_text(encoding='utf-8'))
    sites = pd.read_csv(D29/'inputs/sites_S0TA_42.csv').set_index('site')
    sec = pd.read_csv(D29/'simulation/results/V200_draw701/sectors.csv')
    sec['x_m'] = sec.site.map(sites.x_m)
    sec['y_m'] = sec.site.map(sites.y_m)
    load = pd.read_csv(D29/'inputs/ues_FT_TA_701.csv').query('kind == "load"')
    ev = sec.role.to_numpy() == 'Evaluation'
    # check: N = 200 voice positions equal the deneyler/29 input file
    ref = pd.read_csv(D29/'inputs/ues_V200_701.csv').query('kind == "voice"')
    mine = voice_users(200, plan, sites, load).query('kind == "voice"')
    assert np.allclose(ref[['x_m', 'y_m', 'extra_loss_db']].to_numpy(), mine[['x_m', 'y_m', 'extra_loss_db']].to_numpy(), atol=1e-6)
    out = []
    for n in STEPS:
        ues = voice_users(n, plan, sites, load)
        net = hm.Network(sec, ues, 42)
        rng = np.random.default_rng(31000 + n)
        dem, over, s0, cq0 = [], [], [], []
        for _ in range(DRAWS):
            r = hm.solve(net, net.draw_los(rng), ues.packet_size_bytes.to_numpy(), ues.udp_interval_ms.to_numpy())
            dem.append(r['demand'][ev])
            over.append(np.mean(r['demand'][ev] >= 1.0))
            voice = (ues.kind == 'voice').to_numpy()
            s0.append(np.mean(r['sinr_db'][voice] < 0))
            cq0.append(np.mean(r['cqi'][voice] == 0))
        d = np.array(dem)
        row = {'voice_per_cell': n, 'eval_prb_mean': float(np.minimum(d, 1).mean()), 'eval_demand_max_cell': float(d.max(1).mean()),
               'overloaded_cell_share': float(np.mean(over)), 'overloaded_cells_of_24': float(np.mean(over)*24),
               'voice_sinr_below0': float(np.mean(s0)), 'voice_cqi0_unservable': float(np.mean(cq0))}
        out.append(row)
        print({k: round(v, 3) for k, v in row.items()}, flush=True)
    (HERE/'kapasite_siniri.json').write_text(json.dumps({'steps': out, 'rule': __doc__}, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
