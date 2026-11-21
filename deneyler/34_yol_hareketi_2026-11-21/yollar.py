"""Windows: OpenStreetMap main roads -> model coordinates (same local east-north plane as the sites,
origin 39.2461 N 28.0697 E, deneyler/07). Checks the conversion on the 24 sites, resamples every road
every 50 m, writes inputs/yol_noktalari.csv and yollar.png.
Road data: (c) OpenStreetMap contributors, ODbL."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
D29 = HERE.parent/'29_ihtiyaca_gore_zamanlayici_2026-11-19'
LAT0, LON0 = 39.2461, 28.0697
A, F = 6378137.0, 1/298.257223563
E2 = F*(2 - F)
STEP = 50.0
CLASS = {'motorway': 'otoyol', 'trunk': 'devlet yolu (bölünmüş)', 'primary': 'devlet yolu',
         'secondary': 'il yolu', 'tertiary': 'bağlantı yolu'}


def ecef(lat, lon):
    p, l = np.radians(lat), np.radians(lon)
    n = A/np.sqrt(1 - E2*np.sin(p)**2)
    return np.column_stack((n*np.cos(p)*np.cos(l), n*np.cos(p)*np.sin(l), n*(1 - E2)*np.sin(p)))


def to_xy(lat, lon):
    p, l = np.radians(LAT0), np.radians(LON0)
    R = np.array([[-np.sin(l), np.cos(l), 0], [-np.sin(p)*np.cos(l), -np.sin(p)*np.sin(l), np.cos(p)]])
    return (ecef(np.asarray(lat), np.asarray(lon)) - ecef([LAT0], [LON0])) @ R.T


def resample(xy, step):
    seg = np.hypot(*np.diff(xy, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, s[-1] + 1e-9, step)
    return np.column_stack([np.interp(t, s, xy[:, 0]), np.interp(t, s, xy[:, 1])]), t


def main():
    sites = pd.read_csv(D29/'inputs/sites_S0TA_42.csv')
    coords = pd.read_excel(ROOT/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('site').set_index('site')
    xy = to_xy(coords.loc[sites.site, 'lat'].to_numpy(), coords.loc[sites.site, 'lon'].to_numpy())
    err = np.hypot(xy[:, 0] - sites.x_m, xy[:, 1] - sites.y_m).max()
    print('site conversion check, max error m:', round(float(err), 4))
    assert err < 1.0
    osm = json.loads((HERE/'inputs/osm/osm_ana_yollar.json').read_text(encoding='utf-8'))
    rows = []
    for w in osm['elements']:
        if w.get('type') != 'way' or 'geometry' not in w:
            continue
        g = w['geometry']
        pts = to_xy([q['lat'] for q in g], [q['lon'] for q in g])
        if len(pts) < 2:
            continue
        cls = w['tags'].get('highway', '').replace('_link', '')
        pr, s = resample(pts, STEP)
        for (x, y), d in zip(pr, s):
            rows.append({'way_id': w['id'], 'highway': cls, 'link': w['tags'].get('highway', '').endswith('_link'),
                         'ref': w['tags'].get('ref', ''), 'name': w['tags'].get('name', ''),
                         'maxspeed': w['tags'].get('maxspeed', ''), 'd_along_m': round(float(d), 1),
                         'x_m': round(float(x), 2), 'y_m': round(float(y), 2)})
    p = pd.DataFrame(rows)
    p.to_csv(HERE/'inputs/yol_noktalari.csv', index=False, lineterminator='\n')
    km = p.groupby('highway').size()*STEP/1000
    print('road km by class:', km.round(1).to_dict())
    print('top refs (km):', (p[p.ref != ''].groupby('ref').size()*STEP/1000).sort_values(ascending=False).head(10).round(1).to_dict())
    fig, ax = plt.subplots(figsize=(8, 8))
    style = {'motorway': ('#7b3294', 2.4), 'trunk': ('#c2185b', 2.2), 'primary': ('#e66101', 1.8),
             'secondary': ('#5e81ac', 1.2), 'tertiary': ('#9e9e9e', 0.7)}
    for (wid, cls), g in p.groupby(['way_id', 'highway']):
        c, lw = style.get(cls, ('#bbbbbb', 0.5))
        ax.plot(g.x_m/1000, g.y_m/1000, color=c, lw=lw)
    for cls, (c, lw) in style.items():
        if cls in km.index:
            ax.plot([], [], color=c, lw=lw, label=f'{CLASS[cls]} ({km[cls]:.0f} km)')
    ev = sites.role == 'Evaluation'
    ax.scatter(sites.x_m[~ev]/1000, sites.y_m[~ev]/1000, marker='^', c='k', s=30, label='komşu saha')
    ax.scatter(sites.x_m[ev]/1000, sites.y_m[ev]/1000, marker='^', c='red', s=60, label='ana saha')
    for s in ['SITE_000482', 'SITE_000130']:
        r = sites[sites.site == s].iloc[0]
        ax.annotate(s[-3:] + ' (depremde çöktü)', (r.x_m/1000, r.y_m/1000), xytext=(5, 5), textcoords='offset points', fontsize=9)
    ax.set_xlim(sites.x_m.min()/1000 - 4, sites.x_m.max()/1000 + 4)
    ax.set_ylim(sites.y_m.min()/1000 - 4, sites.y_m.max()/1000 + 4)
    ax.set_aspect('equal')
    ax.set_xlabel('doğu (km, deprem merkezine göre)')
    ax.set_ylabel('kuzey (km)')
    ax.set_title('Bölgedeki ana yollar ve sahalar (yollar: OpenStreetMap)')
    ax.legend(loc='lower left', fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE/'yollar.png', dpi=130)


if __name__ == '__main__':
    main()
