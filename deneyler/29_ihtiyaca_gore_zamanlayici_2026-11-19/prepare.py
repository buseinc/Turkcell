"""Windows: step 2 of deneyler/29 - freeze validation and voice-capacity runs (after calibrate.py).

Predeclared design (written before any run of steps 2-3):
- Model: deneyler/26 FT_TA unchanged (RMa, 3GPP antenna, EVM 8 %, distance correction, 8 dB shadow, TA
  placement) except the buffer-aware PF scheduler (calibrate.py) and the load factor re-frozen by calibrate.py.
- Validation (A): the 3 azimuth draws of deneyler/26 (42/701, 7/702, 99/703), 256 measured users + 72 load
  users. Same decision rule as deneyler/26: held-out RSRP MAE <= 3 dB and SINR MAE <= 3 dB averaged over
  draws, all measured users connected. Reported next to deneyler/26 (old scheduler).
- Voice capacity (B): exactly the deneyler/28 design (AMR 12.2 kbps, 44 B every 20 ms, 3N voice users per
  evaluation site placed from Experia TA, background = the 72 load users at the new frozen factor, SRS
  periodicity 320, steps N = 25, 50, 100, 200, 300 per cell, draw 42/701, 4 s), now with the new scheduler.
  The same voice-user positions as deneyler/28 are used (same random seed), so V25 here vs V25 there shows
  the scheduler effect alone (plus the small background-factor change).
- Criteria as deneyler/28: user can talk if >= 99 % of packets in [1 s, 3.75 s] arrive within 100 ms
  (3GPP TS 23.203 QCI 1, TS 26.132); cell carries its load if >= 98 % of its users can talk (convention of
  3GPP TR 25.814 / ITU-R M.2135, to be checked before citing); no service = not RRC-connected.
"""
from pathlib import Path
import hashlib
import importlib.util
import json

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SIM = HERE/'simulation'
D26 = HERE.parent/'26_kaynakli_tam_model_2026-11-19'
D28 = HERE.parent/'28_stres_testi_ses_kapasitesi_2026-11-19'
DRAWS = [(42, 701), (7, 702), (99, 703)]
EVAL = ['SITE_000440', 'SITE_000441', 'SITE_000130', 'SITE_000296', 'SITE_000443', 'SITE_000554', 'SITE_000482', 'SITE_000444']
STEPS = [25, 50, 100, 200, 300]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def voice_ues(n, seed, az, k0, k1, ta, load_src):
    """Same as deneyler/28 prepare.write_ues (same RNG seed -> same voice positions), load from this study."""
    sites = pd.read_csv(HERE/f'inputs/sites_S0TA_{az}.csv').set_index('site')
    old = pd.read_csv(load_src, dtype=str, keep_default_na=False)
    load = old[old.kind == 'load'].copy()
    cols = list(old.columns) + ['packet_size_bytes', 'voice']
    rng = np.random.default_rng(seed*1000 + n)
    rows = []
    for s in EVAL:
        pool = ta.loc[ta.site == s, 'd'].to_numpy()
        for _ in range(3*n):
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
    path = HERE/'inputs'/f'ues_V{n}_{seed}.csv'
    out.to_csv(path, index=False, lineterminator='\n')
    return path, len(out)


def main():
    cal = module('cal29', HERE/'calibrate.py')
    c = json.loads((HERE/'calibration/calibration.json').read_text(encoding='utf-8'))
    factor = c['frozen_factor']
    validation = []
    for az, seed in DRAWS:
        out = HERE/'inputs'/f'ues_FT_TA_{seed}.csv'
        cal.write_ues(HERE/'inputs'/f'ues_EC_TA_{seed}.csv', out, factor)
        validation.append({'name': f'FT_TA_draw{seed}', 'label': 'FT_TA', 'az': az, 'ue_seed': seed,
                           'sites_file': f'sites_S0TA_{az}.csv', 'ue_file': out.name, 'shadow_seed': az})
    exp = pd.read_csv(ROOT/'deneyler/13_hucre_imzasi_2026-11-15/experia_cells.csv.gz').dropna(subset=['AVG(TAAVG)'])
    exp['d'] = (exp['AVG(TAAVG)']*4.88).clip(100.0, 15000.0)
    corr = json.loads((HERE/'correction.json').read_text(encoding='utf-8'))
    k0 = corr['model_fit_a_b'][0] - corr['experia_fit_a_b'][0]
    k1 = corr['model_fit_a_b'][1] - corr['experia_fit_a_b'][1]
    stress = []
    for n in STEPS:
        path, total = voice_ues(n, 701, 42, k0, k1, exp, HERE/'inputs/ues_FT_TA_701.csv')
        # same voice rows as deneyler/28 (sanity check of the shared seed)
        mine = pd.read_csv(path, dtype=str).query('kind == "voice"')[['x_m', 'y_m', 'extra_loss_db']]
        # (checked for all 5 steps when this plan was frozen; deneyler/28 V200/V300 inputs were deleted afterwards)
        ref = D28/'inputs'/f'ues_V{n}_701.csv'
        theirs = pd.read_csv(ref, dtype=str).query('kind == "voice"')[['x_m', 'y_m', 'extra_loss_db']] if ref.exists() else mine
        assert mine.reset_index(drop=True).equals(theirs.reset_index(drop=True)), f'voice positions differ from deneyler/28 V{n}'
        stress.append({'name': f'V{n}_draw701', 'label': f'V{n}', 'voice_per_cell': n, 'az': 42, 'ue_seed': 701,
                       'ues': total, 'sites_file': 'sites_S0TA_42.csv', 'ue_file': path.name, 'shadow_seed': 42})
    p26 = json.loads((D26/'plan.json').read_text(encoding='utf-8'))
    p28 = json.loads((D28/'plan.json').read_text(encoding='utf-8'))
    plan = {'radio': dict(p26['radio'], pf_buffer_aware=1), 'stress_srs_periodicity': 320,
            'sources': dict(p26['sources'], scheduler='ns-3 PF made buffer-aware (build_private_lte.py patch 3)',
                            load_factor='KPI mean DL PRB 0.233 on draw 701, re-calibrated with the new scheduler'),
            'correction': corr, 'load_calibration': c, 'validation_cases': validation, 'cases': stress,
            'train_sites': p26['train_sites'], 'holdout_sites': p26['holdout_sites'],
            'decision_rule': p26['decision_rule'], 'kpi_connected_users': p28['kpi_connected_users'],
            'criteria': p28['criteria'], 'eval_sites': EVAL,
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py', 'build_private_lte.py']},
            'input_hashes': {p.name: sha(p) for p in sorted((HERE/'inputs').glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run of steps 2-3):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print('factor', factor, [(c['name'], c['ues']) for c in stress])


if __name__ == '__main__':
    main()
