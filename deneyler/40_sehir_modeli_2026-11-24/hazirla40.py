"""Windows: inputs for the Balıkesir city model (KURALLAR.md). Writes
- inputs/sites.csv: 94 sites (core <= 8 km, buffer 8-12 km), x/y in metres from the centre
- experia_40.csv.gz: Experia hourly rows of their cells (operator data, local only)
- inputs/site_prb.csv: per site and model hour, mean DL PRB of its real cells (3 Mondays, deneyler/39)
- hazirla40.json: counts."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
D39 = HERE.parent/'39_trafik_trendleri_2026-11-24'
sys.path.insert(0, str(HERE.parent/'35_bolge_secimi_2026-11-21'))
import secim  # noqa: E402

LAT0, LON0 = 39.6395, 27.8916
R_CORE, R_BUF = 8000.0, 12000.0
HOURS = {'sabah_gidis': '08:45', 'en_kalabalik': '15:30', 'kapasite_zirvesi': '21:15'}
PRB = 'DL_PRB_Util_%_ERI'


def main():
    (HERE/'inputs').mkdir(exist_ok=True)
    cs = pd.read_excel(ROOT/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx')
    co = cs.drop_duplicates('site').set_index('site')
    xy = secim.to_xy(co.lat.to_numpy(), co.lon.to_numpy(), LAT0, LON0)
    co['x_m'], co['y_m'] = xy[:, 0], xy[:, 1]
    co['d_m'] = np.hypot(co.x_m, co.y_m)
    s = co[co.d_m <= R_BUF].copy()
    s['role'] = np.where(s.d_m <= R_CORE, 'core', 'buffer')
    sites = s.reset_index()[['site', 'role', 'lat', 'lon', 'x_m', 'y_m', 'd_m']].sort_values('d_m')
    sites.to_csv(HERE/'inputs/sites.csv', index=False)
    cell_site = cs.drop_duplicates('cell').set_index('cell').site
    # Experia rows of the cells of these sites
    e = pd.read_excel(ROOT/'ana_proje/experia/experia.xlsx')
    e['site'] = e.FIRSTCELL.map(cell_site)
    e = e[e.site.isin(set(sites.site))]
    e.to_csv(HERE/'experia_40.csv.gz', index=False, compression='gzip')
    # KPI load per site and model hour (per-cell file from deneyler/39)
    rows = []
    for name in ['balikesir', 'bandirma']:
        y = pd.read_csv(D39/f'yuk_saatleri_sehir_{name}.csv.gz')
        y['site'] = y.CELL.map(cell_site)
        rows.append(y)
    y = pd.concat(rows)
    y['hour'] = y.hour.str.split().str[0]
    p = y.groupby(['hour', 'site'])[PRB].mean().unstack(0)
    prb = pd.DataFrame(index=sites.site)
    for h in HOURS:
        col = p[h].reindex(sites.site)
        prb[h] = col.fillna(float(p[h].reindex(sites.site).mean()))
        prb[h + '_from_kpi'] = col.notna()
    prb.reset_index().to_csv(HERE/'inputs/site_prb.csv', index=False)
    out = {'centre_lat_lon': [LAT0, LON0], 'sites': int(len(sites)), 'core': int((sites.role == 'core').sum()),
           'buffer': int((sites.role == 'buffer').sum()), 'experia_rows': int(len(e)), 'experia_cells': int(e.FIRSTCELL.nunique()),
           'experia_sites': int(e.site.nunique()), 'experia_dates': sorted(e.DATE_ID.astype(str).str[:10].unique().tolist()),
           'sites_with_kpi': {h: int(prb[h + '_from_kpi'].sum()) for h in HOURS},
           'mean_prb': {h: round(float(prb[h].mean()), 3) for h in HOURS}}
    (HERE/'hazirla40.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
