"""Windows, fast model, read-only for all earlier experiments.
Question: the per-user distance correction is computed from the distance to the user's HOME (or nearest) site and
is applied to ALL links of that user. When that site is removed the penalty stays. How much of the outage result
comes from this? Variant A = as run so far. Variant B = for affected users the correction is recomputed from the
nearest site that is still ON. Writes duzeltme_duyarlilik.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
D33, D34, D37 = DEN/'33_kesinti_ns3_2026-11-20', DEN/'34_yol_hareketi_2026-11-21', DEN/'37_edremit_kesinti_2026-11-22'
sys.path.insert(0, str(D37))
import hazirla as h  # noqa: E402
import senaryo as sc  # noqa: E402
import alan  # noqa: E402
hm = alan.hm


def corr(k0, k1, d):
    return k0 + k1*np.log10(np.clip(d, 100, 15000))


def nearest_on(x, y, sx, sy):
    return np.hypot(x[:, None] - sx[None], y[:, None] - sy[None]).min(1)


def sindirgi():
    plan = json.loads((D33/'plan.json').read_text(encoding='utf-8'))
    b = sc.Builder(42, plan['quake'])
    ues = pd.read_csv(D33/'inputs/ues_quake_42.csv')
    pk, iv = np.full(len(ues), 512.0), np.full(len(ues), plan['udp_interval_ms'])
    out = {}
    for name in ['K1', 'K2', 'K3']:
        off = plan['scenarios'][name]['off']
        on = b.cells_on(off)
        around = ues.home_site.isin(off).to_numpy()
        act = b.sites[~b.sites.index.isin(off)]
        row = {'users_around': int(around.sum())}
        for var in 'AB':
            u = ues.copy()
            if var == 'B':
                d = nearest_on(u.x_m.to_numpy()[around], u.y_m.to_numpy()[around], act.x_m.to_numpy(), act.y_m.to_numpy())
                u.loc[around, 'extra_loss_db'] = corr(b.k0, b.k1, d)
            net = alan.Network34(b.sec, u, 42)
            load = hm.solve(net, net.draw_los(), pk, iv, cell_on=on)['load']
            rr = np.where(on[None, :], net.rsrp(net.draw_los()), -np.inf)
            srv = rr.argmax(1)
            _, sched = hm.sinr(rr, srv, load)
            _, cqi = hm.mcs_from_sinr_db(sched)
            row[f'no_service_around_{var}'] = float((cqi[around] == 0).mean())
        out[name] = row
        print('Sindirgi', name, off, row, flush=True)
    return out


def yol():
    plan = json.loads((D33/'plan.json').read_text(encoding='utf-8'))
    b = sc.Builder(42, plan['quake'])
    ues = pd.read_csv(D33/'inputs/ues_quake_42.csv')
    net_q = alan.Network34(b.sec, ues, 42)
    pk, iv = np.full(len(ues), 512.0), np.full(len(ues), plan['udp_interval_ms'])
    out = {}
    for route, scen in [('A', 'K2'), ('B', 'K1')]:
        r = pd.read_csv(D34/f'inputs/rota_{route}.csv')
        off = plan['scenarios'][scen]['off']
        on = b.cells_on(off)
        load = hm.solve(net_q, net_q.draw_los(), pk, iv, cell_on=on)['load']
        act = b.sites[~b.sites.index.isin(off)]
        step = float(np.median(np.diff(r.d_along_m)))
        row = {}
        for var in 'AB':
            u = r.copy()
            if var == 'B':
                u['extra_loss_db'] = corr(b.k0, b.k1, nearest_on(u.x_m.to_numpy(), u.y_m.to_numpy(), act.x_m.to_numpy(), act.y_m.to_numpy()))
            net = alan.Network34(b.sec, u, 42)
            rr = np.where(on[None, :], net.rsrp(net.draw_los()), -np.inf)
            _, sched = hm.sinr(rr, rr.argmax(1), load)
            _, cqi = hm.mcs_from_sinr_db(sched)
            bad = cqi == 0
            runs, cur = [], 0
            for v in bad:
                if v:
                    cur += 1
                elif cur:
                    runs.append(cur); cur = 0
            if cur:
                runs.append(cur)
            row[f'km_no_service_{var}'] = round(float(bad.sum()*step/1000), 2)
            row[f'longest_gap_km_{var}'] = round(max(runs, default=0)*step/1000, 2)
        out[route] = row
        print('Road', route, scen, row, flush=True)
    return out


def edremit():
    plan = json.loads((D37/'plan.json').read_text(encoding='utf-8'))
    k0, k1 = plan['k0_k1']
    sites, _ = h.sites48()
    ues = pd.read_csv(D37/'inputs/ues_quake.csv')
    pk, iv = np.full(len(ues), 512.0), ues.udp_interval_ms.to_numpy(float)
    rows = []
    for seed in [42, 7, 99]:
        sec, _ = h.m.sectors_of(sites, seed)
        for name, off in [('E1', ['SITE_000529']), ('E2', ['SITE_000105'])]:
            on = ~sec.site.isin(off).to_numpy()
            around = (ues.kind == 'quake').to_numpy() & ues.home_site.isin(off).to_numpy()
            act = sites[~sites.site.isin(off)]
            for var in 'AB':
                u = ues.copy()
                if var == 'B':
                    d = nearest_on(u.x_m.to_numpy()[around], u.y_m.to_numpy()[around], act.x_m.to_numpy(), act.y_m.to_numpy())
                    u.loc[around, 'extra_loss_db'] = corr(k0, k1, d)
                net = h.m.Model35(sec, u, seed, 'RMa')
                r = h.solve_f(net, pk, iv, on, h.F_ON)
                rows.append({'scenario': name, 'seed': seed, 'variant': var, 'no_service_around': float((r['cqi'][around] == 0).mean())})
                print('Edremit', rows[-1], flush=True)
    d = pd.DataFrame(rows)
    return d.groupby(['scenario', 'variant']).no_service_around.mean().unstack().to_dict('index')


if __name__ == '__main__':
    out = {'sindirgi_outage': sindirgi(), 'road': yol(), 'edremit_outage_mean_3_draws': edremit()}
    (HERE/'duzeltme_duyarlilik.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(out['edremit_outage_mean_3_draws'], indent=1))
