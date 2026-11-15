"""Windows: distribution and ranking comparison, simulation vs Experia (no new runs).

Written before looking at the comparison:
- Matched aggregation level. Experia values are hourly averages of per-cell medians; the comparable unit
  is a cell-level central value. Experia: time mean of each of the 55 evaluation-site cells (the same
  table the site targets come from). Simulation: per sector at an evaluation site, the median of its
  measurement UEs' time means; only sectors with >= 3 UEs; 3 azimuth/UE draws pooled.
- Runs: no-load (256 UEs) and the KPI daily-mean load (L1), both already computed.
- Report quantiles (10/25/50/75/90), quantile differences, the Kolmogorov-Smirnov distance and the
  within-site spread (sd of cell/sector values inside a site). Descriptive only: no pass/fail
  threshold, as the draft advises before units/definitions are confirmed.
- Spatial ranking: Spearman correlation between site values (sim vs Experia) per draw and metric,
  and rank stability across draws (Spearman between draws).
"""
from pathlib import Path
import json
import itertools

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPERIA = ROOT / 'ana_proje/analysis/sindirgi/experia_evaluation_cells.csv'
TARGETS = ROOT / 'deneyler/09_kpi_yuk_profili_2026-11-12/inputs/targets.csv'
RUNS = {'noload': ('Yüksüz', ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12/simulation/results', 'n256_draw{s}'),
        'L1': ('Günlük ortalama yük', ROOT / 'deneyler/09_kpi_yuk_profili_2026-11-12/simulation/results', 'L1_daily_mean_draw{s}')}
SEEDS = [701, 702, 703]
N_MEAS = 256
MIN_UES = 3
M = {'rsrp': ('RSRP (dBm)', 'rsrp_mean'), 'sinr': ('SINR (dB)', 'sinr_mean'), 'rsrq': ('RSRQ (dB)', 'rsrq_mean')}
Q = [.1, .25, .5, .75, .9]


def ks(a, b):
    a, b = np.sort(a), np.sort(b)
    x = np.concatenate([a, b])
    return float(np.max(np.abs(np.searchsorted(a, x, side='right') / len(a) - np.searchsorted(b, x, side='right') / len(b))))


def wquantile(values, weights, q):
    o = np.argsort(values)
    v, w = np.asarray(values)[o], np.asarray(weights)[o]
    c = (np.cumsum(w) - 0.5 * w) / w.sum()
    return np.interp(q, c, v)


def sim_sectors(folder):
    m = json.loads((folder / 'metrics.json').read_text())
    u = pd.DataFrame(m['ues'])
    u = u[(u.ue_id < N_MEAS) & (u.role == 'Evaluation')]
    g = u.groupby(['site', 'sector'])
    sec = g[['rsrp', 'sinr', 'rsrq']].median()
    sec['ues'] = g.size()
    return sec[sec.ues >= MIN_UES].reset_index()


def main():
    exp = pd.read_csv(EXPERIA)
    targets = pd.read_csv(TARGETS).set_index('site')
    sites = list(targets.index)
    out = {'experia_cells': int(len(exp)), 'levels': {}}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    for lv, (label, base, pattern) in RUNS.items():
        per = {s: sim_sectors(base / pattern.format(s=s)) for s in SEEDS}
        pooled = pd.concat(per.values())
        res = {'sectors_pooled': int(len(pooled)), 'metrics': {}}
        for k, (lab, col) in M.items():
            e = exp[col].to_numpy()
            s = pooled[k].dropna().to_numpy()
            qe, qs = np.quantile(e, Q), np.quantile(s, Q)
            # Site-balanced: every site gets equal total weight (Experia cells per site differ: 2..14).
            we = 1 / exp.groupby('site_id')[col].transform('size').to_numpy()
            ps = pooled.dropna(subset=[k])
            ws = 1 / ps.groupby('site')[k].transform('size').to_numpy()
            qe_b, qs_b = wquantile(e, we, Q), wquantile(ps[k].to_numpy(), ws, Q)
            within_e = exp.groupby('site_id')[col].std().mean()
            within_s = pooled.groupby('site')[k].std().mean()
            ranks = {}
            site_vals = {}
            for sd, sec in per.items():
                v = sec.groupby('site')[k].mean().reindex(sites)
                site_vals[sd] = v
                ok = v.notna()
                ranks[sd] = float(v[ok].rank().corr(targets.loc[ok, col.replace('_mean', '_target')].rank()))
            between = [float(site_vals[a].rank().corr(site_vals[b].rank())) for a, b in itertools.combinations(SEEDS, 2)]
            res['metrics'][k] = {'experia_quantiles': qe.tolist(), 'sim_quantiles': qs.tolist(),
                                 'quantile_diff_sim_minus_experia': (qs - qe).tolist(),
                                 'site_balanced_experia_quantiles': qe_b.tolist(), 'site_balanced_sim_quantiles': qs_b.tolist(),
                                 'site_balanced_quantile_diff': (qs_b - qe_b).tolist(),
                                 'iqr_experia': float(qe[3] - qe[1]), 'iqr_sim': float(qs[3] - qs[1]),
                                 'ks_distance': ks(s, e), 'within_site_sd_experia': float(within_e),
                                 'within_site_sd_sim': float(within_s),
                                 'site_rank_spearman_by_draw': ranks, 'rank_stability_between_draws': between}
            ax = axes[list(M).index(k)]
            if lv == 'noload':
                ax.step(np.sort(e), np.arange(1, len(e) + 1) / len(e), where='post', color='black', lw=2, label=f'Experia: {len(e)} hücre')
            ax.step(np.sort(s), np.arange(1, len(s) + 1) / len(s), where='post', label=f'Simülasyon, {label}: {len(s)} sektör')
            ax.set_xlabel(lab)
            ax.set_ylabel('Birikimli oran')
            ax.grid(alpha=.3)
        out['levels'][lv] = res
    for ax in axes:
        ax.legend(fontsize=7)
    fig.suptitle('Hücre düzeyi dağılımlar: Experia hücre zaman ortalamaları ve simülasyon sektör medyanları (8 ana saha, 3 örnek)', fontsize=10)
    fig.tight_layout()
    fig.savefig(HERE / 'dagilim_karsilastirma.png', dpi=150)
    (HERE / 'distribution_result.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    for lv, res in out['levels'].items():
        print('==', lv, 'sectors', res['sectors_pooled'])
        for k, r in res['metrics'].items():
            print(k, 'Q exp', np.round(r['experia_quantiles'], 1), 'Q sim', np.round(r['sim_quantiles'], 1),
                  'IQR', round(r['iqr_experia'], 1), round(r['iqr_sim'], 1), 'KS', round(r['ks_distance'], 2),
                  'within sd', round(r['within_site_sd_experia'], 1), round(r['within_site_sd_sim'], 1),
                  'rank', {d: round(v, 2) for d, v in r['site_rank_spearman_by_draw'].items()},
                  'stab', np.round(r['rank_stability_between_draws'], 2))
            print('   balanced Q exp', np.round(r['site_balanced_experia_quantiles'], 1), 'Q sim', np.round(r['site_balanced_sim_quantiles'], 1))


if __name__ == '__main__':
    main()
