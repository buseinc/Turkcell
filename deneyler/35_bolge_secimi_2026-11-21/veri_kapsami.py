"""Windows: which districts have the data a second region needs? (read only, local operator files)
For every CITY_NAME / DISTRICT_NAME in Experia: hourly radio rows, cells, sites (via cell_site_coordinates),
how many of those cells appear in the KPI file of 27 Oct 2025, site density (sites per 100 km2 of the
convex hull) and the mean distance to the nearest other site. Writes veri_kapsami.csv (counts only, no
measurements) and prints the table. Raw files are not copied."""
from pathlib import Path
import glob
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
P = HERE.parent.parent/'ana_proje'


def km_xy(lat, lon):
    return (np.radians(lon - lon.mean())*6371*np.cos(np.radians(lat.mean())), np.radians(lat - lat.mean())*6371)


def hull_area(x, y):
    pts = sorted(set(zip(x, y)))
    if len(pts) < 3:
        return 0.0

    def cross(o, a, b):
        return (a[0] - o[0])*(b[1] - o[1]) - (a[1] - o[1])*(b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    h = lower[:-1] + upper[:-1]
    return 0.5*abs(sum(h[i][0]*h[i - 1][1] - h[i - 1][0]*h[i][1] for i in range(len(h))))


def main():
    e = pd.read_excel(P/'experia/experia.xlsx', usecols=['CITY_NAME', 'DISTRICT_NAME', 'FIRSTCELL'])
    c = pd.read_excel(P/'cell_site_coordinates/cell_site_coordinates.xlsx')
    kc = set(pd.read_excel(glob.glob(str(P/'LTE Main KPI_20251027*'/'*.xlsx'))[0], usecols=['CELL']).CELL)
    e = e.merge(c, left_on='FIRSTCELL', right_on='cell', how='left')
    rows = []
    for (city, dist), g in e.groupby(['CITY_NAME', 'DISTRICT_NAME']):
        cells = set(g.FIRSTCELL)
        s = g.dropna(subset=['site']).drop_duplicates('site')
        x, y = km_xy(s.lat.to_numpy(), s.lon.to_numpy()) if len(s) else (np.array([]), np.array([]))
        nn = np.nan
        if len(s) > 1:
            d = np.hypot(x[:, None] - x[None], y[:, None] - y[None]); np.fill_diagonal(d, np.inf); nn = float(d.min(1).mean())
        area = hull_area(x, y)
        rows.append({'city': city, 'district': dist, 'experia_rows': len(g), 'cells': len(cells), 'sites': len(s),
                     'cells_in_kpi': len(cells & kc), 'area_km2': round(area, 1),
                     'sites_per_100km2': round(100*len(s)/area, 2) if area > 0 else None,
                     'mean_nearest_site_km': round(nn, 2) if nn == nn else None,
                     'lat': round(float(s.lat.mean()), 4) if len(s) else None, 'lon': round(float(s.lon.mean()), 4) if len(s) else None})
    t = pd.DataFrame(rows).sort_values('experia_rows', ascending=False)
    t.to_csv(HERE/'veri_kapsami.csv', index=False)
    print('KPI cells (27 Oct):', len(kc), '| coordinate cells:', len(c))
    print(t.to_string(index=False))


if __name__ == '__main__':
    main()
