"""Windows, fast model: Balıkesir city model against Experia, per model hour (KURALLAR.md).
Main model (TR 38.901 V19.5.0): per-site environment applied by the user's location to all the user's links
(mean distance to 3 nearest sites <= 931 m: city, else rural). City: UMa, shadow 7 dB, 80 % indoor with the
single-frequency < 6 GHz O2I model (20 dB + 0.5 x U(0,25) m, Table 7.4.3-3). Rural: RMa, shadow 4/8 dB, 50 % indoor
(low-loss model, d_in min(U,U) x 10 m, sigma 4.4) and 50 % in car (N(9,5) dB). 25 m / 1.5 m, always-on share 4.8 %,
no distance correction. Side variants change one thing each.
Usage: python model40.py [check]   -> model40.json (saved after every variant), users_<variant>.csv.gz"""
from pathlib import Path
import json
import sys
import time

import numpy as np
import pandas as pd
from scipy.special import erf

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
sys.path.insert(0, str(DEN/'34_yol_hareketi_2026-11-21'))
import alan  # noqa: E402
hm = alan.hm
sys.path.insert(0, str(DEN/'35_bolge_secimi_2026-11-21'))
import model35 as m35  # noqa: E402
import sinamalar as sn  # noqa: E402

DRAWS = [42, 7, 99]
HOURS = {'sabah_gidis': ('08:45', 9), 'en_kalabalik': ('15:30', 16), 'kapasite_zirvesi': ('21:15', 21)}
TS_M, DMIN, DMAX = 4.88, 100.0, 15000.0
H_BS, H_UT = 25.0, 1.5
PER_SITE, MIN_ROWS = 32, 3
N_DIR, CHUNK = 12, 6000
SHADOW_SPACING, LOS_SPACING = 50.0, 50.0
NO_SERVICE_DB = -6.7
MAIN = {'env': 'saha', 'loss_scale': 1.0, 'urban_o2i': '36873', 'f_on': 0.048, 'tilt': 6.0}
ENV_THR_M = (500.0*1732.0)**0.5
INDOOR = {'UMa': 0.8, 'RMa': 0.5}                  # Tables 7.2-1, 7.2-3 (rural: the rest in car)
VARIANTS = {'ana_model': {},
            'tek_ortam_sehir': {'env': 'UMa'},
            'tek_ortam_kirsal': {'env': 'RMa'},
            'bina_ici_yok': {'loss_scale': 0.0},
            'yari_yeni_bina': {'urban_o2i': 'lowhigh'},
            'surekli_yayin_0': {'f_on': 0.0},
            'surekli_yayin_9_5': {'f_on': 0.095},
            'egim_10': {'tilt': 10.0}}
SIGMA = {'UMa_36873': (7.0, 7.0), 'UMa_lowhigh': (4.0, 6.0), 'RMa': (4.0, 8.0)}   # (LOS, NLOS) shadow std (Tables 7.4.3-3, 7.4.1-1)


def user_loss(ue_env, cfg, rng):
    """Per-user penetration loss (TR 38.901 7.4.3), same on every link of the user. Returns loss (dB), indoor flag."""
    n = len(ue_env)
    urb = ue_env == 'UMa'
    fg = hm.F_HZ/1e9
    l_glass, l_irr, l_conc = 2 + 0.2*fg, 25.4 + 0.11*fg, 5 + 4*fg
    tw_low = 5 - 10*np.log10(0.3*10**(-l_glass/10) + 0.7*10**(-l_conc/10))
    tw_high = 5 - 10*np.log10(0.7*10**(-l_irr/10) + 0.3*10**(-l_conc/10))
    u_in, u_low, u1, u2 = rng.random(n), rng.random(n), rng.random(n), rng.random(n)
    nz = rng.normal(0, 1, n)
    is_in = u_in < np.where(urb, INDOOR['UMa'], INDOOR['RMa'])*(cfg['loss_scale'] > 0)
    if cfg['urban_o2i'] == '36873':
        city = 20.0 + 0.5*25.0*u1
    else:
        low = u_low < 0.5
        city = np.where(low, tw_low + 4.4*nz, tw_high + 6.5*nz) + 0.5*25.0*np.minimum(u1, u2)
    rural_in = tw_low + 4.4*nz + 0.5*10.0*np.minimum(u1, u2)
    car = 9.0 + 5.0*nz
    loss = np.where(urb, np.where(is_in, city, 0.0),
                    np.where(is_in, rural_in, car*(cfg['loss_scale'] > 0)))
    return loss, is_in


class Model40(hm.Network):
    """ue_env: 'UMa' or 'RMa' per user (environment where the user is); the formula, LOS probability and
    shadow std of all the user's links follow it."""

    def __init__(self, sectors, ues, seed, ue_env, urban_sigma=SIGMA['UMa_36873']):
        super().__init__(sectors, ues, seed, 0.0)            # link shadow off; smooth field below (RMa loss from hm)
        enb = self.cells[['x_m', 'y_m', 'z_m']].to_numpy(float)
        ue = self.ues[['x_m', 'y_m', 'z_m']].to_numpy(float)
        ex, ey, ux, uy = enb[None, :, 0], enb[None, :, 1], ue[:, None, 0], ue[:, None, 1]
        urb = (np.asarray(ue_env) == 'UMa')[:, None]
        d3 = np.sqrt(self.d2**2 + (enb[None, :, 2] - ue[:, None, 2])**2)
        u_los, u_nlos = m35.uma_loss(self.d2, d3)
        u_p = np.where(self.d2 <= 18, 1.0, 18/self.d2 + np.exp(-self.d2/63)*(1 - 18/self.d2))
        self.los_db = np.where(urb, u_los, self.los_db)
        self.nlos_db = np.where(urb, u_nlos, self.nlos_db)
        self.p_los = np.where(urb, u_p, self.p_los)
        u = 0.5*(1 + erf(alan.field(seed, 2, ex, ey, ux, uy, LOS_SPACING)/np.sqrt(2)))
        self.los_fixed = u < self.p_los
        g = alan.field(seed, 1, ex, ey, ux, uy, SHADOW_SPACING)
        s_los = np.where(urb, urban_sigma[0], SIGMA['RMa'][0])
        s_nlos = np.where(urb, urban_sigma[1], SIGMA['RMa'][1])
        self.shadow = g*np.where(self.los_fixed, s_los, s_nlos)

    def rsrp_all(self):
        return self.fixed_db + self.shadow - np.where(self.los_fixed, self.los_db, self.nlos_db)


def sectors(sites, seed):
    rot = dict(zip(sorted(sites.site), np.random.default_rng(seed).uniform(0, 120, len(sites))))
    rows = [{'site': r.site, 'role': r.role, 'sector': k, 'x_m': r.x_m, 'y_m': r.y_m, 'z_m': H_BS,
             'orientation_ccw_from_east_deg': rot[r.site] + 120*k} for _, r in sites.iterrows() for k in range(3)]
    return pd.DataFrame(rows)


def experia_hour(e, hour):
    x = e[(e.weekday < 5) & (e.HOUR_ID == hour)]
    n = x.groupby('FIRSTCELL').size()
    x = x[x.FIRSTCELL.isin(n[n >= MIN_ROWS].index)]
    cell = x.groupby(['site', 'FIRSTCELL']).agg(rsrp=('AVG(MED_SERVINGRSRPMEDIAN)', 'mean'), sinr=('AVG(MED_SINRMEDIAN)', 'mean'))
    return cell.groupby('site').mean(), x


def place(core_xy, x, rng):
    rows = []
    for s, (sx, sy) in core_xy.items():
        pool = (x.loc[x.site == s, 'AVG(TAAVG)'].dropna()*TS_M).clip(DMIN, DMAX).to_numpy()
        if len(pool) == 0:
            continue
        d = pool[rng.integers(len(pool), size=PER_SITE)]
        a = rng.uniform(0, 2*np.pi, PER_SITE)
        rows.append(pd.DataFrame({'x_m': sx + d*np.cos(a), 'y_m': sy + d*np.sin(a), 'z_m': H_UT,
                                  'placement_site': s, 'placement_distance_m': d}))
    return pd.concat(rows, ignore_index=True)


def best_server_dirs(ues, sites, sec, seed, ue_env, rng, urban_sigma):
    """Keep each user's TA distance; pick the first of N_DIR random directions where the user's placement site
    is the best server in this model (KURALLAR.md). Returns the moved users and a matched flag."""
    n = len(ues)
    s = sites.set_index('site').loc[ues.placement_site]
    d = ues.placement_distance_m.to_numpy()[:, None]
    a = rng.uniform(0, 2*np.pi, (n, N_DIR))
    cx, cy = s.x_m.to_numpy()[:, None] + d*np.cos(a), s.y_m.to_numpy()[:, None] + d*np.sin(a)
    env = np.repeat(ue_env, N_DIR)
    flat = pd.DataFrame({'x_m': cx.ravel(), 'y_m': cy.ravel(), 'z_m': H_UT, 'extra_loss_db': 0.0})
    best = np.empty(len(flat), dtype=object)
    site_of = sec.site.to_numpy()
    for i in range(0, len(flat), CHUNK):
        net = Model40(sec, flat.iloc[i:i + CHUNK], seed, env[i:i + CHUNK], urban_sigma)
        best[i:i + CHUNK] = site_of[net.rsrp_all().argmax(1)]
    ok = best.reshape(n, N_DIR) == ues.placement_site.to_numpy()[:, None]
    pick = np.where(ok.any(1), ok.argmax(1), 0)
    out = ues.copy()
    out['x_m'], out['y_m'] = cx[np.arange(n), pick], cy[np.arange(n), pick]
    return out, ok.any(1)


def run_one(cfg, sites, prb, e, hour_key, seed):
    hhmm, ehour = HOURS[hour_key]
    targets, x = experia_hour(e, ehour)
    core = sites[sites.role == 'core']
    rng = np.random.default_rng(seed*100 + ehour)
    ues = place(dict(zip(core.site, zip(core.x_m, core.y_m))), x, rng)
    env_of = sites.set_index('site').env if cfg['env'] == 'saha' else pd.Series(cfg['env'], index=sites.site)
    ue_env = ues.placement_site.map(env_of).to_numpy()
    loss, is_in = user_loss(ue_env, cfg, np.random.default_rng(seed*100 + ehour + 7))
    usig = SIGMA['UMa_36873'] if cfg['urban_o2i'] == '36873' else SIGMA['UMa_lowhigh']
    hm.TILT = cfg['tilt']
    hm.H_BS, hm.H_UT = H_BS, H_UT
    sec = sectors(sites, seed)
    ues, matched = best_server_dirs(ues, sites, sec, seed, ue_env, rng, usig)
    ues['extra_loss_db'] = loss
    net = Model40(sec, ues, seed, ue_env, usig)
    r = net.rsrp_all()
    srv = r.argmax(1)
    load = sec.site.map(prb[hour_key]).to_numpy(float)
    sinr = sn.sinr_on(r, srv, load, cfg['f_on'])
    rs = r[np.arange(len(r)), srv]
    ms, mr = m35.site_mean(sec, srv, sinr), m35.site_mean(sec, srv, rs)
    ev = [s for s in core.site if s in targets.index and s in ms.index]
    d_s = pd.Series({s: ms[s] - targets.sinr[s] for s in ev})
    d_r = pd.Series({s: mr[s] - targets.rsrp[s] for s in ev})
    mm = matched
    ms2, mr2 = m35.site_mean(sec, srv[mm], sinr[mm]), m35.site_mean(sec, srv[mm], rs[mm])
    ev2 = [s for s in core.site if s in targets.index and s in ms2.index]
    m_s = pd.Series({s: ms2[s] - targets.sinr[s] for s in ev2})
    m_r = pd.Series({s: mr2[s] - targets.rsrp[s] for s in ev2})
    users = pd.DataFrame({'hour': hour_key, 'seed': seed, 'placement_site': ues.placement_site, 'env': ue_env, 'matched': matched,
                          'distance_m': ues.placement_distance_m, 'indoor': is_in, 'o2i_db': loss.round(2),
                          'rsrp': rs.round(2), 'sinr': sinr.round(2), 'serving_site': sec.site.to_numpy()[srv]})
    return {'hour': hour_key, 'seed': seed, 'sites_compared': len(ev), 'unmatched_share': float(1 - matched.mean()),
            'served_by_own_site_share': float((sec.site.to_numpy()[srv] == ues.placement_site.to_numpy()).mean()),
            'sinr_abs': float(d_s.abs().mean()), 'rsrp_abs': float(d_r.abs().mean()),
            'sinr_bias': float(d_s.mean()), 'rsrp_bias': float(d_r.mean()),
            'sinr_abs_matched_only': float(m_s.abs().mean()), 'rsrp_abs_matched_only': float(m_r.abs().mean()),
            'rsrp_bias_matched_only': float(m_r.mean()),
            'no_service_share': float((sinr < NO_SERVICE_DB).mean()),
            'model_sinr_median': float(np.median(sinr)), 'model_rsrp_median': float(np.median(rs)),
            'experia_sinr_median': float(targets.sinr.reindex(ev).median()),
            'experia_rsrp_median': float(targets.rsrp.reindex(ev).median()),
            'sinr_by_site': d_s.round(2).to_dict(), 'rsrp_by_site': d_r.round(2).to_dict()}, users


def site_env(sites):
    """City (UMa) if the mean distance to the 3 nearest sites of the whole inventory is <= 931 m, else rural (RMa)."""
    co = pd.read_excel(DEN.parent/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('site')
    xy = m35.secim.to_xy(co.lat.to_numpy(), co.lon.to_numpy(), 39.6395, 27.8916)
    d = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
    np.fill_diagonal(d, np.inf)
    nn3 = pd.Series(np.sort(d, 1)[:, :3].mean(1), index=co.site)
    sites = sites.copy()
    sites['nn3_m'] = sites.site.map(nn3)
    sites['env'] = np.where(sites.nn3_m <= ENV_THR_M, 'UMa', 'RMa')
    return sites


def main():
    check = len(sys.argv) > 1 and sys.argv[1] == 'check'
    sites = site_env(pd.read_csv(HERE/'inputs/sites.csv'))
    prb = pd.read_csv(HERE/'inputs/site_prb.csv').set_index('site')
    e = pd.read_csv(HERE/'experia_40.csv.gz', parse_dates=['DATE_ID'])
    e['weekday'] = e.DATE_ID.dt.weekday
    out_path = HERE/('model40_check.json' if check else 'model40.json')
    out = json.loads(out_path.read_text(encoding='utf-8')) if out_path.exists() and not check else {}
    variants = {'ana_model': {}} if check else VARIANTS
    for name, change in variants.items():
        if name in out:
            print('skip (done)', name)
            continue
        cfg = {**MAIN, **change}
        runs, users = [], []
        for hour_key in (['en_kalabalik'] if check else HOURS):
            for seed in (DRAWS[:1] if check else DRAWS):
                t0 = time.time()
                res, u = run_one(cfg, sites, prb, e, hour_key, seed)
                res['seconds'] = round(time.time() - t0, 1)
                runs.append(res); users.append(u)
                print(name, hour_key, seed, {k: round(v, 2) for k, v in res.items() if isinstance(v, float)}, flush=True)
        d = pd.DataFrame(runs)
        summary = {h: {c: round(float(g[c].mean()), 3) for c in ['unmatched_share', 'served_by_own_site_share', 'sinr_abs', 'rsrp_abs',
                                                                  'sinr_abs_matched_only', 'rsrp_abs_matched_only', 'rsrp_bias_matched_only', 'sinr_bias', 'rsrp_bias', 'no_service_share',
                                                                  'model_sinr_median', 'experia_sinr_median',
                                                                  'model_rsrp_median', 'experia_rsrp_median']}
                   for h, g in d.groupby('hour', sort=False)}
        for h in summary:
            summary[h]['pass_sinr_le_3'] = summary[h]['sinr_abs'] <= 3.0
            summary[h]['pass_rsrp_le_5'] = summary[h]['rsrp_abs'] <= 5.0
        out[name] = {'config': cfg, 'summary': summary, 'runs': runs}
        out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float), encoding='utf-8')
        pd.concat(users).to_csv(HERE/f'users_{name}{"_check" if check else ""}.csv.gz', index=False)
        print(name, json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
