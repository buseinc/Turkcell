"""Windows: acceptance rule 4 of DUZELTMELER.md. Along the roads near the evaluation sites, points every 10 m:
std of the RSRP change between consecutive points (best cell RSRP of the full network, no outage) must be
< 2 dB with the new model. The old model is reported for comparison. Writes kabul4.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
import alan  # noqa: E402
import yollar  # noqa: E402
hm = alan.hm
sys.path.insert(0, str(HERE.parent/'32_kesinti_hazirligi_2026-11-20'))
import senaryo as sc  # noqa: E402


def main():
    b = sc.Builder(42, '2025-10-27')
    osm = json.loads((HERE/'inputs/osm/osm_ana_yollar.json').read_text(encoding='utf-8'))
    sx, sy = b.sites.x_m.to_numpy(), b.sites.y_m.to_numpy()
    ev = (b.sites.role == 'Evaluation').to_numpy()
    rows = []
    for w in osm['elements']:
        if w.get('type') != 'way' or 'geometry' not in w or w['tags'].get('highway', '').startswith('tertiary'):
            continue
        g = w['geometry']
        pts = yollar.to_xy([q['lat'] for q in g], [q['lon'] for q in g])
        if len(pts) < 2:
            continue
        pr, _ = yollar.resample(pts, 10.0)
        d = np.hypot(pr[:, 0, None] - sx[None], pr[:, 1, None] - sy[None])
        keep = d[:, ev].min(1) <= 6000
        if keep.sum() < 20:
            continue
        dn = np.clip(d.min(1), 100, 15000)
        rows.append(pd.DataFrame({'way': w['id'], 'x_m': pr[:, 0], 'y_m': pr[:, 1], 'z_m': 1.5,
                                  'extra_loss_db': b.k0 + b.k1*np.log10(dn), 'keep': keep}))
    p = pd.concat(rows, ignore_index=True)
    out = {'points': int(len(p))}
    for name, net in [('old', hm.Network(b.sec, p, 42)), ('new', alan.Network34(b.sec, p, 42))]:
        los = net.draw_los(np.random.default_rng(3)) if name == 'old' else net.draw_los()
        best = net.rsrp(los).max(1)
        steps = []
        for _, g in p.assign(best=best).groupby('way'):
            m = g.keep.to_numpy()
            dd = np.diff(g.best.to_numpy())[m[1:] & m[:-1]]
            steps.append(dd)
        s = np.concatenate(steps)
        out[name] = {'step_std_db': float(s.std()), 'step_p99_abs_db': float(np.quantile(abs(s), .99))}
    out['pass'] = out['new']['step_std_db'] < 2.0
    (HERE/'kabul4.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
