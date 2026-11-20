"""Windows: step 2 - how much load did the 8 evaluation sites really carry right after the two earthquakes?

Data: deneyler/09 kpi_cells.csv.gz (15-min KPI). Earthquakes: 2025-08-10 19:53 and 2025-10-27 22:48.
Window: from the earthquake's 15-min slot until the first site outage found in deneyler/30 (130 at 21:30
on Aug 10; 482 at 01:15 on Oct 28), so the load is not mixed with the outage. Baseline: the same clock
times on the 7 days before. Per evaluation site, cell means: connected users (Avg_Sim_RRC_Connected),
DL PRB use (KPI already 0-1), DL volume per user (-> kbit/s per connected user; volume units not verified, deneyler/09, so only the ratio is used). Both the window mean and the highest
15-min slot are reported. Only aggregates are written (no raw rows).
"""
from pathlib import Path
import json

import pandas as pd

HERE = Path(__file__).resolve().parent
U, P, V = 'Avg_Sim_RRC_Connected_User_Num_ERI', 'DL_PRB_Util_%_ERI', 'DLTRF_VOLUME_MBYTE_ERI'
QUAKES = [('2025-08-10 19:53', '2025-08-10 21:30'), ('2025-10-27 22:48', '2025-10-28 01:15')]


def window(k, a, b):
    return k[(k.DATETIME >= a) & (k.DATETIME < b)]


def summarise(w):
    c = w.groupby(['site', 'DATETIME', 'CELL'])[[U, P, V]].mean().reset_index()
    per_slot = c.groupby(['site', 'DATETIME']).agg(users=(U, 'mean'), prb=(P, 'mean'), vol=(V, 'sum'), tot_users=(U, 'sum')).reset_index()
    per_slot['kbps_per_user'] = per_slot.vol*8e3/(15*60)/per_slot.tot_users.where(per_slot.tot_users > 0)
    g = per_slot.groupby('site')
    return pd.DataFrame({'users_per_cell': g.users.mean(), 'users_per_cell_peak': g.users.max(),
                         'prb': g.prb.mean(), 'prb_peak': g.prb.max(), 'kbps_per_user': g.kbps_per_user.mean()})


def main():
    k = pd.read_csv(HERE.parent/'09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', parse_dates=['DATETIME'])
    k = k[k.role == 'Evaluation']
    out = {}
    for q, end in QUAKES:
        a, b = pd.Timestamp(q).floor('15min'), pd.Timestamp(end)
        quake = summarise(window(k, a, b))
        base = summarise(pd.concat([window(k, a - pd.Timedelta(days=d), b - pd.Timedelta(days=d)) for d in range(1, 8)]))
        t = quake.join(base, rsuffix='_normal')
        t['users_ratio'] = t.users_per_cell/t.users_per_cell_normal
        t['prb_ratio'] = t.prb/t.prb_normal
        print(f'\n=== {q} -> {end}  (normal = same hours, 7 days before)')
        print(t[['users_per_cell_normal', 'users_per_cell', 'users_per_cell_peak', 'users_ratio', 'prb_normal', 'prb', 'prb_peak',
                 'kbps_per_user_normal', 'kbps_per_user']].round(2).to_string())
        tot = {'users_ratio_all_sites': float(t.users_per_cell.sum()/t.users_per_cell_normal.sum()),
               'prb_ratio_all_sites': float(t.prb.mean()/t.prb_normal.mean())}
        print(tot)
        out[q] = {'window_end': end, 'sites': t.round(4).to_dict('index'), **tot}
    (HERE/'deprem_yuku.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
