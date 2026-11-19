"""Windows: diagnostic, no new simulation runs. Chosen after seeing deneyler/20-24; reported as such.

1. Experia (raw workbook, local only): SINR vs RSRP curve, reporting range.
2. Simulation (deneyler/24 LC_TA): same curve for data-channel SINR, control SINR and SNR.
3. Re-evaluation with the 3GPP TS 36.104 transmitter EVM limit for 64QAM (8 %), applied per sample as
   SINR_eff = -10 log10(10^(-SINR/10) + EVM^2) (ceiling 21.9 dB). Not a fitted value; same rule for every run.
Output: analysis.json (no operator raw values beyond binned medians and the reporting range).
"""
from pathlib import Path
import json

import numpy as np
import openpyxl
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D = ROOT/'deneyler'
EVM = 0.08
BINS = [-125, -115, -105, -95, -85]
RUNS = {'S0': D/'14_temel_s0_ve_cok_tasiyici_s2_2026-11-15/simulation/results/S0_draw{}',
        'DC_TA': D/'22_veri_tabanli_mesafe_duzeltmesi_2026-11-17/simulation/results/DC_TA_draw{}',
        'A3_TA': D/'23_uc_gpp_anten_deseni_2026-11-18/simulation/results/A3_TA_draw{}',
        'LC_TA': D/'24_yuk_kalibrasyonu_2026-11-19/simulation/results/LC_TA_draw{}'}


def experia():
    ws = openpyxl.load_workbook(ROOT/'ana_proje/experia/experia.xlsx', read_only=True).worksheets[0]
    s, p = [], []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[5] is not None and r[6] is not None:
            s.append(r[5]); p.append(r[6])
    s, p = np.array(s, float), np.array(p, float)
    return {'rows': int(len(s)), 'sinr_min': float(s.min()), 'sinr_max': float(s.max()), 'rows_at_25': int((s == 25).sum()),
            'by_rsrp_bin': {lo: float(np.median(s[(p >= lo) & (p < lo+10)])) for lo in BINS}}


def samples(folder):
    c = pd.read_csv(folder/'sinr_components.csv', usecols=['time_s', 'ue_id', 'synthetic_cell_id', 'native_rsrp_dbm',
                                                            'native_sinr_db', 'control_sinr_db', 'snr_db'])
    u = pd.read_csv(folder/'ues.csv')[['ue_id', 'synthetic_cell_id', 'connected_at_s']].rename(columns={'synthetic_cell_id': 'final'})
    c = c.merge(u, on='ue_id')
    c = c[(c.synthetic_cell_id == c.final) & (c.time_s >= np.maximum(1, c.connected_at_s))].copy()
    c['evm_sinr_db'] = -10*np.log10(10**(-c.native_sinr_db/10) + EVM**2)
    return c


def main():
    t = pd.read_csv(D/'24_yuk_kalibrasyonu_2026-11-19/inputs/targets.csv').set_index('site')
    out = {'evm': EVM, 'experia': experia(), 'runs': {}}
    for name, base in RUNS.items():
        sites = {k: [] for k in ['native_sinr_db', 'evm_sinr_db']}
        curve = []
        for seed in [701, 702, 703]:
            f = Path(str(base).format(seed))
            c = samples(f)
            curve.append(c.groupby('ue_id')[['native_rsrp_dbm', 'native_sinr_db', 'control_sinr_db', 'snr_db', 'evm_sinr_db']].median())
            m = c[c.ue_id < 256]
            sec = pd.read_csv(f/'sectors.csv')[['synthetic_cell_id', 'site']]
            for k in sites:
                pu = m.groupby(['ue_id', 'synthetic_cell_id'])[k].mean().reset_index()
                sites[k].append(pu.groupby('synthetic_cell_id')[k].mean().reset_index().merge(sec).groupby('site')[k].mean())
        curve = pd.concat(curve)
        r = {'curve_by_rsrp_bin': {lo: {k: float(curve[k][(curve.native_rsrp_dbm >= lo) & (curve.native_rsrp_dbm < lo+10)].median())
                                        for k in ['native_sinr_db', 'control_sinr_db', 'snr_db', 'evm_sinr_db']} for lo in BINS}}
        for k, v in sites.items():
            m = sum(v)/3
            m = m.loc[[x for x in t.index if x in m.index]]
            e = m - t.sinr_target.loc[m.index]
            sp = t.split.loc[m.index]
            r[k] = {'holdout_mae': float(e[sp == 'holdout'].abs().mean()), 'train_mae': float(e[sp == 'train'].abs().mean()),
                    'signed': {s: float(x) for s, x in e.items()}}
        out['runs'][name] = r
        print(name, {k: round(r[k]['holdout_mae'], 2) for k in sites})
    (HERE/'analysis.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out['experia'], indent=1))


if __name__ == '__main__':
    main()
