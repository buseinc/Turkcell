"""Windows: SONUCLAR.md and figures for the KPI load study."""
from pathlib import Path
import csv
import json
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D08 = ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12'
M = ['rsrp', 'sinr', 'rsrq']
LAB = {'rsrp': 'RSRP', 'sinr': 'SINR', 'rsrq': 'RSRQ'}
LEVELS = [('08_n256', 'Önceki (08, yük kullanıcısı yok)'), ('L0_idle', 'L0 — yük kullanıcıları boşta'),
          ('L1_daily_mean', 'L1 — günlük ortalama'), ('L3_site_busy_hour', 'L3 — sahaya özel yoğun saat'),
          ('L2_busy_hour', 'L2 — yoğun saat (tek tip)')]


def f(x, d=2, sign=False):
    if x is None:
        return '—'
    s = f'{x:+.{d}f}' if sign else f'{x:.{d}f}'
    return s.replace('.', ',')


def main():
    prof = json.loads((HERE / 'profile.json').read_text(encoding='utf-8'))
    res = json.loads((HERE / 'result.json').read_text(encoding='utf-8'))
    assert res['completed']
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    with (HERE / 'inputs/targets.csv').open(encoding='utf-8-sig') as fh:
        targets = {t['site']: t for t in csv.DictReader(fh)}
    seeds = [701, 702, 703]
    by = {(r['case']['load'], r['case']['ue_seed']): r for r in res['results']}
    old = json.loads((D08 / 'result.json').read_text(encoding='utf-8'))
    for r in old['results']:
        if r['ues'] == 256:
            by['08_n256', r['case']['ue_seed']] = r
    site_kpi = pd.read_csv(HERE / 'site_busy_hour.csv').set_index('site')

    # Figure 1: normal-day hourly PRB.
    hourly = pd.read_csv(HERE / 'normal_hourly_profile.csv')
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for g, w in hourly.groupby('group'):
        ax.plot(w.hour, w.prb, marker='o', label=g)
    for k, ls in [('normal_daily_mean', ':'), ('normal_busy_hour', '--')]:
        ax.axhline(prof['simulation_targets'][k], color='grey', ls=ls, lw=1)
    ax.axhline(0.033, color='red', ls='-', lw=1, label='önceki simülasyon (%3,3)')
    ax.set_xlabel('Saat (yerel)')
    ax.set_ylabel('DL PRB kullanımı')
    ax.set_title('Normal günlerde 24 sahanın saatlik DL PRB kullanımı (KPI)')
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / 'normal_gun_prb.png', dpi=150)

    # Figure 2: signed SINR error by site and load level (mean of draws).
    fig, ax = plt.subplots(figsize=(10, 4))
    sites = list(targets)
    width = 0.16
    for i, (lv, lab) in enumerate(LEVELS):
        vals = [statistics.mean(by[lv, s]['sites'][site]['sinr'] - float(targets[site]['sinr_target']) for s in seeds)
                for site in sites]
        ax.bar([j + (i - 2) * width for j in range(len(sites))], vals, width, label=lab)
    ax.axhline(0, color='black', lw=.8)
    ax.set_xticks(range(len(sites)), [f"{s[-3:]}\n{'kontrol' if targets[s]['split'] == 'holdout' else 'eğitim'}" for s in sites])
    ax.set_ylabel('SINR: simülasyon − Experia (dB)')
    ax.set_title('Yük düzeyine göre saha bazında SINR farkı (üç örnek ortalaması)')
    ax.grid(axis='y', alpha=.3)
    ax.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(HERE / 'yuke_gore_sinr.png', dpi=150)

    q = prof['earthquakes']
    L = ['# KPI yük profili ve gerçekçi yükte radyo karşılaştırması — 12 Kasım 2026', '',
         '> **15 Kasım ek uyarısı:** Raporlanan mixed SINR örneklerinin yalnız ≈%32–41\'i veri kanalı girişimi '
         'içeriyor, kalanı birebir S/N. Bu çalışmadaki yük kullanıcılarının UDP trafiği eşzamanlı başladığından '
         'komşu sektörler aynı alt çerçevelerde yayın yapıyor. Düşük yükün SINR\'yi iyimser gösterdiği sonucu '
         'geçerli; aşağıdaki sayısal yakınlık bu ortalama yöntemine bağlı. Ayrıntı: '
         '[Izgara kapsama haritaları](../10_kapsama_haritalari_2026-11-15/SONUCLAR.md).', '',
         'İki soru: (1) KPI verisine göre bölgedeki ağ normal günde ve deprem anında ne kadar yüklü? '
         '(2) Simülasyona bu yükü verince Experia ile SINR farkı kapanıyor mu?', '',
         '## 1. KPI\'dan yük profili', '',
         f"Simülasyondaki 24 sahanın KPI'da bulunan {prof['cells']} hücresi (ana 8 saha: {prof['cells_by_group']['ana 8']}, "
         f"komşular: {prof['cells_by_group']['komşu']}), 10 gün × 15 dakika. Hücre–saha bağlantısı güncel koordinat dosyasından "
         'hücre kimliğiyle kuruldu. Yük ölçüsü olarak birimsiz DL PRB kullanımı (0–1) seçildi; trafik hacmi/throughput '
         'birimleri henüz doğrulanmadı.', '',
         '| Gösterge (normal günler) | Değer |', '|---|---:|',
         f"| Günlük ortalama DL PRB | {f(prof['normal']['prb_daily_mean'], 3)} |",
         f"| Yoğun saat ({prof['normal']['busy_hour']}:00) ortalaması | {f(prof['normal']['prb_busy_hour_mean'], 3)} |",
         f"| Gece en düşük saat | {f(prof['normal']['prb_night_min'], 3)} |",
         f"| Yoğun saatte hücrelerin %90'lık dilimi | {f(prof['normal']['prb_busy_hour_p90_cell'], 3)} |",
         '| **Önceki simülasyon (08, 256 kullanıcı) sektör ortalaması** | **0,033** |', '',
         '![Normal gün PRB](normal_gun_prb.png)', '',
         '**Önceki simülasyon, ağı gerçeğe göre 7–10 kat daha boş çalıştırıyordu.**', '',
         '### Deprem anı', '',
         'Veride iki Sındırgı depremi aynı 15 dakikalık dilimde görülüyor (kamuya açık kayıtlara göre M6,1, '
         '10 Ağustos 2025 19:53 ve 27 Ekim 2025 22:48 yerel saat; KPI saatleri de yerel saat gibi davranıyor).', '',
         '| 24 saha, ilk 30 dk | 10 Ağustos | 27 Ekim |', '|---|---:|---:|']
    for key, lab in [('users_ratio_vs_hour_before', 'Bağlı kullanıcı / önceki saat'),
                     ('users_ratio_vs_normal_same_time', 'Bağlı kullanıcı / normal günde aynı saat'),
                     ('dl_ratio_vs_hour_before', 'DL hacim / önceki saat'),
                     ('users_ratio_after_3h', 'Bağlı kullanıcı 3 saat sonra / önceki saat')]:
        L.append(f"| {lab} | {f(q['2025-08-10'][key])}× | {f(q['2025-10-27'][key])}× |")
    L.append(f"| DL PRB: önceki saat → ilk 30 dk en düşük | {f(q['2025-08-10']['prb_hour_before'])} → {f(q['2025-08-10']['prb_min_first_30min'])} | "
             f"{f(q['2025-10-27']['prb_hour_before'])} → {f(q['2025-10-27']['prb_min_first_30min'])} |")
    L.append(f"| E-RAB düşme oranı: önceki saat → ilk 30 dk en yüksek | {f(q['2025-08-10']['drop_hour_before'], 3)} → {f(q['2025-08-10']['drop_max_first_30min'], 3)} | "
             f"{f(q['2025-10-27']['drop_hour_before'], 3)} → {f(q['2025-10-27']['drop_max_first_30min'], 3)} |")
    L += ['', '![Deprem anı yük değişimi](deprem_yuk_degisimi.png)', '',
          '**Deprem anı yükü "daha çok veri" değil, "aynı anda yaklaşık iki kat bağlı kullanıcı" şeklinde.** Veri hacmi ve '
          'PRB kullanımı ilk yarım saatte düşüyor, bağlantı düşmeleri artıyor. Bu, kısa ve çok sayıda oturumun (arama, '
          'mesajlaşma) baskın olduğu ya da çekirdek/sinyalleşme tarafında tıkanma olduğu bir tabloya uyuyor; nedeni bu '
          'veriyle ayırt edilemez. Stres testinde yalnız trafik hacmini artırmak deprem anını temsil etmeyebilir.', '']

    # 2. Simulation load
    L += ['## 2. Simülasyona yük verilmesi', '',
          'Seçilen radyo ayarı, güncel 24 saha, 256 ölçüm kullanıcısı ve üç örnek (08 ile aynı) korundu. Her sektöre ölçüme '
          'katılmayan bir **yük kullanıcısı** (sektör yönünde 800 m) eklendi; trafiği sektörün DL PRB kullanımını belirler. '
          'Ölçüm kullanıcılarının trafiği 08 ile aynı (512 B / 200 ms). ns-3 bu zamanlayıcıda veri gönderdiği alt çerçevenin '
          'tamamını kullandığından simülasyondaki PRB oranı, dolu alt çerçeve oranıdır; ortalama girişim açısından KPI PRB '
          'oranıyla karşılaştırılabilir. PRB sayacı spektrum kanalından pasif okunur; eklenmesinin sonuçları değiştirmediği '
          '08 koşularıyla bayt düzeyinde doğrulandı.', '',
          '**Kalibrasyon (ilk test koşusundan sonra plana eklendi):** İlk L2 denemesinde hedef 0,359 iken 0,546 oluştu; '
          'girişim arttıkça paketler birden fazla alt çerçeve kaplıyor. Yük kullanıcılarının aralığı düzey başına bir katsayıyla '
          'ölçeklendi; katsayı yalnız 701 örneğinde bulunup diğer örnekler için donduruldu. '
          f"Son katsayılar: {', '.join(f'{k} = {f(v)}' for k, v in plan['calibration_factors'].items())}. "
          '[Kalibrasyon kayıtları](calibration/).', '',
          '| Düzey | Hedef PRB | Oluşan PRB (örnek 701 / 702 / 703) | Hedef sektörüne bağlanan yük kullanıcısı |', '|---|---:|---|---:|']
    for lv, lab in LEVELS[1:]:
        rows = [by[lv, s] for s in seeds]
        L.append(f"| {lab} | {f(rows[0]['prb_mean_target'], 3)} | {' / '.join(f(r['prb_mean_achieved'], 3) for r in rows)} | "
                 f"{' / '.join(str(r['load_ues_on_target']) for r in rows)} (72'de) |")
    L += ['']

    # 3. Errors
    L += ['## 3. Experia\'ya göre hata', '',
          'Üç örneğin ortalaması ± std (dB; düşük daha yakın). Yalnız 256 ölçüm kullanıcısı kullanılır.', '',
          '| Düzey | Eğitim RSRP | Eğitim SINR | Eğitim RSRQ | Kontrol RSRP | Kontrol SINR | Kontrol RSRQ |', '|---|---:|---:|---:|---:|---:|---:|']
    for lv, lab in LEVELS:
        cells = []
        for sp in ['training', 'control']:
            for m in M:
                v = [by[lv, s][sp]['mae_db'][m] for s in seeds]
                cells.append(f'{f(statistics.mean(v))} ± {f(statistics.stdev(v))}')
        L.append(f'| {lab} | ' + ' | '.join(cells) + ' |')
    L += ['', '### Saha bazında işaretli SINR farkı (simülasyon − Experia, üç örnek ortalaması)', '',
          '| Saha | Bölüm | KPI yoğun saat PRB | ' + ' | '.join(lab.split(' — ')[0] if ' — ' in lab else '08' for lv, lab in LEVELS) + ' |',
          '|---|---|---:|' + '---:|' * len(LEVELS)]
    for site, t in targets.items():
        vals = [statistics.mean(by[lv, s]['sites'][site]['sinr'] - float(t['sinr_target']) for s in seeds) for lv, _ in LEVELS]
        L.append(f"| {site} | {'kontrol' if t['split'] == 'holdout' else 'eğitim'} | {f(site_kpi.prb.get(site), 2)} | "
                 + ' | '.join(f(v, 1, True) for v in vals) + ' |')
    L += ['', '![Yüke göre SINR](yuke_gore_sinr.png)', '',
          '### Aynı kullanıcılar: 08 ile eşli karşılaştırma', '',
          '| Düzey | Aynı sektör | RSRP ort. değişim | SINR ort. değişim | SINR q95 mutlak | RSRQ ort. değişim |', '|---|---:|---:|---:|---:|---:|']
    for lv, lab in LEVELS[1:]:
        p = [by[lv, s]['paired_vs_08'] for s in seeds]
        L.append(f"| {lab} | %{100 * min(x['same_serving_sector_fraction'] for x in p):.0f} | "
                 f"{f(statistics.mean(x['rsrp_mean_change_db'] for x in p), 2, True)} | {f(statistics.mean(x['sinr_mean_change_db'] for x in p), 2, True)} | "
                 f"{f(max(x['sinr_q95_abs_change_db'] for x in p))} | {f(statistics.mean(x['rsrq_mean_change_db'] for x in p), 2, True)} |")
    L += ['', 'RSRQ\'nun değişmemesi beklenen bir model özelliğidir: ns-3.44\'te RSRQ, yükten bağımsız kontrol kanalı '
          'gücünden hesaplanır. Gerçek ağda RSRQ yükle düşer; bu nedenle RSRQ farkı bu modelle yükle kapatılamaz.', '']
    def mean_mae(lv, sp, m):
        return statistics.mean(by[lv, s][sp]['mae_db'][m] for s in seeds)

    def std_mae(lv, sp, m):
        return statistics.stdev(by[lv, s][sp]['mae_db'][m] for s in seeds)

    L += ['## Yorum', '',
          f"- **Hipotez doğrulandı: SINR farkının ana nedeni simülasyondaki düşük yükmüş.** Gerçekçi yük verilince kontrol "
          f"sahalarında SINR hatası {f(mean_mae('08_n256', 'control', 'sinr'))} dB'den {f(mean_mae('L1_daily_mean', 'control', 'sinr'))}–"
          f"{f(mean_mae('L2_busy_hour', 'control', 'sinr'))} dB'ye düştü; örnekler arası oynaklık da "
          f"{f(std_mae('08_n256', 'control', 'sinr'))} dB'den {f(std_mae('L1_daily_mean', 'control', 'sinr'))} dB'ye indi. "
          'Önceki "çoğu sahada SINR sistematik yüksek" durumu büyük ölçüde kayboldu.',
          '- **RSRP hiç değişmedi** (bütün düzeylerde eşli fark 0, hizmet sektörü %100 aynı). Kapsama sonucu yükten bağımsız ve korunuyor.',
          '- **Yük kullanıcılarının yalnız bulunması bir şey değiştirmiyor** (L0 ≈ 08). Etki tamamen eklenen trafikten geliyor.',
          f"- **Yük düzeyleri arasında net bir kazanan yok.** Eğitim SINR'si en iyi L3'te ({f(mean_mae('L3_site_busy_hour', 'training', 'sinr'))} dB), "
          f"kontrol SINR'si en iyi L1'de ({f(mean_mae('L1_daily_mean', 'control', 'sinr'))} dB). Bu farklar, yüksüz duruma göre kazanımdan "
          'çok küçük. Sahaya özel yoğun saat yükü (L3) çok yüklü sahalarda (443, 482) SINR\'yi bu kez düşük gösteriyor; Experia '
          'saatlik ölçümlerinin günün tamamını kapsaması, günlük ortalama yükün (L1) Experia ile karşılaştırma için daha tutarlı '
          'bir seçim olduğunu düşündürüyor. Kontrol sonucuna göre seçim yapmadık.',
          '- **SITE_000554 her yükte düşük kalıyor** (−1,6 … −5,6 dB). Sahada yalnız 2 hücre var ve KPI yükü çok düşük; '
          '3 sektör / tek taşıyıcı varsayımı bu sahada uymuyor olabilir.',
          '- **RSRQ farkı (~4,3 dB kontrol) bu modelde yükle kapanmaz.** ns-3.44 RSRQ\'yu yükten bağımsız hesaplıyor. Kapatmak için '
          'RSRQ hesabına veri kanalı gücünü (RSSI) dahil eden bir değişiklik gerekir; bu ayrı bir model kararıdır.',
          '- **Deprem anı farklı bir yük türü.** KPI\'da deprem anında bağlı kullanıcı ≈2× artarken veri hacmi ve PRB ilk yarım '
          'saatte düşüyor; ardından (özellikle 10 Ağustos\'ta) PRB birkaç saat normalin üstünde kalıyor ve kullanıcı sayısı yavaş iniyor. '
          'Stres testi yalnız PRB/veri yükünü artırarak değil, eşzamanlı kullanıcı/oturum sayısını artırarak da kurulmalı.', '',
          '**Öneri:** Radyo başlangıcı artık gerçekçi yükle birlikte tanımlanmalı: Experia karşılaştırmaları için L1 (günlük ortalama), '
          'stres deneylerinin başlangıç noktası için L2 (yoğun saat). Sonraki adım: L2\'den başlayıp (a) PRB yükünü ve (b) eşzamanlı '
          'kullanıcı sayısını kademeli artıran stres pilotu; throughput, gecikme, paket kaybı ve bağlanamayan kullanıcı ölçütleri '
          'koşulardan önce yazılmalı.', '']
    L += ['## Sınırlar', '',
          '- KPI (2025) ve Experia (Haziran 2026) farklı dönemler; yük düzeyi tipik değer olarak kullanıldı, eşzamanlı değil.',
          '- Yük kullanıcısı her sektörde tek noktada; gerçek trafiğin mekânsal dağılımı ve kullanıcı sayısı temsil edilmedi.',
          '- PRB eşlemesi: simülasyonda dolu alt çerçeve oranı, KPI\'da kaynak bloğu oranı. Ortalama girişim eşdeğer, '
          'anlık girişim örüntüsü değil.',
          '- Kalibrasyon katsayısı tek örnekte bulundu; diğer örneklerde oluşan PRB tabloda raporlandı.',
          '- Kontrol sahaları önceki çalışmalarda görüldü; kör doğrulama değildir. Kısa (4 s) koşular; kapasite doğrulaması değildir.',
          '- Deprem saatleri kamuya açık kayıtlardan; KPI saat diliminin yerel olduğu veriyle tutarlı, ayrıca teyit edilmedi.', '',
          '[KPI çıkarımı](extract.py) — [Profil](profile.py) — [Profil sayıları](profile.json) — [Saha yoğun saat](site_busy_hour.csv) — '
          '[Plan](plan.json) — [Koşu](study.py) — [Tam sonuç](result.json)']
    (HERE / 'SONUCLAR.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('written')


if __name__ == '__main__':
    main()
