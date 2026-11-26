"""Windows: ns-3 inputs of experiment 42 (KURALLAR.md) from experiment 40's main model, 15:30, draw 42.

Users: experiment 40's placement reproduced exactly (100 per core site, checked against users_ana_model.csv.gz),
then the first 32 of each site kept. They carry the load: per serving cell one common packet interval, tuned with
the fast model so that every cell's PRB use equals its site's KPI 15:30 PRB. Cells that serve no user get one load
user on the antenna direction, at the first point (100 m, then 50 m steps) where that cell is the best cell.
Outputs: inputs/sites_42.csv, inputs/ues_42.csv, inputs/fast_42.csv (fast-model values per user), plan42.json.
"""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
D40 = DEN/'40_sehir_modeli_2026-11-24'
sys.path.insert(0, str(D40))
sys.path.insert(0, str(DEN/'36_hep_yayinda_payi_ns3_2026-11-22'))
import model40 as m40  # noqa: E402
from sindirgi_f import sinr_f  # noqa: E402
hm = m40.hm

SEED, HOUR, N_KEEP = 42, 'en_kalabalik', 32
PK, F_ON, EARFCN = 512.0, 0.048, 1651
IV_MIN, IV_MAX = 1.0, 5000.0   # below 1 ms per packet the packet grows instead (one subframe)
IDLE_IV = 1000.0               # users that cannot be served (CQI 0): one packet per second


def placement():
    """experiment 40 run_one up to the user positions (same random streams)."""
    sites = m40.site_env(pd.read_csv(D40/'inputs/sites.csv'))
    e = pd.read_csv(D40/'experia_40.csv.gz', parse_dates=['DATE_ID'])
    e['weekday'] = e.DATE_ID.dt.weekday
    cfg = dict(m40.MAIN)
    _, ehour = m40.HOURS[HOUR]
    _, x = m40.experia_hour(e, ehour)
    core = sites[sites.role == 'core']
    rng = np.random.default_rng(SEED*100 + ehour)
    ues = m40.place(dict(zip(core.site, zip(core.x_m, core.y_m))), x, rng)
    ue_env = ues.placement_site.map(sites.set_index('site').env).to_numpy()
    loss, is_in = m40.user_loss(ue_env, cfg, np.random.default_rng(SEED*100 + ehour + 7))
    hm.TILT = cfg['tilt']
    hm.H_BS, hm.H_UT = m40.H_BS, m40.H_UT
    sec = m40.sectors(sites, SEED)
    usig = m40.SIGMA['UMa_36873']
    ues, matched = m40.best_server_dirs(ues, sites, sec, SEED, ue_env, rng, usig)
    ues['extra_loss_db'], ues['indoor'], ues['env'], ues['matched'] = loss, is_in, ue_env, matched
    return sites, sec, ues, usig


def load_points(sites, sec, served, usig):
    """One load user per cell without users: antenna direction, first distance where the cell is best."""
    env_of = sites.set_index('site').env
    rows = []
    for c in np.flatnonzero(~served):
        s = sec.iloc[c]
        a = np.deg2rad(s.orientation_ccw_from_east_deg)
        d = np.arange(100.0, 3001.0, 50.0)
        cand = pd.DataFrame({'x_m': s.x_m + d*np.cos(a), 'y_m': s.y_m + d*np.sin(a), 'z_m': m40.H_UT, 'extra_loss_db': 0.0})
        env = np.full(len(cand), env_of[s.site])
        best = m40.Model40(sec, cand, SEED, env, usig).rsrp_all().argmax(1)
        ok = np.flatnonzero(best == c)
        if len(ok) == 0:
            raise RuntimeError(f'no load point for cell {c} ({s.site})')
        k = ok[0]
        rows.append({'x_m': cand.x_m[k], 'y_m': cand.y_m[k], 'z_m': m40.H_UT, 'extra_loss_db': 0.0, 'env': env_of[s.site],
                     'placement_site': s.site, 'placement_distance_m': d[k], 'indoor': False, 'matched': True, 'kind': 'load'})
    return pd.DataFrame(rows)


def cell_load(r, srv, iv, pk, n_cells, iters=80):
    """Fast-model PRB use per cell for packet interval iv and size pk per user (experiment 37 solve_f, always-on share)."""
    pps = 1000.0/iv
    load = np.full(n_cells, 0.5)
    for _ in range(iters):
        _, sched = sinr_f(r, srv, load, F_ON)
        mcs, cqi = hm.mcs_from_sinr_db(sched)
        rb = hm.rb_per_packet(mcs, cqi, pk)
        new = np.minimum(np.bincount(srv, weights=np.nan_to_num(rb)*pps, minlength=n_cells)/(hm.N_RB*1000.0), 1.0)
        if np.max(abs(new - load)) < 1e-5:
            return new
        load = 0.5*load + 0.5*new
    return load


def main():
    (HERE/'inputs').mkdir(exist_ok=True)
    sites, sec, ues, usig = placement()
    # reproduction check against experiment 40's saved users (same draw and hour)
    saved = pd.read_csv(D40/'users_ana_model.csv.gz')
    saved = saved[(saved.hour == HOUR) & (saved.seed == SEED)].reset_index(drop=True)
    r100 = m40.Model40(sec, ues, SEED, ues.env.to_numpy(), usig).rsrp_all()
    rs100 = r100[np.arange(len(r100)), r100.argmax(1)]
    repro = float(np.max(np.abs(rs100.round(2) - saved.rsrp.to_numpy())))
    print('reproduction max |RSRP diff| dB', repro)
    if repro > 0.011:
        raise RuntimeError('experiment 40 placement not reproduced')
    keep = ues[ues.groupby('placement_site').cumcount() < N_KEEP].copy()
    keep['kind'] = 'probe'
    r = m40.Model40(sec, keep, SEED, keep.env.to_numpy(), usig).rsrp_all()
    srv0 = r.argmax(1)
    # a cell needs at least one user that can be scheduled (fast-model CQI > 0 at the target loads)
    prb0 = pd.read_csv(D40/'inputs/site_prb.csv').set_index('site')[HOUR]
    _, sched0 = sinr_f(r, srv0, sec.site.map(prb0).to_numpy(float), F_ON)
    ok0 = hm.mcs_from_sinr_db(sched0)[1] > 0
    served = np.bincount(srv0, weights=ok0.astype(float), minlength=len(sec)) > 0
    allu = pd.concat([keep, load_points(sites, sec, served, usig)], ignore_index=True)
    net = m40.Model40(sec, allu, SEED, allu.env.to_numpy(), usig)
    r = net.rsrp_all()
    srv = r.argmax(1)
    n_cells = len(sec)
    if np.any(np.bincount(srv, minlength=n_cells) == 0):
        raise RuntimeError('a cell still has no user')
    prb = pd.read_csv(D40/'inputs/site_prb.csv').set_index('site')[HOUR]
    target = sec.site.map(prb).to_numpy(float)
    # one common packet rate per serving cell (PRB use ~ rate), fixed point on the coupled network.
    # rate = packets of 512 B per ms; above 1 per ms the interval stays 1 ms and the packet grows.
    # Users that cannot be served (CQI 0) get one packet per second and are left out of the tuning.
    _, sched = sinr_f(r, srv, target, F_ON)
    idle = hm.mcs_from_sinr_db(sched)[1] == 0
    rate = np.full(n_cells, 0.01)

    def traffic(rate):
        u = rate[srv]
        iv = np.where(idle, IDLE_IV, np.clip(1.0/u, IV_MIN, IV_MAX))
        pk = np.where(idle, PK, PK*np.maximum(u*IV_MIN, 1.0))
        return iv, np.round(pk)
    for it in range(120):
        iv, pk = traffic(rate)
        load = cell_load(r, srv, iv, pk, n_cells)
        err = np.max(np.abs(load - target))
        if err < 0.002:
            break
        rate = np.clip(rate*np.where(load > 0, target/np.maximum(load, 1e-6), 2.0)**0.5, 1.0/IV_MAX, 50.0)   # damped
    print('iterations', it + 1, 'max |PRB - target|', round(float(err), 4))
    iv_cell = 1.0/rate
    rep, _ = sinr_f(r, srv, load, F_ON)
    rs = r[np.arange(len(r)), srv]
    # files
    rot = dict(zip(sorted(sites.site), np.random.default_rng(SEED).uniform(0, 120, len(sites))))
    st = pd.DataFrame({'site': sites.site, 'role': sites.role, 'x_m': sites.x_m, 'y_m': sites.y_m,
                       'rotation_deg': sites.site.map(rot), 'sector_count': 3, 'carriers': 'B3'})
    st.to_csv(HERE/'inputs/sites_42.csv', index=False, lineterminator='\n', float_format='%.9f')
    out = pd.DataFrame({'ue_id': np.arange(len(allu)), 'x_m': allu.x_m.map(lambda v: f'{v:.9f}'),
                        'y_m': allu.y_m.map(lambda v: f'{v:.9f}'), 'z_m': '1.500000000', 'kind': allu.kind,
                        'home_site': allu.placement_site, 'env': allu.env,
                        'extra_loss_db': allu.extra_loss_db.map(lambda v: f'{v:.6f}'), 'dl_earfcn': EARFCN,
                        'packet_size_bytes': pk.astype(int), 'udp_interval_ms': [f'{v:.6f}' for v in iv]})
    out.to_csv(HERE/'inputs/ues_42.csv', index=False, lineterminator='\n')
    fast = pd.DataFrame({'ue_id': np.arange(len(allu)), 'kind': allu.kind, 'home_site': allu.placement_site, 'env': allu.env,
                         'indoor': allu.indoor, 'matched': allu.matched, 'distance_m': allu.placement_distance_m.round(1),
                         'serving_site': sec.site.to_numpy()[srv], 'serving_sector': sec.sector.to_numpy()[srv],
                         'rsrp_dbm': rs.round(3), 'sinr_db': rep.round(3)})
    fast.to_csv(HERE/'inputs/fast_42.csv', index=False, lineterminator='\n')
    cells = pd.DataFrame({'site': sec.site, 'sector': sec.sector, 'target_prb': target, 'fast_prb': load,
                          'users': np.bincount(srv, minlength=n_cells), 'idle_users': np.bincount(srv, weights=idle.astype(float), minlength=n_cells),
                          'rate_per_ms': rate})
    cells.to_csv(HERE/'inputs/cells_42.csv', index=False, lineterminator='\n', float_format='%.6f')
    plan = {'seed': SEED, 'hour': HOUR, 'probe_users': int((allu.kind == 'probe').sum()),
            'load_users': int((allu.kind == 'load').sum()), 'cells': n_cells,
            'reproduction_max_rsrp_diff_db': repro, 'max_prb_error': float(err),
            'idle_users_cqi0': int(idle.sum()), 'users_with_grown_packets': int((pk > PK).sum()),
            'max_packet_bytes': int(pk.max()), 'interval_ms_min_median': [float(iv[~idle].min()), float(np.median(iv[~idle]))],
            'mean_target_prb': float(target.mean()), 'mean_fast_prb': float(load.mean()),
            'fast_median_rsrp_dbm': float(np.median(rs[allu.kind == 'probe'])),
            'fast_median_sinr_db': float(np.median(rep[allu.kind == 'probe'])),
            'packets_per_second_total': float((1000.0/iv).sum()),
            'input_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'inputs').glob('*.csv'))}}
    (HERE/'plan42.json').write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in plan.items() if k != 'input_hashes'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
