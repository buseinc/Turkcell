"""Windows: which cells went off air after the two Sındırgı earthquakes (KPI cell availability)?

Data: deneyler/09 kpi_cells.csv.gz (15-min KPI, 47 sites: 8 evaluation + interference buffer).
Earthquakes: 2025-08-10 19:53 and 2025-10-27 22:48 (local time, as in the KPI timestamps).
Window: from the earthquake's 15-min slot to 24 h later. Cells already down (< 50 % availability) on the
day before are counted as chronic outages and left out. Outage hours = sum over slots of (1 - availability) x 0.25 h.
Also reports the connected users of each affected cell in the hour before the earthquake (who lost service)
and the change in connected users of the other cells of the same 47 sites during the outage.
"""
from pathlib import Path
import json

import pandas as pd

HERE = Path(__file__).resolve().parent
A, U = 'EUtranCell_Availability_PC_ERI', 'Avg_Sim_RRC_Connected_User_Num_ERI'
QUAKES = [('2025-08-10 19:53', '2025-08-09'), ('2025-10-27 22:48', '2025-10-26')]


def main():
    k = pd.read_csv(HERE.parent/'09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', parse_dates=['DATETIME'])
    cells_per_site = k.groupby('site').CELL.nunique()
    out = {}
    for q, prev in QUAKES:
        t0 = pd.Timestamp(q)
        w = k[(k.DATETIME >= t0.floor('15min')) & (k.DATETIME < t0 + pd.Timedelta('24h'))]
        chronic = set(k[(k.DATETIME.dt.date == pd.Timestamp(prev).date()) & (k[A] < 0.5)].CELL)
        d = w[(w[A] < 0.99) & ~w.CELL.isin(chronic)].assign(lost_h=lambda x: (1 - x[A])*0.25)
        before = k[(k.DATETIME >= t0 - pd.Timedelta('1h')) & (k.DATETIME < t0.floor('15min'))].groupby('CELL')[U].mean()
        c = d.groupby(['site', 'role', 'CELL']).agg(outage_h=('lost_h', 'sum'), min_av=(A, 'min'),
                                                   start=('DATETIME', 'min'), end=('DATETIME', 'max')).reset_index()
        c['users_before'] = c.CELL.map(before)
        s = c[c.outage_h >= 0.25].groupby(['site', 'role']).agg(
            cells_out=('CELL', 'size'), outage_h_total=('outage_h', 'sum'), outage_h_max=('outage_h', 'max'),
            min_av=('min_av', 'min'), users_before=('users_before', 'sum'), start=('start', 'min'), end=('end', 'max')).reset_index()
        s['cells_total'] = s.site.map(cells_per_site)
        s = s.sort_values('outage_h_total', ascending=False)
        print(f'\n=== Deprem {q}  (önceki gün zaten kapalı {len(chronic)} hücre hariç)')
        print(s.round(2).to_string(index=False))
        out[q] = s.assign(start=s.start.astype(str), end=s.end.astype(str)).round(3).to_dict('records')
    (HERE/'kesinti.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
