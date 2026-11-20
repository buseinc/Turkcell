"""Windows: does the fast model (hizli_model.py) give the same answers as the deneyler/29 ns-3 runs?

Predeclared checks (written before the full comparison was run; only the RSRP check of FT_TA_draw701
had been looked at, while debugging the site coordinates):
1. RSRP: serving-link RSRP equals ns-3 within 0.01 dB for >= 99 % of users, every case.
2. Serving cell: share of users served by the same cell as in ns-3 (reported; LOS states are random in
   both, so 100 % is not expected).
3. Cell load: mean PRB use of the 24 evaluation cells within +-0.05 of ns-3 in every case and per-cell
   mean absolute error <= 0.10.
4. SINR: per evaluation site, mean SINR of its users within 1.5 dB of ns-3 on average (MAE) in every
   case; and against Experia the held-out SINR MAE of the fast model within 1 dB of ns-3's.
Fast-model numbers are the mean over 20 LOS draws (every link drawn afresh; an earlier version kept
ns-3's serving-link state and redrew only the others, which gave the fast model a second chance to find a
stronger cell and biased its SINR up by ~1.4 dB - a flaw of the comparison, fixed before the final run). Cases: the 3 validation draws (normal load) and the
4 voice steps V25-V200 of deneyler/29.
Two versions of check 4: "formül" = ns-3's serving cells and ns-3's measured PRB use put into the fast
SINR formula (tests the formula alone); "tam" = everything from the fast model.
"""
from pathlib import Path
import json
import statistics
import time

import numpy as np
import pandas as pd

import hizli_model as hm

HERE = Path(__file__).resolve().parent
D29 = HERE.parent/'29_ihtiyaca_gore_zamanlayici_2026-11-19'
RES = D29/'simulation/results'
DRAWS = 20


def cases():
    p = json.loads((D29/'plan.json').read_text(encoding='utf-8'))
    for c in p['validation_cases'] + p['cases']:
        if (RES/c['name']/'prb_usage.csv').exists():
            yield c, p


def load_case(c):
    f = RES/c['name']
    sec = pd.read_csv(f/'sectors.csv')
    sites = pd.read_csv(D29/'inputs'/c['sites_file']).set_index('site')
    sec['x_m'] = sec.site.map(sites.x_m)     # sectors.csv has only 12 digits; the shadow hash needs the input
    sec['y_m'] = sec.site.map(sites.y_m)
    ues = pd.read_csv(D29/'inputs'/c['ue_file'])
    rs = pd.read_csv(f/'radio_samples.csv')
    rs = rs[rs.time_s >= 1.0]
    final = pd.read_csv(f/'ues.csv').set_index('ue_id').synthetic_cell_id
    rs = rs[rs.synthetic_cell_id.to_numpy() == final.reindex(rs.ue_id).to_numpy()]
    ns3 = rs.groupby('ue_id').agg(rsrp=('rsrp_dbm', 'median'), sinr=('sinr_db', 'mean'))
    ns3['cell'] = final.reindex(ns3.index)
    prb = pd.read_csv(f/'prb_usage.csv').set_index('synthetic_cell_id').dl_prb_utilization
    return sec, ues, ns3, prb


def site_mean(sec, ue_idx, cell_idx, value, only=None):
    d = pd.DataFrame({'ue': ue_idx, 'site': sec.site.to_numpy()[cell_idx], 'sector': sec.sector.to_numpy()[cell_idx], 'v': value})
    if only is not None:
        d = d[d.ue < only]
    return d.groupby(['site', 'sector']).v.mean().groupby('site').mean()


def main():
    targets = pd.read_csv(D29/'inputs/targets.csv').set_index('site')
    out = []
    for c, plan in cases():
        t0 = time.time()
        sec, ues, ns3, prb = load_case(c)
        net = hm.Network(sec, ues, c['shadow_seed'])
        col = {v: i for i, v in enumerate(sec.synthetic_cell_id)}
        u = ns3.index.to_numpy()
        cell = np.array([col[v] for v in ns3.cell])
        L = net.fixed_db[u, cell] - net.los_db[u, cell]
        N = net.fixed_db[u, cell] - net.nlos_db[u, cell]
        err = np.minimum(abs(L - ns3.rsrp.to_numpy()), abs(N - ns3.rsrp.to_numpy()))
        serving_los = abs(L - ns3.rsrp.to_numpy()) < abs(N - ns3.rsrp.to_numpy())
        size = ues.packet_size_bytes.to_numpy(float) if 'packet_size_bytes' in ues else np.full(len(ues), 512.0)
        interval = ues.udp_interval_ms.to_numpy(float)
        eval_cells = sec.role.to_numpy() == 'Evaluation'
        ns3_load = prb.reindex(sec.synthetic_cell_id).to_numpy()
        rng = np.random.default_rng(1000 + c['shadow_seed'])
        same, loads, sinr_full, sinr_formula, below0, full_sites, exp_sites = [], [], [], [], [], [], []
        for _ in range(DRAWS):
            los = net.draw_los(rng)                        # every link drawn afresh: an independent realization
            r = hm.solve(net, los, size, interval, rng=rng)
            same.append(np.mean(r['serving'][u] == cell))
            loads.append(r['load'])
            sinr_full.append(r['sinr_db'])
            below0.append(np.mean(r['sinr_db'] < 0))
            full_sites.append(site_mean(sec, np.arange(len(ues)), r['serving'], r['sinr_db']))
            exp_sites.append(site_mean(sec, np.arange(len(ues)), r['serving'], r['sinr_db'], 256))
            # formula test: ns-3's serving cells and PRB use. What ns-3 tells us is kept: the serving link's
            # LOS state (from its RSRP) and that no other cell was stronger (ns-3 users sit on their
            # strongest cell, measurements.csv serving_gap_db = 0), so links that would beat it are NLOS.
            lf = los.copy()
            lf[u, cell] = serving_los
            rf_all = net.rsrp(lf)[u]
            beat = rf_all > rf_all[np.arange(len(u)), cell][:, None] + 1e-9
            lf[u[np.where(beat)[0]], np.where(beat)[1]] = False
            rf, _ = hm.sinr(net.rsrp(lf)[u], cell, ns3_load)
            sinr_formula.append(rf)
        load = np.mean(loads, 0)
        full = np.concatenate(sinr_full)
        formula = np.mean(sinr_formula, 0)
        ns3_site = site_mean(sec, u, cell, ns3.sinr.to_numpy())
        f_site = site_mean(sec, u, cell, formula)
        full_site = pd.concat(full_sites, axis=1).mean(1)
        ev = [s for s in plan['eval_sites']]
        row = {'case': c['name'], 'users': int(len(ues)),
               'rsrp_match_share': float(np.mean(err < 0.01)), 'rsrp_max_err_db': float(err.max()),
               'same_serving_cell_share': float(np.mean(same)),
               'eval_prb_ns3': float(np.nanmean(ns3_load[eval_cells])), 'eval_prb_fast': float(load[eval_cells].mean()),
               'eval_prb_cell_mae': float(np.nanmean(abs(load - ns3_load)[eval_cells])),
               'sinr_site_mae_formula_db': float(np.mean([abs(f_site[s] - ns3_site[s]) for s in ev if s in ns3_site])),
               'sinr_site_mae_full_db': float(np.mean([abs(full_site[s] - ns3_site[s]) for s in ev if s in ns3_site and s in full_site])),
               'sinr_median_ns3_db': float(ns3.sinr.median()), 'sinr_median_fast_db': float(np.median(full)),
               'below0_ns3': float(np.mean(ns3.sinr < 0)), 'below0_fast': float(np.mean(below0)),
               'seconds': round(time.time() - t0, 1)}
        if c['name'].startswith('FT_TA'):
            m = {'ns3': site_mean(sec, u, cell, ns3.sinr.to_numpy(), 256),
                 'fast': pd.concat(exp_sites, axis=1).mean(1)}
            for k, v in m.items():
                for split in ['train', 'holdout']:
                    ss = targets[targets.split == split].index
                    row[f'experia_sinr_mae_{split}_{k}'] = float(np.mean([abs(v[s] - targets.sinr_target[s]) for s in ss if s in v]))
        out.append(row)
        print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}, ensure_ascii=False), flush=True)
    checks = {
        '1_rsrp': all(r['rsrp_match_share'] >= 0.99 for r in out),
        '3_prb_mean': all(abs(r['eval_prb_fast'] - r['eval_prb_ns3']) <= 0.05 for r in out),
        '3_prb_cell_mae': all(r['eval_prb_cell_mae'] <= 0.10 for r in out),
        '4_sinr_site_full': all(r['sinr_site_mae_full_db'] <= 1.5 for r in out),
        '4_experia_holdout': statistics.mean(r['experia_sinr_mae_holdout_fast'] for r in out if 'experia_sinr_mae_holdout_fast' in r)
                             - statistics.mean(r['experia_sinr_mae_holdout_ns3'] for r in out if 'experia_sinr_mae_holdout_ns3' in r) <= 1.0,
    }
    (HERE/'dogrulama.json').write_text(json.dumps({'checks': checks, 'cases': out, 'rule': __doc__}, indent=2, ensure_ascii=False), encoding='utf-8')
    print(checks)


if __name__ == '__main__':
    main()
