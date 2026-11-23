"""Windows: steps 1-2 for the second region, Edremit coast (DISTRICT_0008). Rule written before running:

Step 1, sites (24, as Sindirgi: 8 evaluation + 16 neighbours; Sindirgi showed 24 is enough, to be re-checked
with the fast model in step 3):
- Centre = mean coordinate of the DISTRICT_0008 sites (39.5851 N, 26.8971 E, Akcay coast).
- Evaluation sites = the 8 DISTRICT_0008 sites nearest the centre that have at least one cell with >= 100
  hourly Experia records (Sindirgi evaluation cells had >= 137).
- Neighbour sites = the next 16 sites nearest the centre from the full coordinate inventory, with or without
  Experia data, any district.
- Local metres: same east-north plane formula as Sindirgi (deneyler/07), origin = the centre.
- Sector hypothesis S0 as Sindirgi: 3 sectors per site, one carrier (B3); rotations later (step 3).
Step 2, data (operator data: local only, *.csv.gz is git-ignored):
- experia_cells.csv.gz: all Experia hourly rows of the cells of the 24 sites.
- kpi_cells.csv.gz: all 15-min KPI rows of those cells from the ten KPI workbooks (same columns as
  deneyler/09 + RACH TA and handover success, as deneyler/13).
Outputs: inputs/sites_edremit.csv, secim.json (cell lists, counts, hashes), secim.png."""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import time

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
P = HERE.parent.parent/'ana_proje'
REGIONS = {'edremit': ['DISTRICT_0008'], 'balikesir': ['DISTRICT_0001', 'DISTRICT_0014']}
A, F = 6378137.0, 1/298.257223563
E2 = F*(2 - F)
KEEP = ['DATETIME', 'CELL', 'EUtranCell_Availability_PC_ERI', 'Avg_Sim_RRC_Connected_User_Num_ERI',
        'DL_PRB_Util_%_ERI', 'UL_PRB_Util_%_ERI', 'DLTRF_VOLUME_MBYTE_ERI', 'ULTRF_Volume_Mbyte',
        'DL_PDCP_USER_THPUT_ERI', 'DL_PDCP_Cell_Thput_ERI', 'Avg_CQI_ERI', 'ERAB_Drop_PC_ERI',
        'Avg_RACH_TA_ERI', 'Intra_Freq_Hand_Succ_PC', 'Inter_Freq_Hand_Succ_PC']


def ecef(lat, lon):
    p, l = np.radians(lat), np.radians(lon)
    n = A/np.sqrt(1 - E2*np.sin(p)**2)
    return np.column_stack((n*np.cos(p)*np.cos(l), n*np.cos(p)*np.sin(l), n*(1 - E2)*np.sin(p)))


def to_xy(lat, lon, lat0, lon0):
    p, l = np.radians(lat0), np.radians(lon0)
    R = np.array([[-np.sin(l), np.cos(l), 0], [-np.sin(p)*np.cos(l), -np.sin(p)*np.sin(l), np.cos(p)]])
    return (ecef(np.asarray(lat), np.asarray(lon)) - ecef([lat0], [lon0])) @ R.T


def main(region='edremit'):
    sfx = '' if region == 'edremit' else '_' + region
    t0 = time.time()
    coords = pd.read_excel(P/'cell_site_coordinates/cell_site_coordinates.xlsx')
    exp = pd.read_excel(P/'experia/experia.xlsx')
    print('read', round(time.time() - t0), 's', flush=True)
    sites = coords.drop_duplicates('site').set_index('site')[['lat', 'lon']]
    exp['site'] = exp.FIRSTCELL.map(coords.set_index('cell').site)
    hours = exp.groupby(['site', 'FIRSTCELL']).size()
    good = set(hours[hours >= 100].index.get_level_values(0))
    dist_sites = exp[exp.DISTRICT_NAME.isin(REGIONS[region])].site.dropna().unique()
    lat0, lon0 = sites.loc[dist_sites, 'lat'].mean(), sites.loc[dist_sites, 'lon'].mean()
    xy = to_xy(sites.lat.to_numpy(), sites.lon.to_numpy(), lat0, lon0)
    sites['x_m'], sites['y_m'] = xy[:, 0], xy[:, 1]
    sites['d_m'] = np.hypot(sites.x_m, sites.y_m)
    cand = sites.loc[[s for s in dist_sites if s in good]].sort_values('d_m')
    ev = list(cand.index[:8])
    nb = list(sites.drop(ev).sort_values('d_m').index[:16])
    chosen = sites.loc[ev + nb].copy()
    chosen['role'] = ['Evaluation']*8 + ['Interference buffer']*16
    chosen['sector_count'] = 3
    chosen['carriers'] = 'B3'
    chosen['rotation_deg'] = 0.0          # set per antenna draw in step 3
    out = chosen.reset_index()[['site', 'role', 'x_m', 'y_m', 'rotation_deg', 'sector_count', 'carriers']]
    (HERE/'inputs').mkdir(exist_ok=True)
    for c in ['x_m', 'y_m']:
        out[c] = out[c].map(lambda v: f'{v:.9f}')
    out.to_csv(HERE/f'inputs/sites_{region}.csv', index=False, lineterminator='\n')
    cells = coords[coords.site.isin(chosen.index)]
    cell_set = set(cells.cell)
    e = exp[exp.FIRSTCELL.isin(cell_set)]
    e.to_csv(HERE/f'experia_cells{sfx}.csv.gz', index=False, compression='gzip')
    kfiles = sorted(P.glob('LTE Main KPI_*/*.xlsx'))
    assert len(kfiles) == 10
    parts = []
    for f in kfiles:
        k = pd.read_excel(f, usecols=lambda c: c in KEEP)
        parts.append(k[k.CELL.isin(cell_set)])
        print(f.name[:40], len(parts[-1]), round(time.time() - t0), 's', flush=True)
    kp = pd.concat(parts)
    kp['site'] = kp.CELL.map(cells.set_index('cell').site)
    kp.to_csv(HERE/f'kpi_cells{sfx}.csv.gz', index=False, compression='gzip')
    per = {s: {'role': chosen.role[s], 'd_center_km': round(chosen.d_m[s]/1000, 2),
               'cells_inventory': int((cells.site == s).sum()),
               'cells_experia': int(e[e.site == s].FIRSTCELL.nunique()), 'experia_rows': int((e.site == s).sum()),
               'cells_kpi': int(kp[kp.site == s].CELL.nunique())} for s in chosen.index}
    meta = {'rule': __doc__, 'centre_lat_lon': [lat0, lon0], 'district_sites': int(len(dist_sites)),
            'district_sites_with_data': int(len(cand)), 'sites': per,
            'experia_rows': int(len(e)), 'kpi_rows': int(len(kp)),
            'hashes': {n: hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in [f'experia_cells{sfx}.csv.gz', f'kpi_cells{sfx}.csv.gz']}}
    (HERE/f'secim{sfx}.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding='utf-8')
    fig, ax = plt.subplots(figsize=(7, 7))
    allxy = sites[sites.d_m < 15000]
    ax.scatter(allxy.x_m/1000, allxy.y_m/1000, c='#cccccc', s=10, label='diğer sahalar')
    b = chosen[chosen.role != 'Evaluation']
    ax.scatter(b.x_m/1000, b.y_m/1000, marker='^', c='k', s=30, label='komşu saha (16)')
    v = chosen[chosen.role == 'Evaluation']
    ax.scatter(v.x_m/1000, v.y_m/1000, marker='^', c='red', s=60, label='ana saha (8)')
    ax.set_aspect('equal'); ax.set_xlabel('doğu (km, bölge merkezine göre)'); ax.set_ylabel('kuzey (km)')
    ax.set_title(('Edremit kıyısı' if region == 'edremit' else 'Balıkesir merkez') + ': seçilen 24 saha'); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(HERE/f'secim{sfx}.png', dpi=120)
    print(json.dumps({k: v for k, v in meta.items() if k not in ('rule', 'sites', 'hashes')}, ensure_ascii=False))
    print(pd.DataFrame(per).T.to_string())


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'edremit')
