"""Windows: coverage along the real roads (step 2 of PLAN.md), fast model = ns-3 formulas, no mobility.

Rule written before the run:
- Network, antenna draw 42, earthquake users and packet interval exactly as deneyler/33 (plan.json).
  For every scenario K0-K3 and LOS draw, the cell loads come from the earthquake users (solve); the road
  points are test points that add no load.
- Road points every 50 m (yol_noktalari.csv), only those within 6 km of an evaluation site (the area where
  users are placed; outside it edge effects dominate, deneyler/10).
- Distance correction of deneyler/26 for a road point: same formula as for the placed users, with the
  distance to the nearest site of the full 24-site network (as deneyler/33: a user keeps its home-site
  correction when that site is off), clipped to 100-15000 m like the placement.
- Service criteria of deneyler/32 TANIMLAR.md: no service = CQI 0 (SINR < -6.7 dB on the scheduled RBs);
  weak = RSRP < -121.8 dBm.
- 20 LOS draws; reported: road km without service by road class and for the main roads, median and 5-95 %.
- Known limit: the 8 dB link shadow is drawn independently at every point (no spatial correlation). Shares of
  road km are fine; the length of single gaps is not and is not reported from this step.
"""
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
DEN = HERE.parent
sys.path.insert(0, str(DEN/'32_kesinti_hazirligi_2026-11-20'))
import senaryo as sc  # noqa: E402
import hizli_model as hm  # noqa: E402

D33 = DEN/'33_kesinti_ns3_2026-11-20'
STEP_KM = 0.05
DRAWS = 20


def main():
    plan = json.loads((D33/'plan.json').read_text(encoding='utf-8'))
    b = sc.Builder(42, plan['quake'])
    ues = pd.read_csv(D33/'inputs/ues_quake_42.csv')
    nq = len(ues)
    net_q = b.network(ues)
    pk, iv = np.full(nq, 512.0), np.full(nq, plan['udp_interval_ms'])

    p = pd.read_csv(HERE/'inputs/yol_noktalari.csv')
    sx, sy = b.sites.x_m.to_numpy(), b.sites.y_m.to_numpy()
    d = np.hypot(p.x_m.to_numpy()[:, None] - sx[None], p.y_m.to_numpy()[:, None] - sy[None])
    ev = (b.sites.role == 'Evaluation').to_numpy()
    p = p[d[:, ev].min(1) <= 6000].reset_index(drop=True)
    d = np.hypot(p.x_m.to_numpy()[:, None] - sx[None], p.y_m.to_numpy()[:, None] - sy[None])
    p['near_site'] = b.sites.index.to_numpy()[d.argmin(1)]
    dn = np.clip(d.min(1), 100.0, 15000.0)
    p['extra_loss_db'] = b.k0 + b.k1*np.log10(dn)
    p['z_m'] = 1.5
    net_r = b.network(p)
    print('road points', len(p), 'km', round(len(p)*STEP_KM, 1))

    nos = {k: np.zeros((DRAWS, len(p)), bool) for k in plan['scenarios']}
    weak = {k: np.zeros((DRAWS, len(p)), bool) for k in plan['scenarios']}
    for i in range(DRAWS):
        los_q = net_q.draw_los(np.random.default_rng(1000 + i))
        los_r = net_r.draw_los(np.random.default_rng(5000 + i))
        r0 = net_r.rsrp(los_r)
        for k, v in plan['scenarios'].items():
            on = b.cells_on(v['off'])
            load = hm.solve(net_q, los_q, pk, iv, cell_on=on)['load']
            r = np.where(on[None, :], r0, -np.inf)
            srv = np.argmax(r, axis=1)
            _, sched = hm.sinr(r, srv, load)
            _, cqi = hm.mcs_from_sinr_db(sched)
            nos[k][i] = cqi == 0
            weak[k][i] = r[np.arange(len(r)), srv] < sc.REFSENS_RE_DBM

    def q(a):
        return [round(float(np.quantile(a, .05)), 3), round(float(np.median(a)), 3), round(float(np.quantile(a, .95)), 3)]

    groups = {'tüm yollar': np.ones(len(p), bool)}
    for cls in ['trunk', 'primary', 'secondary', 'tertiary']:
        groups[cls] = (p.highway == cls).to_numpy()
    for ref in ['D555', 'D565', 'D240']:
        groups[ref] = (p.ref == ref).to_numpy()
    for s in ['SITE_000482', 'SITE_000130']:
        groups[f'yakın saha {s[-3:]}'] = (p.near_site == s).to_numpy()
    out = {'road_points': int(len(p)), 'road_km': round(len(p)*STEP_KM, 1), 'results': {}}
    for g, m in groups.items():
        if m.sum() == 0:
            continue
        out['results'][g] = {'km': round(float(m.sum()*STEP_KM), 1)}
        for k in plan['scenarios']:
            out['results'][g][k] = {'km_no_service': q(nos[k][:, m].sum(1)*STEP_KM),
                                    'share_no_service': q(nos[k][:, m].mean(1)),
                                    'share_weak': q(weak[k][:, m].mean(1))}
    (HERE/'yol_kapsama.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    for g, v in out['results'].items():
        print(g, v['km'], 'km |', ' '.join(f"{k}: {v[k]['km_no_service'][1]:.1f} km ({v[k]['share_no_service'][1]:.1%})" for k in plan['scenarios']))

    # map: share of LOS draws without service at each road point, K0 vs K3
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.5), sharex=True, sharey=True)
    for ax, k, title in [(axs[0], 'K0', 'Kesinti yok'), (axs[1], 'K3', '482 ve 130 kapalı')]:
        f = nos[k].mean(0)
        ax.scatter(p.x_m/1000, p.y_m/1000, c='#d9d9d9', s=1)
        bad = f >= 0.5
        ax.scatter(p.x_m[bad]/1000, p.y_m[bad]/1000, c='#d7301f', s=4, label='servis yok (çekilişlerin yarısından çoğunda)')
        on = b.cells_on(plan['scenarios'][k]['off'])
        st = b.sites.reset_index()
        off_sites = set(plan['scenarios'][k]['off'])
        live = ~st.site.isin(off_sites)
        ax.scatter(st.x_m[live]/1000, st.y_m[live]/1000, marker='^', c='k', s=30, label='çalışan saha')
        if (~live).any():
            ax.scatter(st.x_m[~live]/1000, st.y_m[~live]/1000, marker='x', c='red', s=80, label='çöken saha')
        km = np.median(nos[k].sum(1))*STEP_KM
        ax.set_title(f'{title}: servissiz yol {km:.1f} km / {len(p)*STEP_KM:.0f} km')
        ax.set_aspect('equal')
        ax.set_xlabel('doğu (km)')
        ax.legend(loc='lower left', fontsize=8)
    axs[0].set_ylabel('kuzey (km)')
    fig.suptitle('Yol boyunca servis (ana sahaların 6 km çevresindeki yollar, deprem yükü, 20 görüş hattı çekilişi)')
    fig.tight_layout()
    fig.savefig(HERE/'yol_kapsama.png', dpi=130)


if __name__ == '__main__':
    main()
