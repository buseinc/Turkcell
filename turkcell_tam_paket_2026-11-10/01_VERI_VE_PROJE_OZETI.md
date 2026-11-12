# LTE veri ve proje özeti

> **12 Kasım güncel sonuç:** Hocanın 8 ana + 8 komşu sahası güncel envanterle doğrulandı ve korundu. Yeni yakın sahalarla yedi simülasyon koşusu tamamlandı; komşu genişletmeleri ve üç kullanıcı örneğinin eski–yeni kontrolleri geçti. Güncel 24 sahada kontrol MAE: RSRP 2,96 / SINR 3,63 / RSRQ 4,07 dB. [Sonuçlar ve grafik](../experiments/inventory_refresh_2026-11-12/SONUCLAR.md) — [Hocaya güncel mesaj](../review_2026-11-12/HOCAYA_MESAJ.md). Aşağıdaki 516 saha/eksik koordinat ifadeleri ve eski tablolar tarihsel sürümdür; güncel envanter 563 saha / 6.475 hücredir.

Güncelleme: 9 Kasım 2026. Amaç, ölçümlerden yararlanan bir ns-3 LTE başlangıç senaryosu kurmak. İlk öncelik coğrafi yerleşim ve radyo/kapsama kontrolü; yük ve stres testleri sonraki aşama.

## Veriler

| Kaynak | Kapsam | İçerik |
|---|---|---|
| `cell_site_coordinates.xlsx` | 516 saha, 5.721 hücre | Hücre–saha–koordinat eşlemesi |
| `experia.xlsx` | 851.003 kayıt, 5.867 hücre | Saatlik RSRP, RSRQ, SINR, TAAVG; 22–28 Haziran 2026 |
| 10 LTE KPI XLSX'i | 5.694.304 kayıt, 6.207 farklı hücre | 15 dakikalık trafik, kullanıcı, throughput, PRB, CQI ve hizmet göstergeleri; 2025'te 10 ayrı gün |

Experia ve KPI dönemleri örtüşmüyor; eşzamanlı radyo–trafik gözlemleri gibi birleştirilemezler. Saha başına hücre sayısı 1–47; hücrelerin sektör/taşıyıcı ayrımı bilinmiyor. Frekans, anten, güç, bant genişliği, arazi ve gerçek UE konumları da verilmemiş.

## Üç özet CSV

Bu dosyalar ana Excel kaynaklarından üretildi ve birbirleriyle tutarlılıkları kontrol edildi.

| Dosya | İçerik |
|---|---|
| [site_inventory.csv](analysis/site_inventory.csv) | 516 saha; `site`, envanterdeki hücre sayısı `cells`, `lat/lon` |
| [radio_cell_summary.csv](analysis/radio_cell_summary.csv) | 5.867 hücre; `FIRSTCELL`, eşleşen `site`, kayıt/saat sayısı, RSRP ortalama/medyanı, SINR/RSRQ/ham TA ortalamaları |
| [radio_site_summary.csv](analysis/radio_site_summary.csv) | 516 saha; envanter bilgileri, ölçümle eşleşen `radio_cells`, toplam `radio_rows`, hücre ortalamalarının RSRP ortalaması ve hücre başına min/maks. kayıt |

`rows = hours`; hücre–saat tekrarı yok. Ortalamalar eksik ölçümleri atlar; kayıt sayısı her metrik için geçerli örnek sayısı değildir. `rsrp_mean_of_cell_means` hücreleri eşit ağırlıklandırır; kullanıcı ağırlıklı kapsama ölçüsü değildir.

## Önemli bulgular

- Experia'da 5.144 hücre 505 sahayla eşleşiyor. 723 hücrenin koordinat eşlemesi yok; envanterdeki 577 hücrenin Experia kaydı yok. 11 sahada eşleşen radyo verisi bulunmuyor.
- KPI'da 486 farklı hücrenin koordinatı yok; bunlara ait 228.516 kayıt var. Hücre envanteri günler arasında değişiyor.
- KPI'nın tüm satırlarında `SELECTION_0_NAME = SITE_000282`; bu alan fiziksel saha ayrımı sağlamıyor. Konum bağlantısı hücre kimliğiyle kurulmalı, kaynaklar arası kimlik tutarlılığı teyit edilmeli.
- PRB değerleri 0–1 ölçeğinde: `0,39387` → %39,387. Throughput birimi/payda tanımı, MB/MiB ve saat dilimi henüz doğrulanmadı.
- Experia TAAVG 16–7.968, KPI RACH TA 0–11 aralığında. Birimleri açıklanmadan mesafeye çevrilmemeli.
- Eksik değerler sıfır veya arıza sayılmamalı. Kullanılabilirlikte 209 adet 0–1 dışı kayıt var; ayrıntılar denetim JSON'larında. Taşınan trafik, sunulan talebin tamamını göstermez.

## Sındırgı seçimi ve taslak

Proje kökündeki `sindirgi_lte_sites.csv` ve `sindirgi_lte_cells.csv`, `sindirgi_lte_site_selection.xlsx` içindeki ilgili sayfalarla aynı. Seçim toplam 16 saha (8 değerlendirme + 8 buffer), 96 hücre ve 11.312 kayıtlık özet içeriyor. Değerlendirme kısmındaki **55 hücre / 6.394 kayıt**, `main.tex` ile tutarlı.

Ana koordinat envanteriyle ise yalnızca 13 saha eşleşiyor; eksikler `SITE_000553`, `SITE_000554`, `SITE_000555`. Seçim ekleri bu sahaların konumlarını da sağlıyor. 96 hücrenin tamamı Experia'da, 81'i aynı saha altında ana koordinat tablosunda var; 15'i bu envanterde yok.

**9 Kasım araştırması:** Koordinat dosyasının 5.721 hücresi, 3 Ağustos 2025 KPI hücre kümesiyle birebir aynı. Eksik üç sahaya atanmış 8 hücre 3 Ağustos'ta yok, 9 Ağustos ve sonraki verilen KPI günlerinde var. Koordinat dışa aktarımının ilk günün kapsamıyla sınırlı hazırlanmış olması güçlü bir olasılık; ek konumların asıl kaynağı hâlâ doğrulanmadı. [Kanıt ve açık kalan soru](06_EKSIK_KOORDINAT_ARASTIRMASI.md).

Ana envanter ve tam Experia dönemiyle değerlendirme kısmında **7 saha / 46 hücre / 6.735 kayıt** hesaplanıyor. Seçilen 96 hücrenin tam dönem toplamı 14.363 kayıt; seçim özetinde 11.312. Bu nedenle seçim dosyalarının dönem/filtre ve üretim kodu netleştirilmeli. Merkez/core mesafeleri yaklaşık 5 metre içinde uyuşuyor. Ana envantere ek konumlar dahil edilince, 8 değerlendirme ve 8 buffer sahasının yakınlık sıralaması bilinen aday kümesinde doğrulandı; konumsuz hücreler bu kontrole giremiyor. Artçı koordinatları seçimde kullanılmamış.

## Danışmanın önceliği ve sıradaki işler

Kaynaklar: [danışman notları](<advisors notes.txt>) ve [main.tex](main.tex).

1. **Tamamlandı:** Ana Excel'deki 516 saha ve ChatGPT'nin 16 seçimi ayrı kaynaklar olarak metre cinsinden yerel ENU'ya dönüştürüldü ve üst üste çizildi. 30 km çevresinde 26 ana envanter sahası var; 16 seçimin 13'ü örtüşüyor, 3'ü yalnızca seçim dosyasında. [Önce açılacak harita](analysis/sindirgi/konum_kontrolu/harita.html), [Kartezyen görünüm ve doğrulama](03_KONUM_VE_HARITA_KONTROLU.md).
2. **Tamamlandı:** Mevcut Ubuntu/WSL ns-3.44 klasik LTE/EPC kurulumu doğrulandı. Stok örnek ve 2 saha / 6 sektör / 6 UE testi çalıştı; küçük coğrafi testte tüm UE'ler otomatik bağlanıp veri aldı. [Kod ve çalıştırma](04_NS3_VE_CALISTIRMA.md).
3. **Tamamlandı — radyo deneyleri ve karşılaştırma:** 3 UE yerleşimi × 3 yayılım seçeneği, 3 azimut örneklemesi, buffer genişletmeleri ve ayrılmış 3 saha kontrol edildi. Seçilen koşulda RSRP saha ortalama hatası eğitimde 3,92 dB, ayrılmış kontrolde 3,86 dB; önceden yazılan 5 dB tanı hedefi sağlandı. Buffer için 8 ana + 16 komşu saha seçildi; son 4 s koşusunda 64 UE bağlandı, 60'ı DL verisi aldı. **SINR/RSRQ uyumu henüz doğrulanmadı; bu gerçek ağ doğrulaması değildir.** [Sonuçlar ve grafikler](05_RADYO_DENEYLERI_VE_SONUCLAR.md), [sabitlenen senaryo](analysis/sindirgi/radio_study/frozen/configuration.json). İlk S0 koşusu ayrıca korundu.
4. **Bekliyor:** Radyo başlangıcı değerlendirildikten sonra yük üretimi, stres testi, öncelikli bölge ve rota çalışmaları. Yük modeli henüz kesinleşmedi; şehir merkezi/deniz kenarı senaryoları daha sonra ele alınacak.

S0: tek taşıyıcı, Band 3, 20 MHz, eNB 46 dBm ve anten tepe kazancı 15 dBi; bunlar başlangıç varsayımları. Log-distance yayılımı, düz zemin ve sabit UE'ler kullanıldı; shadowing/fading kapalı. Otomatik ilk hücre seçimi çalışıyor, ancak taşıyıcı/UE arama frekansı, güç, anten ve yerleşim açıkça ayarlanıyor. SINR tanısı kontrol kanalı girişimini kullanıyor. Kısa testte bağlantı kurulması, veri hizmeti veya gerçek kapsamanın doğrulandığı anlamına gelmez.

3. aşamada kaynağı belirsiz üç saha çıkarıldığında UE'lerin %95'inde kapsanan mutlak RSRP değişimi yaklaşık 8 dB'ye ulaştı; hizmet sektörü eşleşmesi %87,5 kaldı. Bu nedenle koordinatların kaynağı sorusu sonuç açısından önemini koruyor. Buffer sonucu seçilen senaryo içindir; başka yük/yerleşimde yeniden kontrol edilmeli.

## Ayrıntılar ve tekrar üretim

Günlük sayımlar [kpi_daily_summary.csv](analysis/kpi_daily_summary.csv), eşlemeler [kpi_cell_site_pairs.csv](analysis/kpi_cell_site_pairs.csv), eksikler ve dağılımlar `*_audit.json` dosyalarında. Ana kaynak denetimini proje kökünde `python analysis/audit_dataset.py` ile yeniden üretmek mümkün (pandas, numpy, openpyxl). Sındırgı ek karşılaştırması ayrıca yapıldı.

Kaynaklar ve `main.tex` değiştirilmedi. `EE550_Project.pdf` çalışma dizininde bulunmadığından okunamadı. Açık kalan başlıca konular: seçim özetinin dönemi/filtresi, eksik envanter bağlantılarının kaynağı, KPI/radyo birimleri ve kullanılacak ns-3 yapılandırması.

## Hocaya sorulacak sorular

**Öncelikli soru işareti:** `SITE_000553`, `SITE_000554`, `SITE_000555` koordinatları seçim CSV/XLSX'inde var, ancak ana koordinat envanterinde yok. Dolayısıyla eksik olan konum bilgisi değil, bu konumların ana kaynakla doğrulanmasıdır. Kaynakları hocaya sorulacak.

1. **Bu üç sahanın koordinatları ve hücre–saha bağlantıları hangi dosyadan veya işlemden alındı? Orijinal kaynak paylaşılabilir mi?**
2. Ana koordinat tablosunun hücre kümesi neden 3 Ağustos 2025 KPI kümesiyle birebir aynı? Tablo ilk günle sınırlı mı; diğer günleri de kapsayan tam/güncel koordinat envanteri var mı?
3. Sındırgı seçim özetleri hangi tarih aralığı ve filtrelerle üretildi? Özetleri yeniden üretmek için kullanılan kod veya işlem adımları paylaşılabilir mi?
4. Farklı kaynak ve dönemlerde aynı anonim hücre kimliği aynı gerçek hücreyi mi temsil ediyor? Eksik eşlemeler için tam hücre–saha listesi var mı?
5. Experia TAAVG ve KPI RACH TA'nın birimleri/ölçekleri nedir? Throughput alanlarının birimi ve hesap tanımı açıklanabilir mi?
6. Experia SINR ve RSRQ hangi kanal, örneklem ve ağırlıklandırmayla üretiliyor? 3. aşamadaki ayrılmış saha kontrolünde bu metriklerin ortalama mutlak farkları yaklaşık 9,97 ve 5,42 dB; ölçüm tanımları netleştirilmeli.
