"""Windows: summer (10 Aug) load check of the Edremit outages, fast model only (KURALLAR.md, Yaz yükü).
Does not touch the October inputs. Writes yaz_yuku.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hazirla as h  # noqa: E402

WINDOW = ('2025-08-10 19:45', '2025-08-10 21:30')
TARGET = 0.39
SEEDS = [42, 7, 99]


def build():
    sites, sec = h.sites48()
    seg = h.kiyi.segments()
    k0, k1 = json.loads((h.D35/'adim3_48.json').read_text(encoding='utf-8'))['models']['RMa']['k0_k1']
    kpi = pd.read_csv(h.D35/'kpi_cells.csv.gz', parse_dates=['DATETIME'])
    w = kpi[(kpi.DATETIME >= WINDOW[0]) & (kpi.DATETIME < WINDOW[1])]
    users_cell = w.groupby(['site', 'DATETIME'])[h.U].mean().groupby('site').mean()
    e = pd.read_csv(h.D35/'experia_cells.csv.gz').dropna(subset=['AVG(TAAVG)'])
    ta = pd.DataFrame({'site': e.site, 'd': (e['AVG(TAAVG)']*4.88).clip(100, 15000)})
    ev = sites.site[sites.role == 'Evaluation'].tolist()
    rng = np.random.default_rng(37810)
    rows = []
    for _, s in sites[sites.role != 'Extra buffer'].iterrows():
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
                if h.kiyi.on_land([x], [y], seg)[0]:
                    rows.append({'x_m': x, 'y_m': y, 'kind': 'quake', 'home_site': s.site, 'distance_m': d}); k += 1
                    break
    for _, c in sec[sec.role == 'Extra buffer'].iterrows():
        x, y, d = h.land_point(c.x_m, c.y_m, c.orientation_ccw_from_east_deg, seg)
        rows.append({'x_m': x, 'y_m': y, 'kind': 'load', 'home_site': c.site, 'distance_m': d})
    ues = pd.DataFrame(rows)
    ues['z_m'] = 1.5
    ues['extra_loss_db'] = k0 + k1*np.log10(np.clip(ues.distance_m, 100, 15000))
    return sites, sec, ues, float(users_cell.reindex(ev).mean())


def main():
    sites, sec, ues, ev_users = build()
    n = len(ues)
    pk = np.full(n, 512.0)
    q = (ues.kind == 'quake').to_numpy()
    load_iv = h.LOAD_FACTOR/TARGET
    evc = (sec.role == 'Evaluation').to_numpy()
    net = h.m.Model35(sec, ues, 42, 'RMa')
    lo, hi = 1.0, 2000.0
    for i in range(16):
        mid = np.sqrt(lo*hi)
        prb = h.solve_f(net, pk, np.where(q, mid, load_iv), np.ones(len(sec), bool), h.F_ON)['load'][evc].mean()
        lo, hi = (mid, hi) if prb > TARGET else (lo, mid)
        print('calibration', i, round(mid, 3), round(float(prb), 4), flush=True)
    q_iv = float(np.sqrt(lo*hi))
    iv = np.where(q, q_iv, load_iv)
    rows = []
    for seed in SEEDS:
        sec_s, _ = h.m.sectors_of(sites, seed)
        net_s = h.m.Model35(sec_s, ues, seed, 'RMa')
        core = (sec_s.role != 'Extra buffer').to_numpy()
        ev_s = (sec_s.role == 'Evaluation').to_numpy()
        base_full = None
        for k, off in h.SCEN.items():
            on = ~sec_s.site.isin(off).to_numpy()
            r = h.solve_f(net_s, pk, iv, on, h.F_ON)
            full = on & (r['demand'] >= 0.95)
            if k == 'E0':
                base_full = full.copy()
            around = q & ues.home_site.isin(off).to_numpy()
            nos = r['cqi'] == 0
            rows.append({'scenario': k, 'seed': seed, 'no_service_all': float(nos[q].mean()),
                         'no_service_around': float(nos[around].mean()) if around.any() else None,
                         'users_around': int(around.sum()),
                         'eval_prb': float(r['load'][ev_s & on].mean()), 'max_core_demand': float(r['demand'][core & on].max()),
                         'full_core': int((full & core).sum()), 'full_extra': int((full & ~core).sum()),
                         'new_full_core': int((full & core & ~base_full).sum()),
                         'users_in_full_core': float(np.mean((full & core)[r['serving'][q]]))})
            print(rows[-1], flush=True)
    d = pd.DataFrame(rows)
    mean = d.drop(columns='seed').groupby('scenario').mean(numeric_only=True).round(4)
    oct_prev = json.loads((HERE/'onizleme.json').read_text(encoding='utf-8-sig'))
    oct_around = {k: float(np.mean([x['no_service_around'] for x in v])) for k, v in oct_prev.items() if v[0]['no_service_around'] is not None}
    # 529 has no KPI rows in August, so E1 has no users around the removed site and cannot be scored
    rise = {k: 100*(float(mean.loc[k, 'no_service_around']) - oct_around[k]) for k in oct_around
            if mean.loc[k, 'users_around'] > 0}
    mean = mean.astype(object).where(mean.notna(), None)
    new_full = int(d.new_full_core.max())
    out = {'window': WINDOW, 'target_prb': TARGET, 'quake_users': int(q.sum()), 'load_users': int((~q).sum()),
           'evaluation_users_per_cell_kpi': ev_users, 'quake_interval_ms': q_iv, 'load_interval_ms': load_iv, 'runs': rows,
           'mean': mean.to_dict('index'), 'october_around': oct_around, 'rise_around_pp': rise,
           'max_new_full_core_cells': new_full, 'recommend_ns3': bool(new_full > 0 or max(rise.values()) > 5.0)}
    (HERE/'yaz_yuku.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(mean.to_string())
    print('users', out['quake_users'], 'interval', round(q_iv, 2), 'rise pp', rise, 'new full', new_full, 'recommend ns-3', out['recommend_ns3'])


if __name__ == '__main__':
    main()
