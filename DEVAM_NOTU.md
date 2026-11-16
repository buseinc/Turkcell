# Devam notu — projeyi başka bir bilgisayarda / başka bir yapay zekâyla sürdürmek için

Son güncelleme: 16 Kasım 2026. Bu belge, projeye hiç bakmamış birinin (insan ya da yapay zekâ) kaldığımız
yerden devam edebilmesi için yazıldı. Önce bunu, sonra gerekirse bağlantı verilen raporları okuyun.

---

## 1. Proje ne?

Turkcell'in Sındırgı (Balıkesir) bölgesindeki LTE ağının **ns-3.44 (klasik LTE/EPC modülü)** ile
ölçümlerden beslenen, **temsili** bir kopyasını kurmak. Birebir kopya iddiası yok; hocanın ifadesiyle
"measurement / real-service informed, full replay değil". Sonraki aşamalarda bu ağ üzerinde deprem anı
yükü, stres testi, saha kesintisi, öncelikli bölgeler ve UAV (dron baz istasyonu) çalışılacak.

- **Danışman (hoca):** Evşen Yanmaz Adam. Kendi notları `ana_proje/advisors notes.txt`; yöntem taslağı
  `ana_proje/main.tex` (kırmızı = hocanın notları, mavi = bizim eklediklerimiz).
- **Ekip:** Repo sahibi GitHub'da `buseinc` (`https://github.com/buseinc/Turkcell`). Çalışmanın çoğu bu
  oturumda 20umu kullanıcılı bir Windows bilgisayarda yapıldı.
- **Bölge:** 8 ana saha (130, 296, 440, 441, 443, 444, 482, 554) + 16 komşu saha = 24 saha. Deprem merkezi
  (10 Ağustos 2025) 39.2461 K, 28.0697 D; yerel koordinatların başlangıç noktası bu.

## 2. Veri

| Veri | İçerik | Git'te mi? |
|---|---|---|
| `ana_proje/cell_site_coordinates/cell_site_coordinates.xlsx` | 563 saha / 6.475 hücre, hücre→saha eşlemesi ve konum | Evet |
| `ana_proje/experia/experia.xlsx` | Telefonlardan saatlik ölçüm: RSRP, SINR, RSRQ, TAAVG; 22–28 Haziran 2026 | **Hayır** (büyük, operatör verisi) |
| `ana_proje/LTE Main KPI_*/*.xlsx` (10 dosya) | Kule kayıtları, 15 dk: bağlı kullanıcı, PRB, trafik, CQI, RACH TA, handover; 2025'ten 10 gün | **Hayır** |
| Hocanın gruplama dosyaları `ana_proje/sindirgi_site_cell_groups*.xlsx`, `all_sites_cell_layers_v2.xlsx`, `cellmapper_check_template.xlsx` | Hücrelerin sektör/taşıyıcı gruplaması ve CellMapper şablonu | Evet (16 Kasım) |

Önemli veri bilgileri:
- Kaynaklar **hücre kimliğiyle** (`CELL_xxxxxx`) bağlanır. KPI'daki `SELECTION_0_NAME` sütunu her satırda
  aynı (`SITE_000282`); kullanılmaz.
- Experia (2026) ve KPI (2025) farklı dönemler; aynı anın ölçümü gibi birleştirilmez.
- PRB 0–1 oranı, CQI 0–15. Trafik hacmi ve throughput birimleri hâlâ belirsiz, kullanılmadı.
- **TA birimi (16 Kasım'da hocadan geldi):** KPI RACH TA bin × 1,5 km (hücre menzili 15 km varsayılan,
  12 yüzde dilimi). Experia TAAVG × 4,88 m (üst sınır 15 km). İkisi hücre bazında tutarlı (r = 0,70).
- Ham veriden süzülen ara dosyalar (`deneyler/09/kpi_cells.csv.gz`, `deneyler/13/*.csv.gz`,
  `deneyler/14/buffer_kpi_cells.csv.gz`) git'te yok; ilgili `extract*.py` ile yeniden üretilir.

## 3. Ortam

Ayrıntı: `CALISTIRMA_REHBERI.md`. Özet:

- **Windows Python 3.12** (analiz, grafik, PDF): numpy 2.0.2, pandas 2.2.3, scipy 1.14.1, openpyxl 3.1.5,
  matplotlib 3.9.2, folium 0.19.6, branca 0.8.1, plotly 5.24.1, reportlab 5.1.0, pillow. Bu bilgisayarda
  `.venv` yok, sistem Python'u kullanıldı.
- **WSL Ubuntu 24.04** (simülasyon): ns-3.44 `~/ns-allinone-3.44/ns-3.44` altında, `./ns3 configure
  --enable-examples && ./ns3 build` ile derlenmiş (profil "default"). `simulation/ns3_paths.py` ns-3'ü
  `~/ns3/ns-3.44` veya `~/ns-allinone-3.44/ns-3.44`'te bulur; farklıysa `NS3_ROOT`.
- Bu bilgisayarda WSL dağıtımının adı **`Ubuntu`**. `calistir.cmd` varsayılan "Ubuntu-22.04" arar;
  `TURKCELL_WSL_DISTRO` ortam değişkeniyle değiştirilebilir.
- LaTeX bu bilgisayarda yok; taslak Overleaf'te derleniyor.

Komut alışkanlıkları (Git Bash'ten):
- WSL komutlarında yol bozulmasın diye `MSYS_NO_PATHCONV=1` kullanıldı:
  `MSYS_NO_PATHCONV=1 wsl -d Ubuntu --cd /mnt/c/.../deneyler/<deney> --exec python3 study.py --workers 3`
- Windows Python'unda Türkçe çıktı için `PYTHONUTF8=1`.
- Bir koşu (24 saha, 256 kullanıcı, gerçekçi yük, 4 s) ~13 dk; 3 paralel koşu sorun değil (20 çekirdek, 6 GB RAM WSL).

## 4. Klasör yapısı

| Yol | İçerik |
|---|---|
| `README.md` | Güncel durum ve deney tablosu |
| `DEVAM_NOTU.md` | Bu belge |
| `ana_proje/` | Ham veriler, ilk analizler, ilk simülasyon kodu, hocanın taslağı (`main.tex`), şekiller (`figures/`) |
| `deneyler/NN_ad_tarih/` | Her deney ayrı klasörde. Tipik dosyalar: `prepare.py` (Windows, girdileri ve `plan.json`'ı dondurur), `study.py` (WSL, koşuları çalıştırır, `result.json`), `summarize.py`/`compare.py` (Windows, rapor ve grafik), `SONUCLAR.md` (sonuç raporu), `simulation/` (o deneyin ns-3 kodu ve sonuçları) |
| `toplantilar/` | Hocaya özetler. En güncelleri `2026-11-15_ilk_asama_ozeti/` (ILK_ASAMA_OZETI.md, BASIT_ANLATIM.md) ve `2026-11-16_dogrulama_ozeti/` (DOGRULAMA_OZETI.pdf) |

Yöntem kuralları (bütün deneylerde uygulandı, devam ederken de uyulmalı):
1. Karar kuralı ve kabul ölçütü **koşulardan önce** `plan.json`/`prepare.py` belgesine yazılır.
2. Ayarlar 5 sahayla (130, 296, 444, 482, 554) seçilir; 440, 441, 443 seçimde kullanılmaz (holdout).
3. Her şey 3 anten yönü / kullanıcı örneğiyle tekrarlanır (tohumlar 42/701, 7/702, 99/703).
4. Simülasyon koduna her eklemeden sonra eski bir koşu tekrarlanır ve çıktıların **bayt düzeyinde** aynı
   olduğu kontrol edilir.
5. Önceki deneylerin dosyaları değiştirilmez; yeni iş yeni klasörde yapılır.

## 5. Deneylerin özeti (kronolojik)

| # | Deney | Ana sonuç |
|---|---|---|
| 01–07 | Sektör sayısı, SINR tanısı, mixed CQI, ortak tarama, kullanıcı/yayılım/güç, 49 ayarlı geniş tarama, güncel envanter kontrolü | Ayar seçildi: 49 dBm, 120°, log-distance üs 3, gölgeleme yok, NF 9 dB, mixed CQI, Band 3 20 MHz, 3 sektör, kullanıcılar ana sahalara 2–6 km. 24 saha yeterli. |
| 08 | Kullanıcı örneklemi (64→128→256) | 64 yetersiz; 256 kullanılmalı. |
| 09 | KPI yük profili | Simülasyon ağı 7–10 kat boştu (PRB %3; KPI günlük ort. 0,233, yoğun saat 0,359). Her hücreye bir "yük kullanıcısı" eklenerek KPI PRB'si verildi. **Deprem anı KPI'da görülüyor:** bağlı kullanıcı ilk yarım saatte ≈2×, indirilen veri ≈1/3 azalıyor. |
| 10 | Izgara kapsama haritaları | Analitik model ns-3 ile birebir; alanın %99,8'inde RSRP ≥ −120 dBm. **ns-3 mixed SINR örneklerinin ≈2/3'ü girişimsiz (S/N)** ve 09'daki yük trafiği eşzamanlıydı. |
| 11 | CQI ve KPI (eşzamanlı) | Simülasyon CQI'sı biraz düşük; tek frekans girişimi abartıyor. ns-3 LteAmc ile SINR→CQI tablosu üretildi (`cqi_table.csv`). |
| 12 | Hücre dağılımı ve sıralama | RSRP sıralaması iyi (Spearman 0,79–0,95), ama hücre dağılımı dar; gerçek ağdaki güçlü hücreler yok. RSRQ karşılaştırılamaz (ns-3 tanımı yükten bağımsız). |
| 13 | Saha içi hücre imzası | KPI frekanslar arası handover kayıtlarına göre 130, 296, 440, 441, 443 çok frekanslı; 444, 554 tek frekans; 482 belirsiz. |
| 14 | Çok taşıyıcılı senaryo S2 | ns-3 koduna taşıyıcı katmanı, alt-GHz yayılım farkı, kullanıcı başına frekans, **rastgele UDP başlangıcı (udpJitter)** eklendi. S2 hücre RSRP düzeyini düzeltti ama saha hataları büyüdü (800 MHz gücü ve kullanıcı ataması tahmin). **S0 temel kaldı.** |
| 15 | Kullanıcıları TA'ya göre yerleştirme | Uzaklıklar gerçeğe yaklaştı ama yakın kullanıcılı sahalarda sinyal 6–12 dB fazla çıktı (kontrol RSRP 1,7→3,3 dB). **Önceki ayarlar yanlış kullanıcı mesafesini telafi ediyormuş;** modelde bina içi kayıp ve anten eğimi (downtilt/dikey desen) eksik. |

Her deneyin ayrıntısı kendi `SONUCLAR.md` dosyasında.

## 6. Güncel temel senaryo (S0) ve sonuçları

Tanım: 24 saha, 3 sektör, tek taşıyıcı (Band 3, 1815 MHz, 20 MHz), 49 dBm, 120° CosineAntenna 15 dBi,
eNB 30 m / UE 1,5 m, log-distance üs 3, gölgeleme yok, NF 9 dB, PF zamanlayıcı, mixed CQI, 256 ölçüm
kullanıcısı (ana sahalara 2–6 km kümeler), her hücreye 1 yük kullanıcısı (KPI günlük ortalama PRB 0,233,
katsayı 1,47), rastgele UDP başlangıcı, 4 s koşu / 1 s ısınma, 3 örnek. Kod ve girdiler:
`deneyler/14_cok_tasiyici_s2_2026-11-15/` (senaryo adı `S0`).

| Ölçüt | Değer |
|---|---|
| Ayarda kullanılmayan sahalarda RSRP / SINR / RSRQ farkı | 1,72 / 2,15 / 4,30 dB |
| Ayarda kullanılan sahalarda | 3,59 / 2,57 / 2,46 dB |
| Saha RSRP sıralaması (Spearman) | 0,79–0,95 |
| KPI CQI farkı | −1,06 puan |
| En çok sapan sahalar | 482, 554 (2'şer hücre, yapı belirsiz) |

## 7. Bilinen tuzaklar

- **ns-3 mixed SINR:** Raporlanan SINR örneklerinin çoğu girişimsiz; SINR karşılaştırması temkinli okunmalı.
- **RSRQ:** ns-3'te yükten bağımsız ve gerçek ağdan farklı tanımlı; kalibrasyonda kullanılmıyor.
- **Eşzamanlı yük:** Yük kullanıcılarının UDP'si aynı anda başlarsa girişim abartılır. Yeni deneylerde
  `--udp-jitter 1` kullanın (deney 14'teki `run_baseline.py`).
- **`ana_proje/simulation/run_radio_study.py` içindeki `metrics()`** okuduğu klasöre `metrics.json`
  yazar. Eski deney klasörleri üzerinde çağırmayın; gerekiyorsa mevcut `metrics.json`'ı okuyun.
- **NaN TA:** Experia'da 29 saatlik kayıtta TAAVG boş; mesafe hesaplarken ayıklayın.
- **Python heredoc'ta `\r`:** LaTeX'e `\ref` gibi metin yazarken Python stringinde kaçış bozuluyor; dosya
  düzenlemelerini doğrudan düzenleme aracıyla yapın.
- **Taslağın iki sürümü var:** Overleaf'teki sürümde ekip mavi notları kendi üslubuyla yeniden yazdı.
  Repodaki `ana_proje/main.tex` ayrıntılı ("prof") sürüm. Overleaf için `ana_proje/figures/` altındaki
  `yerlesim.png`, `saha_karsilastirma.png`, `cqi.png` yüklenmeli.

## 8. Hocanın son geri bildirimleri (16 Kasım)

1. Doğrulama özetini gördü: "Full tuning gerekmeyebilir, yeterince yaklaşıldıysa real-service informed
   diyeceğiz."
2. **TA birimi** (bkz. bölüm 2) verildi.
3. **Başka bölgeler:** "Analiz çabuk oluyorsa diğer bölgelerden benzer boyutta bölge seçip deneyin."
   Önceden şehir merkezi ve sahil bölgesi de anılmıştı.
4. **Handover eklenecek** (X2 + A3 RSRP; kesinti ve UAV için şart).
5. **Hücre gruplaması:** Hocanın dosyaları ardışık hücre numaralarını (üçlü bloklar) taşıyıcı katmanı,
   blok içini sektör sayıyor; katmanları TA'ya göre sıralıyor (uzun menzil = düşük bant). Bantlar hipotez.
   Talimat: güveni yüksek gruplar dosyadaki gibi, diğerleri tek taşıyıcı 3 sektör 1800 MHz; çok
   taşıyıcılıda frekans TA'ya göre (yüksek TA = düşük frekans). Sındırgı'da yalnız **440 "strong"**
   (3 taşıyıcı × 3 sektör).
6. **CellMapper / OpenCelliD kontrolü:** Şablon `cellmapper_check_template.xlsx` (46 saha). Önce
   **SITE_000440, SITE_000206, SITE_000224** CellMapper'da elle kontrol edilecek (bant/EARFCN, sektör
   sayısı, azimut). Koordinatta ölçüm yoksa ~300 m çevresine bakılacak; yetmezse ana yol/otoyol gibi
   ölçümün bol olduğu yerlere. Toplu veri çekme kullanım koşullarını ihlal edebilir; elle bakılmalı.

## 9. Açık görevler (önerilen sıra)

1. **Deney 15'in devamı — bina içi kayıp ve anten eğimi:** TA'ya göre yerleştirmeyi koruyup ns-3
   senaryosuna (a) sabit bir bina içi kayıp, (b) dikey anten deseni / downtilt eklemek; yalnız bu iki
   değeri 5 sahayla ayarlayıp 3 sahada sınamak. Amaç: "kullanıcıyı uzağa koyarak telafi" yerine fiziksel
   açıklama. (Kullanıcıya bu soruldu, cevap bekleniyor: ekle mi, önce hocaya mı soralım.)
2. **CellMapper kontrolü** (440, 206, 224) ve şablonun doldurulması. Uygulama tarayıcısıyla yapılacaksa
   kullanıcıdan onay alınmalı (saha koordinatları dış siteye girilecek).
3. **Hocanın gruplamasıyla yeni senaryo:** 440'ı 3 katmanlı kurmak, diğerlerini S0 gibi; frekansı TA'ya göre.
4. **Handover** eklemek ve test etmek.
5. **Başka bölge:** Bölge ayarlarını tek dosyada toplamak (`region.yaml` fikri, henüz yok), benzer büyüklükte
   bir bölge seçmek (şehir merkezi / sahil), önce Sındırgı ayarlarıyla denemek.
6. **Stres testi:** Yoğun saat yükünden başlayıp (a) PRB yükünü, (b) eşzamanlı kullanıcı sayısını adım adım
   artırmak; S0 ve S2'de; başarı ölçütleri koşudan önce yazılmalı.

## 10. Turkcell'e / hocaya açık sorular

- Hücrelerin bandı / EARFCN'i, taşıyıcı başına güç, hangi hücrelerin aynı sektörde olduğu.
- Experia SINR/RSRQ'nun hangi kanal ve ortalamayla hesaplandığı.
- KPI CQI tablosu (64QAM/256QAM), throughput ve trafik hacmi birimleri.
- KPI saatlerinin yerel saat olduğunun teyidi (deprem sıçramaları 19:45 ve 22:45 dilimlerinde).

## 11. Kullanıcıyla çalışma notları

- Kullanıcı Türkçe konuşuyor; konuya yeni. Açıklamalar sade, örnekli ve terimler açıklanarak yapılmalı
  (bkz. `toplantilar/2026-11-15_ilk_asama_ozeti/BASIT_ANLATIM.md`).
- Hocaya giden metinler kısa, akıcı, "yapay zekâ yazmış gibi" durmayan, gereksiz veri ayrıntısı içermeyen
  Türkçe olmalı; ana bulgular öne çıkmalı.
- "Eğitim/kontrol sahası" yerine "ayarda kullanılan / kullanılmayan sahalar (holdout)" denmeli.
- Commit ve push yalnız kullanıcı isteyince; doğrudan `main` dalına (kullanıcı onayladı). Commit mesajları
  Türkçe ve ekip arkadaşlarının anlayacağı şekilde.
