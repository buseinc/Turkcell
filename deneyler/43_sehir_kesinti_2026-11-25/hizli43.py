"""Windows, fast model: city outages C0-C3 at the three model hours, 10 antenna draws (KURALLAR.md).
Model = experiment 40/42 main model. Users: real count (site mean KPI users per cell x 3) at Experia TA distances,
best-server directions; per-cell packet interval tuned so that C0 cell PRB = KPI PRB (experiment 42 method).
Outage: the same users and intervals, closed cells removed. Resumable per (hour, draw): hizli43.json.
Usage: python hizli43.py [hour_key draw]   (one pair only: timing check)"""
from pathlib import Path
import json
import sys
import time

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
D40, D42 = DEN/'40_sehir_modeli_2026-11-24', DEN/'42_sehir_modeli_ns3_2026-11-25'
sys.path.insert(0, str(D42))
import hazirla42 as h42  # noqa: E402
m40, hm, sinr_f = h42.m40, h42.hm, h42.sinr_f

DRAWS = m40.DRAWS
HOURS = m40.HOURS
CASES = {'C0': [], 'C1': [('SITE_000195', None)], 'C2': [('SITE_000087', None), ('SITE_000108', None)],
         'C3_0': [('SITE_000116', 0)], 'C3_1': [('SITE_000116', 1)], 'C3_2': [('SITE_000116', 2)]}   # (site, kept sector)
NO_SERVICE_DB, WEAK_DBM, FULL = -6.7, -121.8, 0.95
OUT = HERE/'hizli43.json'


def site_users(sites):
    """Per site and hour: mean KPI users per real cell x 3 (sites without KPI: mean of the others)."""
    cs = pd.read_excel(DEN.parent/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('cell').set_index('cell').site
    y = pd.concat([pd.read_csv(DEN/f'39_trafik_trendleri_2026-11-24/yuk_saatleri_sehir_{n}.csv.gz') for n in ['balikesir', 'bandirma']])
    y['site'], y['hour'] = y.CELL.map(cs), y.hour.str.split().str[0]
    p = y.groupby(['hour', 'site'])['Avg_Sim_RRC_Connected_User_Num_ERI'].mean().unstack(0).reindex(sites.site)
    return (3*p.fillna(p.mean())).round().astype(int)


def place(core, x, rng, counts):
    rows = []
    for _, s in core.iterrows():
        pool = (x.loc[x.site == s.site, 'AVG(TAAVG)'].dropna()*m40.TS_M).clip(m40.DMIN, m40.DMAX).to_numpy()
        n = int(counts[s.site])
        if len(pool) == 0 or n == 0:
            continue
        d = pool[rng.integers(len(pool), size=n)]
        a = rng.uniform(0, 2*np.pi, n)
        rows.append(pd.DataFrame({'x_m': s.x_m + d*np.cos(a), 'y_m': s.y_m + d*np.sin(a), 'z_m': m40.H_UT,
                                  'placement_site': s.site, 'placement_distance_m': d}))
    return pd.concat(rows, ignore_index=True)


def closed_cells(sec, case):
    off = np.zeros(len(sec), bool)
    for site, kept in CASES[case]:
        off |= (sec.site == site).to_numpy() & ((sec.sector != kept).to_numpy() if kept is not None else True)
    return off


def state(r_all, iv, pk, off, idle):
    """Serving cell, cell PRB, demand, reported SINR, CQI and served share per user with cells `off` removed."""
    r = np.where(off[None, :], -np.inf, r_all)
    srv = r.argmax(1)
    n = r.shape[1]
    load = h42.cell_load(r, srv, iv, pk, n)
    rep, sched = sinr_f(r, srv, load, h42.F_ON)
    mcs, cqi = hm.mcs_from_sinr_db(sched)
    rb = hm.rb_per_packet(mcs, cqi, pk)
    demand = np.bincount(srv, weights=np.nan_to_num(rb)*1000.0/iv, minlength=n)/(hm.N_RB*1000.0)
    share = np.where(cqi > 0, np.minimum(1.0, 1.0/np.maximum(demand[srv], 1e-9)), 0.0)   # share of offered data received
    return {'srv': srv, 'load': load, 'demand': demand, 'sinr': rep, 'cqi': cqi,
            'rsrp': r[np.arange(len(r)), srv], 'share': share, 'offered': pk*8*1000.0/iv*(~idle)}


def one(sites, prb, users_n, e, hour_key, seed):
    _, ehour = HOURS[hour_key]
    _, x = m40.experia_hour(e, ehour)
    core = sites[sites.role == 'core']
    rng = np.random.default_rng(seed*100 + ehour + 43)
    ues = place(core, x, rng, users_n[hour_key])
    ue_env = ues.placement_site.map(sites.set_index('site').env).to_numpy()
    loss, is_in = m40.user_loss(ue_env, dict(m40.MAIN), np.random.default_rng(seed*100 + ehour + 50))
    hm.TILT, hm.H_BS, hm.H_UT = m40.MAIN['tilt'], m40.H_BS, m40.H_UT
    sec = m40.sectors(sites, seed)
    usig = m40.SIGMA['UMa_36873']
    ues, matched = m40.best_server_dirs(ues, sites, sec, seed, ue_env, rng, usig)
    ues['extra_loss_db'], ues['env'], ues['indoor'], ues['matched'], ues['kind'] = loss, ue_env, is_in, matched, 'user'
    # load users for cells without a user that can be served (experiment 42 rule)
    r = m40.Model40(sec, ues, seed, ue_env, usig).rsrp_all()
    srv0 = r.argmax(1)
    target = sec.site.map(prb[hour_key]).to_numpy(float)
    _, s0 = sinr_f(r, srv0, target, h42.F_ON)
    ok0 = hm.mcs_from_sinr_db(s0)[1] > 0
    served = np.bincount(srv0, weights=ok0.astype(float), minlength=len(sec)) > 0
    h42.SEED = seed
    allu = pd.concat([ues, h42.load_points(sites, sec, served, usig)], ignore_index=True)
    r_all = m40.Model40(sec, allu, seed, allu.env.to_numpy(), usig).rsrp_all()
    srv = r_all.argmax(1)
    n_cells = len(sec)
    _, sched = sinr_f(r_all, srv, target, h42.F_ON)
    idle = hm.mcs_from_sinr_db(sched)[1] == 0
    rate = np.full(n_cells, 0.01)

    def traffic(rate):
        u = rate[srv]
        iv = np.where(idle, h42.IDLE_IV, np.clip(1.0/u, h42.IV_MIN, h42.IV_MAX))
        return iv, np.round(np.where(idle, h42.PK, h42.PK*np.maximum(u*h42.IV_MIN, 1.0)))
    for it in range(120):
        iv, pk = traffic(rate)
        load = h42.cell_load(r_all, srv, iv, pk, n_cells)
        err = float(np.max(np.abs(load - target)))
        if err < 0.002:
            break
        rate = np.clip(rate*np.where(load > 0, target/np.maximum(load, 1e-6), 2.0)**0.5, 1.0/h42.IV_MAX, 50.0)
    is_user = (allu.kind == 'user').to_numpy()
    base = state(r_all, iv, pk, np.zeros(n_cells, bool), idle)
    out = {'hour': hour_key, 'seed': seed, 'users': int(is_user.sum()), 'load_users': int((~is_user).sum()),
           'idle_users': int((idle & is_user).sum()), 'tuning_max_prb_error': err, 'cases': {}}
    for case in CASES:
        off = closed_cells(sec, case)
        st = base if case == 'C0' else state(r_all, iv, pk, off, idle)
        aff = is_user & off[base['srv']] if off.any() else np.zeros(len(allu), bool)
        took = np.unique(st['srv'][aff]) if aff.any() else np.array([], int)
        old_users = is_user & np.isin(base['srv'], took) & ~aff
        ns, weak = st['cqi'] == 0, st['rsrp'] < WEAK_DBM
        rec = {'closed_cells': int(off.sum()), 'affected_users': int(aff.sum()),
               'no_service_all': float(ns[is_user].mean()), 'weak_all': float(weak[is_user].mean()),
               'full_cells': int(((st['demand'] >= FULL) & ~off).sum()), 'mean_prb_open': float(st['load'][~off].mean())}
        if aff.any():
            rec.update({'no_service_affected': float(ns[aff].mean()), 'weak_affected': float(weak[aff].mean()),
                        'no_service_affected_before': float((base['cqi'] == 0)[aff].mean()),
                        'taking_cells': int(len(took)),
                        'taking_prb_before': float(base['load'][took].mean()), 'taking_prb_after': float(st['load'][took].mean()),
                        'taking_demand_after_max': float(st['demand'][took].max()),
                        'data_affected_after_over_before': float((st['offered']*st['share'])[aff].sum()/max((base['offered']*base['share'])[aff].sum(), 1e-9)),
                        'data_old_users_after_over_before': float((st['offered']*st['share'])[old_users].sum()/max((base['offered']*base['share'])[old_users].sum(), 1e-9))
                        if old_users.any() else None,
                        'affected_by_env': {k: int(v) for k, v in pd.Series(allu.env[aff]).value_counts().items()}})
        out['cases'][case] = rec
    return out


def main():
    sites = m40.site_env(pd.read_csv(D40/'inputs/sites.csv'))
    prb = pd.read_csv(D40/'inputs/site_prb.csv').set_index('site')
    users_n = site_users(sites)
    e = pd.read_csv(D40/'experia_40.csv.gz', parse_dates=['DATE_ID'])
    e['weekday'] = e.DATE_ID.dt.weekday
    pairs = [(sys.argv[1], int(sys.argv[2]))] if len(sys.argv) > 2 else [(h, s) for h in HOURS for s in DRAWS]
    res = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    for h, s in pairs:
        key = f'{h}_{s}'
        if key in res:
            continue
        t0 = time.time()
        r = one(sites, prb, users_n, e, h, s)
        r['seconds'] = round(time.time() - t0, 1)
        res[key] = r
        OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float), encoding='utf-8')
        print(key, r['seconds'], 's', {c: {k: round(v, 3) for k, v in d.items() if isinstance(v, float)} for c, d in r['cases'].items()}, flush=True)


if __name__ == '__main__':
    main()
