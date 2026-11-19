"""Windows: freeze the neighbour-site check of the deneyler/26 model.

Predeclared design (written before any run of this experiment):
- Question: the advisor asked whether the model was tried on all the selected sites. Until now only the
  8 evaluation sites were compared with Experia. Does the deneyler/26 model give similar errors on
  neighbour sites it was never compared on?
- Sites, chosen BEFORE any run and only by cell count: among the advisor's 8 neighbour sites, the three
  with the most Experia cells: SITE_000200 (12), SITE_000224 (10), SITE_000206 (9). 506, 475 and 480
  have 1-2 cells; 553 and 555 have no Experia data.
- Caveat stated up front: the region-wide distance correction of deneyler/22/26 excluded only the 8
  evaluation sites, so the cells of these 3 sites were part of its 5,812-cell fit (about 31 of 5,812
  cells, ~0.5 %). They are therefore "nearly", not fully, independent.
- Model: identical to deneyler/26 FT_TA (same simulator incl. private libns3-lte with EVM 8 %, same radio,
  same distance-correction formula, same frozen load factor 1.243, same azimuth draws 42/7/99).
- Users: the 256 measured users and 72 load users of deneyler/26 are kept unchanged (load users are
  renumbered after the new users). 32 new measured users per new site (96 in total) are placed exactly
  like the evaluation-site users of deneyler/15: draw one hourly Experia record of that site at random,
  distance = TAAVG x 4.88 m clipped to [100 m, 15 km], uniformly random direction; random generator seed =
  draw seed + 2700. Their extra_loss_db uses the deneyler/26 correction formula at that distance.
- Targets for the new sites use the same rule as the existing targets (verified to reproduce targets.csv
  exactly for the 8 evaluation sites): mean over hours per cell, then mean over cells.
- Report: per-site signed and absolute RSRP/SINR error of the 3 neighbour sites (mean of 3 draws), their
  MAE next to the evaluation-site MAE of deneyler/26, and the change of the evaluation-site values caused
  by the added users. No value is adjusted after seeing the results.
"""
from pathlib import Path
import csv
import gzip
import hashlib
import json

import numpy as np
import openpyxl
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SIM = HERE/'simulation'
D26 = HERE.parent/'26_kaynakli_tam_model_2026-11-19'
NEW = ['SITE_000200', 'SITE_000224', 'SITE_000206']
DRAWS = [(42, 701), (7, 702), (99, 703)]
PER_SITE, TS_M, DMIN, DMAX = 32, 4.88, 100.0, 15000.0
EXTRACT = HERE/'neighbour_experia.csv.gz'  # operator data, gitignored


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract():
    if EXTRACT.exists():
        return pd.read_csv(EXTRACT)
    cs = openpyxl.load_workbook(ROOT/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx', read_only=True).worksheets[0]
    cell_site = {r[0]: r[1] for r in cs.iter_rows(min_row=2, values_only=True) if r[1] in NEW}
    ws = openpyxl.load_workbook(ROOT/'ana_proje/experia/experia.xlsx', read_only=True).worksheets[0]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        s = cell_site.get(r[4])
        if s:
            rows.append({'site': s, 'FIRSTCELL': r[4], 'sinr': r[5], 'rsrp': r[6], 'rsrq': r[7], 'ta': r[8]})
    d = pd.DataFrame(rows)
    with gzip.open(EXTRACT, 'wt', encoding='utf-8', newline='') as g:
        d.to_csv(g, index=False)
    return d


def main():
    exp = extract()
    cells = exp.groupby(['site', 'FIRSTCELL'])[['rsrp', 'sinr', 'rsrq']].mean()
    hours = exp.groupby(['site', 'FIRSTCELL']).size().groupby('site').min()
    tgt = cells.groupby('site').mean()
    targets = pd.read_csv(D26/'inputs/targets.csv')
    add = pd.DataFrame({'site': NEW, 'measured_cells': [int(cells.loc[s].shape[0]) for s in NEW],
                        'rsrp_target': [tgt.loc[s, 'rsrp'] for s in NEW], 'sinr_target': [tgt.loc[s, 'sinr'] for s in NEW],
                        'rsrq_target': [tgt.loc[s, 'rsrq'] for s in NEW], 'min_hours': [int(hours[s]) for s in NEW],
                        'split': 'neighbour'})
    pd.concat([targets, add]).to_csv(HERE/'inputs/targets.csv', index=False)

    corr = json.loads((D26/'correction.json').read_text(encoding='utf-8'))
    k0, k1 = (float(x) for x in corr['extra_loss_db'].split(' + (')[0:1] + corr['extra_loss_db'].split('(')[1].split(')')[0:1])
    ta = exp.dropna(subset=['ta']).assign(d=lambda x: (x.ta*TS_M).clip(DMIN, DMAX))
    cases, stats = [], {}
    for az, seed in DRAWS:
        sites = pd.read_csv(HERE/f'inputs/sites_S0TA_{az}.csv').set_index('site')
        old = pd.read_csv(D26/f'inputs/ues_FT_TA_{seed}.csv', dtype=str, keep_default_na=False)
        meas, load = old[old.kind == 'measure'], old[old.kind == 'load'].copy()
        assert len(meas) == 256 and int(meas.ue_id.astype(int).max()) == 255
        rng = np.random.default_rng(seed + 2700)
        rows = []
        for i in range(PER_SITE*len(NEW)):
            s = NEW[i % len(NEW)]
            pool = ta.loc[ta.site == s, 'd'].to_numpy()
            d = float(pool[rng.integers(len(pool))])
            a = rng.uniform(0, 2*np.pi)
            x, y = sites.loc[s, 'x_m'] + d*np.cos(a), sites.loc[s, 'y_m'] + d*np.sin(a)
            r = {c: '' for c in old.columns}
            r.update(ue_id=str(256 + i), x_m=f'{x:.9f}', y_m=f'{y:.9f}', z_m='1.500000000', kind='measure',
                     udp_interval_ms='200.0', dl_earfcn=meas.dl_earfcn.iloc[0], placement_site=s,
                     placement_distance_m=f'{d:.1f}', extra_loss_db=f'{k0 + k1*np.log10(d):.6f}')
            rows.append(r)
        load['ue_id'] = (load.ue_id.astype(int) + len(rows)).astype(str)
        out = pd.concat([meas, pd.DataFrame(rows), load], ignore_index=True)[old.columns]
        path = HERE/'inputs'/f'ues_NB_TA_{seed}.csv'
        out.to_csv(path, index=False, lineterminator='\n')
        stats[seed] = pd.DataFrame(rows).assign(d=lambda x: x.placement_distance_m.astype(float)).groupby('placement_site').d.median().round(0).to_dict()
        cases.append({'name': f'NB_TA_draw{seed}', 'label': 'NB_TA', 'az': az, 'ue_seed': seed,
                      'sites_file': f'sites_S0TA_{az}.csv', 'ue_file': path.name, 'shadow_seed': az})
    p26 = json.loads((D26/'plan.json').read_text(encoding='utf-8'))
    plan = {'draws': DRAWS, 'radio': p26['radio'], 'sources': p26['sources'], 'correction': corr,
            'load_calibration': p26['load_calibration'], 'cases': cases, 'measurement_ues': 256 + PER_SITE*len(NEW),
            'train_sites': p26['train_sites'], 'holdout_sites': p26['holdout_sites'], 'neighbour_sites': NEW,
            'new_user_median_distance_m': stats, 'decision_rule': p26['decision_rule'], 'regression': p26['regression'],
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py', 'build_private_lte.py']},
            'input_hashes': {p.name: sha(p) for p in sorted((HERE/'inputs').glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run of this experiment):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(add.round(2).to_string(index=False))
    print('k0,k1', k0, k1, 'median distances', stats)


if __name__ == '__main__':
    main()
