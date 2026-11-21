"""Windows: two routes for the moving-vehicle runs and their coverage with the new model (fast, Network34).
Route A: il yolu 10-31 past site 130 (the road that lost ~15 km in step 2 when 130 is off).
Route B: D240 Simav-Sindirgi past site 482 (state road next to the 2025-10-28 outage site).
Each route = the OSM ways of that ref chained end to end, kept within 6 km of its site, resampled every 10 m.
Coverage: deneyler/33 load and criteria (as yol_kapsama.py), K0 and the outage of that site.
Writes inputs/rota_A.csv, inputs/rota_B.csv, rota.json, rota.png."""
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
import alan  # noqa: E402
import yollar  # noqa: E402
hm = alan.hm
sys.path.insert(0, str(HERE.parent/'32_kesinti_hazirligi_2026-11-20'))
import senaryo as sc  # noqa: E402
D33 = HERE.parent/'33_kesinti_ns3_2026-11-20'
ROUTES = {'A': ('10-31', 'SITE_000130', 'K2'), 'B': ('D240', 'SITE_000482', 'K1')}
STEP = 10.0


def chain(ways):
    """Join polylines whose end points touch (within 1 m) into the longest chain."""
    segs = [np.asarray(w) for w in ways]
    best = None
    for start in range(len(segs)):
        line, used = segs[start].copy(), {start}
        grown = True
        while grown:
            grown = False
            for i, s in enumerate(segs):
                if i in used:
                    continue
                for cand in (s, s[::-1]):
                    if np.hypot(*(line[-1] - cand[0])) < 1.0:
                        line = np.vstack([line, cand[1:]]); used.add(i); grown = True; break
                    if np.hypot(*(line[0] - cand[-1])) < 1.0:
                        line = np.vstack([cand[:-1], line]); used.add(i); grown = True; break
        length = np.hypot(*np.diff(line, axis=0).T).sum()
        if best is None or length > best[1]:
            best = (line, length)
    return best[0]


def main():
    plan = json.loads((D33/'plan.json').read_text(encoding='utf-8'))
    b = sc.Builder(42, plan['quake'])
    ues = pd.read_csv(D33/'inputs/ues_quake_42.csv')
    net_q = alan.Network34(b.sec, ues, 42)
    pk, iv = np.full(len(ues), 512.0), np.full(len(ues), plan['udp_interval_ms'])
    osm = json.loads((HERE/'inputs/osm/osm_ana_yollar.json').read_text(encoding='utf-8'))
    sx, sy = b.sites.x_m.to_numpy(), b.sites.y_m.to_numpy()
    out, fig = {}, plt.figure(figsize=(12, 6))
    for k, (ref, site, scen) in ROUTES.items():
        ways = [yollar.to_xy([q['lat'] for q in w['geometry']], [q['lon'] for q in w['geometry']])
                for w in osm['elements'] if w.get('type') == 'way' and 'geometry' in w and w['tags'].get('ref') == ref]
        line = chain(ways)
        pts, s = yollar.resample(line, STEP)
        c = b.sites.loc[site]
        near = np.hypot(pts[:, 0] - c.x_m, pts[:, 1] - c.y_m) <= 6000
        idx = np.where(near)[0]
        pts, s = pts[idx[0]:idx[-1] + 1], s[idx[0]:idx[-1] + 1] - s[idx[0]]
        d = np.hypot(pts[:, 0, None] - sx[None], pts[:, 1, None] - sy[None])
        r = pd.DataFrame({'d_along_m': s.round(1), 'x_m': pts[:, 0].round(3), 'y_m': pts[:, 1].round(3), 'z_m': 1.5,
                          'extra_loss_db': b.k0 + b.k1*np.log10(np.clip(d.min(1), 100, 15000))})
        r.to_csv(HERE/f'inputs/rota_{k}.csv', index=False, lineterminator='\n')
        net_r = alan.Network34(b.sec, r, 42)
        res = {'ref': ref, 'site': site, 'outage': scen, 'length_km': round(float(s[-1])/1000, 2)}
        ax = fig.add_subplot(1, 2, len(out) + 1)
        for j, sc_name in enumerate(['K0', scen]):
            on = b.cells_on(plan['scenarios'][sc_name]['off'])
            load = hm.solve(net_q, net_q.draw_los(), pk, iv, cell_on=on)['load']
            rr = np.where(on[None, :], net_r.rsrp(net_r.draw_los()), -np.inf)
            srv = rr.argmax(1)
            _, sched = hm.sinr(rr, srv, load)
            _, cqi = hm.mcs_from_sinr_db(sched)
            bad = cqi == 0
            runs, cur = [], 0
            for v in bad:
                if v:
                    cur += 1
                elif cur:
                    runs.append(cur*STEP); cur = 0
            if cur:
                runs.append(cur*STEP)
            res[sc_name] = {'km_no_service': round(float(bad.sum()*STEP/1000), 2), 'gaps': len(runs),
                            'longest_gap_km': round(max(runs, default=0)/1000, 2),
                            'serving_cell_changes': int((np.diff(srv) != 0).sum())}
            ax.plot(s/1000, sched, lw=0.8, label=f'{sc_name} ({"kesinti yok" if sc_name == "K0" else site[-3:] + " kapalı"})')
        ax.axhline(-6.7, color='red', ls='--', lw=0.8)
        ax.set_title(f'Rota {k}: {ref}, {site[-3:]} çevresi ({res["length_km"]} km)')
        ax.set_xlabel('yol boyunca km'); ax.set_ylabel('sinyal kalitesi (SINR, dB)'); ax.legend(fontsize=8)
        out[k] = res
        print(k, res)
    fig.suptitle('Yol boyunca sinyal kalitesi, yeni model (kırmızı çizgi altı: servis yok)')
    fig.tight_layout(); fig.savefig(HERE/'rota.png', dpi=120)
    (HERE/'rota.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
