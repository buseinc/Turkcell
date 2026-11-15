"""Compare the analytical link budget with native ns-3 per-UE results (experiments 08 and 09).

Acceptance (written before looking at the comparison):
- RSRP and RSRQ: max |error| < 0.01 dB and serving sector identical for all measurement UEs.
- Loaded SINR: the method is usable for maps if, for every load level and draw,
  median |error| <= 1 dB and the site-level mean (as used vs Experia) differs by <= 1 dB at
  every evaluation site. The better of 'mean' / 'mc' is used; if neither passes, maps show
  RSRP/serving sector only and SINR maps are not drawn.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from radio_model import received_power_w, link_metrics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D09 = ROOT / 'deneyler/09_kpi_yuk_profili_2026-11-12/simulation/results'
D08 = ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12/simulation/results'
N_MEAS = 256


def native(folder):
    m = json.loads((folder / 'metrics.json').read_text())
    u = pd.DataFrame(m['ues'])
    return u[u.ue_id < N_MEAS].set_index('ue_id')


def main():
    out = {}
    cases = [(f'{lv}_draw{s}', D09 / f'{lv}_draw{s}') for lv in ['L1_daily_mean', 'L2_busy_hour', 'L3_site_busy_hour']
             for s in [701, 702, 703]] + [(f'noload_n256_draw{s}', D08 / f'n256_draw{s}') for s in [701, 702, 703]]
    for name, folder in cases:
        sectors = pd.read_csv(folder / 'sectors.csv')
        ues = pd.read_csv(folder / 'ues.csv').set_index('ue_id')
        nat = native(folder)
        pts = ues.loc[nat.index, ['x_m', 'y_m', 'z_m']].to_numpy(dtype=float)
        pw = received_power_w(pts, sectors)
        prb_path = folder / 'prb_usage.csv'
        if prb_path.exists():
            prb = pd.read_csv(prb_path).set_index('synthetic_cell_id').dl_prb_utilization
        else:  # 08 runs had no counter; use the measured 0.033 baseline profile of the same draw (L0)
            prb = pd.read_csv(D09 / f"L0_idle_draw{name[-3:]}" / 'prb_usage.csv').set_index('synthetic_cell_id').dl_prb_utilization
        rho = prb.reindex(sectors.synthetic_cell_id).fillna(0).to_numpy()
        res = {}
        for method in ['mean', 'mc', 'ns3mix']:
            lm = link_metrics(pw, rho, method)
            serv = sectors.iloc[lm['serving']]
            same = (serv.site.to_numpy() == nat.site.to_numpy()) & (serv.sector.to_numpy() == nat.sector.to_numpy())
            df = pd.DataFrame({'site': nat.site, 'sector': nat.sector, 'rsrp_n': nat.rsrp, 'rsrq_n': nat.rsrq,
                               'sinr_n': nat.sinr, 'rsrp_a': lm['rsrp_dbm'], 'rsrq_a': lm['rsrq_db'],
                               'sinr_a': lm['sinr_db']}).dropna()
            e = df.sinr_a - df.sinr_n
            site = df.groupby(['site', 'sector'])[['sinr_n', 'sinr_a']].mean().groupby('site').mean()
            res[method] = {'same_serving': float(same.mean()),
                           'rsrp_max_abs': float((df.rsrp_a - df.rsrp_n).abs().max()),
                           'rsrq_max_abs': float((df.rsrq_a - df.rsrq_n).abs().max()),
                           'sinr_bias': float(e.mean()), 'sinr_median_abs': float(e.abs().median()),
                           'sinr_q90_abs': float(e.abs().quantile(.9)),
                           'site_sinr_max_abs': float((site.sinr_a - site.sinr_n).abs().max())}
        out[name] = res
        print(name, {m: {k: round(v, 3) for k, v in r.items()} for m, r in res.items()}, flush=True)
    (HERE / 'validation.json').write_text(json.dumps(out, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
