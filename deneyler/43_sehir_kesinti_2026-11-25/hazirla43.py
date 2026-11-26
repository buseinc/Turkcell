"""Windows: ns-3 inputs of experiment 43 (KURALLAR.md) for 15:30, draw 42: C0 (no outage) and C2 (087 + 108 removed).
Same users, load users and packet intervals as hizli43.py (same random streams). The tuning is run until it converges
(max 400 steps) and the cells that miss their KPI PRB are listed. Outage = the closed sites are left out of the site file
(shadow/LOS fields are keyed by site position, so the other links do not change).
Outputs: inputs/sites_C0.csv, inputs/sites_C2.csv, inputs/ues_43.csv, inputs/fast_43.csv, inputs/cells_43.csv, plan43.json.
Usage: python hazirla43.py [max_steps]"""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hizli43 as h  # noqa: E402
h42, m40, hm, sinr_f = h.h42, h.m40, h.hm, h.sinr_f

SEED, HOUR = 42, 'en_kalabalik'
NS3_CASES = {'C0': [], 'C2': ['SITE_000087', 'SITE_000108']}


def main(max_steps=400):
    (HERE/'inputs').mkdir(exist_ok=True)
    sites = m40.site_env(pd.read_csv(h.D40/'inputs/sites.csv'))
    prb = pd.read_csv(h.D40/'inputs/site_prb.csv').set_index('site')
    users_n = h.site_users(sites)
    e = pd.read_csv(h.D40/'experia_40.csv.gz', parse_dates=['DATE_ID'])
    e['weekday'] = e.DATE_ID.dt.weekday
    # --- same steps as hizli43.one up to the tuning
    _, ehour = h.HOURS[HOUR]
    _, x = m40.experia_hour(e, ehour)
    core = sites[sites.role == 'core']
    rng = np.random.default_rng(SEED*100 + ehour + 43)
    ues = h.place(core, x, rng, users_n[HOUR])
    ue_env = ues.placement_site.map(sites.set_index('site').env).to_numpy()
    loss, is_in = m40.user_loss(ue_env, dict(m40.MAIN), np.random.default_rng(SEED*100 + ehour + 50))
    hm.TILT, hm.H_BS, hm.H_UT = m40.MAIN['tilt'], m40.H_BS, m40.H_UT
    sec = m40.sectors(sites, SEED)
    usig = m40.SIGMA['UMa_36873']
    ues, matched = m40.best_server_dirs(ues, sites, sec, SEED, ue_env, rng, usig)
    ues['extra_loss_db'], ues['env'], ues['indoor'], ues['matched'], ues['kind'] = loss, ue_env, is_in, matched, 'user'
    r = m40.Model40(sec, ues, SEED, ue_env, usig).rsrp_all()
    srv0 = r.argmax(1)
    target = sec.site.map(prb[HOUR]).to_numpy(float)
    _, s0 = sinr_f(r, srv0, target, h42.F_ON)
    ok0 = hm.mcs_from_sinr_db(s0)[1] > 0
    served = np.bincount(srv0, weights=ok0.astype(float), minlength=len(sec)) > 0
    h42.SEED = SEED
    allu = pd.concat([ues, h42.load_points(sites, sec, served, usig)], ignore_index=True)
    r_all = m40.Model40(sec, allu, SEED, allu.env.to_numpy(), usig).rsrp_all()
    srv = r_all.argmax(1)
    n_cells = len(sec)
    _, sched = sinr_f(r_all, srv, target, h42.F_ON)
    idle = hm.mcs_from_sinr_db(sched)[1] == 0
    rate = np.full(n_cells, 0.01)

    def traffic(rate):
        u = rate[srv]
        iv = np.where(idle, h42.IDLE_IV, np.clip(1.0/u, h42.IV_MIN, h42.IV_MAX))
        return iv, np.round(np.where(idle, h42.PK, h42.PK*np.maximum(u*h42.IV_MIN, 1.0)))
    hist = []
    for it in range(max_steps):
        iv, pk = traffic(rate)
        load = h42.cell_load(r_all, srv, iv, pk, n_cells)
        err = np.abs(load - target)
        hist.append(float(err.max()))
        if it in (119, max_steps - 1) or err.max() < 0.002:
            print('step', it + 1, 'max err', round(float(err.max()), 4), 'cells > 0.01:', int((err > 0.01).sum()), flush=True)
        if err.max() < 0.002:
            break
        rate = np.clip(rate*np.where(load > 0, target/np.maximum(load, 1e-6), 2.0)**0.5, 1.0/h42.IV_MAX, 50.0)
    users_c = np.bincount(srv, minlength=n_cells)
    idle_c = np.bincount(srv, weights=idle.astype(float), minlength=n_cells)
    cells = pd.DataFrame({'site': sec.site, 'sector': sec.sector, 'role': sec.site.map(sites.set_index('site').role),
                          'target_prb': target, 'fast_prb': load, 'err': load - target, 'users': users_c,
                          'idle_users': idle_c, 'rate_per_ms': rate})
    cells.to_csv(HERE/'inputs/cells_43.csv', index=False, lineterminator='\n', float_format='%.6f')
    bad = cells[cells.err.abs() > 0.01].sort_values('err')
    print('cells missing target by > 0.01:\n', bad.round(3).to_string(), flush=True)
    # cells that take C2's users (fast model)
    off = sec.site.isin(NS3_CASES['C2']).to_numpy()
    aff = (allu.kind == 'user').to_numpy() & off[srv]
    r2 = np.where(off[None, :], -np.inf, r_all)
    took = np.unique(r2.argmax(1)[aff])
    print('C2 taking cells that miss target:', int(cells.iloc[took].err.abs().gt(0.01).sum()), 'of', len(took))
    # files
    rot = dict(zip(sorted(sites.site), np.random.default_rng(SEED).uniform(0, 120, len(sites))))
    for name, closed in NS3_CASES.items():
        s = sites[~sites.site.isin(closed)]
        st = pd.DataFrame({'site': s.site, 'role': s.role, 'x_m': s.x_m, 'y_m': s.y_m, 'rotation_deg': s.site.map(rot),
                           'sector_count': 3, 'carriers': 'B3'})
        st.to_csv(HERE/f'inputs/sites_{name}.csv', index=False, lineterminator='\n', float_format='%.9f')
    out = pd.DataFrame({'ue_id': np.arange(len(allu)), 'x_m': allu.x_m.map(lambda v: f'{v:.9f}'),
                        'y_m': allu.y_m.map(lambda v: f'{v:.9f}'), 'z_m': '1.500000000', 'kind': allu.kind,
                        'home_site': allu.placement_site, 'env': allu.env,
                        'extra_loss_db': allu.extra_loss_db.map(lambda v: f'{v:.6f}'), 'dl_earfcn': 1651,
                        'packet_size_bytes': pk.astype(int), 'udp_interval_ms': [f'{v:.6f}' for v in iv]})
    out.to_csv(HERE/'inputs/ues_43.csv', index=False, lineterminator='\n')
    rep, _ = sinr_f(r_all, srv, load, h42.F_ON)
    fast = pd.DataFrame({'ue_id': np.arange(len(allu)), 'kind': allu.kind, 'home_site': allu.placement_site, 'env': allu.env,
                         'serving_site': sec.site.to_numpy()[srv], 'serving_sector': sec.sector.to_numpy()[srv],
                         'rsrp_dbm': r_all[np.arange(len(r_all)), srv].round(3), 'sinr_db': rep.round(3),
                         'idle': idle, 'c2_affected': aff})
    fast.to_csv(HERE/'inputs/fast_43.csv', index=False, lineterminator='\n')
    plan = {'seed': SEED, 'hour': HOUR, 'users': int((allu.kind == 'user').sum()), 'load_users': int((allu.kind == 'load').sum()),
            'idle_users': int(idle.sum()), 'tuning_steps': len(hist), 'max_prb_error': hist[-1],
            'max_prb_error_at_120': hist[min(119, len(hist) - 1)], 'cells_err_gt_0_01': int(len(bad)),
            'mean_target_prb': float(target.mean()), 'mean_fast_prb': float(load.mean()),
            'c2_affected_users': int(aff.sum()), 'c2_taking_cells': int(len(took)),
            'packets_per_second_total': float((1000.0/iv).sum()), 'max_packet_bytes': int(pk.max()),
            'input_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'inputs').glob('*.csv'))}}
    (HERE/'plan43.json').write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in plan.items() if k != 'input_hashes'}, ensure_ascii=False))


if __name__ == '__main__':
    main(*[int(a) for a in sys.argv[1:]])
