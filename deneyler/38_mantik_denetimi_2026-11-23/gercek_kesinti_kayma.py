"""Windows, no simulation model at all. When a whole site really went off air in the KPI, did its connected users
reappear on the nearby sites? Rule written before looking at any result:
- Event: mean availability of ALL the site's cells < 0.5 for at least 2 consecutive 15-min slots, >= 5 users before.
- Before = the 4 slots just before. Nearby = the 6 nearest other sites with KPI. Control = all other sites (time trend).
- Absorbed share = (nearby during - nearby before x C) / (site before x C - site during), C = control during / before.
- Noise: the same calculation on the same site and clock time on the other days without an outage.
Writes gercek_kesinti_kayma.json (aggregates only)."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
A, U = 'EUtranCell_Availability_PC_ERI', 'Avg_Sim_RRC_Connected_User_Num_ERI'
FILES = [DEN/'09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', DEN/'35_bolge_secimi_2026-11-21/kpi_cells.csv.gz',
         DEN/'35_bolge_secimi_2026-11-21/kpi_cells_balikesir.csv.gz']
QUAKES = [pd.Timestamp('2025-08-10 19:53'), pd.Timestamp('2025-10-27 22:48')]
SLOT = pd.Timedelta('15min')


def calc(users, site, near, ctrl, before, during):
    if not all(t in users.index for t in list(before) + list(during)):
        return None
    b, d = users.loc[before].mean(), users.loc[during].mean()
    if b[ctrl].sum() <= 0:
        return None
    c = d[ctrl].sum()/b[ctrl].sum()
    return {'site_before': float(b[site]), 'site_during': float(d[site]), 'expected_lost': float(b[site]*c - d[site]),
            'nearby_gain': float(d[near].sum() - b[near].sum()*c), 'nearby_before': float(b[near].sum())}


def main():
    k = pd.concat([pd.read_csv(f, usecols=['DATETIME', 'CELL', A, U, 'site'], parse_dates=['DATETIME']) for f in FILES if f.exists()])
    k = k.drop_duplicates(['DATETIME', 'CELL'])
    users = k.pivot_table(index='DATETIME', columns='site', values=U, aggfunc='sum')
    av = k.pivot_table(index='DATETIME', columns='site', values=A, aggfunc='mean')
    co = pd.read_excel(DEN.parent/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('site').set_index('site')
    sites = [s for s in users.columns if s in co.index]
    la, lo = co.lat.reindex(sites).to_numpy(), co.lon.reindex(sites).to_numpy()
    x, y = (lo - lo.mean())*111320*np.cos(np.radians(la.mean())), (la - la.mean())*110574
    pos = pd.DataFrame({'x': x, 'y': y}, index=sites)
    rows = []
    for s in sites:
        low = av[s].reindex(users.index) < 0.5
        idx = list(users.index)
        i = 0
        while i < len(idx):
            if not low.iloc[i]:
                i += 1; continue
            j = i
            while j + 1 < len(idx) and low.iloc[j + 1] and idx[j + 1] - idx[j] == SLOT:
                j += 1
            during = idx[i:j + 1]
            i = j + 1
            if len(during) < 2:
                continue
            before = [during[0] - SLOT*n for n in range(4, 0, -1)]
            d = np.hypot(pos.x - pos.x[s], pos.y - pos.y[s]).drop(s).sort_values()
            near = list(d.index[:6])
            ctrl = [c for c in sites if c != s and c not in near]
            r = calc(users[sites].fillna(0), s, near, ctrl, before, during)
            if r is None or r['site_before'] < 5 or r['expected_lost'] <= 0:
                continue
            noise = []
            for day in sorted(set(users.index.normalize())):
                sh = day - during[0].normalize()
                if sh == pd.Timedelta(0):
                    continue
                b2, d2 = [t + sh for t in before], [t + sh for t in during]
                if not all(t in av.index for t in b2 + d2) or (av.loc[b2 + d2, s] < 0.99).any():
                    continue
                n = calc(users[sites].fillna(0), s, near, ctrl, b2, d2)
                if n:
                    noise.append(n['nearby_gain']/r['expected_lost'])
            hrs = [(during[0] - q)/pd.Timedelta('1h') for q in QUAKES]
            rows.append({'site': s, 'start': str(during[0]), 'slots': len(during), 'after_quake_24h': any(0 <= h <= 24 for h in hrs),
                         'nearest_km': round(float(d.iloc[0])/1000, 2), 'mean_km_6': round(float(d.iloc[:6].mean())/1000, 2), **{a: round(b, 1) for a, b in r.items()},
                         'absorbed': round(r['nearby_gain']/r['expected_lost'], 2),
                         'noise_sd': round(float(np.std(noise)), 2) if len(noise) >= 3 else None, 'noise_days': len(noise)})
    e = pd.DataFrame(rows).sort_values('start')
    pd.set_option('display.width', 250)
    print('sites with KPI', len(sites), 'whole-site outages', len(e))
    print(e.drop(columns=['nearby_before']).to_string(index=False))
    out = {'events': rows}
    for name, g in [('all', e), ('not_after_quake', e[~e.after_quake_24h])]:
        if len(g):
            w = float(g.nearby_gain.sum()/g.expected_lost.sum())
            out[name] = {'events': int(len(g)), 'users_lost_total': float(g.expected_lost.sum()), 'absorbed_weighted': w, 'absorbed_median': float(g.absorbed.median())}
            print(name, out[name])
    (HERE/'gercek_kesinti_kayma.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
