"""Windows: within-site cell signatures (draft 'Radio consistency checks'). Descriptive evidence only.

Written before looking at the results:
- Per cell: Experia mean/sd of RSRP, SINR, RSRQ, raw TAAVG, observed hours; KPI mean DL PRB, connected
  users, DL volume, CQI, RACH TA, and the share of 15-min intervals with a reported inter-frequency /
  intra-frequency / IRAT handover success rate (a reported rate implies attempts of that type).
- Per site pair of cells: mean RSRP difference and Pearson correlation of hourly RSRP over common
  hours (Experia), plus correlation of 15-min connected users after removing the site's diurnal shape
  (each cell's share of site users, KPI).
- Interpretation rules (hints, not identification):
  * A cell reporting inter-frequency handovers implies at least one other LTE frequency nearby.
  * Within a site, cells forming distinct RSRP/TA levels with similar group sizes suggest carrier
    layers (lower band: stronger RSRP, larger TA); similar levels suggest sectors of one layer.
  * The draft is explicit: aggregate serving-user statistics cannot identify azimuth or band.
"""
from pathlib import Path
import itertools
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EXP = {'AVG(MED_SERVINGRSRPMEDIAN)': 'rsrp', 'AVG(MED_SINRMEDIAN)': 'sinr',
       'AVG(MED_SERVINGRSRQMEDIAN)': 'rsrq', 'AVG(TAAVG)': 'taavg'}


def main():
    e = pd.read_csv(HERE / 'experia_cells.csv.gz').rename(columns=EXP)
    e['ts'] = pd.to_datetime(e.DATE_ID.astype(str).str[:10]) + pd.to_timedelta(e.HOUR_ID.astype(int), unit='h')
    k = pd.read_csv(HERE / 'kpi_cells.csv.gz', parse_dates=['DATETIME'])

    cell = e.groupby(['site', 'FIRSTCELL']).agg(hours=('ts', 'nunique'), rsrp=('rsrp', 'mean'), rsrp_sd=('rsrp', 'std'),
                                                sinr=('sinr', 'mean'), rsrq=('rsrq', 'mean'), taavg=('taavg', 'mean'))
    cell.index.names = ['site', 'cell']
    kc = k.groupby(['site', 'CELL']).agg(
        kpi_intervals=('DATETIME', 'size'), prb=('DL_PRB_Util_%_ERI', 'mean'),
        users=('Avg_Sim_RRC_Connected_User_Num_ERI', 'mean'), dl_mb=('DLTRF_VOLUME_MBYTE_ERI', 'mean'),
        cqi=('Avg_CQI_ERI', 'mean'), rach_ta=('Avg_RACH_TA_ERI', 'mean'),
        interfreq_share=('Inter_Freq_Hand_Succ_PC', lambda s: s.notna().mean()),
        intrafreq_share=('Intra_Freq_Hand_Succ_PC', lambda s: s.notna().mean()),
        irat_share=('IRAT_HO_Succ_PC', lambda s: s.notna().mean()))
    kc.index.names = ['site', 'cell']
    cells = cell.join(kc, how='outer').reset_index().sort_values(['site', 'cell'])
    cells.to_csv(HERE / 'cell_signatures.csv', index=False, float_format='%.4f')

    # Pairwise within-site relations.
    piv = e.pivot_table(index='ts', columns='FIRSTCELL', values='rsrp')
    k['site_users'] = k.groupby(['site', 'DATETIME']).Avg_Sim_RRC_Connected_User_Num_ERI.transform('sum')
    k['share'] = k.Avg_Sim_RRC_Connected_User_Num_ERI / k.site_users.replace(0, np.nan)
    share = k.pivot_table(index='DATETIME', columns='CELL', values='share')
    pairs = []
    for site, g in cells.groupby('site'):
        for a, b in itertools.combinations(g.cell, 2):
            row = {'site': site, 'a': a, 'b': b,
                   'rsrp_diff': float(g.set_index('cell').rsrp[a] - g.set_index('cell').rsrp[b])}
            if a in piv and b in piv:
                c = piv[[a, b]].dropna()
                row['common_hours'] = int(len(c))
                row['rsrp_hourly_corr'] = float(c[a].corr(c[b])) if len(c) > 10 else None
            if a in share and b in share:
                c = share[[a, b]].dropna()
                row['user_share_corr'] = float(c[a].corr(c[b])) if len(c) > 10 else None
            pairs.append(row)
    pairs = pd.DataFrame(pairs)
    pairs.to_csv(HERE / 'cell_pairs.csv', index=False, float_format='%.4f')

    # Per-site summary.
    summary = []
    for site, g in cells.groupby('site'):
        p = pairs[pairs.site == site]
        summary.append({'site': site, 'cells': int(len(g)),
                        'rsrp_range_db': float(g.rsrp.max() - g.rsrp.min()),
                        'rsrp_sd_db': float(g.rsrp.std()),
                        'taavg_range': float(g.taavg.max() - g.taavg.min()),
                        'rsrp_vs_taavg_corr': float(g.rsrp.corr(g.taavg)) if len(g) > 2 else None,
                        'rsrp_vs_rach_ta_corr': float(g.rsrp.corr(g.rach_ta)) if len(g) > 2 else None,
                        'cells_with_interfreq_ho': int((g.interfreq_share > 0.5).sum()),
                        'cells_with_irat_ho': int((g.irat_share > 0.5).sum()),
                        'median_pair_rsrp_hourly_corr': float(p.rsrp_hourly_corr.median()) if 'rsrp_hourly_corr' in p and p.rsrp_hourly_corr.notna().any() else None,
                        'median_pair_user_share_corr': float(p.user_share_corr.median()) if 'user_share_corr' in p and p.user_share_corr.notna().any() else None})
    summary = pd.DataFrame(summary)
    summary.to_csv(HERE / 'site_summary.csv', index=False, float_format='%.3f')

    # Figure: per site, RSRP vs TAAVG for each cell, size ~ users.
    sites = list(summary.site)
    fig, axes = plt.subplots(2, 4, figsize=(16, 7.5))
    for ax, site in zip(axes.ravel(), sites):
        g = cells[cells.site == site]
        size = 20 + 4 * g.users.fillna(0)
        sc = ax.scatter(g.taavg, g.rsrp, s=size, c=g.interfreq_share, cmap='coolwarm', vmin=0, vmax=1, edgecolors='black')
        for r in g.itertuples():
            ax.annotate(r.cell[-4:], (r.taavg, r.rsrp), xytext=(3, 3), textcoords='offset points', fontsize=7)
        ax.set_title(f'{site} — {len(g)} hücre', fontsize=10)
        ax.set_xlabel('Experia TAAVG (ham birim)')
        ax.set_ylabel('Experia RSRP (dBm)')
        ax.grid(alpha=.3)
    fig.subplots_adjust(hspace=.45, wspace=.35)
    fig.colorbar(sc, ax=axes, shrink=.6, label='Frekanslar arası HO raporlanan 15 dk oranı (KPI)')
    fig.suptitle('Saha içi hücre imzaları: RSRP–TAAVG düzeyi (nokta boyu: ortalama bağlı kullanıcı)', fontsize=12)
    fig.savefig(HERE / 'hucre_imzalari.png', dpi=140, bbox_inches='tight')

    print(summary.round(2).to_string())
    print(cells[['site', 'cell', 'hours', 'rsrp', 'sinr', 'taavg', 'prb', 'users', 'cqi', 'rach_ta',
                 'interfreq_share', 'intrafreq_share', 'irat_share']].round(2).to_string())


if __name__ == '__main__':
    main()
