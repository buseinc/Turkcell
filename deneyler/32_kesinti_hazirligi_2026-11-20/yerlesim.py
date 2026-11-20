"""Windows: step 3 - how much do the results depend on where the users are placed?

Predeclared: the three placement rules of senaryo.py (A = deneyler/26-29 rule, B = busy-hour weighted,
C = exponential spread) are compared; A stays the main rule (it is the one validated against Experia in
deneyler/26 and 29). The comparison is NOT used to pick a rule; in the outage scenarios B and C are reported
next to A as a sensitivity band. Load: 27 Oct earthquake window (the one with the real 482 outage).
Per rule: 3 antenna draws x 3 user placements x 10 LOS draws. Reported: users beyond 5 km, step-1 metrics
without outage, and the same metrics for the users placed around 482 when site 482 is switched off.
"""
from pathlib import Path
import json

import numpy as np

import senaryo as sc

HERE = Path(__file__).resolve().parent
QUAKE = '2025-10-27'


def main():
    out = {}
    for rule in ['A', 'B', 'C']:
        acc = {'far_5km': [], 'base': [], 'off482_home482': [], 'off482_all': []}
        for az in sc.AZ:
            b = sc.Builder(az, QUAKE)
            for p in range(3):
                rng = np.random.default_rng(hash((rule, az, p)) % 2**32)
                ues = b.place(rule, rng)
                net = b.network(ues)
                los = [net.draw_los(rng) for _ in range(10)]
                iv = b.calibrate_interval(net, los[:3])
                size, inter = np.full(len(ues), 512.0), np.full(len(ues), iv)
                home = (ues.home_site == 'SITE_000482').to_numpy()
                acc['far_5km'].append(float((ues.distance_m > 5000).mean()))
                for L in los:
                    acc['base'].append(sc.outcome(b, ues, sc.hm.solve(net, L, size, inter)))
                    r = sc.hm.solve(net, L, size, inter, cell_on=b.cells_on(['SITE_000482']))
                    acc['off482_home482'].append(sc.outcome(b, ues, r, home))
                    acc['off482_all'].append(sc.outcome(b, ues, r))
        res = {'far_5km': float(np.mean(acc['far_5km']))}
        for k in ['base', 'off482_home482', 'off482_all']:
            rows = acc[k]
            res[k] = {m: [float(np.mean([x[m] for x in rows])), float(np.percentile([x[m] for x in rows], 5)),
                          float(np.percentile([x[m] for x in rows], 95))] for m in rows[0] if m != 'users'}
            res[k]['users'] = float(np.mean([x['users'] for x in rows]))
        out[rule] = res
        print(rule, json.dumps({k: (v if not isinstance(v, dict) else {m: [round(x, 3) for x in w] if isinstance(w, list) else round(w, 1)
                                                                        for m, w in v.items()}) for k, v in res.items()}), flush=True)
    (HERE/'yerlesim.json').write_text(json.dumps({'rule': __doc__, 'results': out}, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
