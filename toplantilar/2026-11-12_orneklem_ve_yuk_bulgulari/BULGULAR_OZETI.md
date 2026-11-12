# Kullanıcı örneklemi ve gerçekçi ağ yükü — bulgular özeti (12 Kasım 2026)

Bu not, 12 Kasım'da eklenen iki çalışmayı ekip için özetler. Ayrıntılı sayılar, grafikler ve kod
her çalışmanın kendi klasöründe.

## Kısaca

1. **Sanal kullanıcı sayısı yetersizdi.** 64 kullanıcıyla bulunan saha ortalamaları, kullanıcıların
   nereye düştüğüne bağlıydı. Karşılaştırmalarda artık **256 kullanıcı** kullanılmalı.
2. **Simülasyondaki ağ neredeyse boştu.** Sektörlerin DL PRB kullanımı simülasyonda ortalama %3,3,
   KPI'da ise normal günde %23 ve akşam yoğun saatinde %36.
3. **SINR farkının ana nedeni bu düşük yükmüş.** KPI'daki yük verilince kontrol sahalarındaki SINR
   hatası **4,74 dB → 1,44–1,72 dB** oldu. RSRP hiç değişmedi.
4. **Deprem anı KPI'da açıkça görülüyor.** İki Sındırgı depreminde aynı anda bağlı kullanıcı sayısı
   ilk yarım saatte yaklaşık **2 katına** çıkıyor. İndirilen veri ve PRB ise ilk yarım saatte düşüyor.

## Çalışma 1 — Kullanıcı örneklemi duyarlılığı

[Klasör](../../deneyler/08_kullanici_orneklemi_2026-11-12/) · [Sonuçlar](../../deneyler/08_kullanici_orneklemi_2026-11-12/SONUCLAR.md)

**Soru:** 64 sanal kullanıcı yeterli mi? Bazı sahalara yalnız 1–2 kullanıcı düşüyordu.

**Yöntem**
- Seçilen radyo ayarı, güncel envanterden 24 saha ve önceki üç kullanıcı/anten örneği korundu.
- Yalnız kullanıcı sayısı değişti: 64 → 128 → 256. Büyük örnekler küçükleri içeriyor.
- Toplam sunulan yük sabit tutuldu. Kullanıcı başına UDP aralığı 50 / 100 / 200 ms.
- Yeterlilik ölçütü koşulardan önce yazıldı: 128→256 geçişinde hata değişimi ≤ 0,5 dB.

**Sonuçlar**
- Bu PC'de yeniden üretim tuttu. 64 kullanıcılık koşular 12 Kasım sonuçlarını 0,000 dB farkla verdi.
- **Ölçüt geçmedi.** 128→256 geçişinde bazı saha ortalamaları 3 dB'ye kadar oynadı.
- İlk 64 kullanıcının kendi değerleri değişmedi: RSRP/RSRQ farkı 0, hizmet sektörü %100 aynı.
  Değişim, yeni eklenen kullanıcı konumlarından geliyor.
- Kontrol sahalarında RSRP hatası 2,96 → 1,72 dB'ye indi.
- SINR hatası 256 kullanıcıda arttı (4,74 dB). Simülasyon SINR'si 554 dışındaki sahalarda
  Experia'dan sistematik olarak yüksek çıkıyordu. Bu bulgu ikinci çalışmayı başlattı.

## Çalışma 2 — KPI'dan yük profili ve gerçekçi yükte radyo karşılaştırması

[Klasör](../../deneyler/09_kpi_yuk_profili_2026-11-12/) · [Sonuçlar](../../deneyler/09_kpi_yuk_profili_2026-11-12/SONUCLAR.md)

**Soru:** Ağ gerçekte ne kadar dolu? Bu yükü simülasyona verince SINR farkı kapanıyor mu?

**KPI yük profili**
- Kapsam: simülasyondaki 24 sahanın KPI'daki 171 hücresi, 10 gün × 15 dakika.
- Hücre–saha bağlantısı koordinat dosyasındaki hücre kimliğiyle kuruldu.
- Yük ölçüsü birimsiz DL PRB kullanımı. Trafik hacmi ve throughput birimleri henüz doğrulanmadı.
- Normal gün değerleri: günlük ortalama 0,233; yoğun saat (21:00) 0,359; gece en düşük 0,061.
- Saha bazında yük çok farklı. Yoğun saatte 443 ve 441 sahalarında ≈0,55, 554 ve 444 sahalarında
  ≈0,05–0,07.

**Deprem anı (24 saha, depremden sonraki ilk 30 dakika)**

KPI saatleri yerel saat gibi davranıyor; iki deprem de aynı 15 dakikalık dilimde görünüyor.

| | 10 Ağustos 2025 19:53 | 27 Ekim 2025 22:48 |
|---|---:|---:|
| Bağlı kullanıcı / bir önceki saat | 1,95× | 1,90× |
| DL veri hacmi / bir önceki saat | 0,73× | 0,65× |
| Bağlantı (E-RAB) düşme oranı | 0,025 → 0,034 | 0,020 → 0,038 |

10 Ağustos'ta PRB ilk düşüşten sonra yaklaşık 4 saat normalin üstünde kaldı. Bu, stres testi
tasarımı için önemli: deprem anı yükü yalnız "daha çok veri" ile değil, "aynı anda çok daha fazla
kullanıcı" ile de temsil edilmeli.

**Simülasyona yük verme**
- Her sektöre ölçüme katılmayan bir "yük kullanıcısı" eklendi; 72 sektörün yaklaşık yarısında hiç
  ölçüm kullanıcısı yoktu. Trafiği o sektörün PRB kullanımını belirliyor.
- Simülasyona pasif bir DL PRB sayacı ve kullanıcı başına UDP aralığı desteği eklendi. Bu iki eklemenin
  sonuçları değiştirmediği önceki koşularla dosya düzeyinde birebir doğrulandı.
- Dört yük düzeyi denendi: boşta, günlük ortalama, sahaya özel yoğun saat, tek tip yoğun saat.
- Kalibrasyon ilk test koşusundan sonra plana eklendi; ilk denemede hedef 0,359 iken 0,546 oluştu.
  Katsayı yalnız bir örnekte üç turda bulundu ve diğer örneklerde değiştirilmedi. Bütün düzeyler
  hedefin ±%5'i içinde.

**Sonuç: kontrol sahalarında hata** (dB, üç örnek ortalaması ± std; düşük daha yakın)

| Yük | RSRP | SINR | RSRQ |
|---|---:|---:|---:|
| Yüksüz (önceki) | 1,72 ± 0,54 | 4,74 ± 1,69 | 4,30 ± 0,39 |
| Günlük ortalama | 1,72 ± 0,54 | **1,44 ± 0,25** | 4,30 ± 0,39 |
| Sahaya özel yoğun saat | 1,72 ± 0,54 | 2,05 ± 0,97 | 4,30 ± 0,39 |
| Tek tip yoğun saat | 1,72 ± 0,54 | **1,72 ± 0,47** | 4,30 ± 0,39 |

- Yükle SINR hatası belirgin düştü, örnekler arası oynaklık da azaldı. RSRP değişmedi.
- Yük kullanıcılarının yalnız bulunması bir şey değiştirmiyor; etki eklenen trafikten geliyor.
- Yük düzeyleri arasında net kazanan yok. Eğitim sahaları sahaya özel yükü, kontrol sahaları günlük
  ortalamayı biraz öne çıkarıyor. Kontrol sonucuna göre seçim yapılmadı.
- **RSRQ farkı bu modelde yükle kapanmaz.** ns-3.44, RSRQ'yu yükten bağımsız kontrol kanalı
  gücünden hesaplıyor. Kapatmak için ayrı bir model değişikliği gerekir.
- **554 sahası** her yükte Experia'nın altında. Sahada 2 hücre var; 3 sektör varsayımı uymuyor olabilir.

## Bundan sonra

- **Karşılaştırma standardı:** 256 ölçüm kullanıcısı ve KPI'dan gelen yük. Experia
  karşılaştırmalarında günlük ortalama, stres deneylerinde yoğun saat yükü başlangıç olsun.
- **Sıradaki adım — stres pilotu:** Yoğun saat yükünden başlayıp PRB yükünü ve eşzamanlı kullanıcı
  sayısını kademeli artırmak. Throughput, gecikme, paket kaybı ve bağlanamayan kullanıcı ölçütleri
  koşulardan önce yazılmalı.
- **Açık sorular:** Experia SINR/RSRQ tanımı; KPI trafik hacmi ve throughput birimleri; 554 sahasının
  sektör/taşıyıcı yapısı; RSRQ hesabının yükü içermesi gerekip gerekmediği.

## Yeniden üretim ve dosyalar

- Simülasyon koşuları WSL'de ns-3.44 ile, analiz ve özetler Windows Python ile yapıldı.
  Her klasörde `prepare.py` → `study.py` → `summarize.py` sırası var.
- Ham KPI'dan süzülen `kpi_cells.csv.gz` git'e konmadı; ham Excel'ler gibi operatör verisi içeriyor.
  `extract.py` ile ham dosyalardan yeniden üretilir.
- Yük çalışmasının değiştirilmiş ns-3 kaynağı kendi klasöründe (`simulation/sindirgi_baseline.cc`).
  Önceki deneylerin kaynakları değiştirilmedi.
- Kullanıcı örneklemi çalışmasında kontrol kodu ilk sürümde önceki bir deney klasöründeki üç
  `metrics.json` dosyasının yazımını değiştirdi (`1.0` → `1`). Dosyalar geri alındı, kod artık eski
  klasörleri yalnız okuyor.
- Toplam koşu sayısı: örneklem çalışmasında 9; yük çalışmasında 12 ana koşu, 4 kalibrasyon koşusu ve
  2 doğrulama koşusu.
