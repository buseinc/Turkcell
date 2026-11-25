"""Windows, fast model. Real whole-site outage of SITE_000200 (27 Oct, KPI: 67 +- 12 % of the missing users appear on
the 6 nearest sites) against the ways of applying the distance correction (KURALLAR.md). Writes kesinti_200.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import duzeltme_sinama as z  # noqa: E402
h, alan, sc = z.h, z.alan, z.sc
SITE = 'SITE_000200'
KPI_VALUE, KPI_SD = 0.67, 0.12
VARIANTS = {'A (100% kullanıcıda)': 1.0, '%75': 0.75, '%50': 0.5, '%25': 0.25, 'S (0% kullanıcıda)': 0.0, 'C (bağlantı başına)': None}


def nearest_six():
    k = pd.concat([pd.read_csv(f, usecols=['site']).drop_duplicates() for f in z_files() if f.exists()]).site.unique()
    co = pd.read_excel(z.DEN.parent/'ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('site').set_index('site')
    s = [x for x in k if x in co.index]
    la, lo = co.lat.reindex(s).to_numpy(), co.lon.reindex(s).to_numpy()
    p = pd.DataFrame({'x': (lo - lo.mean())*111320*np.cos(np.radians(la.mean())), 'y': (la - la.mean())*110574}, index=s)
    d = np.hypot(p.x - p.x[SITE], p.y - p.y[SITE]).drop(SITE).sort_values()
    return list(d.index[:6]), d.iloc[:6].round(0).to_dict()


def z_files():
    return [z.DEN/'09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', z.D35/'kpi_cells.csv.gz', z.D35/'kpi_cells_balikesir.csv.gz']


def set_variant(net, p, k0, k1, on):
    if p is None:
        return z.apply(net, 'C', k0, k1)
    extra = net.ues['extra_loss_db'].to_numpy(float)
    base = net.fixed_db + extra[:, None]
    r = np.where(on[None, :], base - np.where(net.draw_los(), net.los_db, net.nlos_db), -np.inf)
    d = net.d2[np.arange(len(r)), r.argmax(1)]
    net.fixed_db = base - (p*extra + (1 - p)*z.corr(k0, k1, d))[:, None]
    return net


def main():
    plan = json.loads((z.D33/'plan.json').read_text(encoding='utf-8'))
    ues = pd.read_csv(z.D33/'inputs/ues_quake_42.csv')
    near, dist = nearest_six()
    pk, iv = np.full(len(ues), 512.0), np.full(len(ues), plan['udp_interval_ms'])
    home = ues.home_site.eq(SITE).to_numpy()
    rows = []
    for az in [42, 7, 99]:
        b = sc.Builder(az, plan['quake'])
        on = b.cells_on([SITE])
        cell_site = b.sec.site.to_numpy()
        for name, p in VARIANTS.items():
            net = set_variant(alan.Network34(b.sec, ues, 42), p, b.k0, b.k1, on)
            r = h.solve_f(net, pk, iv, on, z.F)
            ok = r['cqi'] != 0
            on_near = np.isin(cell_site[r['serving']], near)
            rows.append({'variant': name, 'az': az, 'on_6_nearest': float((ok & on_near)[home].mean()),
                         'service_elsewhere': float((ok & ~on_near)[home].mean()), 'no_service': float((~ok)[home].mean())})
            print(rows[-1], flush=True)
    d = pd.DataFrame(rows)
    mean = d.groupby('variant', sort=False)[['on_6_nearest', 'service_elsewhere', 'no_service']].mean()
    rng = d.groupby('variant', sort=False).on_6_nearest.agg(['min', 'max'])
    in_model = [s for s in near if s in set(ues.home_site) or s in set(b.sec.site)]
    out = {'site': SITE, 'users_in_model': int(home.sum()), 'kpi_on_6_nearest': KPI_VALUE, 'kpi_sd': KPI_SD, 'nearest_6_m': dist,
           'nearest_6_in_model': in_model, 'n_nearest_in_model': len(in_model), 'mean': mean.round(4).to_dict('index'),
           'range_on_6': rng.round(4).to_dict('index'), 'agrees_55_79': {k: bool(0.55 <= v <= 0.79) for k, v in mean.on_6_nearest.items()}, 'runs': rows}
    (HERE/'kesinti_200.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print('nearest 6', dist, '| in model', len(in_model), in_model)
    print((100*mean).round(1).to_string())
    print(out['agrees_55_79'])


if __name__ == '__main__':
    main()
