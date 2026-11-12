"""Windows: KPI load profile for the simulated 24 sites (normal day + two earthquakes).

Earthquake times (local, from AFAD/USGS public reports; verify in report): M6.1 2025-08-10 19:53,
M6.1 2025-10-27 22:48. KPI timestamps appear to be local: the jump is in the 19:45 and 22:45 bins.
"""
from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRB, USERS, DLMB = 'DL_PRB_Util_%_ERI', 'Avg_Sim_RRC_Connected_User_Num_ERI', 'DLTRF_VOLUME_MBYTE_ERI'
QUAKES = {'2025-08-10': pd.Timestamp('2025-08-10 19:45'), '2025-10-27': pd.Timestamp('2025-10-27 22:45')}
# Affected windows (quake bin through next day) are excluded from the normal-day baseline.
EXCLUDE = [(pd.Timestamp('2025-08-10 19:45'), pd.Timestamp('2025-08-12 00:00')),
           (pd.Timestamp('2025-10-27 22:45'), pd.Timestamp('2025-10-29 00:00'))]


def main():
    with (ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12/inputs/sites_24_42.csv').open(encoding='utf-8-sig') as f:
        sim_sites = {r['site']: r['role'] for r in csv.DictReader(f)}
    d = pd.read_csv(HERE / 'kpi_cells.csv.gz', parse_dates=['DATETIME'])
    d = d[d.site.isin(sim_sites)].copy()
    d['group'] = d.role.map({'Evaluation': 'ana 8', 'Interference buffer': 'komşu'})
    d['hour'] = d.DATETIME.dt.hour
    affected = pd.Series(False, index=d.index)
    for a, b in EXCLUDE:
        affected |= d.DATETIME.between(a, b, inclusive='left')
    normal = d[~affected]
    out = {'sites': len(sim_sites), 'cells': int(d.CELL.nunique()),
           'cells_by_group': d.groupby('group').CELL.nunique().to_dict(),
           'normal_days': sorted({str(x) for x in normal.DATETIME.dt.date})}

    # 1) Normal-day hourly profile: mean PRB per cell, users per cell.
    hourly = normal.groupby(['group', 'hour']).agg(prb=(PRB, 'mean'), users_per_cell=(USERS, 'mean'),
                                                   dl_mb_per_cell=(DLMB, 'mean')).reset_index()
    hourly.to_csv(HERE / 'normal_hourly_profile.csv', index=False, float_format='%.4f')
    allh = normal.groupby('hour').agg(prb=(PRB, 'mean'), users=(USERS, 'mean'))
    busy = int(allh.prb.idxmax())
    out['normal'] = {'busy_hour': busy,
                     'prb_busy_hour_mean': float(allh.prb.max()), 'prb_night_min': float(allh.prb.min()),
                     'prb_daily_mean': float(normal[PRB].mean()),
                     'prb_busy_hour_p90_cell': float(normal[normal.hour == busy][PRB].quantile(.9))}

    # 2) Earthquake windows vs same clock time on normal days (24 sites, totals per 15 min).
    tot = d.groupby(['DATETIME']).agg(prb=(PRB, 'mean'), users=(USERS, 'sum'), dl=(DLMB, 'sum'),
                                     drop=('ERAB_Drop_PC_ERI', 'mean'), cells=('CELL', 'nunique')).reset_index()
    tot['clock'] = tot.DATETIME.dt.strftime('%H:%M')
    ntot = normal.groupby('DATETIME').agg(prb=(PRB, 'mean'), users=(USERS, 'sum'), dl=(DLMB, 'sum'),
                                         drop=('ERAB_Drop_PC_ERI', 'mean')).reset_index()
    ntot['clock'] = ntot.DATETIME.dt.strftime('%H:%M')
    ref = ntot.groupby('clock')[['prb', 'users', 'dl', 'drop']].median()
    quake = {}
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.5), sharex='col')
    for row, (day, t0) in enumerate(QUAKES.items()):
        w = tot[tot.DATETIME.between(t0 - pd.Timedelta('3h'), t0 + pd.Timedelta('6h'))].copy()
        w = w.join(ref, on='clock', rsuffix='_ref')
        w['hours'] = (w.DATETIME - t0) / pd.Timedelta('1h')
        peak = w[w.hours.between(0, 0.5)]
        pre = w[w.hours.between(-1, -0.25)]
        quake[day] = {'bin': str(t0),
                      'users_ratio_vs_hour_before': float(peak.users.max() / pre.users.mean()),
                      'users_ratio_vs_normal_same_time': float((peak.users / peak.users_ref).max()),
                      'prb_min_first_30min': float(peak.prb.min()), 'prb_hour_before': float(pre.prb.mean()),
                      'dl_ratio_vs_hour_before': float(peak.dl.min() / pre.dl.mean()),
                      'drop_max_first_30min': float(peak['drop'].max()), 'drop_hour_before': float(pre['drop'].mean()),
                      'users_ratio_after_3h': float(w[w.hours.between(3, 3.25)].users.mean() / pre.users.mean())}
        for col, (m, lab) in enumerate([('users', 'Bağlı kullanıcı (toplam)'), ('prb', 'DL PRB kullanımı (ort.)'),
                                         ('dl', 'DL hacim (MB / 15 dk)')]):
            ax = axes[row][col]
            ax.plot(w.hours, w[m], marker='.', label=f'{day}')
            ax.plot(w.hours, w[m + '_ref'], color='grey', ls='--', label='normal gün medyanı')
            ax.axvline(0, color='red', lw=1)
            ax.set_title(f'{day} — {lab}', fontsize=10)
            ax.grid(alpha=.3)
            if row == 1:
                ax.set_xlabel('Depremden sonra saat')
        axes[row][0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / 'deprem_yuk_degisimi.png', dpi=150)
    out['earthquakes'] = quake

    # 3) Per-site normal busy-hour PRB and users per cell (20:00-23:59 on normal days).
    eve = normal[normal.hour.between(20, 23)]
    site = eve.groupby('site').agg(role=('role', 'first'), cells=('CELL', 'nunique'), prb=(PRB, 'mean'),
                                   users_per_cell=(USERS, 'mean')).reset_index()
    site.to_csv(HERE / 'site_busy_hour.csv', index=False, float_format='%.4f')
    out['busy_window_20_24'] = {'prb_mean_all': float(eve[PRB].mean()),
                                'prb_mean_core': float(eve[eve.role == 'Evaluation'][PRB].mean())}

    # Simulation load levels (target mean DL PRB over the 24 sites' cells).
    out['simulation_targets'] = {
        'night': round(out['normal']['prb_night_min'], 3),
        'normal_daily_mean': round(out['normal']['prb_daily_mean'], 3),
        'normal_busy_hour': round(out['normal']['prb_busy_hour_mean'], 3),
        'busy_hour_p90_cell': round(out['normal']['prb_busy_hour_p90_cell'], 3)}
    (HERE / 'profile.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
