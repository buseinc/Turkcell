"""Windows: compare TA-based placement (S0TA) with the uniform 2-6 km clusters (S0 of study 14)."""
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
D14 = ROOT / 'deneyler/14_cok_tasiyici_s2_2026-11-15'
SEEDS = [701, 702, 703]
M = ['rsrp', 'sinr', 'rsrq']
SCEN = {'S0': ('Önceki yerleşim (2–6 km)', D14), 'S0TA': ('TA’ya göre yerleşim', HERE)}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


cqi11 = module('cqi11', ROOT / 'deneyler/11_cqi_karsilastirmasi_2026-11-15/compare.py')
dist12 = module('dist12', ROOT / 'deneyler/12_dagilim_karsilastirmasi_2026-11-15/compare.py')


def main():
    targets = pd.read_csv(HERE / 'inputs/targets.csv').set_index('site')
    sites = list(targets.index)
    t = pd.read_csv(ROOT / 'deneyler/11_cqi_karsilastirmasi_2026-11-15/cqi_table.csv')
    tdb, tcq = t.sinr_db.to_numpy(), t.cqi_mean.to_numpy()

    def lookup(x):
        return tcq[np.clip(np.floor((np.asarray(x, float) - tdb[0]) / 0.01 + 1e-9).astype(int), 0, len(tdb) - 1)]

    kpi = pd.read_csv(ROOT / 'deneyler/09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', parse_dates=['DATETIME'])
    kpi = kpi[kpi.site.isin(sites)]
    bad = pd.Series(False, index=kpi.index)
    for a, b in cqi11.EXCLUDE:
        bad |= kpi.DATETIME.between(a, b, inclusive='left')
    kpi_cqi = kpi[~bad].groupby(['site', 'CELL'])['Avg_CQI_ERI'].mean().groupby('site').mean()
    exp = pd.read_csv(dist12.EXPERIA)
    expta = pd.read_csv(ROOT / 'deneyler/13_hucre_imzasi_2026-11-15/experia_cells.csv.gz')
    expta['km'] = (expta['AVG(TAAVG)'] * 4.88 / 1000).clip(0.1, 15)
    real_km = expta.groupby('site').km.median()

    out = {}
    for sc, (label, base) in SCEN.items():
        res = json.loads((base / 'result.json').read_text(encoding='utf-8'))
        runs = {r['case']['ue_seed']: r for r in res['results'] if r['case']['scenario'] == sc}
        folders = [base / 'simulation/results' / f'{sc}_draw{s}' for s in SEEDS]
        mae = {sp: {m: [runs[s][sp]['mae_db'][m] for s in SEEDS] for m in M} for sp in ['training', 'control']}
        signed = {site: {m: statistics.mean(runs[s]['sites'][site][m] - targets.loc[site, f'{m}_target'] for s in SEEDS) for m in M}
                  for site in sites}
        site_vals = {m: pd.Series({site: statistics.mean(runs[s]['sites'][site][m] for s in SEEDS) for site in sites}) for m in M}
        spearman = {m: float(site_vals[m].rank().corr(targets[f'{m}_target'].rank())) for m in ['rsrp', 'sinr']}
        cq = [cqi11.sim_cqi(fd, lookup) for fd in folders]
        sim_cqi = pd.concat([c['all'] for c in cq], axis=1).mean(axis=1)
        pooled = pd.concat([dist12.sim_sectors(fd) for fd in folders])
        dist = {m: {'ks': dist12.ks(pooled[m].dropna().to_numpy(), exp[c].to_numpy()),
                    'median_sim': float(pooled[m].median()), 'median_exp': float(exp[c].median()),
                    'iqr_sim': float(np.subtract(*np.quantile(pooled[m].dropna(), [.75, .25]))),
                    'iqr_exp': float(np.subtract(*np.quantile(exp[c], [.75, .25])))}
                for m, c in [('rsrp', 'rsrp_mean'), ('sinr', 'sinr_mean')]}
        dists = []
        for fd in folders:
            mm = json.loads((fd / 'metrics.json').read_text())
            u = pd.DataFrame(mm['ues'])
            dists.append(u[(u.ue_id < 256) & (u.role == 'Evaluation')][['site', 'serving_distance_m']])
        dists = pd.concat(dists)
        out[sc] = {'label': label,
                   'mae': {sp: {m: [statistics.mean(v), statistics.stdev(v)] for m, v in d.items()} for sp, d in mae.items()},
                   'signed': signed, 'site_values': {m: s.to_dict() for m, s in site_vals.items()},
                   'spearman': spearman,
                   'cqi': {'bias': float((sim_cqi - kpi_cqi).mean()), 'mae': float((sim_cqi - kpi_cqi).abs().mean()),
                           'spearman': float(sim_cqi.rank().corr(kpi_cqi.rank()))},
                   'distribution': dist,
                   'prb': statistics.mean(runs[s]['prb_mean_achieved'] for s in SEEDS),
                   'connected': [runs[s]['measurement_connected'] for s in SEEDS],
                   'with_dl': [runs[s]['measurement_with_dl'] for s in SEEDS],
                   'serving_km_by_site': (dists.groupby('site').serving_distance_m.median() / 1000).to_dict()}
    out['real_ta_km_by_site'] = real_km.to_dict()
    (HERE / 'comparison.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

    fig, axes = plt.subplots(2, 2, figsize=(9.6, 9.0))
    for col, (m, lab, lim) in enumerate([('rsrp', 'RSRP (dBm)', (-120, -95)), ('sinr', 'SINR (dB)', (0, 25))]):
        for row, sc in enumerate(['S0', 'S0TA']):
            ax = axes[row][col]
            xs = np.linspace(*lim, 2)
            ax.fill_between(xs, xs - 3, xs + 3, color='#2ca02c', alpha=.12)
            ax.plot(xs, xs, color='black', lw=.8)
            for site in sites:
                y = out[sc]['site_values'][m][site]
                ax.plot(targets.loc[site, f'{m}_target'], y, 'o', ms=6,
                        color='#1f77b4' if targets.loc[site, 'split'] == 'train' else '#d62728')
                ax.annotate(site[-3:], (targets.loc[site, f'{m}_target'], y), xytext=(5, -9), textcoords='offset points', fontsize=7.5)
            ax.set_xlim(lim)
            ax.set_ylim(lim)
            ax.set_aspect('equal')
            ax.grid(alpha=.3)
            ax.set_xlabel(f'Ölçüm (Experia) — {lab}')
            ax.set_ylabel(f'Simülasyon — {lab}')
            mae_c = out[sc]['mae']['control'][m][0]
            ax.set_title(f"{out[sc]['label']}\nayarda kullanılmayan sahalarda fark {mae_c:.1f} dB".replace('.', ','), fontsize=9)
    fig.tight_layout()
    fig.savefig(HERE / 'ta_yerlesim_karsilastirma.png', dpi=160)

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = np.arange(len(sites))
    ax.bar(x - .27, [real_km[s] for s in sites], .27, color='#444444', label='Gerçek (Experia TA)')
    ax.bar(x, [out['S0']['serving_km_by_site'][s] for s in sites], .27, color='#9ecae1', label='Önceki yerleşim')
    ax.bar(x + .27, [out['S0TA']['serving_km_by_site'][s] for s in sites], .27, color='#3182bd', label='TA’ya göre yerleşim')
    ax.set_xticks(x, [s[-3:] for s in sites])
    ax.set_ylabel('Kullanıcının hizmet aldığı sahaya\nmedyan uzaklığı (km)')
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=.3)
    fig.tight_layout()
    fig.savefig(HERE / 'kullanici_uzakligi.png', dpi=160)

    for sc in ['S0', 'S0TA']:
        o = out[sc]
        print('==', sc, o['label'])
        for sp in ['control', 'training']:
            print(' ', sp, {m: f'{v[0]:.2f}±{v[1]:.2f}' for m, v in o['mae'][sp].items()})
        print('  spearman', {k: round(v, 2) for k, v in o['spearman'].items()}, 'cqi', {k: round(v, 2) for k, v in o['cqi'].items()})
        print('  dist', {m: {k: round(v, 2) for k, v in d.items()} for m, d in o['distribution'].items()})
        print('  prb', round(o['prb'], 3), 'conn', o['connected'], 'dl', o['with_dl'])
        print('  signed rsrp', {s[-3:]: round(v['rsrp'], 1) for s, v in o['signed'].items()})
        print('  signed sinr', {s[-3:]: round(v['sinr'], 1) for s, v in o['signed'].items()})
        print('  serving km', {s[-3:]: round(v, 1) for s, v in o['serving_km_by_site'].items()})
    print('real km', {s[-3:]: round(v, 1) for s, v in real_km.items()})


if __name__ == '__main__':
    main()
