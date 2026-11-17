"""Windows: compare the sourced-parameter runs (R_TA, R_S0yer) with S0 (deneyler/14) and S0TA (deneyler/15)."""
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
D14 = ROOT/'deneyler/14_temel_s0_ve_cok_tasiyici_s2_2026-11-15'
D15 = ROOT/'deneyler/15_ta_yerlesim_2026-11-16'
SEEDS = [701, 702, 703]
M = ['rsrp', 'sinr', 'rsrq']
# label, folder, scenario key in that folder's result.json
SCEN = {'S0': ('Eski temel (ayarlı değerler, 2–6 km)', D14, 'S0'),
        'S0TA': ('Ayarlı değerler, TA yerleşimi', D15, 'S0TA'),
        'R_S0yer': ('Kaynaklı değerler, 2–6 km', HERE, 'R_S0yer'),
        'R_TA': ('Kaynaklı değerler, TA yerleşimi', HERE, 'R_TA')}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


cqi11 = module('cqi11', ROOT/'deneyler/11_cqi_karsilastirmasi_2026-11-15/compare.py')
dist12 = module('dist12', ROOT/'deneyler/12_dagilim_karsilastirmasi_2026-11-15/compare.py')


def runs_of(base, key):
    res = json.loads((base/'result.json').read_text(encoding='utf-8'))
    out = {}
    for r in res['results']:
        c = r['case']
        if c.get('scenario', c.get('label')) == key:
            out[c['ue_seed']] = r
    return out


def main():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    targets = pd.read_csv(HERE/'inputs/targets.csv').set_index('site')
    sites = list(targets.index)
    t = pd.read_csv(ROOT/'deneyler/11_cqi_karsilastirmasi_2026-11-15/cqi_table.csv')
    tdb, tcq = t.sinr_db.to_numpy(), t.cqi_mean.to_numpy()

    def lookup(x):
        return tcq[np.clip(np.floor((np.asarray(x, float) - tdb[0]) / 0.01 + 1e-9).astype(int), 0, len(tdb) - 1)]

    kpi = pd.read_csv(ROOT/'deneyler/09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', parse_dates=['DATETIME'])
    kpi = kpi[kpi.site.isin(sites)]
    bad = pd.Series(False, index=kpi.index)
    for a, b in cqi11.EXCLUDE:
        bad |= kpi.DATETIME.between(a, b, inclusive='left')
    kpi_cqi = kpi[~bad].groupby(['site', 'CELL'])['Avg_CQI_ERI'].mean().groupby('site').mean()
    exp = pd.read_csv(dist12.EXPERIA)

    out = {}
    for sc, (label, base, key) in SCEN.items():
        runs = runs_of(base, key)
        assert sorted(runs) == SEEDS, (sc, sorted(runs))
        folders = [base/'simulation/results'/f'{key}_draw{s}' for s in SEEDS]
        mae = {sp: {m: [runs[s][sp]['mae_db'][m] for s in SEEDS] for m in M} for sp in ['training', 'control']}
        site_vals = {m: pd.Series({site: statistics.mean(runs[s]['sites'][site][m] for s in SEEDS) for site in sites}) for m in M}
        signed = {site: {m: float(site_vals[m][site] - targets.loc[site, f'{m}_target']) for m in M} for site in sites}
        spearman = {m: float(site_vals[m].rank().corr(targets[f'{m}_target'].rank())) for m in ['rsrp', 'sinr']}
        cq = [cqi11.sim_cqi(fd, lookup) for fd in folders]
        sim_cqi = pd.concat([c['all'] for c in cq], axis=1).mean(axis=1)
        pooled = pd.concat([dist12.sim_sectors(fd) for fd in folders])
        dist = {m: {'ks': dist12.ks(pooled[m].dropna().to_numpy(), exp[c].to_numpy()),
                    'median_sim': float(pooled[m].median()), 'median_exp': float(exp[c].median()),
                    'iqr_sim': float(np.subtract(*np.quantile(pooled[m].dropna(), [.75, .25]))),
                    'iqr_exp': float(np.subtract(*np.quantile(exp[c], [.75, .25])))}
                for m, c in [('rsrp', 'rsrp_mean'), ('sinr', 'sinr_mean')]}
        out[sc] = {'label': label,
                   'mae': {sp: {m: [statistics.mean(v), statistics.stdev(v)] for m, v in d.items()} for sp, d in mae.items()},
                   'signed': signed, 'site_values': {m: s.to_dict() for m, s in site_vals.items()},
                   'spearman': spearman,
                   'cqi': {'bias': float((sim_cqi - kpi_cqi).mean()), 'mae': float((sim_cqi - kpi_cqi).abs().mean()),
                           'spearman': float(sim_cqi.rank().corr(kpi_cqi.rank()))},
                   'distribution': dist,
                   'prb': statistics.mean(runs[s]['prb_mean_achieved'] for s in SEEDS),
                   'connected': [runs[s]['measurement_connected'] for s in SEEDS],
                   'with_dl': [runs[s]['measurement_with_dl'] for s in SEEDS]}
    rule = plan['decision_rule']
    r = out['R_TA']
    out['decision'] = {'rule': rule,
                       'holdout_rsrp_mae': r['mae']['control']['rsrp'][0], 'holdout_sinr_mae': r['mae']['control']['sinr'][0],
                       'all_connected': all(c == 256 for c in r['connected'])}
    d = out['decision']
    d['passed'] = (d['holdout_rsrp_mae'] <= rule['holdout_rsrp_mae_max_db'] and
                   d['holdout_sinr_mae'] <= rule['holdout_sinr_mae_max_db'] and d['all_connected'])
    (HERE/'comparison.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

    order = ['S0', 'R_S0yer', 'R_TA']
    fig, axes = plt.subplots(2, 3, figsize=(12.6, 8.6))
    for row, (m, lab, lim) in enumerate([('rsrp', 'RSRP (dBm)', (-135, -90)), ('sinr', 'SINR (dB)', (-12, 25))]):
        for col, sc in enumerate(order):
            ax = axes[row][col]
            xs = np.linspace(*lim, 2)
            ax.fill_between(xs, xs - 3, xs + 3, color='#2ca02c', alpha=.12)
            ax.plot(xs, xs, color='black', lw=.8)
            for site in sites:
                y = out[sc]['site_values'][m][site]
                hold = targets.loc[site, 'split'] == 'holdout'
                ax.plot(targets.loc[site, f'{m}_target'], y, 'o', ms=6, color='#d62728' if hold else '#1f77b4')
                ax.annotate(site[-3:], (targets.loc[site, f'{m}_target'], y), xytext=(5, -9), textcoords='offset points', fontsize=7.5)
            ax.set_xlim(lim)
            ax.set_ylim(lim)
            ax.set_aspect('equal')
            ax.grid(alpha=.3)
            ax.set_xlabel(f'Ölçüm (Experia) — {lab}')
            ax.set_ylabel(f'Simülasyon — {lab}')
            mc = out[sc]['mae']['control'][m][0]
            ax.set_title(f"{out[sc]['label']}\nayarda kullanılmayan sahalarda fark {mc:.1f} dB".replace('.', ','), fontsize=9)
    axes[0][0].plot([], [], 'o', color='#1f77b4', label='Ayarda kullanılan saha')
    axes[0][0].plot([], [], 'o', color='#d62728', label='Ayarda kullanılmayan saha (holdout)')
    axes[0][0].legend(fontsize=7.5, loc='upper left')
    fig.tight_layout()
    fig.savefig(HERE/'kaynakli_karsilastirma.png', dpi=160)

    for sc in SCEN:
        o = out[sc]
        print('==', sc, o['label'])
        for sp in ['control', 'training']:
            print(' ', sp, {m: f'{v[0]:.2f}±{v[1]:.2f}' for m, v in o['mae'][sp].items()})
        print('  spearman', {k: round(v, 2) for k, v in o['spearman'].items()}, 'cqi', {k: round(v, 2) for k, v in o['cqi'].items()})
        print('  dist', {m: {k: round(v, 2) for k, v in dd.items()} for m, dd in o['distribution'].items()})
        print('  prb', round(o['prb'], 3), 'conn', o['connected'], 'dl', o['with_dl'])
        print('  signed rsrp', {s[-3:]: round(v['rsrp'], 1) for s, v in o['signed'].items()})
        print('  signed sinr', {s[-3:]: round(v['sinr'], 1) for s, v in o['signed'].items()})
    print('decision', out['decision'])


if __name__ == '__main__':
    main()
