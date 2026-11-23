"""Windows: tests A (several bands) and B (always-on neighbour signals) of ADIM3_KURALLAR.md, Ek 2.
Fast model, RMa, 24 sites, the saved users / sectors / correction of adim3 (Edremit, Balikesir).
Usage: py sinamalar.py edremit|balikesir. Writes sinama_<region>.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
import model35 as m  # noqa: E402
hm = m.hm

BANDS = {'B20': 806.0e6, 'B3': (1805.0 + 0.1*(1651 - 1200))*1e6, 'B1': 2140.0e6, 'B7': 2655.0e6}
F_ON = 2/14 + 12/168
CELLMAPPER = {'SITE_000370': {'B1', 'B3', 'B7', 'B20'}, 'SITE_000105': {'B1', 'B3', 'B7', 'B20'},
              'SITE_000507': {'B1', 'B3', 'B7'}, 'SITE_000529': {'B1', 'B7'}, 'SITE_000006': {'B1', 'B20'},
              'SITE_000007': {'B1'}}


def sinr_on(rsrp_dbm, serving, load, f_on, samples=100):
    """hizli_model.sinr (packed RBs) with neighbour activity f_on + (1 - f_on) x data activity."""
    p = 10**(rsrp_dbm/10)
    u = np.arange(len(p))
    s = p[u, serving]
    interf = p.copy()
    interf[u, serving] = 0.0
    x = (np.arange(samples) + 0.5)/samples
    act = f_on + (1 - f_on)*(x[:, None] < load[None, :]).astype(float)
    i = interf @ act.T
    lin = s[:, None]/(hm.NOISE_MW + hm.EVM**2*s[:, None] + i)
    return 10*np.log10(lin.mean(1))


def network_at(freq, sec, ues, seed):
    old = hm.F_HZ
    hm.F_HZ = freq
    try:
        return m.Model35(sec, ues, seed, 'RMa')
    finally:
        hm.F_HZ = old


def evaluate(sec, ues, seed, load, bands_of_site, f_on):
    """Per-site SINR / RSRP: mean over the site's (band, sector) cells of the mean of the users each serves."""
    rows = []
    for b, f in BANDS.items():
        cells = sec.site.map(lambda s: b in bands_of_site(s)).to_numpy()
        if not cells.any():
            continue
        net = network_at(f, sec, ues, seed)
        r = np.where(cells[None, :], net.rsrp(net.draw_los()), -np.inf)
        srv = r.argmax(1)
        rep = sinr_on(r, srv, np.where(cells, load, 0.0), f_on)
        rows.append(pd.DataFrame({'band': b, 'site': sec.site.to_numpy()[srv], 'sector': sec.sector.to_numpy()[srv],
                                  'sinr': rep, 'rsrp': r[np.arange(len(r)), srv]}))
    d = pd.concat(rows)
    cell = d.groupby(['site', 'band', 'sector'])[['sinr', 'rsrp']].mean()
    return cell.groupby('site').mean()


def main(region):
    sfx = '' if region == 'edremit' else '_' + region
    a3 = json.loads((HERE/f'adim3{sfx}.json').read_text(encoding='utf-8'))
    targets = pd.DataFrame(a3['targets'])
    train, test = a3['train_sites'], a3['test_sites']
    prb = pd.Series(a3['site_prb'])
    fill = a3.get('fill_prb', 0.21)
    all4 = set(BANDS)
    variants = {'taban': (lambda s: {'B3'}, 0.0), 'A1': (lambda s: all4, 0.0), 'B': (lambda s: {'B3'}, F_ON),
                'A1+B': (lambda s: all4, F_ON)}
    if region == 'edremit':
        variants['A2'] = (lambda s: CELLMAPPER.get(s, all4), 0.0)
    out = {'region': region, 'f_on': F_ON, 'train': train, 'test': test, 'variants': {}}
    for name, (bands_of, f_on) in variants.items():
        per = []
        for seed in m.DRAWS:
            secf = HERE/f'inputs/sectors_{region}24_{seed}.csv'
            uef = HERE/f'inputs/ues_{region}24_RMa_{seed}.csv'
            if not secf.exists():                       # first Edremit run used names without the site count
                secf, uef = HERE/f'inputs/sectors_{region}_{seed}.csv', HERE/f'inputs/ues_{region}_RMa_{seed}.csv'
            sec, ues = pd.read_csv(secf), pd.read_csv(uef)
            load = sec.site.map(prb).fillna(fill).to_numpy()
            site = evaluate(sec, ues, seed, load, bands_of, f_on)
            row = {}
            for g, ss in [('train', train), ('test', test)]:
                for q in ['sinr', 'rsrp']:
                    row[f'{q}_{g}'] = float(np.mean([abs(site.loc[s, q] - targets.loc[s, q]) for s in ss if s in site.index]))
            row['sinr_signed_mean'] = float(np.mean([site.loc[s, 'sinr'] - targets.loc[s, 'sinr'] for s in train + test]))
            per.append(row)
        mean = pd.DataFrame(per).mean().round(3).to_dict()
        out['variants'][name] = mean
        print(region, name, mean, flush=True)
    v = out['variants']
    best = min(v, key=lambda k: v[k]['sinr_train'])
    close = [k for k in v if v[k]['sinr_train'] - v[best]['sinr_train'] < 0.3]
    chosen = min(close, key=lambda k: v[k]['rsrp_train'])
    out['chosen'] = chosen
    out['accept'] = {'sinr_test_le_3': v[chosen]['sinr_test'] <= 3.0, 'rsrp_test_le_5': v[chosen]['rsrp_test'] <= 5.0}
    out['accepted'] = all(out['accept'].values())
    print('chosen', chosen, out['accept'])
    (HERE/f'sinama_{region}.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1])
