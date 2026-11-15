"""Validate the analytical interference-time SINR ('mc') against native ns-3 samples that carry
fresh PDSCH interference (data_interference_fresh == 1), i.e. the physically loaded SINR.

Acceptance (written before the comparison): per load level and draw, median |error| <= 1 dB and
site-level mean difference <= 1 dB at every evaluation site.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from radio_model import received_power_w, link_metrics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D09 = ROOT / 'deneyler/09_kpi_yuk_profili_2026-11-12/simulation/results'
N_MEAS = 256


def main():
    out = {}
    for lv in ['L1_daily_mean', 'L2_busy_hour', 'L3_site_busy_hour']:
        for s in [701, 702, 703]:
            folder = D09 / f'{lv}_draw{s}'
            sectors = pd.read_csv(folder / 'sectors.csv')
            c = pd.read_csv(folder / 'sinr_components.csv',
                            usecols=['time_s', 'ue_id', 'synthetic_cell_id', 'native_sinr_db', 'data_interference_fresh'])
            c = c[(c.time_s >= 1) & (c.ue_id < N_MEAS)]
            m = json.loads((folder / 'metrics.json').read_text())
            nat = pd.DataFrame(m['ues']).set_index('ue_id')
            nat = nat[nat.index < N_MEAS]
            serving_cell = pd.read_csv(folder / 'ues.csv').set_index('ue_id').synthetic_cell_id
            c = c[c.synthetic_cell_id == c.ue_id.map(serving_cell)]
            fresh = c[c.data_interference_fresh == 1].groupby('ue_id').native_sinr_db.mean()
            ues = pd.read_csv(folder / 'ues.csv').set_index('ue_id').loc[fresh.index]
            pw = received_power_w(ues[['x_m', 'y_m', 'z_m']].to_numpy(dtype=float), sectors)
            rho = pd.read_csv(folder / 'prb_usage.csv').set_index('synthetic_cell_id').dl_prb_utilization \
                .reindex(sectors.synthetic_cell_id).fillna(0).to_numpy()
            res = {}
            for method in ['mc', 'mean']:
                a = pd.Series(link_metrics(pw, rho, method)['sinr_db'], index=fresh.index)
                e = a - fresh
                df = pd.DataFrame({'site': nat.loc[fresh.index, 'site'], 'sector': nat.loc[fresh.index, 'sector'],
                                   'n': fresh, 'a': a})
                site = df.groupby(['site', 'sector'])[['n', 'a']].mean().groupby('site').mean()
                ev = site.loc[[x for x in site.index if x in m['sites'] and nat[nat.site == x].role.iloc[0] == 'Evaluation']]
                res[method] = {'ues': int(len(fresh)), 'bias': float(e.mean()), 'median_abs': float(e.abs().median()),
                               'q90_abs': float(e.abs().quantile(.9)),
                               'eval_site_max_abs': float((ev.a - ev.n).abs().max())}
            res['fresh_fraction_mean'] = float(c.data_interference_fresh.mean())
            out[f'{lv}_draw{s}'] = res
            print(f'{lv}_draw{s}', json.dumps({k: (v if not isinstance(v, dict) else {q: round(w, 2) for q, w in v.items()}) for k, v in res.items()}), flush=True)
    (HERE / 'validation_fresh.json').write_text(json.dumps(out, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
