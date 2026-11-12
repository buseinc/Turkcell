# Sındırgı: ilk coğrafi kontrol

> **12 Kasım güncel sonuç:** Hocanın 8 ana + 8 komşu sahası güncel envanterle doğrulandı ve korundu. Yeni yakın sahalarla yedi simülasyon koşusu tamamlandı; komşu genişletmeleri ve üç kullanıcı örneğinin eski–yeni kontrolleri geçti. Güncel 24 sahada kontrol MAE: RSRP 2,96 / SINR 3,63 / RSRQ 4,07 dB. [Sonuçlar ve grafik](../deneyler/07_guncel_envanter_kontrolu_2026-11-12/SONUCLAR.md) — [Hocaya güncel mesaj](../toplantilar/2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/HOCAYA_MESAJ.md). Aşağıdaki 516 saha/eksik koordinat ifadeleri ve eski tablolar tarihsel sürümdür; güncel envanter 563 saha / 6.475 hücredir.

**Önce açılacak karşılaştırma:** [Ana Excel ve ChatGPT seçimi aynı coğrafi haritada](analysis/sindirgi/konum_kontrolu/harita.html), [internetsiz Kartezyen görünüm](analysis/sindirgi/konum_kontrolu/kartezyen.html), [açıklama ve eşleşme tablosu](03_KONUM_VE_HARITA_KONTROLU.md). İki kaynağın konumları bu kontrolde ayrı tutuldu: 30 km içinde 26 ana envanter sahası; 16 seçimin 13'ü örtüşüyor, 3'ü yalnızca seçim ekinde.

İlk adım için sade [Türkçe görsel](analysis/sindirgi/01_saha_secimi.png) ve [numaralı saha tablosu](analysis/sindirgi/01_saha_secimi.csv): mavi 1–8 ana sahalar, turuncu 9–16 komşu sahalar. Bu görseli yeniden üretmek için `python analysis/explain_site_selection.py`.

İnteraktif [haritanın](analysis/sindirgi/site_map.html) çalışma dosyaları HTML'ye gömülüdür. Esri arka planı internet kullanır; erişim kesilirse yerel referans çizgilerine geçilir ve sahalar görünür kalır. İnternetsiz [koordinat grafiği](analysis/sindirgi/topology_offline.html) ve dışa aktarılabilir [PNG](analysis/sindirgi/site_positions.png) / [SVG](analysis/sindirgi/site_positions.svg) de üretildi. İşaretler saha konumudur; kapsama alanı veya hasar haritası değildir.

## Doğrulanan seçim

- Ana envanterdeki 516 sahaya, seçim dosyasında bulunan 3 saha eklenince bilinen 519 konum oluşuyor. Bunların 508'inde radyo hücresi bağlantısı var; merkezin 30 km çevresinde 29 saha bulunuyor.
- Mevcut ve ek konumlardan oluşan aday kümesinde değerlendirme grubu, referansa en yakın 8 uygun sahayla; buffer grubu, değerlendirme sahalarına en yakın kalan 8 uygun sahayla tam örtüşüyor.
- Ek dosyalardan gelen `SITE_000553`, `SITE_000554`, `SITE_000555` mor halkayla gösteriliyor. 15 hücre bağlantısı da seçim dosyasından tamamlandı; kaynağı [bağlantı tablosunda](analysis/sindirgi/selected_cell_linkage.csv) korunuyor. Bu eklerin saha gerçekliği bağımsız doğrulanmadı.
- [9 Kasım araştırması](06_EKSIK_KOORDINAT_ARASTIRMASI.md): ana koordinat kümesi 3 Ağustos 2025 KPI hücre kümesiyle aynı; bu üç sahaya atanan 8 hücre 9 Ağustos ve sonraki KPI'larda var. İlk güne göre sınırlanmış koordinat aktarımı olasılığı güçlü, ancak üretim kaynağı açıklanmadan kesin değil.
- Ortak saha koordinatları arasındaki en büyük fark 0,059 m; CSV mesafeleriyle yeniden hesaplanan mesafeler arasındaki en büyük fark 4,91 m. Farklar verilen yuvarlama düzeyiyle uyumlu.
- Konumu hâlâ bilinmeyen 708 Experia hücresi coğrafi sıralamaya katılamıyor. Bu nedenle yakınlık kontrolü, bütün operatör ağına ilişkin kesin bir envanter doğrulaması değildir. 30 km yalnızca gösterim yarıçapıdır; buffer yeterliliği henüz test edilmedi.

## Yerel koordinatlar

[sites_local.csv](analysis/sindirgi/sites_local.csv), seçilmiş 16 saha için simülasyona aktarılabilir konumları içerir. [candidate_sites.csv](analysis/sindirgi/candidate_sites.csv) bilinen 519 konumu ve sıralamalarını kapsar.

- Referans: 39,2461 N / 28,0697 E; danışman/seçim dosyasındaki girdi, harici deprem kataloğuyla tekrar doğrulanmadı.
- WGS84 varsayımıyla enlem/boylam → ECEF → yerel ENU. `x_m` doğu, `y_m` kuzey yönünde metredir. Negatif değerler referansın batısını/güneyini gösterir.
- `z_ground_m = 0` düz zemin varsayımıdır. `enu_up_curvature_m` Dünya eğriliğinden gelen yardımcı değerdir; arazi yüksekliği veya eNB yüksekliği olarak kullanılmaz.
- Seçili sahalar arası düzlemsel mesafeler yaklaşık 998 m–34,4 km. ENU mesafelerinin küresel mesafelerden farkı en fazla %0,247; bu sayı elipsoid/küre farkını da içerir, yalnızca izdüşüm hatası değildir.
- Dönüşümün ters kontrolü, eksen yönleri, kimlik eşlemeleri ve iki yakınlık sıralaması kodda denetlendi. Ayrıntılar [validation.json](analysis/sindirgi/validation.json), yöntem ve kaynak özetleri [coordinate_manifest.json](analysis/sindirgi/coordinate_manifest.json) içinde.

## Tekrar üretim

Proje kökünde `python analysis/prepare_sindirgi.py`. Python paketleri: numpy, pandas, openpyxl, matplotlib, plotly, folium. Kaynak dosyalar değiştirilmez.

Koordinat yöntemi: [ESA Navipedia, ECEF–ENU dönüşümü](https://gssc.esa.int/navipedia/index.php/Transformations_between_ECEF_and_ENU_coordinates).

## İlk simülasyon çıktıları

**Güncel 3. aşama sonucu:** [Radyo deneyleri ve duyarlılık kontrolü](05_RADYO_DENEYLERI_VE_SONUCLAR.md) tamamlandı. Sabit girdilerle yerleşim, yayılım, azimut, buffer, ayrılmış saha ve süre/prob kontrolleri yapıldı. Aşağıdaki ilk S0 çalışması tarihsel başlangıç olarak korunuyor.

[UE radyo örnekleri](analysis/sindirgi/ue_radio_samples.png) ve [Experia dağılım karşılaştırması](analysis/sindirgi/radio_distribution_comparison.png) üretildi. 16 saha / 48 sentetik sektör / 100 UE ile 2 saniyelik S0 koşusunda 100 UE bağlandı, 75'i DL verisi aldı. Radyo varsayımları henüz kalibre edilmedi; karşılaştırma farklı örneklemleri içeriyor. Çalıştırma ve model açıklaması [simulation/README.md](04_NS3_VE_CALISTIRMA.md), özet sayımlar [baseline_summary.json](analysis/sindirgi/baseline_summary.json) içinde. `ue_radio_summary.csv` 0,5 saniye sonrasındaki UE zaman ortalamalarını; `experia_evaluation_cells.csv` 55 değerlendirme hücresinin tam dönem özetlerini içerir.
