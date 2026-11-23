"""Windows: ADIM3_KURALLAR.md Ek 4 - share c of neighbour power that comes from cells whose reference signals
collide with the serving cell (same PCI mod 3), per user. P1: PCI group = sector index; P2: random groups
(co-site sectors still different). No fitting. Writes pci_payi.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
import model35 as m  # noqa: E402
import alan  # noqa: E402
hm = m.hm
D29 = HERE.parent/'29_ihtiyaca_gore_zamanlayici_2026-11-19'


def share(r, groups):
    p = 10**(r/10)
    u = np.arange(len(p))
    srv = p.argmax(1)
    nb = p.copy(); nb[u, srv] = 0.0
    same = groups[None, :] == groups[srv][:, None]
    return (nb*same).sum(1)/nb.sum(1)


def p2_groups(sec, rng):
    g = np.empty(len(sec), int)
    for s, idx in sec.groupby('site').indices.items():
        g[idx] = rng.permutation(3)[:len(idx)] if len(idx) <= 3 else rng.integers(0, 3, len(idx))
    return g


def cases():
    for region in ['edremit', 'balikesir']:
        for seed in m.DRAWS:
            secf = HERE/f'inputs/sectors_{region}24_{seed}.csv'
            uef = HERE/f'inputs/ues_{region}24_RMa_{seed}.csv'
            if not secf.exists():
                secf, uef = HERE/f'inputs/sectors_{region}_{seed}.csv', HERE/f'inputs/ues_{region}_RMa_{seed}.csv'
            sec, ues = pd.read_csv(secf), pd.read_csv(uef)
            net = m.Model35(sec, ues, seed, 'RMa')
            yield region, seed, sec, net.rsrp(net.draw_los())
    plan = json.loads((D29/'plan.json').read_text(encoding='utf-8'))
    for c in plan['validation_cases']:
        sec = pd.read_csv(D29/'simulation/results'/c['name']/'sectors.csv')
        sites = pd.read_csv(D29/'inputs'/c['sites_file']).set_index('site')
        sec['x_m'], sec['y_m'] = sec.site.map(sites.x_m), sec.site.map(sites.y_m)
        ues = pd.read_csv(D29/'inputs'/c['ue_file']).iloc[:256]
        net = alan.Network34(sec, ues, c['shadow_seed'])
        yield 'sindirgi', c['shadow_seed'], sec, net.rsrp(net.draw_los())


def main():
    rows = []
    for region, seed, sec, r in cases():
        c1 = share(r, sec.sector.to_numpy())
        c2 = np.mean([share(r, p2_groups(sec, np.random.default_rng(100 + k))) for k in range(10)], axis=0)
        rows.append({'region': region, 'seed': seed, 'P1_mean': float(c1.mean()), 'P1_median': float(np.median(c1)),
                     'P2_mean': float(c2.mean()), 'P2_median': float(np.median(c2))})
    d = pd.DataFrame(rows)
    by = d.groupby('region')[['P1_mean', 'P1_median', 'P2_mean', 'P2_median']].mean().round(3)
    p1 = float(by.P1_mean.mean())
    out = {'by_region': by.to_dict('index'), 'P1_mean_three_regions': p1, 'fitted_f': 0.03,
           'supported': bool(0.015 <= p1 <= 0.06), 'draws': rows}
    (HERE/'pci_payi.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(by.to_string()); print('P1 mean of regions', round(p1, 3), 'supported', out['supported'])


if __name__ == '__main__':
    main()
