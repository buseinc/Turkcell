"""Windows: S0 vs S2 comparison against Experia (site MAE, cell distribution) and KPI CQI."""
from pathlib import Path
import importlib.util
import json
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEEDS = [701, 702, 703]
M = ['rsrp', 'sinr', 'rsrq']
LAB = {'S0': 'S0 — tek taşıyıcı', 'S2': 'S2 — çok taşıyıcı'}


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


cqi11 = module('cqi11', ROOT / 'deneyler/11_cqi_karsilastirmasi_2026-11-15/compare.py')
dist12 = module('dist12', ROOT / 'deneyler/12_dagilim_karsilastirmasi_2026-11-15/compare.py')


def f(x, d=2):
    return '—' if x is None else f'{x:.{d}f}'.replace('.', ',')


def main():
    res = json.loads((HERE / 'result.json').read_text(encoding='utf-8'))
    assert res['completed']
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    by = {(r['case']['scenario'], r['case']['ue_seed']): r for r in res['results']}
    targets = pd.read_csv(HERE / 'inputs/targets.csv').set_index('site')
    sites = list(targets.index)
    # SINR -> CQI table produced by ns-3's LteAmc in the CQI study.
    t =pd.read_csv(ROOT / 'deneyler/11_cqi_karsilastirmasi_2026-11-15/cqi_table.csv')
    table_db, table_cqi = t.sinr_db.to_numpy(), t.cqi_mean.to_numpy()

    def lookup(x):
        idx = np.clip(np.floor((np.asarray(x, float) - table_db[0]) / 0.01 + 1e-9).astype(int), 0, len(table_db) - 1)
        return table_cqi[idx]

    # KPI CQI, all normal-day intervals (same window as the 'daily mean' level).
    d = pd.read_csv(ROOT / 'deneyler/09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', parse_dates=['DATETIME'])
    d = d[d.site.isin(sites)]
    bad = pd.Series(False, index=d.index)
    for a, b in cqi11.EXCLUDE:
        bad |= d.DATETIME.between(a, b, inclusive='left')
    d = d[~bad]
    kpi_cqi = d.groupby(['site', 'CELL'])['Avg_CQI_ERI'].mean().groupby('site').mean()

    exp = pd.read_csv(dist12.EXPERIA)
    out = {'scenarios': {}}
    rows = []
    for sc in ['S0', 'S2']:
        runs = [by[sc, s] for s in SEEDS]
        folders = [HERE / 'simulation/results' / f'{sc}_draw{s}' for s in SEEDS]
        mae = {sp: {m: [r[sp]['mae_db'][m] for r in runs] for m in M} for sp in ['training', 'control']}
        cq = [cqi11.sim_cqi(fd, lookup) for fd in folders]
        sim_cqi = pd.concat([c['all'] for c in cq], axis=1).mean(axis=1)
        sim_cqi_fresh = pd.concat([c['fresh'] for c in cq], axis=1).mean(axis=1)
        pooled = pd.concat([dist12.sim_sectors(fd) for fd in folders])
        dist = {}
        for m, (lab, col) in dist12.M.items():
            e, s = exp[col].to_numpy(), pooled[m].dropna().to_numpy()
            dist[m] = {'ks': dist12.ks(s, e), 'median_sim': float(np.median(s)), 'median_exp': float(np.median(e)),
                       'iqr_sim': float(np.subtract(*np.quantile(s, [.75, .25]))),
                       'iqr_exp': float(np.subtract(*np.quantile(e, [.75, .25]))),
                       'within_site_sd_sim': float(pooled.groupby('site')[m].std().mean()),
                       'within_site_sd_exp': float(exp.groupby('site_id')[col].std().mean()),
                       'site_rank_spearman': [float(r_.groupby('site')[m].mean().reindex(sites).dropna().rank().corr(
                           targets[col.replace('_mean', '_target')].reindex(r_.groupby('site')[m].mean().reindex(sites).dropna().index).rank()))
                           for r_ in [dist12.sim_sectors(fd) for fd in folders]],
                       'sim_values': s.tolist()}
        signed = {site: {m: statistics.mean(r['sites'][site][m] - targets.loc[site, f'{m}_target'] for r in runs
                                            if site in r['sites'] and r['sites'][site][m] is not None) for m in M} for site in sites}
        out['scenarios'][sc] = {
            'mae': {sp: {m: {'mean': statistics.mean(v), 'std': statistics.stdev(v)} for m, v in d_.items()} for sp, d_ in mae.items()},
            'cqi': {'sim_mean': float(sim_cqi.mean()), 'kpi_mean': float(kpi_cqi.mean()),
                    'bias': float((sim_cqi - kpi_cqi).mean()), 'mae': float((sim_cqi - kpi_cqi).abs().mean()),
                    'spearman': float(sim_cqi.rank().corr(kpi_cqi.rank())),
                    'fresh_only_bias': float((sim_cqi_fresh - kpi_cqi).mean()),
                    'fresh_fraction': statistics.mean(c['fresh_fraction'] for c in cq),
                    'per_site': {s: float(sim_cqi[s]) for s in sites}},
            'distribution': {m: {k: v for k, v in x.items() if k != 'sim_values'} for m, x in dist.items()},
            'signed_error': signed,
            'prb': {'mean': statistics.mean(r['prb_mean_achieved'] for r in runs),
                    'by_carrier': {k: statistics.mean(r['prb_mean_achieved_by_carrier'][k] for r in runs)
                                   for k in runs[0]['prb_mean_achieved_by_carrier']}},
            'measurement_on_b20': [r['measurement_on_b20'] for r in runs],
            'measurement_connected': [r['measurement_connected'] for r in runs],
            'load_ues_on_target': [f"{r['load_ues_on_target']}/{r['load_cells']}" for r in runs],
            'wall_seconds': [r['wall_seconds'] for r in runs]}
        rows.append((sc, dist, sim_cqi, signed))
    out['kpi_cqi_per_site'] = {s: float(kpi_cqi[s]) for s in sites}
    (HERE / 'comparison.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

    # Figure: cell distributions (RSRP, SINR) and CQI per site.
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.3))
    for ax, (m, col) in zip(axes[:2], [('rsrp', 'rsrp_mean'), ('sinr', 'sinr_mean')]):
        e = np.sort(exp[col].to_numpy())
        ax.step(e, np.arange(1, len(e) + 1) / len(e), where='post', color='black', lw=2, label='Experia (55 hücre)')
        for sc, dist, _, _ in rows:
            s = np.sort(dist[m]['sim_values'])
            ax.step(s, np.arange(1, len(s) + 1) / len(s), where='post', label=f'{LAB[sc]} ({len(s)} hücre)')
        ax.set_xlabel(dist12.M[m][0])
        ax.set_ylabel('Birikimli oran')
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
        ax.set_title(f'Hücre düzeyi {m.upper()} dağılımı')
    ax = axes[2]
    x = np.arange(len(sites))
    ax.bar(x - .25, [kpi_cqi[s] for s in sites], .25, color='black', label='KPI (günlük ortalama)')
    for i, (sc, _, sim_cqi, _) in enumerate(rows):
        ax.bar(x + i * .25, [sim_cqi[s] for s in sites], .25, label=LAB[sc])
    ax.set_xticks(x, [s[-3:] for s in sites])
    ax.set_ylabel('Ortalama CQI')
    ax.set_title('Saha CQI: KPI ve simülasyon (günlük ortalama yük)')
    ax.grid(axis='y', alpha=.3)
    ax.set_ylim(0, 14)
    ax.legend(fontsize=8, loc='upper center', ncol=3)
    fig.tight_layout()
    fig.savefig(HERE / 's0_s2_karsilastirma.png', dpi=150)

    s0, s2 = out['scenarios']['S0'], out['scenarios']['S2']
    print(json.dumps({sc: {k: v for k, v in x.items() if k not in ('signed_error',)} for sc, x in out['scenarios'].items()}, indent=1, ensure_ascii=False)[:6000])
    print('signed S0', {k: {m: round(v, 1) for m, v in d.items()} for k, d in s0['signed_error'].items()})
    print('signed S2', {k: {m: round(v, 1) for m, v in d.items()} for k, d in s2['signed_error'].items()})
    print('kpi cqi', {k: round(v, 2) for k, v in out['kpi_cqi_per_site'].items()})


if __name__ == '__main__':
    main()
