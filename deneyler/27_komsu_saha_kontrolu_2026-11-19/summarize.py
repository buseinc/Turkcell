"""Windows: neighbour-site check. Per-site errors (mean of 3 draws) for the 8 evaluation + 3 neighbour sites,
compared with deneyler/26 for the evaluation sites."""
from pathlib import Path
import json
import statistics

import pandas as pd

HERE = Path(__file__).resolve().parent
D26 = HERE.parent/'26_kaynakli_tam_model_2026-11-19'
SEEDS = [701, 702, 703]


def site_means(res):
    runs = {r['case']['ue_seed']: r for r in res['results']}
    assert sorted(runs) == SEEDS
    sites = set.intersection(*(set(runs[s]['sites']) for s in SEEDS))
    return {site: {m: statistics.mean(runs[s]['sites'][site][m] for s in SEEDS) for m in ['rsrp', 'sinr']} for site in sites}, runs


def main():
    t = pd.read_csv(HERE/'inputs/targets.csv').set_index('site')
    now, runs = site_means(json.loads((HERE/'result.json').read_text(encoding='utf-8')))
    old, _ = site_means(json.loads((D26/'result.json').read_text(encoding='utf-8')))
    rows = []
    for site in t.index:
        r = {'site': site, 'split': t.loc[site, 'split'], 'cells': int(t.loc[site, 'measured_cells'])}
        for m in ['rsrp', 'sinr']:
            r[f'{m}_err'] = now[site][m] - t.loc[site, f'{m}_target']
            r[f'{m}_err_26'] = old[site][m] - t.loc[site, f'{m}_target'] if site in old else None
            r[f'{m}_per_draw'] = [runs[s]['sites'][site][m] - t.loc[site, f'{m}_target'] for s in SEEDS]
        rows.append(r)
    df = pd.DataFrame(rows)
    groups = {g: {m: float(df[df.split == g][f'{m}_err'].abs().mean()) for m in ['rsrp', 'sinr']} for g in ['holdout', 'train', 'neighbour']}
    out = {'sites': rows, 'mae_by_group': groups,
           'connected': [runs[s]['measurement_connected'] for s in SEEDS], 'with_dl': [runs[s]['measurement_with_dl'] for s in SEEDS],
           'prb': statistics.mean(runs[s]['prb_mean_achieved'] for s in SEEDS),
           'eval_site_change_vs_26_db': {m: float((df[df.split != 'neighbour'][f'{m}_err'] - df[df.split != 'neighbour'][f'{m}_err_26']).abs().max()) for m in ['rsrp', 'sinr']}}
    (HERE/'comparison.json').write_text(json.dumps(out, indent=2, ensure_ascii=False, default=float), encoding='utf-8')
    pd.set_option('display.width', 200)
    print(df[['site', 'split', 'cells', 'rsrp_err', 'rsrp_err_26', 'sinr_err', 'sinr_err_26']].round(1).to_string(index=False))
    for r in rows:
        if r['split'] == 'neighbour':
            print(r['site'], 'rsrp per draw', [round(x, 1) for x in r['rsrp_per_draw']], 'sinr per draw', [round(x, 1) for x in r['sinr_per_draw']])
    print(json.dumps({k: out[k] for k in ['mae_by_group', 'connected', 'with_dl', 'prb', 'eval_site_change_vs_26_db']}, indent=1, default=float))


if __name__ == '__main__':
    main()
