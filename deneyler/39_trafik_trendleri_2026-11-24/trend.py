"""Windows: daily traffic trends from KPI, following KURALLAR.md.
Usage: python trend.py <name>   (reads kpi_<name>.csv.gz, writes trend_<name>.json, trend_<name>.png,
yuk_saatleri_<name>.csv.gz [per-cell load at the 3 representative hours, operator-derived, local only])."""
from pathlib import Path
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
P = HERE.parent.parent/'ana_proje'
A, U = 'EUtranCell_Availability_PC_ERI', 'Avg_Sim_RRC_Connected_User_Num_ERI'
PRB, VOL = 'DL_PRB_Util_%_ERI', 'DLTRF_VOLUME_MBYTE_ERI'
REGIONS = {'sehir': {'Balıkesir merkez': ['DISTRICT_0001', 'DISTRICT_0014'], 'Bandırma': ['DISTRICT_0004']}}
WINDOWS = {'Gece': (3, 5), 'Sabah gidiş': (7, 9), 'Mesai / okul': (9, 16), 'Akşam dönüş': (16, 19), 'Akşam': (19, 23)}
LIMIT = 0.2
NAMES = {'G1 hafta içi, okul açık': 'hafta içi (pazartesi), okul açık', 'G2 hafta sonu, okul açık': 'hafta sonu, okul açık (26 Eki)',
         'G3 hafta sonu, yaz': 'hafta sonu, yaz (Ağustos)', 'G4 deprem sonrası': 'deprem sonrası (20:00 sıçraması: 10 Ağu depremi)'}


def ts(s):
    return pd.Timestamp(s)


# day groups: list of (date, first slot, last slot exclusive) ; None = whole day
G1 = [('2025-10-20', None, None), ('2025-11-03', None, None), ('2025-10-27', None, '2025-10-27 22:45')]
G2 = [('2025-10-26', None, None)]
G3_BASE = [('2025-08-03', None, None), ('2025-08-09', None, None), ('2025-08-10', None, '2025-08-10 19:45')]
G3_17 = ('2025-08-17', None, None)
G4 = [('2025-08-10', '2025-08-10 19:45', None), ('2025-08-11', None, None), ('2025-10-27', '2025-10-27 22:45', None),
      ('2025-10-28', None, None)]


def day_series(k, day):
    """Per 15-min slot (minutes since midnight): mean over available cells of users, PRB, volume."""
    d, a, b = day
    x = k[k.DATETIME.dt.date == ts(d).date()]
    if a:
        x = x[x.DATETIME >= ts(a)]
    if b:
        x = x[x.DATETIME < ts(b)]
    g = x.groupby(x.DATETIME.dt.hour*60 + x.DATETIME.dt.minute)
    return pd.DataFrame({'users': g[U].mean(), 'prb': g[PRB].mean(), 'vol': g[VOL].mean(), 'cells': g.CELL.nunique()})


def group_profile(k, days):
    s = [day_series(k, d) for d in days]
    return pd.concat(s).groupby(level=0).mean().reindex(range(0, 1440, 15))


def hourly(series):
    return series.groupby(series.index//60).mean()


def shape_diff(a, b, hours=None):
    """Max abs difference of hourly shapes, each normalised by its mean over the common hours."""
    ha, hb = hourly(a), hourly(b)
    h = ha.index.intersection(hb.index) if hours is None else hours
    ha, hb = ha.loc[h]/ha.loc[h].mean(), hb.loc[h]/hb.loc[h].mean()
    return float((ha - hb).abs().max())


def peak(series):
    """Start of the 1-hour window with the highest mean (slot label)."""
    r = series.rolling(4).mean().shift(-3)
    return int(r.idxmax()), float(r.max())


def hhmm(m):
    return f'{m//60:02d}:{m % 60:02d}'


def win_mean(series, w):
    a, b = WINDOWS[w]
    return float(series[(series.index >= a*60) & (series.index < b*60)].mean())


def analyse(k, label):
    out = {}
    # condition: 17 Aug
    d3, d9, d17 = (day_series(k, d).users for d in [G3_BASE[0], G3_BASE[1], G3_17])
    base = pd.concat([d3, d9], axis=1).mean(axis=1)
    diff17 = shape_diff(d17, base)
    g3 = G3_BASE + ([G3_17] if diff17 <= LIMIT else [])
    out['aug17_max_shape_diff'] = round(diff17, 3)
    out['aug17_in_G3'] = diff17 <= LIMIT
    # condition: three Mondays (common hours 0-21)
    mon = {d[0]: day_series(k, d).users for d in G1}
    hrs = list(range(0, 22))
    pairs = {f'{a} / {b}': round(shape_diff(mon[a], mon[b], hrs), 3) for i, a in enumerate(mon) for b in list(mon)[i + 1:]}
    out['monday_pair_max_shape_diff'] = pairs
    out['mondays_consistent'] = all(v <= LIMIT for v in pairs.values())
    groups = {'G1 hafta içi, okul açık': G1, 'G2 hafta sonu, okul açık': G2, 'G3 hafta sonu, yaz': g3, 'G4 deprem sonrası': G4}
    prof = {g: group_profile(k, d) for g, d in groups.items()}
    res = {}
    for g, p in prof.items():
        u = p.users
        day_mean = float(u.mean())
        pk, pv = peak(u)
        pp, _ = peak(p.prb)
        r = {'users_per_cell_day_mean': round(day_mean, 2), 'peak_hour_users': hhmm(pk), 'peak_users_per_cell': round(pv, 2),
             'peak_hour_prb': hhmm(pp), 'prb_day_mean': round(float(p.prb.mean()), 3),
             'window_over_night': {w: round(win_mean(u, w)/win_mean(u, 'Gece'), 2) for w in WINDOWS},
             'window_users_per_cell': {w: round(win_mean(u, w), 2) for w in WINDOWS},
             'morning_rise_pct_of_day_mean': round(100*(u.loc[9*60] - u.loc[7*60])/day_mean, 1),
             'hourly_shape': [round(v, 3) for v in (hourly(u)/day_mean).tolist()]}
        res[g] = r
    out['groups'] = res
    # summer vs autumn weekend
    out['G3_vs_G2_weekend_max_shape_diff'] = round(shape_diff(prof['G3 hafta sonu, yaz'].users, prof['G2 hafta sonu, okul açık'].users), 3)
    # day / evening cells (G1)
    x = pd.concat([k[(k.DATETIME.dt.date == ts(d).date()) & ((k.DATETIME < ts(b)) if b else True)] for d, _, b in G1])
    m = x.DATETIME.dt.hour
    day_c = x[(m >= 9) & (m < 16)].groupby('CELL')[U].mean()
    eve_c = x[(m >= 19) & (m < 23)].groupby('CELL')[U].mean()
    ratio = (day_c/eve_c).replace([np.inf], np.nan).dropna()
    kind = pd.cut(ratio, [-np.inf, 0.8, 1.2, np.inf], labels=['akşam', 'karışık', 'gündüz'], right=False)
    out['cells_classified'] = int(len(ratio))
    out['cell_share'] = {str(c): round(float(v), 3) for c, v in kind.value_counts(normalize=True).items()}
    out['cell_ratio_median'] = round(float(ratio.median()), 2)
    # representative hours (G1)
    u1 = prof['G1 hafta içi, okul açık'].users
    mor = u1[(u1.index >= 7*60) & (u1.index < 9*60)]
    g1 = res['G1 hafta içi, okul açık']
    out['simulation_hours'] = {'sabah_gidis': hhmm(int(mor.idxmax())), 'en_kalabalik': g1['peak_hour_users'],
                               'kapasite_zirvesi': g1['peak_hour_prb']}
    return out, prof, ratio


def plot(results, profs, ratios, k, name):
    co = pd.read_excel(P/'cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('cell').set_index('cell')
    n = len(results)
    fig, ax = plt.subplots(n, 2, figsize=(14, 4.8*n), gridspec_kw={'width_ratios': [2.2, 1]}, squeeze=False)
    colors = {'G1 hafta içi, okul açık': '#1f5fa8', 'G2 hafta sonu, okul açık': '#2e9e5b', 'G3 hafta sonu, yaz': '#e08a1e',
              'G4 deprem sonrası': '#b03030'}
    for i, (label, res) in enumerate(results.items()):
        a = ax[i, 0]
        for w, (s, e) in WINDOWS.items():
            a.axvspan(s, e, color='0.93' if list(WINDOWS).index(w) % 2 else '0.86', zorder=0)
            a.text((s + e)/2, 1.0, w, transform=a.get_xaxis_transform(), ha='center', va='bottom', fontsize=8)
        for g, p in profs[label].items():
            a.plot(p.index/60, p.users, color=colors[g], lw=2.2 if g.startswith('G1') else 1.4,
                   ls='--' if g.startswith('G4') else '-', label=NAMES[g])
        rep = res['simulation_hours']
        g1 = res['groups']['G1 hafta içi, okul açık']
        top = a.get_ylim()[1]
        for t_, txt in [(rep['sabah_gidis'], 'sabah gidişin sonu'), (g1['peak_hour_users'], 'günün en kalabalık saati')]:
            h, mi = map(int, t_.split(':'))
            a.axvline(h + mi/60, color='#1f5fa8', lw=0.8, ls=':')
            a.annotate(f'{txt}\n{t_}', (h + mi/60, top*(0.9 if h > 12 else 0.8)), fontsize=8, color='#1f5fa8', ha='right' if h > 12 else 'left')
        a.set_xlim(0, 24)
        a.set_xticks(range(0, 25, 2))
        a.set_xlabel('saat (Türkiye saati)')
        a.set_ylabel('hücre başına ortalama bağlı kullanıcı')
        a.set_title(f"{label}: gün içinde hücre başına bağlı kullanıcı\n(hafta içi kapasite kullanımı en yüksek: {g1['peak_hour_prb']}; bağlı kişide ayrı akşam zirvesi yok)", loc='left', pad=18, fontsize=10)
        a.legend(fontsize=8, loc='lower center')
        b = ax[i, 1]
        r = ratios[label]
        c = co.reindex(r.index).assign(lr=np.log(r.to_numpy()))
        s = c.groupby('site').agg(lat=('lat', 'mean'), lon=('lon', 'mean'), lr=('lr', 'mean'), n=('lr', 'size'))
        s['ratio'] = np.exp(s.lr)
        lat0, lon0 = float(s.lat.median()), float(s.lon.median())
        s['x'] = (s.lon - lon0)*111.32*np.cos(np.radians(lat0))
        s['y'] = (s.lat - lat0)*110.57
        col = np.where(s.ratio >= 1.2, '#d0451b', np.where(s.ratio < 0.8, '#3a6fb0', '#bbbbbb'))
        b.scatter(s.x, s.y, c=col, s=12 + 6*s.n, edgecolor='k', lw=0.3, alpha=0.85)
        sh = res['cell_share']
        b.set_title(f"Harita: her daire bir saha (büyüklük = hücre sayısı)\n"
                    f"hücrelerin %{100*sh.get('gündüz', 0):.0f}'i gündüz, %{100*sh.get('akşam', 0):.0f}'i akşam kalabalık",
                    fontsize=9)
        b.scatter([], [], c='#d0451b', label='gündüz kalabalık (09-16, akşamdan ≥ %20 fazla)')
        b.scatter([], [], c='#3a6fb0', label='akşam kalabalık (19-23, gündüzden ≥ %20 fazla)')
        b.scatter([], [], c='#bbbbbb', label='ikisi yakın')
        b.legend(fontsize=7, loc='lower left')
        b.set_xlabel('batı ← merkezden uzaklık (km) → doğu')
        b.set_ylabel('güney ← (km) → kuzey')
        b.set_aspect('equal')
        b.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE/f'trend_{name}.png', dpi=130)


def main():
    name = sys.argv[1]
    k = pd.read_csv(HERE/f'kpi_{name}.csv.gz', parse_dates=['DATETIME'])
    k = k[k[A] >= 0.99]
    results, profs, ratios = {}, {}, {}
    for label, dists in REGIONS[name].items():
        kr = k[k.district.isin(dists)]
        results[label], profs[label], ratios[label] = analyse(kr, label)
        results[label]['cells'] = int(kr.CELL.nunique())
        print(label, json.dumps({x: y for x, y in results[label].items() if x != 'groups'}, ensure_ascii=False), flush=True)
        for g, r in results[label]['groups'].items():
            print('  ', g, {x: y for x, y in r.items() if x != 'hourly_shape'})
        # per-cell load at representative hours (G1 days), local only
        rep = results[label]['simulation_hours']
        rows = []
        for d, _, b in G1:
            x = kr[kr.DATETIME.dt.date == ts(d).date()]
            for key, hm in rep.items():
                t0 = ts(f'{d} {hm}')
                s = x[(x.DATETIME >= t0) & (x.DATETIME < t0 + pd.Timedelta('1h'))]
                rows.append(s.groupby('CELL')[[U, PRB]].mean().assign(hour=f'{key} {hm}', day=d))
        pd.concat(rows).reset_index().groupby(['hour', 'CELL'])[[U, PRB]].mean().reset_index().to_csv(
            HERE/f'yuk_saatleri_{name}_{label.split()[0].lower().replace("ı", "i")}.csv.gz', index=False)
    (HERE/f'trend_{name}.json').write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding='utf-8')
    plot(results, profs, ratios, k, name)
    print('written')


if __name__ == '__main__':
    main()
