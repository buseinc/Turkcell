"""Freeze the UE sample-size study: nested 64 -> 128 -> 256 'far' draws.

Run on Windows Python (numpy/pandas). The simulation step (study.py) runs in WSL.
Rule: same selected radio settings, same current 24-site inventory, same azimuths.
Only the number of synthetic UEs grows; per-UE UDP interval grows in proportion so
the total offered downlink load stays at 64 x 512 B / 50 ms.
"""
from pathlib import Path
import hashlib
import json
import shutil

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D05 = ROOT / 'deneyler/05_kullanici_yayilim_guc_2026-11-10'
D06 = ROOT / 'deneyler/06_genis_tarama_secilen_ayar_2026-11-10'
D07 = ROOT / 'deneyler/07_guncel_envanter_kontrolu_2026-11-12'
DRAWS = [(42, 701, 'ensemble_reference_0', 'updated_24'),
         (7, 702, 'ensemble_reference_1', 'updated_draw_1'),
         (99, 703, 'ensemble_reference_2', 'updated_draw_2')]
SIZES = [64, 128, 256]
BASE_UES, BASE_INTERVAL_MS = 64, 50.0


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def far_placement(seed, n, sites):
    """Same draw order as 05/prepare.py placement('far'): the first 64 rows are identical."""
    anchors = sites[sites.role.eq('Evaluation')].reset_index(drop=True)
    rng = np.random.default_rng(seed)
    rows = []
    for u in range(n):
        anchor = anchors.iloc[u % 8]
        angle = rng.uniform(0, 2 * np.pi)
        radius = np.sqrt(rng.uniform(2000 * 2000, 6000 * 6000))
        point = anchor[['x_m', 'y_m']].to_numpy(dtype=float) + radius * np.array([np.cos(angle), np.sin(angle)])
        rows.append({'ue_id': u, 'x_m': point[0], 'y_m': point[1], 'z_m': 1.5, 'placement_anchor': anchor.site})
    return pd.DataFrame(rows)


def main():
    inputs = HERE / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    sim = HERE / 'simulation'
    sim.mkdir(exist_ok=True)
    for name in ['run_baseline.py', 'sindirgi_baseline.cc', 'ns3_paths.py', 'static-shadow-model.h']:
        shutil.copy2(D06 / 'simulation' / name, sim / name)
        assert sha(sim / name) == sha(D06 / 'simulation' / name)
    shutil.copy2(D06 / 'inputs/targets.csv', inputs / 'targets.csv')
    anchors = pd.read_csv(D05 / 'inputs/sites.csv')
    for az, seed, _, _ in DRAWS:
        shutil.copy2(D07 / f'inputs/sites_24_{az}.csv', inputs / f'sites_24_{az}.csv')
        for n in SIZES:
            path = inputs / f'ues_far_{seed}_{n}.csv'
            far_placement(seed, n, anchors).to_csv(path, index=False, float_format='%.9f')
        # Nesting check: 64-UE file reproduces the frozen 06 draw byte for byte,
        # and every larger draw starts with the smaller one.
        assert (inputs / f'ues_far_{seed}_64.csv').read_bytes() == (D06 / f'inputs/ues_far_{seed}.csv').read_bytes()
        small = pd.read_csv(inputs / f'ues_far_{seed}_64.csv')
        for n in SIZES[1:]:
            big = pd.read_csv(inputs / f'ues_far_{seed}_{n}.csv')
            pd.testing.assert_frame_equal(big.iloc[:len(small)].reset_index(drop=True), small)
            small = big
    cases = []
    for az, seed, old06, old07 in DRAWS:
        for n in SIZES:
            cases.append(dict(name=f'n{n}_draw{seed}', ues=n, az=az, ue_seed=seed,
                              udp_interval_ms=BASE_INTERVAL_MS * n / BASE_UES, duration=4, warmup=1,
                              reproduce=f'refresh_20261112_{old07}' if n == BASE_UES else None))
    plan = {
        'cases': cases,
        'radio': {'mixed_cqi': 1, 'beamwidth': 120, 'exponent': 3, 'enb_power': 49,
                  'receiver_nf': 9, 'shadow_std': 0, 'dl_earfcn': 1300, 'sectors': 'three'},
        'offered_load': {'total_dl_bps': BASE_UES * 512 * 8 / (BASE_INTERVAL_MS / 1000),
                         'note': 'per-UE interval = 50 ms x n/64; packet 512 B'},
        'source_sha256': sha(sim / 'sindirgi_baseline.cc'),
        'input_hashes': {p.name: sha(p) for p in sorted(inputs.glob('*.csv'))},
        'rule': ('Predeclared before runs. No retuning. (1) n=64 runs must reproduce the 07 refresh runs '
                 '(paired RSRP/SINR q95 <= 0.01 dB, same sector 100%). (2) Original 64 UEs, paired across n: '
                 'report RSRP/SINR/RSRQ q95 change and serving-sector agreement (load effect on SINR/RSRQ expected '
                 'to be small because total offered load is fixed). (3) Sample-size adequacy: for each draw, '
                 'training and control MAE of RSRP/SINR/RSRQ change by <= 0.5 dB between n=128 and n=256, and the '
                 'spread across the three draws does not grow with n. Also report UEs per evaluation site.'),
    }
    (HERE / 'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Prepared', len(cases), 'native runs')


if __name__ == '__main__':
    main()
