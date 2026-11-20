"""Windows: freeze the voice-capacity stress test of the deneyler/26 model.

Predeclared design (written before any run of this experiment, agreed with the user):
- Question: how many simultaneous voice calls can each cell of the 8 evaluation sites carry before calls
  fail, and how does that compare with the KPI's normal and earthquake-time number of connected users?
- Model: identical to deneyler/26 FT_TA (RMa, 3GPP antenna, EVM 8 % in the private libns3-lte, distance
  correction, 8 dB shadow, frozen load factor 1.243). Only the users change. SRS periodicity is set to 320
  so that up to 320 UEs can attach to one cell (ns-3 default allows far fewer); this does not change radio.
- Users:
  * Background data: the 72 load users of deneyler/26 unchanged (normal-day KPI load, PRB ~0.23). Kept
    constant at every step; during the earthquakes the KPI data volume actually fell by about one third,
    so this is on the conservative side.
  * Voice: N voice users per cell, i.e. 3N per evaluation site (3 sectors), placed like the measured users
    of deneyler/15/26: distance from a random hourly Experia TA record of that site (TAAVG x 4.88 m,
    100 m-15 km), uniformly random direction, extra_loss_db from the deneyler/26 correction formula.
    Each voice user receives an AMR 12.2 kbps call: one packet every 20 ms (3GPP TS 26.114), UDP payload
    44 bytes (32 B speech frame + 12 B RTP), 72 B at IP level (28.8 kbps). Neighbour sites get no voice
    users (they stay at normal load and act as interference).
  * Steps N = 25, 50, 100, 200, 300 voice users per cell (300 is just under the 320 SRS limit). The same N
    is used for every evaluation cell, so each cell's capacity is read directly; the KPI number of connected
    users per cell (normal and x2 for the earthquake signature) is compared with it afterwards.
- Criteria (3GPP / ITU, fixed before the runs):
  * A voice user "can talk" if >= 99 % of its packets sent in the measurement window arrive within 100 ms
    (3GPP TS 23.203 QCI 1: 100 ms delay budget, 1 % packet loss; TS 26.132 Annex E: 99 % within budget).
  * A cell "carries" its load if >= 98 % of the voice users served by it can talk (VoIP-capacity convention
    of 3GPP TR 25.814 / ITU-R M.2135; to be checked against the documents before it is cited).
  * "No service": a voice user that is not RRC-connected at the end.
  * Measurement window: packets sent between 1 s (warm-up) and duration - 0.25 s.
- Runs: one azimuth draw (42, UE seed 701) for all steps because of run time; the step around the capacity
  limit and N = 2 x KPI may be repeated with draws 7/702 and 99/703 afterwards. 4 s per run.
- Regression first: with the new options unused the simulator must reproduce deneyler/16
  regression_disabled_draw701 byte for byte (after CRLF->LF).
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SIM = HERE/'simulation'
D26 = HERE.parent/'26_kaynakli_tam_model_2026-11-19'
EVAL = ['SITE_000440', 'SITE_000441', 'SITE_000130', 'SITE_000296', 'SITE_000443', 'SITE_000554', 'SITE_000482', 'SITE_000444']
STEPS = [25, 50, 100, 200, 300]
DRAW = (42, 701)
TS_M, DMIN, DMAX = 4.88, 100.0, 15000.0


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_ues(n_per_cell, seed, az, k0, k1, ta):
    sites = pd.read_csv(HERE/f'inputs/sites_S0TA_{az}.csv').set_index('site')
    old = pd.read_csv(D26/f'inputs/ues_FT_TA_{seed}.csv', dtype=str, keep_default_na=False)
    load = old[old.kind == 'load'].copy()
    cols = list(old.columns) + ['packet_size_bytes', 'voice']
    rng = np.random.default_rng(seed*1000 + n_per_cell)
    rows = []
    for s in EVAL:
        pool = ta.loc[ta.site == s, 'd'].to_numpy()
        for _ in range(3*n_per_cell):
            d = float(pool[rng.integers(len(pool))])
            a = rng.uniform(0, 2*np.pi)
            r = {c: '' for c in cols}
            r.update(ue_id=str(len(rows)), x_m=f'{sites.loc[s, "x_m"] + d*np.cos(a):.9f}', y_m=f'{sites.loc[s, "y_m"] + d*np.sin(a):.9f}',
                     z_m='1.500000000', kind='voice', udp_interval_ms='20', dl_earfcn=load.dl_earfcn.iloc[0],
                     placement_site=s, placement_distance_m=f'{d:.1f}', extra_loss_db=f'{k0 + k1*np.log10(d):.6f}',
                     packet_size_bytes='44', voice='1')
            rows.append(r)
    load['ue_id'] = [str(len(rows) + i) for i in range(len(load))]
    load['packet_size_bytes'] = '512'
    load['voice'] = '0'
    out = pd.concat([pd.DataFrame(rows), load], ignore_index=True)[cols]
    path = HERE/'inputs'/f'ues_V{n_per_cell}_{seed}.csv'
    out.to_csv(path, index=False, lineterminator='\n')
    return path, len(out)


def main():
    spec = importlib.util.spec_from_file_location('cqi11', ROOT/'deneyler/11_cqi_karsilastirmasi_2026-11-15/compare.py')
    cqi11 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cqi11)
    kpi = pd.read_csv(ROOT/'deneyler/09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', parse_dates=['DATETIME'])
    kpi = kpi[kpi.site.isin(EVAL)]
    bad = pd.Series(False, index=kpi.index)
    for a, b in cqi11.EXCLUDE:
        bad |= kpi.DATETIME.between(a, b, inclusive='left')
    u = 'Avg_Sim_RRC_Connected_User_Num_ERI'
    normal = kpi[~bad]
    base = normal.groupby(['site', 'CELL'])[u].mean().groupby('site').mean()
    busy = normal[normal.DATETIME.dt.hour.between(19, 22)].groupby(['site', 'CELL'])[u].mean().groupby('site').mean()
    kpi_users = {s: {'normal_mean_per_cell': float(base[s]), 'evening_mean_per_cell': float(busy[s]),
                     'earthquake_x2_per_cell': float(2*base[s])} for s in EVAL}

    exp = pd.read_csv(ROOT/'deneyler/13_hucre_imzasi_2026-11-15/experia_cells.csv.gz').dropna(subset=['AVG(TAAVG)'])
    exp['d'] = (exp['AVG(TAAVG)']*TS_M).clip(DMIN, DMAX)
    corr = json.loads((D26/'correction.json').read_text(encoding='utf-8'))
    k0 = corr['model_fit_a_b'][0] - corr['experia_fit_a_b'][0]
    k1 = corr['model_fit_a_b'][1] - corr['experia_fit_a_b'][1]
    az, seed = DRAW
    cases = []
    steps = [int(x) for x in sys.argv[1:]] or STEPS
    for n in steps:
        path, total = write_ues(n, seed, az, k0, k1, exp)
        cases.append({'name': f'V{n}_draw{seed}', 'label': f'V{n}', 'voice_per_cell': n, 'az': az, 'ue_seed': seed,
                      'ues': total, 'sites_file': f'sites_S0TA_{az}.csv', 'ue_file': path.name, 'shadow_seed': az})
    p26 = json.loads((D26/'plan.json').read_text(encoding='utf-8'))
    plan = {'radio': dict(p26['radio'], srs_periodicity=320), 'sources': p26['sources'], 'correction': corr,
            'load_calibration': p26['load_calibration'], 'kpi_connected_users': kpi_users, 'cases': cases,
            'criteria': {'voice_deadline_ms': 100, 'user_can_talk_min_on_time_share': 0.99,
                         'cell_carries_min_satisfied_share': 0.98, 'window_s': [1.0, 3.75]},
            'eval_sites': EVAL, 'regression': p26['regression'],
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py', 'build_private_lte.py']},
            'input_hashes': {p.name: sha(p) for p in sorted((HERE/'inputs').glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run of this experiment, agreed with the user):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(kpi_users, indent=1))
    print([(c['name'], c['ues']) for c in cases])


if __name__ == '__main__':
    main()
