"""Windows: ADIM3_KURALLAR.md Ek 3 - one shared always-on share f, fitted on the TRAINING sites of Edremit and
Balikesir only, then tested on their held-out sites and on the three Sindirgi validation cases.
Writes kalibrasyon.json and kalibrasyon.png."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
import model35 as m  # noqa: E402
import sinamalar as sn  # noqa: E402
import alan  # noqa: E402  (deneyler/34, on the path through model35)
hm = m.hm
GRID = np.round(np.arange(0.0, 0.2141, 0.005), 3)
D29 = HERE.parent/'29_ihtiyaca_gore_zamanlayici_2026-11-19'


def region_cache(region):
    """Per draw: sectors, serving, RSRP matrix and load (f does not change RSRP or serving)."""
    sfx = '' if region == 'edremit' else '_' + region
    a3 = json.loads((HERE/f'adim3{sfx}.json').read_text(encoding='utf-8'))
    prb = pd.Series(a3['site_prb'])
    fill = a3.get('fill_prb', 0.21)
    out = []
    for seed in m.DRAWS:
        secf = HERE/f'inputs/sectors_{region}24_{seed}.csv'
        uef = HERE/f'inputs/ues_{region}24_RMa_{seed}.csv'
        if not secf.exists():
            secf, uef = HERE/f'inputs/sectors_{region}_{seed}.csv', HERE/f'inputs/ues_{region}_RMa_{seed}.csv'
        sec, ues = pd.read_csv(secf), pd.read_csv(uef)
        net = m.Model35(sec, ues, seed, 'RMa')
        r = net.rsrp(net.draw_los())
        out.append((sec, r, r.argmax(1), sec.site.map(prb).fillna(fill).to_numpy()))
    return a3, pd.DataFrame(a3['targets']), out


def site_errors(a3, targets, cache, f):
    res = []
    for sec, r, srv, load in cache:
        ss = m.site_mean(sec, srv, sn.sinr_on(r, srv, load, f))
        res.append({g: float(np.mean([abs(ss[s] - targets.sinr[s]) for s in a3[f'{g}_sites'] if s in ss]))
                    for g in ['train', 'test']})
    return pd.DataFrame(res).mean()


def sindirgi(f_values):
    """Sindirgi validation cases (deneyler/34 kabul3 method, new shadow/LOS): site SINR error vs Experia."""
    targets = pd.read_csv(D29/'inputs/targets.csv').set_index('site')
    plan = json.loads((D29/'plan.json').read_text(encoding='utf-8'))
    rows = {f: [] for f in f_values}
    for c in plan['validation_cases']:
        fo = D29/'simulation/results'/c['name']
        sec = pd.read_csv(fo/'sectors.csv')
        sites = pd.read_csv(D29/'inputs'/c['sites_file']).set_index('site')
        sec['x_m'], sec['y_m'] = sec.site.map(sites.x_m), sec.site.map(sites.y_m)
        ues = pd.read_csv(D29/'inputs'/c['ue_file'])
        size = ues.packet_size_bytes.to_numpy(float) if 'packet_size_bytes' in ues else np.full(len(ues), 512.0)
        net = alan.Network34(sec, ues, c['shadow_seed'])
        sol = hm.solve(net, net.draw_los(), size, ues.udp_interval_ms.to_numpy(float))
        r = np.where(np.ones(len(sec), bool)[None, :], net.rsrp(net.draw_los()), -np.inf)
        srv = sol['serving']
        for f in f_values:
            rep = sn.sinr_on(r, srv, sol['load'], f)
            d = pd.DataFrame({'site': sec.site.to_numpy()[srv][:256], 'sector': sec.sector.to_numpy()[srv][:256], 'v': rep[:256]})
            ss = d.groupby(['site', 'sector']).v.mean().groupby('site').mean()
            rows[f].append({sp: float(np.mean([abs(ss[s] - targets.sinr_target[s]) for s in targets[targets.split == sp].index if s in ss]))
                            for sp in ['train', 'holdout']})
    return {f: pd.DataFrame(v).mean().to_dict() for f, v in rows.items()}


def main():
    reg = {r: region_cache(r) for r in ['edremit', 'balikesir']}
    scan = []
    for f in GRID:
        e = {r: site_errors(*reg[r], f) for r in reg}
        scan.append({'f': float(f), 'train_both': float(np.mean([e[r]['train'] for r in reg])),
                     **{f'{r}_{g}': float(e[r][g]) for r in reg for g in ['train', 'test']}})
    s = pd.DataFrame(scan)
    best = s.loc[s.train_both.idxmin()]
    f_star = float(best.f)
    sind = sindirgi([0.0, f_star])
    checks = {'edremit_test_le_3': bool(best.edremit_test <= 3.0), 'balikesir_test_le_3': bool(best.balikesir_test <= 3.0),
              'sindirgi_train_within_1db': bool(sind[f_star]['train'] <= sind[0.0]['train'] + 1.0),
              'sindirgi_holdout_within_1db': bool(sind[f_star]['holdout'] <= sind[0.0]['holdout'] + 1.0)}
    out = {'f_star': f_star, 'at_f_star': best.round(3).to_dict(), 'sindirgi': sind, 'checks': checks,
           'note': 'f is a fitted coefficient, not a physical share', 'scan': s.round(3).to_dict('list')}
    (HERE/'kalibrasyon.json').write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float), encoding='utf-8')
    print('f*', f_star, best.round(2).to_dict()); print('sindirgi', sind); print(checks)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for col, lab, st in [('edremit_train', 'Edremit eğitim', '-'), ('edremit_test', 'Edremit test', '--'),
                         ('balikesir_train', 'Balıkesir eğitim', '-'), ('balikesir_test', 'Balıkesir test', '--')]:
        ax.plot(s.f, s[col], st, label=lab)
    ax.axvline(f_star, color='grey', lw=0.8); ax.axhline(3, color='red', lw=0.8, ls=':')
    ax.set_xlabel('komşuların hep yayında sayılan payı f (ayar katsayısı)'); ax.set_ylabel('saha başına SINR farkı (dB)')
    ax.set_title(f'Ayar yalnız eğitim sahalarına göre: f = {f_star}'); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(HERE/'kalibrasyon.png', dpi=120)


if __name__ == '__main__':
    main()
