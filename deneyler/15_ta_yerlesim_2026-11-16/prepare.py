"""Windows: freeze the TA-based user placement study (draft option U3).

Predeclared design (written before any run):
- Question: does placing the measured users at the distances the real users have (from timing
  advance) bring the simulation closer to Experia than the uniform 2-6 km clusters?
- Everything else is identical to S0 of the multi-carrier study (deneyler/14): same 24 sites,
  same azimuth draws (42/7/99), same load users and load factor (frozen 1.47, KPI daily-mean
  PRB 0.233), randomised UDP start, 256 measured users (32 per evaluation site), 4 s, 1 s warm-up.
- Only the measured users move. For each user of evaluation site s: draw one hourly Experia record
  of s at random (so busier cells and hours weigh more), take its TA distance
  d = AVG(TAAVG) x 4.88 m (unit given by the advisor/Turkcell), clip to [100 m, 15 km], and place
  the user at distance d in a uniformly random direction (antenna azimuths are unknown).
- TA is an input about where users are, like the site coordinates; it is not RSRP/SINR, so
  the comparison with Experia RSRP/SINR stays a fair check. The held-out sites keep their role.
- Compare with deneyler/14 S0 on the same metrics: site MAE (tuning and held-out sites), signed
  errors, site ranking, cell-level RSRP/SINR distribution, KPI CQI. No other change, no retuning.
"""
from pathlib import Path
import hashlib
import json
import shutil

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D14 = ROOT / 'deneyler/14_temel_s0_ve_cok_tasiyici_s2_2026-11-15'
EXPERIA = ROOT / 'deneyler/13_hucre_imzasi_2026-11-15/experia_cells.csv.gz'
DRAWS = [(42, 701), (7, 702), (99, 703)]
PER_SITE = 32
TS_M = 4.88
DMIN, DMAX = 100.0, 15000.0


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    inputs = HERE / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    sim = HERE / 'simulation'
    sim.mkdir(exist_ok=True)
    for name in ['run_baseline.py', 'sindirgi_baseline.cc', 'ns3_paths.py', 'static-shadow-model.h']:
        shutil.copy2(D14 / 'simulation' / name, sim / name)
    shutil.copy2(D14 / 'inputs/targets.csv', inputs / 'targets.csv')
    exp = pd.read_csv(EXPERIA)
    # 29 of 8,159 hourly records have no TA value; they cannot give a distance.
    exp = exp.dropna(subset=['AVG(TAAVG)'])
    exp['d_m'] = (exp['AVG(TAAVG)'] * TS_M).clip(DMIN, DMAX)
    cases, stats = [], {}
    for az, seed in DRAWS:
        sites = pd.read_csv(D14 / f'inputs/sites_S0_{az}.csv')
        sites.to_csv(inputs / f'sites_S0TA_{az}.csv', index=False, float_format='%.9f')
        old = pd.read_csv(D14 / f'inputs/ues_S0_{seed}.csv', dtype=str, keep_default_na=False)
        load = old[old.kind == 'load']  # copied verbatim from the S0 run
        ev = sites[sites.role == 'Evaluation'].reset_index(drop=True)
        rng = np.random.default_rng(seed)
        rows = []
        for u in range(PER_SITE * len(ev)):
            s = ev.iloc[u % len(ev)]
            pool = exp.loc[exp.site == s.site, 'd_m'].to_numpy()
            d = pool[rng.integers(len(pool))]
            a = rng.uniform(0, 2 * np.pi)
            rows.append(dict(ue_id=u, x_m=f'{s.x_m + d * np.cos(a):.9f}', y_m=f'{s.y_m + d * np.sin(a):.9f}',
                             z_m='1.500000000', kind='measure', target_site='', target_sector='', target_prb='',
                             udp_interval_ms=200.0, dl_earfcn=1300, placement_site=s.site, placement_distance_m=round(d, 1)))
        meas = pd.DataFrame(rows)
        assert int(load.ue_id.astype(int).min()) == len(meas), 'load users must follow the measured users'
        load = load.assign(placement_site='', placement_distance_m='')
        out = pd.concat([meas, load[meas.columns]], ignore_index=True)
        path = inputs / f'ues_S0TA_{seed}.csv'
        out.to_csv(path, index=False)
        stats[seed] = meas.groupby('placement_site').placement_distance_m.median().round(0).to_dict()
        cases.append(dict(name=f'S0TA_draw{seed}', scenario='S0TA', az=az, ue_seed=seed, ues=len(out),
                          measurement_ues=len(meas), duration=4, warmup=1))
    plan = {'cases': cases, 'calibration_factors': {'S0TA': 1.47}, 'placement_median_m': stats,
            'radio': {'mixed_cqi': 1, 'beamwidth': 120, 'exponent': 3, 'enb_power': 49, 'receiver_nf': 9,
                      'shadow_std': 0, 'dl_earfcn': 1300, 'udp_jitter': 1},
            'source_sha256': sha(sim / 'sindirgi_baseline.cc'),
            'input_hashes': {p.name: sha(p) for p in sorted(inputs.glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run):')[1].strip()}
    (HERE / 'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
