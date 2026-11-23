"""Windows: land / sea test from the OpenStreetMap coastline ((c) OpenStreetMap contributors, ODbL).
OSM rule: land is on the LEFT of every coastline way's direction. A point is on land when it lies on the left
of its nearest coastline segment. Check: the 24 sites must all be on land. Writes inputs/kiyi_segmentleri.csv
(local metres, region centre origin) and kiyi.png."""
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
import secim  # noqa: E402


def segments():
    meta = json.loads((HERE/'secim.json').read_text(encoding='utf-8'))
    lat0, lon0 = meta['centre_lat_lon']
    osm = json.loads((HERE/'inputs/osm/osm_kiyi.json').read_text(encoding='utf-8'))
    rows = []
    for w in osm['elements']:
        if w.get('type') != 'way' or 'geometry' not in w:
            continue
        g = w['geometry']
        xy = secim.to_xy([q['lat'] for q in g], [q['lon'] for q in g], lat0, lon0)
        for a, b in zip(xy[:-1], xy[1:]):
            rows.append((w['id'], a[0], a[1], b[0], b[1]))
    return pd.DataFrame(rows, columns=['way', 'x0', 'y0', 'x1', 'y1'])


def on_land(x, y, seg):
    """True where (x, y) is on the land side of its nearest coastline segment."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    out = np.empty(len(x), bool)
    a = seg[['x0', 'y0']].to_numpy(); b = seg[['x1', 'y1']].to_numpy(); ab = b - a
    L2 = np.maximum((ab**2).sum(1), 1e-9)
    for i in range(0, len(x), 2000):
        px, py = x[i:i + 2000, None], y[i:i + 2000, None]
        t = np.clip(((px - a[:, 0])*ab[:, 0] + (py - a[:, 1])*ab[:, 1])/L2, 0, 1)
        cx, cy = a[:, 0] + t*ab[:, 0], a[:, 1] + t*ab[:, 1]
        d = (px - cx)**2 + (py - cy)**2
        k = d.argmin(1)
        cross = ab[k, 0]*(py[:, 0] - a[k, 1]) - ab[k, 1]*(px[:, 0] - a[k, 0])
        out[i:i + 2000] = cross > 0
    return out


def main():
    seg = segments()
    seg.to_csv(HERE/'inputs/kiyi_segmentleri.csv', index=False)
    s = pd.read_csv(HERE/'inputs/sites_edremit.csv')
    land = on_land(s.x_m, s.y_m, seg)
    print('segments', len(seg), 'ways', seg.way.nunique(), '| sites on land', int(land.sum()), '/', len(s))
    gx, gy = np.meshgrid(np.arange(-15000, 15001, 250.0), np.arange(-15000, 15001, 250.0))
    g = on_land(gx.ravel(), gy.ravel(), seg).reshape(gx.shape)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.contourf(gx/1000, gy/1000, g.astype(float), levels=[-0.5, 0.5, 1.5], colors=['#cfe3f5', '#f2ede1'])
    for _, r in seg.iterrows():
        ax.plot([r.x0/1000, r.x1/1000], [r.y0/1000, r.y1/1000], color='#2b6ca3', lw=0.6)
    ev = s.role == 'Evaluation'
    ax.scatter(s.x_m[~ev]/1000, s.y_m[~ev]/1000, marker='^', c='k', s=25, label='komşu saha')
    ax.scatter(s.x_m[ev]/1000, s.y_m[ev]/1000, marker='^', c='red', s=50, label='ana saha')
    ax.set_xlim(-15, 15); ax.set_ylim(-15, 15); ax.set_aspect('equal')
    ax.set_title('Edremit kıyısı: kara (bej) ve deniz (mavi), OpenStreetMap kıyı çizgisi')
    ax.set_xlabel('doğu (km)'); ax.set_ylabel('kuzey (km)'); ax.legend(fontsize=8, loc='lower left')
    fig.tight_layout(); fig.savefig(HERE/'kiyi.png', dpi=120)
    assert land.all(), 'a site is in the sea: the land test is wrong'


if __name__ == '__main__':
    main()
