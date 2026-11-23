"""Windows: Edremit coast step 3 (ADIM3_KURALLAR.md) with the fast model: inputs, distance correction,
RMa vs UMa choice on the training sites, test on the held-out sites, 24 vs 48 site edge check.
Writes adim3.json, adim3.png and inputs/ (sites per draw, users per draw and model)."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from scipy.special import erf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent/'34_yol_hareketi_2026-11-21'))
import alan  # noqa: E402
import secim  # noqa: E402
import kiyi  # noqa: E402
hm = alan.hm

DRAWS = [42, 7, 99]
TS_M, DMIN, DMAX = 4.88, 100.0, 15000.0
QUAKE_DAYS = ['2025-08-10', '2025-10-27', '2025-10-28']
PROP = {'RMa': {'sigma': 8.0, 'shadow_spacing': 120.0, 'los_spacing': 60.0},
        'UMa': {'sigma': 6.0, 'shadow_spacing': 50.0, 'los_spacing': 50.0}}
PROVINCE_FIT = [-68.33640440362697, -10.621472507923482]


def uma_loss(d2, d3):
    fg = hm.F_HZ/1e9
    dbp = 4*(hm.H_BS - 1.0)*(hm.H_UT - 1.0)*hm.F_HZ/hm.C
    pl1 = 28.0 + 22.0*np.log10(d3) + 20.0*np.log10(fg)
    pl2 = 28.0 + 40.0*np.log10(d3) + 20.0*np.log10(fg) - 9.0*np.log10(dbp**2 + (hm.H_BS - hm.H_UT)**2)
    los = np.where(d2 <= dbp, pl1, pl2)
    nlos = 13.54 + 39.08*np.log10(d3) + 20.0*np.log10(fg) - 0.6*(hm.H_UT - 1.5)
    return los, np.maximum(los, nlos)


class Model35(hm.Network):
    """hizli_model.Network with smooth shadow + position LOS (deneyler/34) for RMa or UMa."""

    def __init__(self, sectors, ues, seed, prop):
        p = PROP[prop]
        super().__init__(sectors, ues, seed, p['sigma'])
        enb = self.cells[['x_m', 'y_m', 'z_m']].to_numpy(float)
        ue = self.ues[['x_m', 'y_m', 'z_m']].to_numpy(float)
        ex, ey, ux, uy = enb[None, :, 0], enb[None, :, 1], ue[:, None, 0], ue[:, None, 1]
        self.fixed_db = (self.fixed_db - hm.link_shadow(enb, ue, p['sigma'], seed)
                         + p['sigma']*alan.field(seed, 1, ex, ey, ux, uy, p['shadow_spacing']))
        if prop == 'UMa':
            d3 = np.sqrt(self.d2**2 + (enb[None, :, 2] - ue[:, None, 2])**2)
            self.los_db, self.nlos_db = uma_loss(self.d2, d3)
            self.p_los = np.where(self.d2 <= 18, 1.0, 18/self.d2 + np.exp(-self.d2/63)*(1 - 18/self.d2))
        u = 0.5*(1 + erf(alan.field(seed, 2, ex, ey, ux, uy, p['los_spacing'])/np.sqrt(2)))
        self.los_fixed = u < self.p_los

    def draw_los(self, rng=None):
        return self.los_fixed


def fit(d, y):
    a = np.vstack([np.ones(len(d)), np.log10(d)]).T
    b = np.linalg.lstsq(a, y, rcond=None)[0]
    return [float(b[0]), float(b[1])]


def sectors_of(sites, seed):
    s = sites.sort_values('site').reset_index(drop=True)
    rot = dict(zip(s.site, np.random.default_rng(seed).uniform(0, 120, len(s))))
    rows = []
    for _, r in sites.iterrows():
        for k in range(3):
            rows.append({'site': r.site, 'role': r.role, 'sector': k, 'x_m': r.x_m, 'y_m': r.y_m, 'z_m': 30.0,
                         'orientation_ccw_from_east_deg': rot[r.site] + 120*k})
    out = pd.DataFrame(rows)
    out.insert(0, 'synthetic_cell_id', np.arange(1, len(out) + 1))
    return out, rot


def place(ev_sites, sites, ta, seg, rng, per_site=32):
    rows = []
    for s in ev_sites:
        c = sites.set_index('site').loc[s]
        pool = ta[ta.site == s].d.to_numpy()
        n = 0
        while n < per_site:
            d = pool[rng.integers(len(pool))]
            for _ in range(50):
                a = rng.uniform(0, 2*np.pi)
                x, y = c.x_m + d*np.cos(a), c.y_m + d*np.sin(a)
                if seg is None or kiyi.on_land([x], [y], seg)[0]:
                    rows.append({'x_m': x, 'y_m': y, 'z_m': 1.5, 'placement_site': s, 'placement_distance_m': d})
                    n += 1
                    break
    return pd.DataFrame(rows)


def site_mean(sec, serving, value):
    d = pd.DataFrame({'site': sec.site.to_numpy()[serving], 'sector': sec.sector.to_numpy()[serving], 'v': value})
    return d.groupby(['site', 'sector']).v.mean().groupby('site').mean()


def main(n_sites=24, region='edremit'):
    sfx = '' if region == 'edremit' else '_' + region
    label = 'Edremit kıyısı' if region == 'edremit' else 'Balıkesir merkez'
    meta = json.loads((HERE/f'secim{sfx}.json').read_text(encoding='utf-8'))
    lat0, lon0 = meta['centre_lat_lon']
    sites = pd.read_csv(HERE/f'inputs/sites_{region}.csv')
    ev = sorted(sites.site[sites.role == 'Evaluation'])
    test = sorted(np.array(ev)[np.random.default_rng(35).choice(8, 3, replace=False)])
    train = [s for s in ev if s not in test]
    seg = kiyi.segments() if region == 'edremit' else None   # inland region: no sea
    # Experia: TA records and site targets
    e = pd.read_csv(HERE/f'experia_cells{sfx}.csv.gz')
    e = e.dropna(subset=['AVG(TAAVG)'])
    ta = pd.DataFrame({'site': e.site, 'd': (e['AVG(TAAVG)']*TS_M).clip(DMIN, DMAX)})
    hrs = e.groupby('FIRSTCELL').size()
    ec = e[e.FIRSTCELL.isin(hrs[hrs >= 100].index)]
    cm = ec.groupby(['site', 'FIRSTCELL']).agg(rsrp=('AVG(MED_SERVINGRSRPMEDIAN)', 'mean'), sinr=('AVG(MED_SINRMEDIAN)', 'mean'))
    targets = cm.groupby('site').mean().loc[ev]
    # KPI load per site (no quake days)
    k = pd.read_csv(HERE/f'kpi_cells{sfx}.csv.gz', parse_dates=['DATETIME'])
    k = k[~k.DATETIME.dt.strftime('%Y-%m-%d').isin(QUAKE_DAYS)]
    site_prb = k.groupby(['site', 'CELL'])['DL_PRB_Util_%_ERI'].mean().groupby('site').mean()
    # Experia distance fit: cells of sites within 15 km of the centre, evaluation sites excluded
    rc = pd.read_csv(ROOT/'ana_proje/analysis/radio_cell_summary.csv').dropna(subset=['rsrp_mean', 'ta_mean', 'site'])
    co = pd.read_excel(ROOT/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('site').set_index('site')
    xy = secim.to_xy(co.lat.to_numpy(), co.lon.to_numpy(), lat0, lon0)
    co['x_m'], co['y_m'] = xy[:, 0], xy[:, 1]
    co['d'] = np.hypot(co.x_m, co.y_m)
    near = set(co.index[co.d <= 15000]) - set(ev)
    rcn = rc[rc.site.isin(near)]
    exp_fit = fit((rcn.ta_mean*TS_M).clip(DMIN, DMAX).to_numpy(), rcn.rsrp_mean.to_numpy())
    # 48-site network for the edge check: next 24 sites nearest the centre
    extra = co.drop(sites.site).sort_values('d').head(24)
    sites48 = pd.concat([sites, pd.DataFrame({'site': extra.index, 'role': 'Extra buffer', 'x_m': extra.x_m.to_numpy(),
                                              'y_m': extra.y_m.to_numpy()})], ignore_index=True)

    out = {'train_sites': train, 'test_sites': test, 'experia_fit_local_a_b': exp_fit, 'experia_cells_local': int(len(rcn)),
           'experia_fit_province_a_b': PROVINCE_FIT, 'site_prb': site_prb.round(3).to_dict(),
           'targets': targets.round(2).to_dict(), 'models': {}}
    draws = {}
    fill = 0.21 if region == 'edremit' else round(float(site_prb.mean()), 3)   # extra sites without KPI
    out['fill_prb'] = fill
    net_sites = sites if n_sites == 24 else sites48     # edge rule: 48 sites if 24 are not enough
    for seed in DRAWS:
        sec, rot = sectors_of(net_sites, seed)
        ues = place(ev, sites, ta, seg, np.random.default_rng(seed + 1000))
        ues['extra_loss_db'] = 0.0
        load = sec.site.map(site_prb).fillna(fill).to_numpy()
        sec.to_csv(HERE/f'inputs/sectors_{region}{n_sites}_{seed}.csv', index=False)
        draws[seed] = (sec, ues, load)
    for prop in PROP:
        # model distance fit from uncorrected RSRP (correction is the same on every link of a user)
        dd, yy = [], []
        for seed, (sec, ues, load) in draws.items():
            net = Model35(sec, ues, seed, prop)
            r = net.rsrp(net.draw_los())
            srv = r.argmax(1)
            dd.append(np.clip(net.d2[np.arange(len(r)), srv], DMIN, DMAX)); yy.append(r[np.arange(len(r)), srv])
        mod_fit = fit(np.concatenate(dd), np.concatenate(yy))
        k0, k1 = mod_fit[0] - exp_fit[0], mod_fit[1] - exp_fit[1]
        per = []
        for seed, (sec, ues, load) in draws.items():
            u = ues.copy()
            u['extra_loss_db'] = k0 + k1*np.log10(np.clip(u.placement_distance_m, DMIN, DMAX))
            u.to_csv(HERE/f'inputs/ues_{region}{n_sites}_{prop}_{seed}.csv', index=False)
            net = Model35(sec, u, seed, prop)
            r = net.rsrp(net.draw_los())
            srv = r.argmax(1)
            rep, _ = hm.sinr(r, srv, load)
            ss = site_mean(sec, srv, rep); sr = site_mean(sec, srv, r[np.arange(len(r)), srv])
            row = {'seed': seed}
            for name, group in [('train', train), ('test', test)]:
                row[f'sinr_{name}'] = float(np.mean([abs(ss[s] - targets.sinr[s]) for s in group if s in ss]))
                row[f'rsrp_{name}'] = float(np.mean([abs(sr[s] - targets.rsrp[s]) for s in group if s in sr]))
            row['sinr_by_site'] = ss.reindex(ev).round(2).to_dict(); row['rsrp_by_site'] = sr.reindex(ev).round(2).to_dict()
            row['los_share'] = float(net.los_fixed.mean())
            row['cell_rsrp_median'] = float(pd.DataFrame({'c': srv, 'v': r[np.arange(len(r)), srv]}).groupby('c').v.mean().median())
            per.append(row)
        m = pd.DataFrame(per)
        out['models'][prop] = {'model_fit_a_b': mod_fit, 'k0_k1': [k0, k1],
                               'mean': {c: float(m[c].mean()) for c in ['sinr_train', 'rsrp_train', 'sinr_test', 'rsrp_test']},
                               'draws': per}
        print(prop, 'k0 k1', round(k0, 2), round(k1, 2), out['models'][prop]['mean'], flush=True)
    a, b = out['models']['RMa']['mean'], out['models']['UMa']['mean']
    if abs(a['sinr_train'] - b['sinr_train']) < 0.3:
        chosen = 'RMa' if a['rsrp_train'] <= b['rsrp_train'] else 'UMa'
    else:
        chosen = 'RMa' if a['sinr_train'] < b['sinr_train'] else 'UMa'
    cm_ = out['models'][chosen]['mean']
    out['chosen'] = chosen
    out['accept'] = {'sinr_test_le_3': cm_['sinr_test'] <= 3.0, 'rsrp_test_le_5': cm_['rsrp_test'] <= 5.0}
    out['accepted'] = all(out['accept'].values())
    # edge check with the chosen model: 24 vs 48 sites, same users
    k0, k1 = out['models'][chosen]['k0_k1']
    diffs = []
    for seed, (sec, ues, load) in draws.items():
        u = ues.copy(); u['extra_loss_db'] = k0 + k1*np.log10(np.clip(u.placement_distance_m, DMIN, DMAX))
        if n_sites != 24:
            break                                           # edge check only for the 24-site network
        sec48, _ = sectors_of(sites48, seed)
        load48 = sec48.site.map(site_prb).fillna(fill).to_numpy()
        res = []
        for s_, l_ in [(sec, load), (sec48, load48)]:
            net = Model35(s_, u, seed, chosen)
            r = net.rsrp(net.draw_los()); srv = r.argmax(1)
            rep, _ = hm.sinr(r, srv, l_)
            res.append(site_mean(s_, srv, rep).reindex(ev))
        diffs.append(float((res[1] - res[0]).abs().mean()))
    out['n_sites'] = n_sites
    if diffs:
        out['edge_check_mean_abs_sinr_change_db'] = float(np.mean(diffs))
        out['edge_ok'] = out['edge_check_mean_abs_sinr_change_db'] < 0.5
    (HERE/f'adim3{sfx}{"" if n_sites == 24 else "_48"}.json').write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float), encoding='utf-8')
    print('chosen', chosen, 'accept', out['accept'], 'edge', out.get('edge_check_mean_abs_sinr_change_db'))
    # figure: per evaluation site, model (chosen, mean of draws) vs Experia
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, q, lab in [(axs[0], 'sinr', 'SINR (dB)'), (axs[1], 'rsrp', 'RSRP (dBm)')]:
        mv = pd.DataFrame([d[f'{q}_by_site'] for d in out['models'][chosen]['draws']]).mean()
        tv = targets[q]
        lo, hi = min(mv.min(), tv.min()) - 3, max(mv.max(), tv.max()) + 3
        ax.fill_between([lo, hi], [lo - 3, hi - 3], [lo + 3, hi + 3], color='#eeeeee', label='±3 dB')
        ax.plot([lo, hi], [lo, hi], color='grey', lw=0.8)
        for s in ev:
            ax.scatter(tv[s], mv[s], c='#e66101' if s in test else '#1f78b4', s=40)
            ax.annotate(s[-3:], (tv[s], mv[s]), fontsize=7, xytext=(3, 3), textcoords='offset points')
        ax.scatter([], [], c='#1f78b4', label='eğitim sahası'); ax.scatter([], [], c='#e66101', label='test sahası')
        ax.set_xlabel(f'Experia {lab}'); ax.set_ylabel(f'model {lab}'); ax.legend(fontsize=8)
        ax.set_title(f'{lab.split()[0]}: model ({chosen}) ve gerçek ölçüm, saha başına')
    fig.suptitle(f'{label} ({n_sites} saha): model gerçek ölçüme ne kadar yakın? (üç anten yönü çekilişinin ortalaması)')
    fig.tight_layout(); fig.savefig(HERE/f'adim3{sfx}{"" if n_sites == 24 else "_48"}.png', dpi=120)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 24, sys.argv[2] if len(sys.argv) > 2 else 'edremit')
