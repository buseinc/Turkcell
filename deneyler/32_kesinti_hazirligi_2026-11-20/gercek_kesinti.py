"""Windows: step 4 - the real 28 Oct 2025 outage of one 482 cell (KPI) next to the fast model.

KPI facts (deneyler/09 kpi_cells.csv.gz, 08:00-21:59 of 28 Oct vs the same hours of the normal days before
26 Oct): site 482 has 2 KPI cells; CELL_006252 was off all day, CELL_006253 stayed on.
What the KPI can and cannot tell:
- users of the remaining 482 cell vs its normal level -> did the same site absorb the lost cell's users?
- users of 443+441 and of the other evaluation sites vs normal -> neighbour increase, but 443/441 rose far more
  than 482 lost while the other sites stayed normal, so the cause cannot be attributed to 482 alone.
Model counterpart (predeclared): the fast model has 3 sectors at 482 (azimuths unknown, 3 draws). Each
482 sector is switched off in turn (27 Oct earthquake load, placement A, 10 LOS draws per placement); the
users it served are followed: share now on another 482 sector, on another site, without service.
"""
from pathlib import Path
import datetime as dt
import json

import numpy as np
import pandas as pd

import senaryo as sc

HERE = Path(__file__).resolve().parent
U = sc.U


def kpi_facts():
    k = sc.kpi()
    k['h'], k['d'] = k.DATETIME.dt.hour, k.DATETIME.dt.date
    k = k[(k.h >= 8) & (k.h <= 21)]
    out_day = dt.date(2025, 10, 28)
    normal = [d for d in k.d.unique() if d < dt.date(2025, 10, 26)]

    def users(sel, days):
        x = k[sel & k.d.isin(days)]
        return float(x.groupby(['d', 'h', 'CELL'])[U].mean().groupby(['d', 'h']).sum().mean())
    s482 = k.site == 'SITE_000482'
    f = {'482_both_cells_normal': users(s482, normal),
         '482_lost_cell_normal': users(k.CELL == 'CELL_006252', normal),
         '482_remaining_cell_normal': users(k.CELL == 'CELL_006253', normal),
         '482_remaining_cell_outage': users(k.CELL == 'CELL_006253', [out_day]),
         '443_441_normal': users(k.site.isin(['SITE_000443', 'SITE_000441']), normal),
         '443_441_outage_day': users(k.site.isin(['SITE_000443', 'SITE_000441']), [out_day]),
         'other_eval_normal': users(k.site.isin(['SITE_000440', 'SITE_000130', 'SITE_000296', 'SITE_000444', 'SITE_000554']), normal),
         'other_eval_outage_day': users(k.site.isin(['SITE_000440', 'SITE_000130', 'SITE_000296', 'SITE_000444', 'SITE_000554']), [out_day])}
    f['remaining_cell_absorbed_share_of_lost'] = (f['482_remaining_cell_outage'] - f['482_remaining_cell_normal'])/f['482_lost_cell_normal']
    f['443_441_increase'] = f['443_441_outage_day'] - f['443_441_normal']
    return f


def model():
    acc = {'same_site': [], 'other_site': [], 'no_service': []}
    for az in sc.AZ:
        b = sc.Builder(az, '2025-10-27')
        cells482 = np.where(b.sec.site.to_numpy() == 'SITE_000482')[0]
        for p in range(3):
            rng = np.random.default_rng(4000 + az*10 + p)
            ues = b.place('A', rng)
            net = b.network(ues)
            los = [net.draw_los(rng) for _ in range(10)]
            iv = b.calibrate_interval(net, los[:3])
            size, inter = np.full(len(ues), 512.0), np.full(len(ues), iv)
            for L in los:
                base = sc.hm.solve(net, L, size, inter)
                for c in cells482:
                    on = np.ones(len(b.sec), bool)
                    on[c] = False
                    r = sc.hm.solve(net, L, size, inter, cell_on=on)
                    moved = base['serving'] == c
                    if not moved.any():
                        continue
                    ns = r['cqi'][moved] == 0
                    same = np.isin(r['serving'][moved], cells482) & ~ns
                    acc['same_site'].append(float(same.mean()))
                    acc['other_site'].append(float((~same & ~ns).mean()))
                    acc['no_service'].append(float(ns.mean()))
    return {k: [float(np.mean(v)), float(np.percentile(v, 5)), float(np.percentile(v, 95))] for k, v in acc.items()}


def main():
    f = kpi_facts()
    print(json.dumps({k: round(v, 2) for k, v in f.items()}, indent=1))
    m = model()
    print(json.dumps(m, indent=1))
    (HERE/'gercek_kesinti.json').write_text(json.dumps({'rule': __doc__, 'kpi': f, 'model_one_482_sector_off': m},
                                                       indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
