"""Windows: outage events in kpi41.csv.gz classified as automatic (fault) / manual / mixed (KURALLAR.md).
Writes olaylar41.csv (one row per event, counts only) and olay41.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
A, AU, MA = 'EUtranCell_Availability_PC_ERI', 'DownTime_Auto_PC_ERI', 'DownTime_Man_PC_ERI'
U, V = 'Avg_Sim_RRC_Connected_User_Num_ERI', 'DLTRF_VOLUME_MBYTE_ERI'
QUAKES = [pd.Timestamp('2025-08-10 19:53'), pd.Timestamp('2025-10-27 22:48')]
SLOT = pd.Timedelta('15min')
FOCUS = {'SITE_000130': '130 (modelde kapatılan)', 'SITE_000482': '482 (modelde kapatılan)', 'SITE_000200': '200 (gerçek kesinti karşılaştırması)',
         'SITE_000438': '28 Eki toplu', 'SITE_000199': '28 Eki toplu', 'SITE_000389': '28 Eki toplu', 'SITE_000208': '28 Eki toplu',
         'SITE_000205': '28 Eki toplu', 'SITE_000283': '28 Eki toplu', 'SITE_000484': 'Ağustos', 'SITE_000494': 'Ağustos',
         'SITE_000552': 'Ekim', 'SITE_000011': '011 (Ağustos)'}


def events(g, n_cells):
    """Consecutive slots of one site where at least one cell is below 99 % availability."""
    g = g.sort_values('DATETIME')
    slot = g.groupby('DATETIME').agg(down=(A, lambda s: (s < 0.99).sum()), off=(A, lambda s: (s <= 0.0).sum()),
                                      lost=(A, lambda s: (1 - s).sum()),
                                      auto=(AU, 'sum'), man=(MA, 'sum'), users=(U, 'sum'), vol=(V, 'sum'))
    bad = slot[slot.down > 0]
    if bad.empty:
        return []
    grp = (bad.index.to_series().diff() != SLOT).cumsum()
    out = []
    for _, b in bad.groupby(grp.to_numpy()):
        t0, t1 = b.index.min(), b.index.max() + SLOT
        per_cell = g[(g.DATETIME >= t0) & (g.DATETIME < t1)].assign(l=lambda x: (1 - x[A])*0.25).groupby('CELL').l.sum()
        if per_cell.max() < 0.5:
            continue
        before = slot[(slot.index >= t0 - pd.Timedelta('1h')) & (slot.index < t0)]
        tot = b.auto.sum() + b.man.sum()
        auto_share = float(b.auto.sum()/tot) if tot > 0 else np.nan
        full = b[b.off == n_cells]                     # every cell fully off in the slot
        q = min(QUAKES, key=lambda x: abs((t0 - x).total_seconds()))
        out.append({'start': str(t0), 'end': str(t1), 'hours': round((t1 - t0).total_seconds()/3600, 2),
                    'cells_down_max': int(b.down.max()), 'cells_site': int(n_cells),
                    'whole_site': bool(b.down.max() == n_cells), 'slots_all_cells_off': int(len(full)), 'cell_hours_lost': round(float(per_cell.sum()), 2),
                    'auto_share': round(auto_share, 3), 'man_share': round(1 - auto_share, 3) if tot > 0 else np.nan,
                    'class': 'arıza' if auto_share >= 0.9 else ('elle kapatma' if auto_share <= 0.1 else 'karışık'),
                    'users_before': round(float(before.users.mean()), 1) if len(before) else np.nan,
                    'users_min_during': round(float(b.users.min()), 1),
                    'users_traffic_zero_when_all_cells_off': bool(((full.vol <= 0.01) & (full.users <= 0.01)).all()) if len(full) else None,
                    'hours_from_nearest_quake': round((t0 - q).total_seconds()/3600, 1)})
    return out


def main():
    k = pd.read_csv(HERE/'kpi41.csv.gz', parse_dates=['DATETIME'])
    check = (k[A] + k[AU] + k[MA] - 1).abs().max()
    rows = []
    for (site, day), g in k.groupby(['site', k.DATETIME.dt.date]):
        for e in events(g, g.CELL.nunique()):
            rows.append({'site': site, 'day': str(day), 'focus': FOCUS.get(site, ''), **e})
    ev = pd.DataFrame(rows).sort_values(['start', 'site'])
    ev.to_csv(HERE/'olaylar41.csv', index=False)
    f = ev[ev.focus != '']
    print('max |avail+auto+man-1| =', round(float(check), 6))
    print('all events', len(ev), ev['class'].value_counts().to_dict())
    print(f[['site', 'focus', 'start', 'hours', 'cells_down_max', 'cells_site', 'auto_share', 'class', 'users_before',
             'users_min_during', 'users_traffic_zero_when_all_cells_off', 'hours_from_nearest_quake']].to_string())
    out = {'sum_check_max_abs': float(check), 'events_total': int(len(ev)), 'by_class': ev['class'].value_counts().to_dict(),
           'by_class_quake_window_0_24h': ev[(ev.hours_from_nearest_quake >= 0) & (ev.hours_from_nearest_quake <= 24)]['class'].value_counts().to_dict(),
           'focus_events': f.to_dict('records')}
    (HERE/'olay41.json').write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding='utf-8')


if __name__ == '__main__':
    main()
