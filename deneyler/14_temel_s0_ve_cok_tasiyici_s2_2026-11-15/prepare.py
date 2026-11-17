"""Windows: freeze the S0-vs-S2 comparison (run after extract_buffer_kpi.py).

Predeclared design (written before any S2 run):
- Common to both: selected radio settings, current 24 sites, the three azimuth/UE draws, 256 measurement
  UEs (512 B / 200 ms), one load UE per cell at 800 m on its boresight targeting the KPI daily-mean DL PRB
  (0.233), 4 s, 1 s warm-up. NEW for both: UDP start times jittered within one interval (removes the
  synchronised-load artefact found by the coverage-map study). So S0 here is re-run, not reused.
- S0: every site 3 sectors x B3 (1800 MHz, 20 MHz).
- S2: carriers from KPI handover evidence (cell signature study): a site whose cells mostly report
  inter-frequency handovers gets B3 + B20 (800 MHz, 10 MHz) on each sector; otherwise B3 only.
  Sites without KPI cells keep B3 only. SITE_000554 gets 2 sectors (S1 hint). Same 49 dBm per carrier.
  B20 path loss: free-space reference difference (+7.05 dB DL) on top of the same log-distance law.
- UE camping rule (assumption; ns-3 does no inter-frequency initial selection): a UE camps on B3 if its
  best B3 RSRP >= -110 dBm; otherwise on B20 if its best B20 RSRP is higher; else B3. Computed with the
  analytical link budget validated in the coverage-map study (RSRP exact).
- Metrics vs Experia and KPI CQI exactly as in the earlier studies; per-cell = (sector, carrier).
- Load calibration: interval = factor / target_prb, one factor per scenario fitted on draw 701 only,
  then frozen; accept if mean achieved PRB within +/-10 % of target.
"""
from pathlib import Path
import hashlib
import json
import math
import shutil
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D08 = ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12'
sys.path.insert(0, str(ROOT / 'deneyler/10_kapsama_haritalari_2026-11-15'))
from radio_model import received_power_w  # noqa: E402

DRAWS = [(42, 701), (7, 702), (99, 703)]
N_MEAS = 256
MEAS_INTERVAL_MS = 200.0
TARGET_PRB = 0.233
LOAD_DISTANCE_M = 800.0
CAMP_B3_MIN_RSRP = -110.0
B20_DL_GAIN_DB = 20 * math.log10(1815e6 / 806e6)       # free-space reference difference
B20_RSRP_OFFSET_DB = B20_DL_GAIN_DB + 10 * math.log10(2)  # same power on half the REs
EARFCN = {'B3': 1300, 'B20': 6300}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sector_table(sites, az_seed_sectors):
    """Cells (site, sector, carrier, orientation) as the C++ will create them."""
    rows = []
    orient = az_seed_sectors.groupby('site').orientation_ccw_from_east_deg.first()
    for s in sites.itertuples():
        for sec in range(int(s.sector_count)):
            for k, c in enumerate(s.carriers.split(';')):
                rows.append({'site': s.site, 'role': s.role, 'sector': sec + 10 * k, 'carrier': c,
                             'x_m': s.x_m, 'y_m': s.y_m, 'z_m': 30.0,
                             'orientation_ccw_from_east_deg': orient[s.site] + 120 * sec})
    return pd.DataFrame(rows)


def main():
    hints = pd.read_csv(HERE / 'site_frequency_hints.csv').set_index('site')
    cal_path = HERE / 'calibration.json'
    factors = json.loads(cal_path.read_text())['factors'] if cal_path.exists() else {'S0': 1.75, 'S2': 1.75}
    inputs = HERE / 'inputs'
    inputs.mkdir(exist_ok=True)
    shutil.copy2(D08 / 'inputs/targets.csv', inputs / 'targets.csv')
    cases, camping = [], {}
    for az, seed in DRAWS:
        base = pd.read_csv(D08 / f'inputs/sites_24_{az}.csv')
        ref_sectors = pd.read_csv(D08 / f'simulation/results/n256_draw{seed}/sectors.csv')
        meas = pd.read_csv(D08 / f'inputs/ues_far_{seed}_{N_MEAS}.csv')
        for scen in ['S0', 'S2']:
            s = base.copy()
            if scen == 'S0':
                s['sector_count'] = 3
                s['carriers'] = 'B3'
            else:
                s['sector_count'] = s.site.map(lambda x: 2 if x == 'SITE_000554' else 3)
                s['carriers'] = s.site.map(lambda x: 'B3;B20' if (x in hints.index and hints.loc[x, 'multi_frequency'] is True)
                                           or (x in hints.index and str(hints.loc[x, 'multi_frequency']) == 'True') else 'B3')
            sp = inputs / f'sites_{scen}_{az}.csv'
            s.to_csv(sp, index=False, float_format='%.9f')
            cells = sector_table(s, ref_sectors)
            # Camping carrier for measurement UEs (analytical RSRP; exact vs ns-3 for B3).
            pts = meas[['x_m', 'y_m', 'z_m']].to_numpy(float)
            b3 = cells[cells.carrier == 'B3'].reset_index(drop=True)
            pw3 = received_power_w(pts, b3)
            rsrp3 = 10 * np.log10(pw3.max(axis=1) / (100 * 12)) + 30
            earfcn = np.full(len(meas), EARFCN['B3'])
            if (cells.carrier == 'B20').any():
                b20 = cells[cells.carrier == 'B20'].reset_index(drop=True)
                pw20 = received_power_w(pts, b20)
                rsrp20 = 10 * np.log10(pw20.max(axis=1) / (100 * 12)) + 30 + B20_RSRP_OFFSET_DB
                earfcn = np.where(rsrp3 >= CAMP_B3_MIN_RSRP, EARFCN['B3'],
                                  np.where(rsrp20 > rsrp3, EARFCN['B20'], EARFCN['B3']))
            camping[f'{scen}_{seed}'] = {'b20_share': float((earfcn == EARFCN['B20']).mean()),
                                         'cells': int(len(cells)), 'b20_cells': int((cells.carrier == 'B20').sum())}
            rows = [dict(ue_id=int(r.ue_id), x_m=f'{r.x_m:.9f}', y_m=f'{r.y_m:.9f}', z_m=f'{r.z_m:.9f}',
                         kind='measure', target_site='', target_sector='', target_prb='',
                         udp_interval_ms=MEAS_INTERVAL_MS, dl_earfcn=int(e))
                    for r, e in zip(meas.itertuples(), earfcn)]
            for i, c in enumerate(cells.itertuples()):
                a = math.radians(c.orientation_ccw_from_east_deg)
                rows.append(dict(ue_id=N_MEAS + i, x_m=f'{c.x_m + LOAD_DISTANCE_M * math.cos(a):.9f}',
                                 y_m=f'{c.y_m + LOAD_DISTANCE_M * math.sin(a):.9f}', z_m='1.500000000',
                                 kind='load', target_site=c.site, target_sector=c.sector, target_prb=f'{TARGET_PRB:.6f}',
                                 udp_interval_ms=f'{factors[scen] / TARGET_PRB:.6f}', dl_earfcn=EARFCN[c.carrier]))
            up = inputs / f'ues_{scen}_{seed}.csv'
            pd.DataFrame(rows).to_csv(up, index=False)
            cases.append(dict(name=f'{scen}_draw{seed}', scenario=scen, az=az, ue_seed=seed, ues=len(rows),
                              measurement_ues=N_MEAS, duration=4, warmup=1))
    plan = {'cases': cases, 'calibration_factors': factors, 'camping': camping,
            'site_carriers_S2': pd.read_csv(inputs / 'sites_S2_42.csv').set_index('site').carriers.to_dict(),
            'site_sectors_S2': pd.read_csv(inputs / 'sites_S2_42.csv').set_index('site').sector_count.to_dict(),
            'radio': {'mixed_cqi': 1, 'beamwidth': 120, 'exponent': 3, 'enb_power': 49, 'receiver_nf': 9,
                      'shadow_std': 0, 'dl_earfcn': 1300, 'udp_jitter': 1},
            'constants': {'camp_b3_min_rsrp_dbm': CAMP_B3_MIN_RSRP, 'b20_dl_gain_db': B20_DL_GAIN_DB,
                          'b20_rsrp_offset_db': B20_RSRP_OFFSET_DB, 'target_prb': TARGET_PRB},
            'source_sha256': sha(HERE / 'simulation/sindirgi_baseline.cc'),
            'input_hashes': {p.name: sha(p) for p in sorted(inputs.glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any S2 run):')[1].strip()}
    (HERE / 'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: plan[k] for k in ['camping', 'site_carriers_S2', 'calibration_factors']}, indent=1))


if __name__ == '__main__':
    main()
