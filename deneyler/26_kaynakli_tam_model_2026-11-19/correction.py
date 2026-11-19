"""Windows: re-derive the deneyler/22 distance correction for the 3GPP-antenna radio (step 1 of deneyler/26).

Predeclared design (written before any run of this experiment):
- Context: deneyler/22 derived extra_loss(d) = RSRP_model(d) - RSRP_Experia(d) with the cosine antenna. In
  deneyler/23-24 the antenna became the 3GPP pattern but the correction was not re-derived, and RSRP got worse
  (held-out 3.5 -> 5.4 dB). deneyler/25 showed the missing SINR ceiling (transmitter EVM). All of this was
  seen before designing deneyler/26; reported as such.
- Same method as deneyler/22, applied to the 3GPP-antenna model:
  * RSRP_Experia(d): unchanged fit from deneyler/22 (Experia cells of the region, 8 evaluation sites excluded).
  * RSRP_model(d): fit a + b*log10(d) over the measured users of the three deneyler/24 LC_TA runs, using the
    UNCORRECTED RSRP = simulated RSRP + that user's deneyler/22 extra_loss_db. This is exact, because the
    correction is the same on every link of a user (verified in deneyler/22: RSRP change = -extra_loss,
    correlation 1.0) and RSRP does not depend on load or EVM. d = serving distance, clipped 100 m-15 km.
    Only simulation output is used; no Experia value of the evaluation sites.
  * New extra_loss(d) = RSRP_model(d) - RSRP_Experia(d), applied per user as before (measured users: TA
    placement distance; load users: distance to target site).
- Load intervals are copied from deneyler/24 (factor 1.243) and re-calibrated by calibrate.py.
"""
from pathlib import Path
import csv
import json

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D22 = HERE.parent/'22_veri_tabanli_mesafe_duzeltmesi_2026-11-17'
D24 = HERE.parent/'24_yuk_kalibrasyonu_2026-11-19'
DRAWS = [(42, 701), (7, 702), (99, 703)]
DMIN, DMAX = 100.0, 15000.0


def fit(d, y):
    a = np.vstack([np.ones(len(d)), np.log10(d)]).T
    b = np.linalg.lstsq(a, y, rcond=None)[0]
    return [float(b[0]), float(b[1])], float(np.std(y - a @ b))


def main():
    exp_b = json.loads((D22/'plan.json').read_text(encoding='utf-8'))['correction']['experia_fit_a_b']
    users = []
    for _, seed in DRAWS:
        m = pd.DataFrame(json.loads((D24/f'simulation/results/LC_TA_draw{seed}/metrics.json').read_text())['ues'])
        extra = pd.read_csv(D24/f'inputs/ues_LC_TA_{seed}.csv')[['ue_id', 'extra_loss_db']]
        m = m[(m.ue_id < 256) & m.rsrp.notna()].merge(extra, on='ue_id')
        m['rsrp_raw'] = m.rsrp + m.extra_loss_db
        users.append(m)
    users = pd.concat(users)
    mod_b, mod_sd = fit(users.serving_distance_m.clip(DMIN, DMAX).to_numpy(), users.rsrp_raw.to_numpy())
    k0, k1 = mod_b[0] - exp_b[0], mod_b[1] - exp_b[1]
    stats = {}
    for az, seed in DRAWS:
        sites = pd.read_csv(HERE/f'inputs/sites_S0TA_{az}.csv').set_index('site')
        with (D24/f'inputs/ues_LC_TA_{seed}.csv').open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        losses = []
        for r in rows:
            if r['kind'] == 'measure':
                d = float(r['placement_distance_m'])
            else:
                s = sites.loc[r['target_site']]
                d = float(np.hypot(float(r['x_m']) - s.x_m, float(r['y_m']) - s.y_m))
            v = k0 + k1*np.log10(np.clip(d, DMIN, DMAX))
            r['extra_loss_db'] = f'{v:.6f}'
            losses.append(v)
        with (HERE/f'inputs/ues_EC_TA_{seed}.csv').open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator='\n')
            w.writeheader()
            w.writerows(rows)
        stats[seed] = {'min': float(np.min(losses)), 'median': float(np.median(losses)), 'max': float(np.max(losses))}
    out = {'experia_fit_a_b': exp_b, 'model_fit_a_b': mod_b, 'model_fit_resid_sd_db': mod_sd, 'model_users_used': int(len(users)),
           'extra_loss_db': f'{k0:.3f} + ({k1:.3f})*log10(d_m), d clipped to [{DMIN:g}, {DMAX:g}] m',
           'per_draw_extra_loss_stats': stats,
           'rule': __doc__.split('Predeclared design (written before any run of this experiment):')[1].strip()}
    (HERE/'correction.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'rule'}, indent=1))


if __name__ == '__main__':
    main()
