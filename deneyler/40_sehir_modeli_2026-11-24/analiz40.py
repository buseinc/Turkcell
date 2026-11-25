"""Windows: tables and figure for model40.json (Balıkesir city model vs Experia). Writes analiz40.json, sehir_modeli.png."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
TS_M = 4.88
HOUR_NAMES = {'sabah_gidis': 'sabah 08:45', 'en_kalabalik': 'en kalabalık 15:30', 'kapasite_zirvesi': 'kapasite zirvesi 21:15'}
EHOUR = {'sabah_gidis': 9, 'en_kalabalik': 16, 'kapasite_zirvesi': 21}
VNAMES = {'ana_model': 'ana model (saha başına şehir/kırsal)', 'tek_ortam_sehir': 'bütün bölge şehir',
          'tek_ortam_kirsal': 'bütün bölge kırsal', 'bina_ici_yok': 'bina içi ve araba kaybı yok', 'yari_yeni_bina': 'şehirde yarı eski yarı yeni bina',
          'surekli_yayin_0': 'sürekli yayın %0', 'surekli_yayin_9_5': 'sürekli yayın %9,5', 'egim_10': 'anten eğimi 10°'}
BINS = [100, 200, 300, 500, 700, 1000, 1500, 2000, 3000, 5000, 15000]


def binned(d, v):
    c = pd.cut(d, BINS)
    g = pd.DataFrame({'c': c, 'v': v}).groupby('c', observed=True).v
    mid = np.sqrt([b.left*b.right for b in g.median().index])
    return mid, g.median().to_numpy(), g.size().to_numpy()


def main():
    res = json.loads((HERE/'model40.json').read_text(encoding='utf-8'))
    rows = []
    for v, r in res.items():
        for h, s in r['summary'].items():
            rows.append({'variant': v, 'hour': h, **s})
    t = pd.DataFrame(rows)
    print(t[['variant', 'hour', 'unmatched_share', 'served_by_own_site_share', 'sinr_abs', 'rsrp_abs', 'sinr_bias', 'rsrp_bias', 'sinr_abs_matched_only', 'rsrp_abs_matched_only', 'rsrp_bias_matched_only', 'no_service_share']]
          .round(2).to_string())
    # distance curves: Experia (core sites, weekdays, hour 16) vs model users at 15:30
    sites = pd.read_csv(HERE/'inputs/sites.csv')
    core = set(sites.site[sites.role == 'core'])
    e = pd.read_csv(HERE/'experia_40.csv.gz', parse_dates=['DATE_ID'])
    e = e[(e.DATE_ID.dt.weekday < 5) & e.site.isin(core)].dropna(subset=['AVG(TAAVG)'])
    curves = {}
    eh = e[e.HOUR_ID == EHOUR['en_kalabalik']]
    curves['Experia'] = binned((eh['AVG(TAAVG)']*TS_M).clip(100, 15000), eh['AVG(MED_SERVINGRSRPMEDIAN)'])
    curves['Experia_sinr'] = binned((eh['AVG(TAAVG)']*TS_M).clip(100, 15000), eh['AVG(MED_SINRMEDIAN)'])
    keys = [v for v in ['ana_model', 'tek_ortam_sehir', 'bina_ici_yok'] if v in res]  # side variants may still be running
    for v in keys:
        u = pd.read_csv(HERE/f'users_{v}.csv.gz')
        u = u[u.hour == 'en_kalabalik']
        curves[v] = binned(u.distance_m, u.rsrp)
        curves[v + '_sinr'] = binned(u.distance_m, u.sinr)
    near = {k: float(curves[k][1][0] - curves['Experia'][1][0]) for k in keys}
    far = {k: float(curves[k][1][-1] - curves['Experia'][1][-1]) for k in keys}
    # site errors by distance from the centre (15:30, mean over draws)
    sd = sites.set_index('site').d_m/1000
    by_ring = {}
    for v in [k for k in ['ana_model', 'tek_ortam_sehir'] if k in res]:
        rr = [x for x in res[v]['runs'] if x['hour'] == 'en_kalabalik']
        q = pd.DataFrame({'rsrp': pd.DataFrame([x['rsrp_by_site'] for x in rr]).mean(),
                          'sinr': pd.DataFrame([x['sinr_by_site'] for x in rr]).mean()})
        q['ring'] = pd.cut(sd.reindex(q.index), [0, 2, 4, 8]).astype(str)
        by_ring[v] = q.groupby('ring')[['rsrp', 'sinr']].median().round(1).to_dict('index')
        by_ring[v + '_n'] = q.groupby('ring').size().to_dict()
    # main model users: no service by indoor / distance
    u = pd.read_csv(HERE/'users_ana_model.csv.gz')
    u['ns'] = u.sinr < -6.7
    ns_by = {'indoor': round(float(u[u.indoor].ns.mean()), 3), 'outdoor': round(float(u[~u.indoor].ns.mean()), 3),
             'distance_le_1km': round(float(u[u.distance_m <= 1000].ns.mean()), 3),
             'distance_gt_2km': round(float(u[u.distance_m > 2000].ns.mean()), 3),
             'share_users_gt_2km': round(float((u.distance_m > 2000).mean()), 3)}
    out = {'table': t.round(3).to_dict('records'), 'site_error_by_ring_1530': by_ring, 'near_tower_rsrp_diff_db_100_200m': near,
           'far_rsrp_diff_db_5_15km': far, 'no_service_main_by': ns_by}
    (HERE/'analiz40.json').write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float), encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'table'}, ensure_ascii=False))

    fig, ax = plt.subplots(1, 3, figsize=(19, 5.6), gridspec_kw={'width_ratios': [1, 1.1, 1.2]})
    # 1: site scatter, main model, 15:30, mean over draws
    a = ax[0]
    m = res['ana_model']
    runs = [r for r in m['runs'] if r['hour'] == 'en_kalabalik']
    ds = pd.DataFrame([r['sinr_by_site'] for r in runs]).mean()
    dr = pd.DataFrame([r['rsrp_by_site'] for r in runs]).mean()
    a.add_patch(plt.Rectangle((-5, -3), 10, 6, color='#dcebdc', zorder=0))
    a.scatter(dr, ds, s=18, c='#1f5fa8')
    a.axhline(0, color='grey', lw=0.7); a.axvline(0, color='grey', lw=0.7)
    a.set_xlabel('sinyal gücü farkı, model − ölçüm (dB)\n(sağda: model güçlü)')
    a.set_ylabel('sinyal kalitesi farkı, model − ölçüm (dB)\n(yukarıda: model iyi)')
    inside = float(((ds.abs() <= 3) & (dr.abs() <= 5)).mean())
    a.set_title(f'Ana model, 15:30: her nokta bir saha\nyeşil kutu = iki sınırın da içi; sahaların %{100*inside:.0f}\'i içinde', fontsize=10)
    # 2: RSRP vs distance
    a = ax[1]
    for k, lab, st in [('Experia', 'gerçek ölçüm (Experia)', dict(color='k', lw=2.2)),
                       ('ana_model', 'ana model (saha başına şehir/kırsal)', dict(color='#1f5fa8', lw=1.8)),
                       ('tek_ortam_sehir', 'bütün bölge şehir', dict(color='#7a4fa0', lw=1.2, ls='-.')),
                       ('bina_ici_yok', 'herkes dışarıda', dict(color='#e08a1e', lw=1.4, ls='--'))]:
        if k not in curves:
            continue
        x, y, n = curves[k]
        a.plot(x, y, marker='o', ms=4, label=lab, **st)
    a.set_xscale('log')
    a.set_xlabel('kuleye uzaklık (m, logaritmik)')
    a.set_ylabel('sinyal gücü, RSRP (dBm)')
    a.set_title('Kuleye uzaklığa göre sinyal gücü (15:30, ortanca)\nkuleye yakında model güçlü kalıyor mu?', fontsize=10)
    a.legend(fontsize=8)
    a.grid(alpha=0.3)
    # 3: variants, mean abs difference averaged over hours
    a = ax[2]
    g = t.groupby('variant', sort=False)[['sinr_abs', 'rsrp_abs']].mean()
    yy = np.arange(len(g))
    a.barh(yy - 0.18, g.sinr_abs, height=0.36, color='#1f5fa8', label='sinyal kalitesi farkı (sınır 3 dB)')
    a.barh(yy + 0.18, g.rsrp_abs, height=0.36, color='#9ab', label='sinyal gücü farkı (sınır 5 dB)')
    a.axvline(3, color='#1f5fa8', ls=':', lw=1); a.axvline(5, color='#789', ls=':', lw=1)
    a.set_yticks(yy); a.set_yticklabels([VNAMES[v] for v in g.index]); a.invert_yaxis()
    a.set_xlabel('saha başına ortalama fark, model − ölçüm (dB, mutlak)')
    a.set_title('Ana model ve yan denemeler (3 saatin ortalaması)\nkısa çubuk = ölçüme daha yakın', fontsize=10)
    a.legend(fontsize=8, loc='lower right')
    fig.suptitle('Balıkesir merkez şehir modeli (mesafe düzeltmesi yok): model gerçek ölçüme ne kadar yakın?', fontsize=12)
    fig.tight_layout()
    fig.savefig(HERE/'sehir_modeli.png', dpi=130)


if __name__ == '__main__':
    main()
