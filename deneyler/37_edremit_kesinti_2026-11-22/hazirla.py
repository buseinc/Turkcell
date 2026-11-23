"""Windows: inputs of deneyler/37 (KURALLAR.md) and the fast-model preview.
Writes inputs/ (sites_E0..E2.csv, ues_quake.csv), plan.json, onizleme.json."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
D35 = DEN/'35_bolge_secimi_2026-11-21'
sys.path.insert(0, str(D35))
sys.path.insert(0, str(DEN/'36_hep_yayinda_payi_ns3_2026-11-22'))
import model35 as m  # noqa: E402
import kiyi  # noqa: E402
import secim  # noqa: E402
from sindirgi_f import sinr_f  # noqa: E402
hm = m.hm

F_ON = 0.03
QUAKE = ('2025-10-27 22:45', '2025-10-28 01:15')
TARGET_PRB = 0.18
LOAD_FACTOR = 0.2605345440100384*0.142/0.193          # deneyler/34 hazirla_yol.py (ms x PRB)
SCEN = {'E0': [], 'E1': ['SITE_000529'], 'E2': ['SITE_000105']}
U = 'Avg_Sim_RRC_Connected_User_Num_ERI'


def sites48():
    meta = json.loads((D35/'secim.json').read_text(encoding='utf-8'))
    lat0, lon0 = meta['centre_lat_lon']
    s = pd.read_csv(D35/'inputs/sites_edremit.csv')
    co = pd.read_excel(DEN.parent/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('site').set_index('site')
    xy = secim.to_xy(co.lat.to_numpy(), co.lon.to_numpy(), lat0, lon0)
    co['x_m'], co['y_m'] = xy[:, 0], xy[:, 1]
    co['d'] = np.hypot(co.x_m, co.y_m)
    extra = co.drop(s.site).sort_values('d').head(24)
    s = pd.concat([s, pd.DataFrame({'site': extra.index, 'role': 'Extra buffer', 'x_m': extra.x_m.to_numpy(),
                                    'y_m': extra.y_m.to_numpy()})], ignore_index=True)
    sec, rot = m.sectors_of(s, 42)
    s['rotation_deg'] = s.site.map(rot)
    s['sector_count'], s['carriers'] = 3, 'B3'
    return s, sec


def land_point(x0, y0, ang, seg):
    for da in [0, 30, -30, 60, -60]:
        for d in [800, 600, 400, 200]:
            a = np.radians(ang + da)
            x, y = x0 + d*np.cos(a), y0 + d*np.sin(a)
            if kiyi.on_land([x], [y], seg)[0]:
                return x, y, d
    raise RuntimeError('no land point')


def solve_f(net, pk, iv, on, f, iters=60):
    r = np.where(on[None, :], net.rsrp(net.draw_los()), -np.inf)
    srv = r.argmax(1)
    pps = 1000.0/iv
    load = np.where(on, 0.5, 0.0)
    for _ in range(iters):
        _, sched = sinr_f(r, srv, load, f)
        mcs, cqi = hm.mcs_from_sinr_db(sched)
        rb = hm.rb_per_packet(mcs, cqi, pk)
        dem = np.bincount(srv, weights=np.nan_to_num(rb)*pps, minlength=len(on))/(hm.N_RB*1000.0)
        new = np.where(on, np.minimum(dem, 1.0), 0.0)
        if np.max(abs(new - load)) < 1e-4:
            load = new
            break
        load = 0.5*load + 0.5*new
    rep, sched = sinr_f(r, srv, load, f)
    _, cqi = hm.mcs_from_sinr_db(sched)
    return {'serving': srv, 'rsrp': r[np.arange(len(r)), srv], 'sinr': rep, 'cqi': cqi, 'load': load, 'demand': dem}


def main():
    (HERE/'inputs').mkdir(exist_ok=True)
    sites, sec = sites48()
    seg = kiyi.segments()
    k0, k1 = json.loads((D35/'adim3_48.json').read_text(encoding='utf-8'))['models']['RMa']['k0_k1']
    kpi = pd.read_csv(D35/'kpi_cells.csv.gz', parse_dates=['DATETIME'])
    w = kpi[(kpi.DATETIME >= QUAKE[0]) & (kpi.DATETIME < QUAKE[1])]
    users_cell = w.groupby(['site', 'DATETIME'])[U].mean().groupby('site').mean()
    e = pd.read_csv(D35/'experia_cells.csv.gz').dropna(subset=['AVG(TAAVG)'])
    ta = pd.DataFrame({'site': e.site, 'd': (e['AVG(TAAVG)']*4.88).clip(100, 15000)})
    ev = sites.site[sites.role == 'Evaluation'].tolist()
    rng = np.random.default_rng(37042)
    rows = []
    core = sites[sites.role != 'Extra buffer']
    for _, s in core.iterrows():
        n = int(round(users_cell.get(s.site, 0.0)*3))
        pool = ta[ta.site == s.site].d.to_numpy()
        if len(pool) == 0:
            pool = ta[ta.site.isin(ev)].d.to_numpy()
        k = 0
        while k < n:
            d = pool[rng.integers(len(pool))]
            for _ in range(50):
                a = rng.uniform(0, 2*np.pi)
                x, y = s.x_m + d*np.cos(a), s.y_m + d*np.sin(a)
                if kiyi.on_land([x], [y], seg)[0]:
                    rows.append({'x_m': x, 'y_m': y, 'kind': 'quake', 'home_site': s.site, 'distance_m': d}); k += 1
                    break
    ext = sec[sec.role == 'Extra buffer']
    for _, c in ext.iterrows():
        x, y, d = land_point(c.x_m, c.y_m, c.orientation_ccw_from_east_deg, seg)
        rows.append({'x_m': x, 'y_m': y, 'kind': 'load', 'home_site': c.site, 'distance_m': d})
    ues = pd.DataFrame(rows)
    ues['z_m'] = 1.5
    ues['extra_loss_db'] = k0 + k1*np.log10(np.clip(ues.distance_m, 100, 15000))
    # common interval of the earthquake users: evaluation-cell PRB = TARGET_PRB without outage (fast model, f)
    net = m.Model35(sec, ues, 42, 'RMa')
    n = len(ues)
    pk = np.full(n, 512.0)
    load_iv = LOAD_FACTOR/TARGET_PRB
    is_q = (ues.kind == 'quake').to_numpy()
    evc = (sec.role == 'Evaluation').to_numpy()
    lo, hi = 1.0, 2000.0
    for _ in range(16):
        mid = np.sqrt(lo*hi)
        iv = np.where(is_q, mid, load_iv)
        prb = solve_f(net, pk, iv, np.ones(len(sec), bool), F_ON)['load'][evc].mean()
        lo, hi = (mid, hi) if prb > TARGET_PRB else (lo, mid)
    q_iv = float(np.sqrt(lo*hi))
    ues['udp_interval_ms'] = np.where(is_q, q_iv, load_iv)
    out = pd.DataFrame({'ue_id': np.arange(n), 'x_m': ues.x_m.map(lambda v: f'{v:.9f}'), 'y_m': ues.y_m.map(lambda v: f'{v:.9f}'),
                        'z_m': '1.500000000', 'kind': ues.kind, 'home_site': ues.home_site, 'distance_m': ues.distance_m.round(1),
                        'extra_loss_db': ues.extra_loss_db.map(lambda v: f'{v:.6f}'), 'dl_earfcn': 1651, 'packet_size_bytes': 512,
                        'udp_interval_ms': ues.udp_interval_ms.map(lambda v: f'{v:.6f}')})
    out.to_csv(HERE/'inputs/ues_quake.csv', index=False, lineterminator='\n')
    for k, off in SCEN.items():
        sites[~sites.site.isin(off)][['site', 'role', 'x_m', 'y_m', 'rotation_deg', 'sector_count', 'carriers']].to_csv(
            HERE/f'inputs/sites_{k}.csv', index=False, lineterminator='\n', float_format='%.9f')
    # preview with the fast model (users as written)
    back = pd.read_csv(HERE/'inputs/ues_quake.csv')
    prev = {}
    for seed in [42, 7, 99]:
        sec_s, _ = m.sectors_of(sites, seed)
        net_s = m.Model35(sec_s, back, seed, 'RMa')
        for k, off in SCEN.items():
            on = ~sec_s.site.isin(off).to_numpy()
            r = solve_f(net_s, pk, back.udp_interval_ms.to_numpy(float), on, F_ON)
            q = (back.kind == 'quake').to_numpy()
            around = q & back.home_site.isin(off).to_numpy()
            nos = r['cqi'] == 0
            prev.setdefault(k, []).append({'seed': seed, 'no_service_all': float(nos[q].mean()),
                                           'no_service_around': float(nos[around].mean()) if around.any() else None,
                                           'weak_around': float((r['rsrp'] < -121.8)[around].mean()) if around.any() else None,
                                           'eval_prb': float(r['load'][evc & on].mean()), 'full_cells': int((r['demand'][on] >= 0.95).sum())})
    for k, v in prev.items():
        print(k, pd.DataFrame(v).drop(columns='seed').mean().round(3).to_dict())
    (HERE/'onizleme.json').write_text(json.dumps(prev, indent=1), encoding='utf-8')
    plan = {'quake_interval_ms': q_iv, 'load_interval_ms': load_iv, 'users': int(is_q.sum()), 'load_users': int((~is_q).sum()),
            'users_by_site': ues[is_q].home_site.value_counts().to_dict(), 'k0_k1': [k0, k1], 'f_on': F_ON,
            'scenarios': {k: {'off': v, 'sites_file': f'sites_{k}.csv'} for k, v in SCEN.items()},
            'input_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'inputs').glob('*.csv'))}}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding='utf-8')
    print('users', plan['users'], 'load users', plan['load_users'], 'interval ms', round(q_iv, 2))


if __name__ == '__main__':
    main()
