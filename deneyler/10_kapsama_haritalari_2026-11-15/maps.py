"""Grid coverage maps of the selected baseline (Windows Python).

Only quantities reproduced exactly by validate*.py are mapped: serving sector, RSRP, RSRQ,
S/N (no neighbour transmits: best case) and control-channel SINR (all neighbours transmit:
worst case). Loaded data-channel SINR lies between the two; no analytical loaded-SINR map is
drawn because it did not meet the predeclared agreement with native ns-3 (see SONUCLAR.md).
"""
from pathlib import Path
import json
import sys

import folium
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd

from radio_model import received_power_w, link_metrics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D08 = ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12'
sys.path.insert(0, str(ROOT / 'ana_proje/analysis'))
from map_background import add_resilient_background  # noqa: E402

DRAWS = {701: 42, 702: 7, 703: 99}
MAIN = 701
STEP = 100.0          # grid resolution [m]
MARGIN = 4000.0       # around the 24 sites [m]
EVAL_RADIUS = 6000.0  # evaluation area: within 6 km of an evaluation site (UE placement range)
LAT0, LON0 = 39.2461, 28.0697
A, F = 6378137.0, 1 / 298.257223563
E2 = F * (2 - F)
RSRP_LEVELS = [-200, -120, -110, -100, -90, 0]
RSRP_LABELS = ['< −120', '−120…−110', '−110…−100', '−100…−90', '≥ −90']
RSRP_COLORS = ['#d73027', '#fc8d59', '#fee08b', '#91cf60', '#1a9850']
SINR_LEVELS = [-50, -3, 0, 5, 10, 50]
SINR_LABELS = ['< −3', '−3…0', '0…5', '5…10', '≥ 10']


def ecef(lat, lon):
    p, l = np.radians(lat), np.radians(lon)
    n = A / np.sqrt(1 - E2 * np.sin(p) ** 2)
    return np.column_stack((n * np.cos(p) * np.cos(l), n * np.cos(p) * np.sin(l), n * (1 - E2) * np.sin(p)))


def rotation():
    p, l = np.radians(LAT0), np.radians(LON0)
    return np.array([[-np.sin(l), np.cos(l), 0], [-np.sin(p) * np.cos(l), -np.sin(p) * np.sin(l), np.cos(p)],
                     [np.cos(p) * np.cos(l), np.cos(p) * np.sin(l), np.sin(p)]])


def to_latlon(x, y):
    xyz = np.column_stack((x, y, np.zeros_like(x))) @ rotation() + ecef([LAT0], [LON0])
    X, Y, Z = xyz.T
    h = np.hypot(X, Y)
    p = np.arctan2(Z, h * (1 - E2))
    for _ in range(12):
        n = A / np.sqrt(1 - E2 * np.sin(p) ** 2)
        p = np.arctan2(Z + E2 * n * np.sin(p), h)
    return np.degrees(p), np.degrees(np.arctan2(Y, X))


def grid_for(sectors):
    x0, x1 = sectors.x_m.min() - MARGIN, sectors.x_m.max() + MARGIN
    y0, y1 = sectors.y_m.min() - MARGIN, sectors.y_m.max() + MARGIN
    xs = np.arange(x0, x1 + STEP / 2, STEP)
    ys = np.arange(y0, y1 + STEP / 2, STEP)
    X, Y = np.meshgrid(xs, ys)
    return xs, ys, X, Y


def compute(seed):
    sectors = pd.read_csv(D08 / f'simulation/results/n256_draw{seed}/sectors.csv')
    xs, ys, X, Y = grid_for(sectors)
    pts = np.column_stack((X.ravel(), Y.ravel(), np.full(X.size, 1.5)))
    lm = link_metrics(received_power_w(pts, sectors))
    shape = X.shape
    ev = sectors[sectors.role == 'Evaluation'].drop_duplicates('site')[['x_m', 'y_m']].to_numpy()
    d = np.sqrt(((pts[:, None, :2] - ev[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    return {'sectors': sectors, 'xs': xs, 'ys': ys, 'X': X, 'Y': Y,
            'site': sectors.site.to_numpy()[lm['serving']].reshape(shape),
            'cell': lm['serving'].reshape(shape),
            'rsrp': lm['rsrp_dbm'].reshape(shape), 'rsrq': lm['rsrq_db'].reshape(shape),
            'snr': lm['snr_db'].reshape(shape), 'ctrl': lm['control_sinr_db'].reshape(shape),
            'eval': (d <= EVAL_RADIUS).reshape(shape)}


def share(values, mask, levels):
    v = values[mask]
    return [float(((v >= a) & (v < b)).mean()) for a, b in zip(levels[:-1], levels[1:])]


def main():
    res = {s: compute(s) for s in DRAWS}
    g = res[MAIN]
    sectors = g['sectors']
    sites = sectors.drop_duplicates('site')[['site', 'role', 'x_m', 'y_m']].reset_index(drop=True)
    targets = pd.read_csv(D08 / 'inputs/targets.csv').set_index('site')
    ext = [g['xs'][0] / 1000, g['xs'][-1] / 1000, g['ys'][0] / 1000, g['ys'][-1] / 1000]

    # Serving-site agreement across the three azimuth draws (azimuth sensitivity).
    same = (res[701]['site'] == res[702]['site']) & (res[701]['site'] == res[703]['site'])

    def decorate(ax, title):
        ev = sites[sites.role == 'Evaluation']
        bu = sites[sites.role != 'Evaluation']
        ax.scatter(bu.x_m / 1000, bu.y_m / 1000, s=14, c='white', edgecolors='black', linewidths=.6, zorder=3)
        ax.scatter(ev.x_m / 1000, ev.y_m / 1000, s=30, marker='^', c='black', zorder=4)
        for r in ev.itertuples():
            ax.annotate(r.site[-3:], (r.x_m / 1000, r.y_m / 1000), xytext=(3, 3), textcoords='offset points', fontsize=7, zorder=5)
        ax.contour(g['xs'] / 1000, g['ys'] / 1000, g['eval'].astype(float), levels=[.5], colors='black', linewidths=.8, linestyles='--')
        ax.set_title(title, fontsize=10)
        ax.set_aspect('equal')
        ax.set_xlabel('Doğu (km)')
        ax.set_ylabel('Kuzey (km)')

    fig, axes = plt.subplots(2, 3, figsize=(17, 11))
    # (a) serving site
    codes, uniq = pd.factorize(g['site'].ravel())
    palette = list(plt.get_cmap('tab20').colors) + list(plt.get_cmap('tab20b').colors)
    cmap = ListedColormap(palette[:len(uniq)])
    axes[0][0].imshow(codes.reshape(g['site'].shape), origin='lower', extent=ext, cmap=cmap, interpolation='nearest')
    edges = (np.diff(g['cell'], axis=0, prepend=g['cell'][:1]) != 0) | (np.diff(g['cell'], axis=1, prepend=g['cell'][:, :1]) != 0)
    axes[0][0].imshow(np.ma.masked_where(~edges, edges), origin='lower', extent=ext, cmap=ListedColormap(['#333333']), interpolation='nearest', alpha=.6)
    decorate(axes[0][0], 'Hizmet veren saha (renk) ve sektör sınırları')
    # (b) RSRP
    norm = BoundaryNorm(RSRP_LEVELS, len(RSRP_COLORS))
    im = axes[0][1].imshow(g['rsrp'], origin='lower', extent=ext, cmap=ListedColormap(RSRP_COLORS), norm=norm, interpolation='nearest')
    cb = fig.colorbar(im, ax=axes[0][1], ticks=[(a + b) / 2 for a, b in zip([-130] + RSRP_LEVELS[1:-1], RSRP_LEVELS[1:-1] + [-80])], shrink=.8)
    cb.ax.set_yticklabels(RSRP_LABELS)
    cb.set_label('RSRP (dBm)')
    decorate(axes[0][1], 'RSRP — en güçlü sektör')
    # (c) SNR best case, (d) control SINR worst case
    snorm = BoundaryNorm(SINR_LEVELS, len(RSRP_COLORS))
    for ax, key, title in [(axes[0][2], 'snr', 'SINR üst sınır: komşular yayında değil (S/N)'),
                           (axes[1][0], 'ctrl', 'SINR alt sınır: bütün komşular yayında (kontrol kanalı)')]:
        im = ax.imshow(g[key], origin='lower', extent=ext, cmap=ListedColormap(RSRP_COLORS), norm=snorm, interpolation='nearest')
        cb = fig.colorbar(im, ax=ax, ticks=[-6, -1.5, 2.5, 7.5, 15], shrink=.8)
        cb.ax.set_yticklabels(SINR_LABELS)
        cb.set_label('SINR (dB)')
        decorate(ax, title)
    # (e) RSRQ
    im = axes[1][1].imshow(g['rsrq'], origin='lower', extent=ext, cmap='viridis', vmin=-20, vmax=-6, interpolation='nearest')
    fig.colorbar(im, ax=axes[1][1], shrink=.8).set_label('RSRQ (dB)')
    decorate(axes[1][1], 'RSRQ (ns-3 tanımı, yükten bağımsız)')
    # (f) azimuth sensitivity
    axes[1][2].imshow(same.astype(float), origin='lower', extent=ext, cmap=ListedColormap(['#e66101', '#f7f7f7']), interpolation='nearest')
    decorate(axes[1][2], 'Üç azimut örneğinde aynı saha hizmet veriyor mu?\n(turuncu: hayır)')
    fig.suptitle('Seçilen başlangıç senaryosu — ızgara kapsama haritaları (100 m, azimut örneği 42; kesikli çizgi: değerlendirme alanı, ana sahalara ≤ 6 km)', fontsize=12)
    fig.tight_layout()
    fig.savefig(HERE / 'kapsama_haritalari.png', dpi=130)
    plt.close(fig)

    # Area statistics in the evaluation area, all three draws.
    stats = {}
    for s, r in res.items():
        m = r['eval']
        stats[str(s)] = {'grid_points': int(m.sum()), 'area_km2': float(m.sum() * STEP * STEP / 1e6),
                         'rsrp_share': dict(zip(RSRP_LABELS, share(r['rsrp'], m, RSRP_LEVELS))),
                         'snr_share': dict(zip(SINR_LABELS, share(r['snr'], m, SINR_LEVELS))),
                         'ctrl_sinr_share': dict(zip(SINR_LABELS, share(r['ctrl'], m, SINR_LEVELS))),
                         'rsrp_median': float(np.median(r['rsrp'][m])), 'ctrl_median': float(np.median(r['ctrl'][m])),
                         'snr_median': float(np.median(r['snr'][m]))}
    ev_mask = res[701]['eval']
    stats['azimuth_same_serving_site_share_eval'] = float(same[ev_mask].mean())
    # Serving area per evaluation site in the evaluation area (draw 701).
    area = pd.Series(g['site'][g['eval']]).value_counts() * STEP * STEP / 1e6
    stats['serving_area_km2_main'] = {k: float(v) for k, v in area.items()}
    # Grid RSRP at each evaluation site's own serving area vs Experia target (site-level, descriptive).
    comp = {}
    for site in targets.index:
        sel = (g['site'] == site) & g['eval']
        comp[site] = {'grid_median_rsrp_in_serving_area': float(np.median(g['rsrp'][sel])) if sel.any() else None,
                      'experia_rsrp': float(targets.loc[site, 'rsrp_target'])}
    stats['site_rsrp_grid_vs_experia'] = comp
    (HERE / 'coverage_stats.json').write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding='utf-8')

    # Interactive map: PNG overlays on the project's offline-capable Leaflet background.
    lat_c, lon_c = to_latlon(np.array([g['xs'][0], g['xs'][-1]]), np.array([g['ys'][0], g['ys'][-1]]))
    bounds = [[float(lat_c[0]), float(lon_c[0])], [float(lat_c[1]), float(lon_c[1])]]
    m = folium.Map(location=[LAT0, LON0], zoom_start=11, tiles=None, control_scale=True)
    add_resilient_background(m, LAT0, LON0)
    layers = [('RSRP (dBm)', g['rsrp'], RSRP_LEVELS, RSRP_COLORS, True),
              ('SINR alt sınır (bütün komşular yayında)', g['ctrl'], SINR_LEVELS, RSRP_COLORS, False),
              ('SINR üst sınır (komşular yayında değil)', g['snr'], SINR_LEVELS, RSRP_COLORS, False)]
    for name, val, lv, cols, show in layers:
        rgba = np.zeros(val.shape + (4,))
        idx = np.digitize(val, lv[1:-1])
        for i, c in enumerate(cols):
            rgba[idx == i, :3] = matplotlib.colors.to_rgb(c)
        rgba[..., 3] = .55
        folium.raster_layers.ImageOverlay(np.flipud(rgba), bounds=bounds, name=name, show=show,
                                          interactive=False, cross_origin=False, zindex=2).add_to(m)
    rgb = cmap(codes.reshape(g['site'].shape))
    rgb[..., 3] = .45
    rgb[edges] = [0.2, 0.2, 0.2, .8]
    folium.raster_layers.ImageOverlay(np.flipud(rgb), bounds=bounds, name='Hizmet veren saha / sektör sınırları', show=False,
                                      interactive=False, zindex=2).add_to(m)
    lat_s, lon_s = to_latlon(sites.x_m.to_numpy(), sites.y_m.to_numpy())
    fg = folium.FeatureGroup(name='Sahalar').add_to(m)
    for r, la, lo in zip(sites.itertuples(), lat_s, lon_s):
        tip = f'{r.site} — {"ana" if r.role == "Evaluation" else "komşu"}'
        if r.site in targets.index:
            tip += f' — Experia RSRP {targets.loc[r.site, "rsrp_target"]:.1f} dBm, SINR {targets.loc[r.site, "sinr_target"]:.1f} dB'
        folium.CircleMarker([la, lo], radius=6 if r.role == 'Evaluation' else 4, color='black', weight=1,
                            fill=True, fill_color='#0072b2' if r.role == 'Evaluation' else '#d55e00', fill_opacity=1,
                            tooltip=tip).add_to(fg)
    folium.Marker([39.2461, 28.0697], tooltip='10 Ağustos 2025 deprem merkezi (referans)',
                  icon=folium.DivIcon(html='<div style="font-size:18px;color:#b2182b">✱</div>')).add_to(m)
    legend = ('<div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:white;padding:8px 10px;'
              'border:1px solid #999;font:12px sans-serif">'
              '<b>RSRP (dBm)</b> / <b>SINR (dB)</b><br>' +
              ''.join(f'<span style="display:inline-block;width:12px;height:12px;background:{c};margin-right:4px"></span>'
                      f'{a} / {b}<br>' for c, a, b in zip(RSRP_COLORS, RSRP_LABELS, SINR_LABELS)) +
              '<i>Varsayımsal senaryo; operatör kapsama haritası değildir.</i></div>')
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(str(HERE / 'kapsama_haritasi.html'))
    print(json.dumps({k: v for k, v in stats.items() if k != 'site_rsrp_grid_vs_experia'}, indent=1, ensure_ascii=False)[:3000])
    print(json.dumps(stats['site_rsrp_grid_vs_experia'], indent=1))


if __name__ == '__main__':
    main()
