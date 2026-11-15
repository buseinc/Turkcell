"""Windows: compare simulated wideband CQI with KPI Avg_CQI_ERI at matched load windows.

Predeclared (before looking at the comparison):
- Simulated CQI per sample = ns-3.44 LteAmc (Vienna) CQI of the native mixed SINR sample the UE uses
  for CQI (cqi_table.csv, flat channel). Per UE mean -> sector mean -> site mean (as for RSRP/SINR).
- KPI CQI per site = mean over the site's cells of the mean over 15-min intervals in the window.
- Matched windows (normal days, same exclusions as the load profile):
  no-load run  <-> KPI hour with the lowest DL PRB (night),
  L1 daily mean <-> all intervals, L2 busy hour <-> 21:00-21:45, L3 site busy hour <-> 20:00-23:45.
- Report per site signed difference, MAE over the 8 evaluation sites, Spearman rank correlation across
  sites, and whether sim and KPI move in the same direction from night to busy hour.
- Sensitivity: CQI from fresh-interference samples only (physically loaded SINR).
No parameter is tuned to CQI.
"""
from pathlib import Path
import json
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D08 = ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12/simulation/results'
D09 = ROOT / 'deneyler/09_kpi_yuk_profili_2026-11-12'
SEEDS = [701, 702, 703]
N_MEAS = 256
EXCLUDE = [(pd.Timestamp('2025-08-10 19:45'), pd.Timestamp('2025-08-12 00:00')),
           (pd.Timestamp('2025-10-27 22:45'), pd.Timestamp('2025-10-29 00:00'))]
LEVELS = {'noload': ('Yüksüz (PRB ≈ 0,03)', 'night'), 'L1_daily_mean': ('Günlük ortalama', 'all'),
          'L3_site_busy_hour': ('Sahaya özel yoğun saat', 'evening'), 'L2_busy_hour': ('Yoğun saat', 'busy')}


def cqi_lookup():
    t = pd.read_csv(HERE / 'cqi_table.csv')
    assert (t.cqi_min == t.cqi_max).all()
    db = t.sinr_db.to_numpy()
    cq = t.cqi_mean.to_numpy()

    def f(x):
        x = np.asarray(x, dtype=float)
        idx = np.clip(np.floor((x - db[0]) / 0.01 + 1e-9).astype(int), 0, len(db) - 1)  # largest grid <= x
        return cq[idx]
    return f


def sim_cqi(folder, lookup):
    c = pd.read_csv(folder / 'sinr_components.csv',
                    usecols=['time_s', 'ue_id', 'synthetic_cell_id', 'native_sinr_db', 'data_interference_fresh'])
    serving = pd.read_csv(folder / 'ues.csv').set_index('ue_id').synthetic_cell_id
    c = c[(c.time_s >= 1) & (c.ue_id < N_MEAS)]
    c = c[c.synthetic_cell_id == c.ue_id.map(serving)].copy()
    c['cqi'] = lookup(c.native_sinr_db)
    sectors = pd.read_csv(folder / 'sectors.csv').set_index('synthetic_cell_id')
    out = {}
    for name, sub in [('all', c), ('fresh', c[c.data_interference_fresh == 1])]:
        ue = sub.groupby('ue_id').agg(cqi=('cqi', 'mean'), cell=('synthetic_cell_id', 'last'))
        ue['site'] = ue.cell.map(sectors.site)
        out[name] = ue.groupby(['site', 'cell']).cqi.mean().groupby('site').mean()
    out['fresh_fraction'] = float(c.data_interference_fresh.mean())
    out['samples'] = int(len(c))
    return out


def main():
    lookup = cqi_lookup()
    targets = pd.read_csv(D09 / 'inputs/targets.csv').set_index('site')
    sites = list(targets.index)

    # KPI side.
    d = pd.read_csv(D09 / 'kpi_cells.csv.gz', parse_dates=['DATETIME'])
    d = d[d.site.isin(sites)]
    bad = pd.Series(False, index=d.index)
    for a, b in EXCLUDE:
        bad |= d.DATETIME.between(a, b, inclusive='left')
    d = d[~bad].copy()
    d['hour'] = d.DATETIME.dt.hour
    prb_by_hour = d.groupby('hour')['DL_PRB_Util_%_ERI'].mean()
    night = int(prb_by_hour.idxmin())
    windows = {'night': d[d.hour == night], 'all': d, 'busy': d[d.hour == 21], 'evening': d[d.hour.between(20, 23)]}
    kpi = {}
    for w, sub in windows.items():
        cell = sub.groupby(['site', 'CELL']).agg(cqi=('Avg_CQI_ERI', 'mean'), prb=('DL_PRB_Util_%_ERI', 'mean'))
        kpi[w] = cell.groupby('site').mean()
    hourly = d.groupby(['site', 'hour'])['Avg_CQI_ERI'].mean().unstack()

    # Simulation side.
    sim = {}
    for lv in LEVELS:
        per = []
        for s in SEEDS:
            folder = D08 / f'n256_draw{s}' if lv == 'noload' else D09 / f'simulation/results/{lv}_draw{s}'
            per.append(sim_cqi(folder, lookup))
        sim[lv] = {'all': pd.concat([p['all'] for p in per], axis=1).mean(axis=1),
                   'fresh': pd.concat([p['fresh'] for p in per], axis=1).mean(axis=1),
                   'all_std': pd.concat([p['all'] for p in per], axis=1).std(axis=1),
                   'fresh_fraction': statistics.mean(p['fresh_fraction'] for p in per)}

    rows, summary = [], {}
    for lv, (label, w) in LEVELS.items():
        for site in sites:
            rows.append({'level': lv, 'site': site, 'split': targets.loc[site, 'split'],
                         'kpi_cqi': kpi[w].loc[site, 'cqi'], 'kpi_prb': kpi[w].loc[site, 'prb'],
                         'sim_cqi': sim[lv]['all'][site], 'sim_cqi_std_draws': sim[lv]['all_std'][site],
                         'sim_cqi_fresh_only': sim[lv]['fresh'][site]})
        t = pd.DataFrame([r for r in rows if r['level'] == lv])
        summary[lv] = {'label': label, 'kpi_window': w, 'kpi_cqi_mean': float(t.kpi_cqi.mean()),
                       'sim_cqi_mean': float(t.sim_cqi.mean()), 'bias': float((t.sim_cqi - t.kpi_cqi).mean()),
                       'mae': float((t.sim_cqi - t.kpi_cqi).abs().mean()),
                       'mae_fresh_only': float((t.sim_cqi_fresh_only - t.kpi_cqi).abs().mean()),
                       'bias_fresh_only': float((t.sim_cqi_fresh_only - t.kpi_cqi).mean()),
                       'spearman': float(t.sim_cqi.rank().corr(t.kpi_cqi.rank())),
                       'spearman_fresh_only': float(t.sim_cqi_fresh_only.rank().corr(t.kpi_cqi.rank())),
                       'sim_fresh_fraction': sim[lv]['fresh_fraction']}
    table = pd.DataFrame(rows)
    table.to_csv(HERE / 'cqi_site_comparison.csv', index=False, float_format='%.4f')
    trend = {'kpi_busy_minus_night': float((kpi['busy'].cqi - kpi['night'].cqi).mean()),
             'sim_busy_minus_noload': float((sim['L2_busy_hour']['all'] - sim['noload']['all']).mean()),
             'sim_busy_minus_noload_fresh_only': float((sim['L2_busy_hour']['fresh'] - sim['noload']['fresh']).mean()),
             'night_hour': night}
    out = {'summary': summary, 'trend': trend,
           'kpi_hourly_cqi_eval_mean': {int(h): float(v) for h, v in hourly.mean().items()},
           'kpi_hourly_prb_eval_mean': {int(h): float(v) for h, v in prb_by_hour.items()}}
    (HERE / 'cqi_result.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

    # Figures.
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3))
    ax = axes[0]
    x = np.arange(len(sites))
    w = 0.2
    for i, (lv, (label, win)) in enumerate(LEVELS.items()):
        t = table[table.level == lv].set_index('site').loc[sites]
        ax.bar(x + (i - 1.5) * w, t.sim_cqi - t.kpi_cqi, w, label=label)
    ax.axhline(0, color='black', lw=.8)
    ax.set_xticks(x, [f"{s[-3:]}\n{'kontrol' if targets.loc[s, 'split'] == 'holdout' else 'eğitim'}" for s in sites])
    ax.set_ylabel('CQI: simülasyon − KPI')
    ax.set_title('Saha bazında CQI farkı (eşleşen yük penceresi)')
    ax.grid(axis='y', alpha=.3)
    ax.legend(fontsize=8)
    ax = axes[1]
    k = [summary[lv]['kpi_cqi_mean'] for lv in LEVELS]
    s_ = [summary[lv]['sim_cqi_mean'] for lv in LEVELS]
    p = [table[table.level == lv].kpi_prb.mean() for lv in LEVELS]
    ax.plot(p, k, marker='o', label='KPI (gerçek ağ)')
    ax.plot(p, s_, marker='s', label='Simülasyon (ns-3 mixed SINR → CQI)')
    ax.plot(p, [summary[lv]['sim_cqi_mean'] - summary[lv]['bias'] + summary[lv]['bias_fresh_only'] for lv in LEVELS],
            marker='^', ls='--', label='Simülasyon, yalnız girişimli örnekler')
    for i, (xi, yi, lv) in enumerate(zip(p, k, LEVELS)):
        ax.annotate(LEVELS[lv][0], (xi, yi), xytext=(-60 if i == 2 else 4, 10 if i % 2 else -14),
                    textcoords='offset points', fontsize=7)
    ax.set_xlabel('Eşleşen penceredeki KPI DL PRB (ana 8 saha)')
    ax.set_ylabel('Ortalama CQI (8 ana saha)')
    ax.set_title('Yüke göre CQI')
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / 'cqi_karsilastirma.png', dpi=150)
    print(json.dumps(out['summary'], indent=1, ensure_ascii=False))
    print(json.dumps(trend, indent=1))
    print(table.round(2).to_string())


if __name__ == '__main__':
    main()
