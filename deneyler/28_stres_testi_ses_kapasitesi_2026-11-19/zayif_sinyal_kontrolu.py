"""Windows: are the model's weak-signal (SINR < 0 dB) users as common as in Experia?

Experia has no per-user rows, only hourly per-cell averages of per-session median SINR, together with the
hourly mean TA (distance). So the comparison is made per distance band:
- Experia: hourly records of the 8 evaluation sites, distance = TAAVG x 4.88 m.
- Model, normal load: deneyler/26 FT_TA measured users (3 draws), distance = placement distance.
- Model, stress: deneyler/28 V25 voice users (high load, more interference).
An hourly Experia value is an average over several users, so its spread is narrower than per-user values;
its share below 0 dB is a lower bound for the real per-user share. The band medians are comparable.
"""
from pathlib import Path
import json

import pandas as pd

HERE = Path(__file__).resolve().parent
D = HERE.parent
EVAL = ['SITE_000440', 'SITE_000441', 'SITE_000130', 'SITE_000296', 'SITE_000443', 'SITE_000554', 'SITE_000482', 'SITE_000444']
BINS = [0, 1000, 2000, 4000, 8000, 16000]


def model_users(res, ue_file, kind):
    u = pd.read_csv(ue_file)
    r = pd.read_csv(res/'radio_samples.csv')
    s = r[r.time_s >= 1].groupby('ue_id').sinr_db.median().rename('sinr')
    u = u[(u.kind == kind) & u.placement_site.isin(EVAL)].join(s, on='ue_id')
    return pd.DataFrame({'d': u.placement_distance_m, 'sinr': u.sinr}).dropna()


def table(df):
    df = df.assign(band=pd.cut(df.d, BINS))
    t = df.groupby('band', observed=True).agg(n=('sinr', 'size'), median_sinr=('sinr', 'median'),
                                              below0=('sinr', lambda x: (x < 0).mean()))
    t.loc['all'] = [len(df), df.sinr.median(), (df.sinr < 0).mean()]
    return t


def main():
    e = pd.read_csv(D/'13_hucre_imzasi_2026-11-15/experia_cells.csv.gz').dropna(subset=['AVG(TAAVG)', 'AVG(MED_SINRMEDIAN)'])
    e = e[e.site.isin(EVAL)]
    exp = pd.DataFrame({'d': (e['AVG(TAAVG)']*4.88).clip(100, 15000), 'sinr': e['AVG(MED_SINRMEDIAN)']})
    d26 = D/'26_kaynakli_tam_model_2026-11-19'
    m26 = pd.concat([model_users(d26/f'simulation/results/FT_TA_draw{s}', d26/f'inputs/ues_FT_TA_{s}.csv', 'measure')
                     for s in (701, 702, 703)])
    m28 = model_users(HERE/'simulation/results/V25_draw701', HERE/'inputs/ues_V25_701.csv', 'voice')
    out = {}
    for name, df in [('experia_hourly', exp), ('model_normal_load_26', m26), ('model_V25_stress', m28)]:
        t = table(df)
        out[name] = {str(k): {c: float(v) for c, v in row.items()} for k, row in t.iterrows()}
        print(f'\n{name}\n', t.round(2).to_string())
    (HERE/'zayif_sinyal_kontrolu.json').write_text(json.dumps(out, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
