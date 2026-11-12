"""Windows: freeze the KPI-informed load study (run after profile.py).

Design (predeclared, written before runs):
- Same selected radio settings, current 24 sites, 3 azimuth/UE draws, 256 measurement UEs (08, n=256).
- Measurement UEs keep the 08 traffic (512 B every 200 ms) and are the only UEs used in metrics.
- One extra 'load UE' per sector (72), 800 m along the sector boresight, ids 256..327. Its UDP
  rate sets the sector's DL PRB occupancy. ns-3 PF scheduling gives each scheduled TTI the whole
  band, so a 512 B packet ~ one fully used subframe: interval_ms = 1 / target_prb.
- Cases: L0 (load UEs present, ~no traffic: isolates their presence), uniform daily mean,
  uniform busy hour, site-specific busy hour (KPI 20:00-24:00 mean per site).
- Hypothesis: simulated SINR (mixed CQI) falls toward Experia as load rises; RSRP must not change.
- Amendment after the first test run (L2, draw 701): achieved mean PRB 0.546 vs target 0.359,
  because packets need more than one subframe once interference lowers the MCS. Load-UE intervals
  are therefore multiplied by a per-level calibration factor (calibration.json), fitted on draw 701
  only, then frozen for all draws. Accept a level if its mean achieved PRB is within +/-10% of target.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import shutil

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D08 = ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12'
DRAWS = [(42, 701), (7, 702), (99, 703)]
N_MEAS = 256
MEAS_INTERVAL_MS = 200.0
LOAD_DISTANCE_M = 800.0
IDLE_INTERVAL_MS = 1.0e6


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    prof = json.loads((HERE / 'profile.json').read_text(encoding='utf-8'))
    site_prb = pd.read_csv(HERE / 'site_busy_hour.csv').set_index('site').prb.to_dict()
    inputs = HERE / 'inputs'
    inputs.mkdir(exist_ok=True)
    shutil.copy2(D08 / 'inputs/targets.csv', inputs / 'targets.csv')
    loads = {'L0_idle': None, 'L1_daily_mean': prof['simulation_targets']['normal_daily_mean'],
             'L2_busy_hour': prof['simulation_targets']['normal_busy_hour'], 'L3_site_busy_hour': 'site'}
    cal_path = HERE / 'calibration.json'
    calibration = json.loads(cal_path.read_text(encoding='utf-8'))['factors'] if cal_path.exists() else {}
    cases, filled = [], {}
    for az, seed in DRAWS:
        shutil.copy2(D08 / f'inputs/sites_24_{az}.csv', inputs / f'sites_24_{az}.csv')
        meas = pd.read_csv(D08 / f'inputs/ues_far_{seed}_{N_MEAS}.csv')
        sectors = pd.read_csv(D08 / f'simulation/results/n{N_MEAS}_draw{seed}/sectors.csv')
        assert len(sectors) == 72
        for name, level in loads.items():
            rows = [dict(ue_id=int(r.ue_id), x_m=f'{r.x_m:.9f}', y_m=f'{r.y_m:.9f}', z_m=f'{r.z_m:.9f}',
                         kind='measure', target_cell=0, target_prb='', udp_interval_ms=MEAS_INTERVAL_MS)
                    for r in meas.itertuples()]
            for i, s in enumerate(sectors.itertuples()):
                if level is None:
                    p = 0.0
                elif level == 'site':
                    p = site_prb.get(s.site)
                    if p is None:  # site absent from KPI extract: use its group mean
                        p = float(pd.Series([v for k, v in site_prb.items()]).mean())
                        filled[s.site] = p
                else:
                    p = level
                a = math.radians(s.orientation_ccw_from_east_deg)
                rows.append(dict(ue_id=N_MEAS + i, x_m=f'{s.x_m + LOAD_DISTANCE_M * math.cos(a):.9f}',
                                 y_m=f'{s.y_m + LOAD_DISTANCE_M * math.sin(a):.9f}', z_m='1.500000000',
                                 kind='load', target_cell=int(s.synthetic_cell_id), target_prb=f'{p:.6f}',
                                 udp_interval_ms=f'{(calibration.get(name, 1.0) / p if p > 0 else IDLE_INTERVAL_MS):.6f}'))
            path = inputs / f'ues_{name}_{seed}.csv'
            with path.open('w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
            cases.append(dict(name=f'{name}_draw{seed}', load=name, az=az, ue_seed=seed, ues=len(rows),
                              measurement_ues=N_MEAS, duration=4, warmup=1,
                              baseline_08=f'n{N_MEAS}_draw{seed}'))
    plan = {'cases': cases, 'levels': {k: v for k, v in loads.items()}, 'filled_site_prb': filled,
            'calibration_factors': calibration,
            'radio': {'mixed_cqi': 1, 'beamwidth': 120, 'exponent': 3, 'enb_power': 49, 'receiver_nf': 9,
                      'shadow_std': 0, 'dl_earfcn': 1300},
            'source_sha256': sha(HERE / 'simulation/sindirgi_baseline.cc'),
            'input_hashes': {p.name: sha(p) for p in sorted(inputs.glob('*.csv'))},
            'rule': __doc__.split('Design (predeclared, written before runs):')[1].strip()}
    (HERE / 'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Prepared', len(cases), 'runs; filled', filled)


if __name__ == '__main__':
    main()
