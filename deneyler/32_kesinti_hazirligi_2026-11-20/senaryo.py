"""Earthquake-time scenario for the fast model (deneyler/31), as fixed in TANIMLAR.md steps 1-2.

- Sites, antenna draws and distance correction as deneyler/29 (azimuth draws 42 / 7 / 99).
- Users per site = KPI connected users per cell in the earthquake window (deprem_yuku.py rule, here for all
  24 model sites) x the site's sectors. Site 549 has no KPI rows: it keeps its cells but gets no users.
- Placement around the site, uniform direction; distance by one of three rules (step 3):
    'A' Experia hourly cell TA records of the site, every record equally likely (deneyler/26-29 rule);
    'B' the same records weighted by the site's KPI connected users at that hour of day (busy hours count more);
    'C' exponential distances with the site's mean TA (individual users spread more than hourly averages).
  Buffer sites have no TA: they use the 8 evaluation sites' records pooled.
- Traffic: every user one DL flow of 512-byte packets; one common interval, chosen so that the mean PRB use
  of the 24 evaluation cells without outage equals the KPI earthquake value (0.27 Aug 10, 0.23 Oct 27).
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DEN = HERE.parent
D29 = DEN/'29_ihtiyaca_gore_zamanlayici_2026-11-19'
sys.path.insert(0, str(DEN/'31_hizli_model_2026-11-20'))
import hizli_model as hm  # noqa: E402

U, P = 'Avg_Sim_RRC_Connected_User_Num_ERI', 'DL_PRB_Util_%_ERI'
QUAKES = {'2025-08-10': ('2025-08-10 19:53', '2025-08-10 21:30', 0.27),
          '2025-10-27': ('2025-10-27 22:48', '2025-10-28 01:15', 0.23)}
AZ = {42: 701, 7: 702, 99: 703}            # azimuth draw -> deneyler/29 UE seed / sectors folder


def kpi():
    return pd.read_csv(DEN/'09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', parse_dates=['DATETIME'])


def quake_users(k, quake, peak=False):
    """Connected users per cell per site in the earthquake window (mean, or highest 15-min slot)."""
    a, b, _ = QUAKES[quake]
    w = k[(k.DATETIME >= pd.Timestamp(a).floor('15min')) & (k.DATETIME < pd.Timestamp(b))]
    per_slot = w.groupby(['site', 'DATETIME'])[U].mean()
    g = per_slot.groupby('site')
    return (g.max() if peak else g.mean()).to_dict()


def ta_records():
    e = pd.read_csv(DEN/'13_hucre_imzasi_2026-11-15/experia_cells.csv.gz').dropna(subset=['AVG(TAAVG)'])
    e['d'] = (e['AVG(TAAVG)']*4.88).clip(100.0, 15000.0)
    return e[['site', 'HOUR_ID', 'd']]


def hour_weights(k):
    k = k.assign(h=k.DATETIME.dt.hour)
    return k.groupby(['site', 'h'])[U].mean()


class Builder:
    def __init__(self, az, quake, peak=False):
        self.az, self.quake = az, quake
        sites = pd.read_csv(D29/'inputs'/f'sites_S0TA_{az}.csv').set_index('site')
        sec = pd.read_csv(D29/'simulation/results'/f'FT_TA_draw{AZ[az]}'/'sectors.csv')
        sec['x_m'] = sec.site.map(sites.x_m)
        sec['y_m'] = sec.site.map(sites.y_m)
        self.sites, self.sec = sites, sec
        k = kpi()
        self.users = quake_users(k, quake, peak)
        self.hw = hour_weights(k)
        self.ta = ta_records()
        corr = json.loads((D29/'correction.json').read_text(encoding='utf-8'))
        self.k0 = corr['model_fit_a_b'][0] - corr['experia_fit_a_b'][0]
        self.k1 = corr['model_fit_a_b'][1] - corr['experia_fit_a_b'][1]
        self.eval_sites = list(sites.index[sites.role == 'Evaluation'])

    def distances(self, site, n, rule, rng):
        own = self.ta[self.ta.site == site]
        pool = own if len(own) else self.ta
        if rule == 'A':
            return pool.d.to_numpy()[rng.integers(len(pool), size=n)]
        if rule == 'B':
            w = np.array([self.hw.get((s, h), 0.0) for s, h in zip(pool.site, pool.HOUR_ID)]) + 1e-9
            return pool.d.to_numpy()[rng.choice(len(pool), size=n, p=w/w.sum())]
        if rule == 'C':
            return np.clip(rng.exponential(pool.d.mean(), size=n), 100.0, 15000.0)
        raise ValueError(rule)

    def place(self, rule, rng):
        rows = []
        for s, row in self.sites.iterrows():
            n = int(round(self.users.get(s, 0.0)*row.sector_count))
            if n == 0:
                continue
            d = self.distances(s, n, rule, rng)
            a = rng.uniform(0, 2*np.pi, n)
            rows.append(pd.DataFrame({'x_m': row.x_m + d*np.cos(a), 'y_m': row.y_m + d*np.sin(a), 'z_m': 1.5,
                                      'extra_loss_db': self.k0 + self.k1*np.log10(d), 'home_site': s, 'distance_m': d}))
        return pd.concat(rows, ignore_index=True)

    def network(self, ues):
        return hm.Network(self.sec, ues, self.az)

    def cells_on(self, off_sites=()):
        return ~self.sec.site.isin(off_sites).to_numpy()

    def calibrate_interval(self, net, los_list):
        """Common packet interval (ms) giving the KPI earthquake PRB on the evaluation cells, no outage."""
        target = QUAKES[self.quake][2]
        ev = self.sec.role.to_numpy() == 'Evaluation'
        n = len(net.ues)
        lo, hi = 1.0, 2000.0
        for _ in range(16):
            mid = np.sqrt(lo*hi)
            prb = np.mean([hm.solve(net, los, np.full(n, 512.0), np.full(n, mid))['load'][ev].mean() for los in los_list])
            lo, hi = (mid, hi) if prb > target else (lo, mid)
        return float(np.sqrt(lo*hi))


REFSENS_RE_DBM = -91.0 - 10*np.log10(1200)      # TS 36.101 Table 7.3.1-1, Band 3, 20 MHz


def outcome(builder, ues, r, mask=None):
    """Step-1 metrics for the users in mask (default: all)."""
    m = np.ones(len(ues), bool) if mask is None else mask
    dem = r['demand']
    served_share = np.minimum(1.0, 1.0/np.maximum(dem[r['serving']], 1e-9))
    no_service = r['cqi'] == 0
    ev = builder.sec.role.to_numpy() == 'Evaluation'
    return {'users': int(m.sum()),
            'no_service': float(no_service[m].mean()),
            'weak': float((r['rsrp'] < REFSENS_RE_DBM)[m].mean()),
            'not_served_overload': float(((1 - served_share)*~no_service)[m].mean()),
            'overloaded_cells_eval': int((dem[ev] >= 1).sum()),
            'max_cell_demand_eval': float(dem[ev].max()),
            'eval_prb': float(r['load'][ev].mean())}
