"""Windows: freeze the data-derived distance correction on top of the RMa scenario (deneyler/21).

Predeclared design (written before any run of this experiment):
- Context: no further operator information (indoor share, real tilt/height) can be obtained. In
  deneyler/21 the RMa model got the overall level right but its RSRP falls ~43 dB per decade of distance,
  while the real network seen by Experia falls ~11 dB per decade. Chosen after seeing deneyler/20 and /21.
- Idea: keep the physical model of deneyler/21 for every link (so interference geometry stays physical) and
  give each user one extra loss/gain, the same on all its links, that maps the RMa distance law onto the
  distance law of the operator's own measurements:
      extra_loss_db(d) = RSRP_RMa(d) - RSRP_Experia(d),  both fitted as a + b*log10(d)
  * RSRP_Experia(d): least-squares fit of cell mean RSRP vs cell mean TA distance (TAAVG x 4.88 m, clipped
    to 100 m-15 km) over ALL Experia cells of the region EXCEPT the 8 evaluation sites (no cell of 130,
    296, 440, 441, 443, 444, 482, 554 is used). So the comparison sites stay unseen.
  * RSRP_RMa(d): same fit over the measured users of the three deneyler/21 runs (simulated RSRP vs serving
    distance). This uses simulation output only, never Experia values of the evaluation sites.
  * d of a user: measured users use their TA placement distance; load users use the distance to their
    target site. d clipped to 100 m-15 km.
  The correction is an empirical stand-in for what the model cannot represent (indoor share, real tilt and
  height, cell planning). It is not a physical propagation law and is reported as such.
- Everything else identical to deneyler/21 RMa_TA (RMa, 1850 MHz, 49 dBm, 65 deg / 15 dBi, 6 deg tilt,
  8 dB link shadow, NF 9 dB, TA placement, load users and 1.47 factor, three draws, 4 s, 1 s warm-up).
- Regression first: without the extra_loss_db column the copied simulator must reproduce deneyler/16
  regression_disabled_draw701 byte for byte (after CRLF->LF).
- Same decision rule as deneyler/20: becomes the reference if held-out RSRP MAE <= 3 dB and SINR MAE
  <= 3 dB averaged over draws and all 256 measured users connect in every draw. No value is adjusted after
  seeing the results.
"""
from pathlib import Path
import csv
import hashlib
import json

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SIM = HERE/'simulation'
D21 = HERE.parent/'21_kirsal_yol_kaybi_rma_2026-11-17'
DRAWS = [(42, 701), (7, 702), (99, 703)]
EVAL = ['SITE_000130', 'SITE_000296', 'SITE_000444', 'SITE_000482', 'SITE_000554',
        'SITE_000440', 'SITE_000441', 'SITE_000443']
TS_M, DMIN, DMAX = 4.88, 100.0, 15000.0


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fit(d, y):
    a = np.vstack([np.ones(len(d)), np.log10(d)]).T
    b = np.linalg.lstsq(a, y, rcond=None)[0]
    return [float(b[0]), float(b[1])], float(np.std(y - a @ b))


def main():
    cells = pd.read_csv(ROOT/'ana_proje/analysis/radio_cell_summary.csv').dropna(subset=['rsrp_mean', 'ta_mean'])
    eval_cells = pd.read_csv(ROOT/'deneyler/13_hucre_imzasi_2026-11-15/experia_cells.csv.gz').FIRSTCELL.unique()
    cells = cells[~cells.site.isin(EVAL) & ~cells.FIRSTCELL.isin(eval_cells)]
    exp_b, exp_sd = fit((cells.ta_mean*TS_M).clip(DMIN, DMAX).to_numpy(), cells.rsrp_mean.to_numpy())
    users = []
    for _, seed in DRAWS:
        m = pd.DataFrame(json.loads((D21/f'simulation/results/RMa_TA_draw{seed}/metrics.json').read_text())['ues'])
        users.append(m[(m.ue_id < 256) & m.rsrp.notna()])
    users = pd.concat(users)
    rma_b, rma_sd = fit(users.serving_distance_m.clip(DMIN, DMAX).to_numpy(), users.rsrp.to_numpy())
    k0, k1 = rma_b[0] - exp_b[0], rma_b[1] - exp_b[1]

    def extra(d):
        return k0 + k1*np.log10(np.clip(d, DMIN, DMAX))

    inputs = HERE/'inputs'
    cases, stats = [], {}
    for az, seed in DRAWS:
        sites = pd.read_csv(inputs/f'sites_S0TA_{az}.csv').set_index('site')
        with (inputs/f'ues_R_TA_{seed}.csv').open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        cols = list(rows[0].keys()) + ['extra_loss_db']
        losses = []
        for r in rows:
            if r['kind'] == 'measure':
                d = float(r['placement_distance_m'])
            else:
                s = sites.loc[r['target_site']]
                d = float(np.hypot(float(r['x_m']) - s.x_m, float(r['y_m']) - s.y_m))
            r['extra_loss_db'] = f'{extra(d):.6f}'
            losses.append(extra(d))
        out = inputs/f'ues_DC_TA_{seed}.csv'
        with out.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n')
            w.writeheader()
            w.writerows(rows)
        stats[seed] = {'min': float(np.min(losses)), 'median': float(np.median(losses)), 'max': float(np.max(losses))}
        cases.append({'name': f'DC_TA_draw{seed}', 'label': 'DC_TA', 'az': az, 'ue_seed': seed,
                      'sites_file': f'sites_S0TA_{az}.csv', 'ue_file': out.name, 'shadow_seed': az})
    p21 = json.loads((D21/'plan.json').read_text(encoding='utf-8'))
    plan = {'draws': DRAWS, 'radio': p21['radio'], 'sources': dict(p21['sources'],
            distance_correction='fit over Experia cells of the region excluding the 8 evaluation sites, minus fit over deneyler/21 simulated users'),
            'correction': {'experia_fit_a_b': exp_b, 'experia_fit_resid_sd_db': exp_sd, 'experia_cells_used': int(len(cells)),
                           'rma_fit_a_b': rma_b, 'rma_fit_resid_sd_db': rma_sd, 'rma_users_used': int(len(users)),
                           'extra_loss_db': f'{k0:.3f} + ({k1:.3f})*log10(d_m), d clipped to [{DMIN:g}, {DMAX:g}] m',
                           'per_draw_extra_loss_stats': stats},
            'cases': cases, 'train_sites': p21['train_sites'], 'holdout_sites': p21['holdout_sites'],
            'decision_rule': dict(p21['decision_rule'], scenario='DC_TA'), 'regression': p21['regression'],
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py']},
            'input_hashes': {p.name: sha(p) for p in sorted(inputs.glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run of this experiment):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(plan['correction'], indent=1))


if __name__ == '__main__':
    main()
