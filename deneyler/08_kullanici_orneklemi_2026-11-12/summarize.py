"""Windows: build SONUCLAR.md and the figure from result.json."""
from pathlib import Path
import json
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
M = ['rsrp', 'sinr', 'rsrq']
LABEL = {'rsrp': 'RSRP', 'sinr': 'SINR', 'rsrq': 'RSRQ'}
THRESHOLD = 0.5


def f(x, d=2):
    return '—' if x is None else f'{x:.{d}f}'.replace('.', ',')


def main():
    res = json.loads((HERE / 'result.json').read_text(encoding='utf-8'))
    assert res['completed']
    rows = res['results']
    sizes = sorted({r['ues'] for r in rows})
    seeds = sorted({r['case']['ue_seed'] for r in rows})
    by = {(r['case']['ue_seed'], r['ues']): r for r in rows}

    # Figure: MAE vs n, one line per draw, train/control x metric.
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.5), sharex=True)
    for i, split in enumerate(['training', 'control']):
        for j, m in enumerate(M):
            ax = axes[i][j]
            for s in seeds:
                ax.plot(sizes, [by[s, n][split]['mae_db'][m] for n in sizes], marker='o', label=f'örnek {s}')
            mean = [statistics.mean(by[s, n][split]['mae_db'][m] for s in seeds) for n in sizes]
            ax.plot(sizes, mean, color='black', lw=2.2, ls='--', label='ortalama')
            ax.set_xscale('log', base=2)
            ax.set_xticks(sizes, [str(n) for n in sizes])
            ax.set_title(f"{'Eğitim' if split == 'training' else 'Kontrol'} — {LABEL[m]} MAE (dB)")
            ax.grid(alpha=.3)
            if i == 1:
                ax.set_xlabel('Sanal kullanıcı sayısı (toplam yük sabit)')
    axes[0][0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / 'kullanici_orneklemi.png', dpi=150)

    L = ['# Kullanıcı örneklemi duyarlılığı: 64 → 128 → 256 — 12 Kasım 2026', '',
         'Soru: Seçilen radyo ayarının Experia ile karşılaştırması, saha başına az sayıda sanal kullanıcıya mı bağlı?',
         '',
         '**Sabit tutulanlar:** seçilen ayar (2–6 km kümeler, 120°, n=3, 49 dBm, NF 9 dB, gölgeleme yok, Band 3 / 20 MHz, '
         'mixed CQI, 3 sektör), güncel envanterden 24 saha (hocanın 8+8 sahası dahil), üç anten-yönü/kullanıcı örneği '
         '(42/701, 7/702, 99/703), 4 s koşu, 1 s ısınma. **Değişen:** yalnız kullanıcı sayısı. Örnekler iç içe: 128 kullanıcının '
         'ilk 64\'ü önceki 64 kullanıcıdır, 256\'nın ilk 128\'i de 128\'liktir. **Toplam sunulan yük sabit:** kullanıcı başına UDP aralığı '
         '50 / 100 / 200 ms (toplam ≈ 5,24 Mbit/s). Ayar yeniden seçilmedi. Kural koşulardan önce [plan.json](plan.json) içine yazıldı.', '']

    L += ['## 1. Bu PC\'de yeniden üretim', '',
          '64 kullanıcılık üç koşu, 12 Kasım koşularıyla (deney 07) aynı kullanıcılarda karşılaştırıldı:', '',
          '| Örnek | Eşli UE | Aynı sektör | RSRP / SINR / RSRQ q95 fark (dB) |', '|---|---:|---:|---|']
    for s in seeds:
        p = by[s, 64]['reproduction']
        L.append(f"| {s} | {p['paired_ues']} | %{p['same_serving_sector_fraction'] * 100:.0f} | "
                 f"{f(p['rsrp_q95_abs_change_db'], 3)} / {f(p['sinr_q95_abs_change_db'], 3)} / {f(p['rsrq_q95_abs_change_db'], 3)} |")
    L += ['']

    L += ['## 2. Experia\'ya göre hata — kullanıcı sayısına göre', '',
          'Üç örneğin ortalaması ± standart sapması (dB; düşük daha yakın). ± üç örnek arası yayılımdır, güven aralığı değildir.', '',
          '| Kullanıcı | Eğitim RSRP | Eğitim SINR | Eğitim RSRQ | Kontrol RSRP | Kontrol SINR | Kontrol RSRQ |', '|---:|---:|---:|---:|---:|---:|---:|']
    spread = {}
    for n in sizes:
        cells = []
        for split in ['training', 'control']:
            for m in M:
                v = [by[s, n][split]['mae_db'][m] for s in seeds]
                spread[split, m, n] = statistics.stdev(v)
                cells.append(f'{f(statistics.mean(v))} ± {f(statistics.stdev(v))}')
        L.append(f'| {n} | ' + ' | '.join(cells) + ' |')
    L += ['', '![Kullanıcı sayısına göre hata](kullanici_orneklemi.png)', '',
          'Örnek bazında (eğitim / kontrol MAE, RSRP · SINR · RSRQ):', '',
          '| Örnek | Kullanıcı | Eğitim | Kontrol | Bağlı / veri alan | Süre (s) |', '|---|---:|---|---|---:|---:|']
    for s in seeds:
        for n in sizes:
            r = by[s, n]
            t = lambda sp: ' · '.join(f(r[sp]['mae_db'][m]) for m in M)
            L.append(f"| {s} | {n} | {t('training')} | {t('control')} | {r['connected_ues']}/{r['ues']} · {r['ues_with_dl']}/{r['ues']} | {r['wall_seconds']:.0f} |")
    L += ['']

    L += ['## 3. Değerlendirme sahası başına kullanıcı', '',
          'Sahaya hizmet sektörü üzerinden bağlanan ve ölçüm üreten kullanıcı sayısı; üç örnekteki en küçük değer.', '',
          '| Saha | ' + ' | '.join(f'n={n}' for n in sizes) + ' |', '|---|' + '---:|' * len(sizes)]
    sites = list(by[seeds[0], sizes[0]]['ues_per_evaluation_site'])
    for site in sites:
        L.append(f'| {site} | ' + ' | '.join(str(min(by[s, n]['ues_per_evaluation_site'][site] for s in seeds)) for n in sizes) + ' |')
    L += ['']

    L += ['## 4. İlk 64 kullanıcının kendisi değişti mi?', '',
          'Aynı konumdaki kullanıcılar küçük ve büyük koşuda eşleştirildi. Fark, yalnız kullanıcı başına yük ve zamanlama '
          'değişiminden gelir; konum ve ayar aynıdır.', '',
          '| Örnek | Geçiş | Eşli UE | Aynı sektör | RSRP q95 | SINR q95 | RSRQ q95 | SINR ort. değişim |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for p in res['paired_original_ues']:
        L.append(f"| {p['ue_seed']} | {p['from_ues']}→{p['to_ues']} | {p['paired_ues']} | %{p['same_serving_sector_fraction'] * 100:.0f} | "
                 f"{f(p['rsrp_q95_abs_change_db'])} | {f(p['sinr_q95_abs_change_db'])} | {f(p['rsrq_q95_abs_change_db'])} | {f(p['sinr_mean_change_db'])} |")
    L += ['']

    # Predeclared adequacy rule.
    a, b = sizes[-2], sizes[-1]
    checks = []
    for s in seeds:
        for split in ['training', 'control']:
            for m in M:
                d = abs(by[s, b][split]['mae_db'][m] - by[s, a][split]['mae_db'][m])
                checks.append((s, split, m, d))
    worst = max(checks, key=lambda x: x[3])
    rule1 = all(d <= THRESHOLD for *_, d in checks)
    rule2 = all(spread[sp, m, b] <= spread[sp, m, sizes[0]] + 1e-9 for sp in ['training', 'control'] for m in M)
    fails = [c for c in checks if c[3] > THRESHOLD]
    L += ['## 5. Önceden yazılan yeterlilik ölçütü', '',
          f'- **{a}→{b} geçişinde her örnek, her bölüm ve her metrikte MAE değişimi ≤ {f(THRESHOLD, 1)} dB:** '
          f"{'geçti' if rule1 else 'geçmedi'}. En büyük değişim {f(worst[3])} dB "
          f"(örnek {worst[0]}, {'eğitim' if worst[1] == 'training' else 'kontrol'} {LABEL[worst[2]]})."
          + ('' if rule1 else f' Eşiği aşan {len(fails)}/{len(checks)} durum.'),
          f"- **Örnekler arası yayılım {b} kullanıcıda {sizes[0]}'e göre büyümüyor:** {'geçti' if rule2 else 'geçmedi'}.", '']
    for sp in ['training', 'control']:
        L.append(f"  - {'Eğitim' if sp == 'training' else 'Kontrol'} std (dB), " + '; '.join(
            f"{LABEL[m]} " + ' → '.join(f(spread[sp, m, n]) for n in sizes) for m in M))
    import csv
    with (HERE / 'inputs/targets.csv').open(encoding='utf-8-sig') as fh:
        targets = {t['site']: t for t in csv.DictReader(fh)}
    L += ['', '## 6. Saha bazında işaretli hata (simülasyon − Experia)', '',
          'Üç örneğin ortalaması (dB). Pozitif: simülasyon daha yüksek. Ortalama mutlak hata bu yönü gizler.', '',
          '| Saha | Bölüm | ' + ' | '.join(f'SINR n={n}' for n in sizes) + ' | ' + ' | '.join(f'RSRP n={n}' for n in sizes) + ' |',
          '|---|---|' + '---:|' * (2 * len(sizes))]
    for site, t in targets.items():
        cells = []
        for m in ['sinr', 'rsrp']:
            for n in sizes:
                v = [by[s, n]['sites'][site][m] - float(t[m + '_target']) for s in seeds if by[s, n]['sites'].get(site, {}).get(m) is not None]
                cells.append(f'{statistics.mean(v):+.1f}'.replace('.', ',') if v else '—')
        L.append(f"| {site} | {'eğitim' if t['split'] == 'train' else 'kontrol'} | " + ' | '.join(cells) + ' |')
    L += ['', '## Yorum', '',
          '- **İlk 64 kullanıcı değişmedi.** Aynı konumdaki kullanıcılarda RSRP/RSRQ farkı 0, hizmet sektörü %100 aynı, SINR q95 ≈ 1 dB '
          've altı. Yani hata değişimleri yük değişiminden değil, **yeni eklenen kullanıcı konumlarından** geliyor.',
          '- **64 kullanıcılık sonuçlar örnekleme bağımlıymış.** Ölçüt geçmedi: 128→256 geçişinde bazı saha ortalamaları hâlâ '
          'birkaç dB oynuyor. Saha değeri, aktif sektörlerin eşit ağırlıklı ortalaması olduğundan yeni bir sektöre ilk kullanıcıların '
          'düşmesi saha ortalamasını sıçratabiliyor. SITE_000443 ve SITE_000296 256 kullanıcıda bile az örnekli.',
          '- **RSRP kontrol hatası örneklem büyüdükçe azaldı** ve yayılımı daraldı; RSRQ yaklaşık sabit kaldı.',
          '- **SINR için daha düşük 64-kullanıcı MAE kısmen şanstı.** Örnek büyüdükçe çoğu sahada simülasyon SINR\'sinin Experia\'dan '
          '**sistematik olarak yüksek** olduğu (SITE_000554 hariç) daha net görünüyor. Bu, ölçüm tanımı (mixed CQI, düşük yük) ve '
          'taşıyıcı/sektör varsayımları sorusunu güçlendiriyor.',
          '- **Öneri:** Sonraki karşılaştırmalarda en az 256 kullanıcı ve saha başına en az ~15 örnek kullanılmalı; az örnekli sahalar '
          'ayrıca işaretlenmeli. İstenirse 512 kullanıcıyla bir yakınsama kontrolü (koşu başına ≈ 15–20 dk) yapılabilir. '
          'Seçilen radyo ayarı bu deneyde yeniden seçilmedi.']
    L += ['', '## Sınırlar', '',
          '- Kullanıcı konumları varsayımsaldır (2–6 km kümeler); gerçek kullanıcı dağılımı bilinmiyor.',
          '- Kontrol sahaları önceki çalışmalarda görüldü; kör doğrulama değildir.',
          '- Kısa (4 s), düşük ve sabit toplam yükte radyo karşılaştırmasıdır; kapasite veya yük doğrulaması değildir.',
          '- Kullanıcı sayısı arttıkça kullanıcı başına yük azaldı; mixed CQI SINR\'si veri kanalı girişimine bağlı olduğundan '
          'bu, yük dağılımındaki değişimin etkisini de içerir.', '',
          '[Tam sayısal sonuç](result.json) — [Önceden yazılan plan](plan.json) — [Hazırlık](prepare.py) — [Koşu](study.py)']
    (HERE / 'SONUCLAR.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('rule1', rule1, 'rule2', rule2, 'worst', worst)


if __name__ == '__main__':
    main()
