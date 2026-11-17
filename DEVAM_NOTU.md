# Devam notu — projeyi başka bir bilgisayarda / başka bir yapay zekâyla sürdürmek için

Son güncelleme: 17 Kasım 2026. Bu belge, projeye hiç bakmamış birinin (insan ya da yapay zekâ) kaldığımız
yerden devam edebilmesi için yazıldı. Önce bunu, sonra gerekirse bağlantı verilen raporları okuyun.

---

## 0. Devralma özeti — önce bunu okuyun

**Aktif koşu yok. Deney 16, 17, 18 ve 19 tamamlandı. Tamamlanmış koşuları yeniden başlatmayın.**

- **Ana referans S0:** Ölçüm uyumu için Deney 14'ün S0 sonuçları kullanılıyor. Gruplamalı alternatif
  Deney 17'de kuruldu, Deney 18'de yükü eşlendi; S0'dan daha iyi ölçüm uyumu göstermedi.
- **Handover hazır:** Deney 19'da S0'a X2 + A3 RSRP eklendi ve bütün kontroller geçti. Yeni handover
  gereken S0 işleri bu yerel koddan ilerlemeli; özellik `--handover 1` ile açılır, varsayılan kapalı.
  Çok taşıyıcılı handover ve tam ağda hareket/arıza/UAV performansı henüz doğrulanmadı.
- **Sıradaki önerilen iş:** S0 üzerinde önceden planlanmış yük/stres pilotu; önce trafik yükü,
  sonra eşzamanlı kullanıcı sayısı ayrı ayrı artırılacak. Sonra saha kesintisi ve UAV. Deney 20
  henüz oluşturulmadı; kullanıcı yalnız durum sorarsa kendiliğinden yeni kampanya başlatmayın.
- **Okuma sırası:** Bu belge → [Deney 19](deneyler/19_s0_handover_2026-11-17/SONUCLAR.md) →
  [Deney 18](deneyler/18_tasiyici_yuk_esleme_2026-11-16/SONUCLAR.md). Önceki denemeler gerekiyorsa
  [Deney 17](deneyler/17_saha440_gruplama_2026-11-16/SONUCLAR.md) ve
  [Deney 16](deneyler/16_bina_anten_2026-11-16/SONUCLAR.md).
- **Git:** Commit/push yapılmadı. Deney 16–19 bu çalışma klasöründe mevcut, henüz Git'e eklenmemiş.
  Başka AI aynı klasörü açarsa dosyaları görür; yalnız GitHub'dan çekerek bu oturumun dosyalarını alamaz.
- **İletişim:** Kullanıcı kısa, sade Türkçe ve düzenli dosyalar istiyor. Tek deney/tek sonuç raporu;
  30 saniyelik izleyici veya sık durum mesajı istemiyor. İstemediği eski koşuları gereksiz yere tekrarlamayın.

## 1. Proje ne?

Turkcell'in Sındırgı (Balıkesir) bölgesindeki LTE ağının **ns-3.44 (klasik LTE/EPC modülü)** ile
ölçümlerden beslenen, **temsili** bir kopyasını kurmak. Birebir kopya iddiası yok; hocanın ifadesiyle
"measurement / real-service informed, full replay değil". Sonraki aşamalarda bu ağ üzerinde deprem anı
yükü, stres testi, saha kesintisi, öncelikli bölgeler ve UAV (dron baz istasyonu) çalışılacak.

- **Danışman (hoca):** Evşen Yanmaz Adam. Kendi notları `ana_proje/advisors notes.txt`; yöntem taslağı
  `ana_proje/main.tex` (kırmızı = hocanın notları, mavi = bizim eklediklerimiz).
- **Ekip:** Repo sahibi GitHub'da `buseinc` (`https://github.com/buseinc/Turkcell`). Çalışmanın çoğu bu
  önceki oturumda 20umu kullanıcılı başka bir Windows bilgisayarda yapıldı; güncel ortam aşağıda.
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

- **Güncel bilgisayar:** `C:\Users\bi025305\Downloads\paylasim\Turkcell`, PowerShell.
- **Windows analiz:** `.venv/Scripts/python.exe`, Python **3.10.22**; numpy 2.0.2, pandas 2.2.3,
  openpyxl 3.1.5 doğrulandı. Komutlarda `-X utf8` kullanın; düz `python` PATH'te yok.
- **Simülasyon:** `wsl -d Ubuntu-22.04`, Python 3.10.12, ns-3.44
  **`/home/buse/ns3/ns-3.44`**, profil `default`. Kurulum ve LTE kütüphaneleri hazır.
  Güncel CMake kaydında LTE örneği yok; yerel çalıştırıcılar derleyici seçenekleri için stok
  `perf-io.cc` kaydını yedek olarak kullanıyor. Ns-3 kaynakları değiştirilmedi.
- Önceki bilgisayarda Python 3.12, WSL `Ubuntu` 24.04 ve `~/ns-allinone-3.44/ns-3.44` kullanılmıştı.
  Eski sonuçlardaki bu yolları güncel bilgisayar ayarı sanmayın. `ns3_paths.py` / `NS3_ROOT` taşınabilirliği var.
- WSL ilk erişimde takılmıştı; kullanıcı talimatıyla hizmet yönetici yetkisiyle yeniden başlatıldı ve
  bütün deneyler tamamlandı. Şu an yeniden kurma/yeniden başlatma gereği olduğuna dair bulgu yok.

Komut alışkanlıkları:
- Windows: `.venv/Scripts/python.exe -X utf8 <script>`.
- WSL: `wsl -d Ubuntu-22.04 --cd /mnt/c/Users/bi025305/Downloads/paylasim/Turkcell/deneyler/<deney> --exec python3 <script>`.
  Bunlar sözdizimi örneği; bitmiş `study.py` kampanyalarını sırf kontrol için tekrar çalıştırmayın.
- Git Bash kullanılırsa `MSYS_NO_PATHCONV=1` gerekebilir. Güncel oturum PowerShell kullandı.
- Tam 4 saniyelik senaryo gerçek zamanda yaklaşık 17 dakika, üç paralel koşu yaklaşık 25–30 dakika
  sürebildi. Girdiye ve bilgisayara göre değişir; koşu öncesi amacı ve zaman maliyetini kısaca açıklayın.

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
4. Simülasyon C++ kodu veya dahil edilen başlık değiştiğinde bir eski koşuyla davranış korunumu sınanır.
   Karşılaştırma yalnız CRLF→LF normalizasyonu sonrası bayt düzeyindedir; yuvarlama/satır sıralama yok.
   Kod/binary aynıysa, hash'leri eşleşen mevcut doğrulama yeniden kullanılabilir; gereksiz tam tekrar yapmayın.
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
| 15 | Kullanıcıları TA'ya göre yerleştirme | Kontrol RSRP farkı 1,7→3,3 dB. Önceki uyum yerleşim varsayımına duyarlı; bina/dikey desen açıklama adayıydı, bunların sorunu çözdüğü kanıtlanmadı. |
| 16 | TA + bina kaybı/dikey desen | 9 koşu tamamlandı. Seçilen 6 dB + 0° dikey desen, ayar sahalarını iyileştirdi fakat kontrol RSRP farkı 3,28→5,01 dB oldu. Kabul edilmedi. |
| 17 | Hocanın strong grupları | 198/220/224/440 grupları, diğer 20 saha tek B3; 99 hücre. B20/B3/B1 TA'ya göre varsayım. Kontrol RSRP/SINR farkı 2,64/3,61 dB; B20 yükü düşük kaldı. |
| 18 | Yalnız B20 yük eşlemesi | Kod/RF aynı; 14 yük kullanıcısının aralığı 5,021216 ms. B20 PRB 0,093→0,226, hedef 0,233; üç örnek geçti. Kontrol RSRP/SINR 2,64/3,44 dB. S0 daha yakın. |
| 19 | S0 handover | Kapalı S0 tekrar kontrolü, 6 hareket açık/kapalı testi, 3 tam sabit S0 A3 testi geçti. Otomatik 441→443 geçişi doğrulandı; S0 hücreleri ve RSRP korundu. |

Her deneyin ayrıntısı kendi `SONUCLAR.md` dosyasında.

## 6. Güncel temel senaryo (S0) ve sonuçları

Tanım: 24 saha, 3 sektör, tek taşıyıcı (Band 3, 1815 MHz, 20 MHz), 49 dBm, 120° CosineAntenna 15 dBi,
eNB 30 m / UE 1,5 m, log-distance üs 3, gölgeleme yok, NF 9 dB, PF zamanlayıcı, mixed CQI, 256 ölçüm
kullanıcısı (ana sahalara 2–6 km kümeler), her hücreye 1 yük kullanıcısı (KPI günlük ortalama PRB 0,233,
katsayı 1,47), rastgele UDP başlangıcı, 4 s koşu / 1 s ısınma, 3 örnek. Kod ve girdiler:
`deneyler/14_cok_tasiyici_s2_2026-11-15/` (senaryo adı `S0`).

Handover gereken yeni S0 işleri için `deneyler/19_s0_handover_2026-11-17/simulation/` kodu ve
`--handover 1` kullanılır. Deney 19 ayrı bir entegrasyon kopyasıdır; eski S0 değiştirilmedi.
Yukarıdaki radyo uyumu sayıları Deney 14 referansına aittir; yeni handover testinin kapsamı bölüm 15'te.

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
- **Hareketli kullanıcı ölçümleri:** Eski `metrics()` yalnız son hizmet hücresinin örneklerini tutar;
  hareket/handover analizinde geçiş öncesi veriyi kaybettirir. Deney 19'un olay, zaman çizgisi ve paket
  kayıtları üzerinden analiz edin. Statik testlerde mevcut metrics() kullanılabilir.
- **Handover varsayılan kapalı:** Yeni çalışmalarda gerekiyorsa `--handover 1` açıkça verilmeli.
  Deney 19 yalnız aynı frekansta S0'ı doğrular; çok taşıyıcılı girdiyle handover şu aşamada reddedilir.
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
4. **Handover istendi** (X2 + A3 RSRP); 17 Kasım'da Deney 19 ile S0 için tamamlandı.
5. **Hücre gruplaması:** Hocanın dosyaları ardışık hücre numaralarını (üçlü bloklar) taşıyıcı katmanı,
   blok içini sektör sayıyor; katmanları TA'ya göre sıralıyor (uzun menzil = düşük bant). Bantlar hipotez.
   Talimat: güveni yüksek gruplar dosyadaki gibi, diğerleri tek taşıyıcı 3 sektör 1800 MHz; çok
   taşıyıcılıda frekans TA'ya göre (yüksek TA = düşük frekans). Sekiz ana değerlendirme sahasında
   yalnız **440 strong** (3 taşıyıcı × 3 sektör). Güncel tüm ağ v2 dosyası 24 sahalık bölgeye
   uygulandığında komşu **198 (3+3+3), 220 (4+3+4), 224 (3+4+3)** de strong; tam senaryoya dahiller.
6. **CellMapper / OpenCelliD kontrolü:** Şablon `cellmapper_check_template.xlsx` (46 saha). Önce
   **SITE_000440, SITE_000206, SITE_000224** CellMapper'da elle kontrol edilecek (bant/EARFCN, sektör
   sayısı, azimut). Koordinatta ölçüm yoksa ~300 m çevresine bakılacak; yetmezse ana yol/otoyol gibi
   ölçümün bol olduğu yerlere. Toplu veri çekme kullanım koşullarını ihlal edebilir; elle bakılmalı.

## 9. Açık görevler (önerilen sıra)

1. **S0 yük/stres pilotu:** Trafik yükü ve eşzamanlı kullanıcı sayısını ayrı deney kollarında artırın.
   Seviye, süre, tohumlar ve başarı/bozulma ölçütlerini koşudan önce yazın. S0 handover kodu hazır.
   Önce küçük pilot; rastgele geniş ayar taraması veya aynı bitmiş koşuların tekrarı değil.
2. **Saha kesintisi:** Stres davranışı anlaşıldıktan sonra bir sahayı kapatıp kapsama, bağlantı ve
   hücre geçişlerini değerlendirin. Henüz uygulama veya sonuç yok.
3. **Öncelikli bölgeler / UAV:** Ardından dron konumu, rota ve öncelik tasarımı. Henüz yapılmadı.
4. **Hocaya kısa durum özeti:** Gerekirse S0'ın referans kalma nedeni ve alternatifin belirsizliklerini
   özetleyin; kullanıcı açıkça istemeden hocaya veya başka birine mesaj göndermeyin.
5. **Ek işler:** Benzer büyüklükte şehir/sahil bölgesi ve çok taşıyıcılı handover henüz açık.
   `region.yaml` henüz yok. Bunlar güncel S0 stres pilotunu otomatik engelleyen önkoşul değildir.
6. **RF doğrulaması:** Gerçek bant/EARFCN/güçler ve TA'ya dayalı yerleşim belirsizliği açık kalır.
   CellMapper destekleyicidir; varsayımları açıkça işaretleyerek ilerlemeye hoca izin verdi.

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
- Kullanıcı dosya düzenine özellikle önem veriyor: gereksiz dosya/rapor sürümleri oluşturmayın.
  Her deney tek klasörde, kullanıcıya yönelik sonuçlar tek `SONUCLAR.md` içinde tutulsun;
  teknik girdiler, simülasyon çıktıları ve günlükler kendi alt klasörlerinde kalsın.
- Ara mesajları ve 30 saniyelik rapor güncellemesini istemiyor; sormadıkça sonuçta haber verin.
  Uzun bir kontrol gerekiyorsa başlamadan önce nedenini kısaca açıklayın. Aynı kod/girdilerle geçen
  kontrolleri cache/hash eşleşmesi varsa kullanın; sırf yeni oturum diye yeniden koşmayın.

## 12. Deney 16 — tamamlandı, tekrar başlatmayın

Klasör: `deneyler/16_bina_anten_2026-11-16/`.

- TA yerleşimi korunup sabit bina kaybı ve dikey desen/eğim sınandı. Önce 3 örnekte analitik
  tarama, ardından seçilen birleşik aday ve iki ayrı etki için 9 ns-3 koşusu tamamlandı.
- Seçim yalnız 5 ayar sahasıyla yapıldı: 6 dB ek kayıp, dikey desen açık, eğim 0°.
  Ayar RSRP farkı 8,25→4,68 dB iyileşti; kontrol farkı 3,28→5,01 dB kötüleşti. Kabul edilmedi.
- Bütün 256 ölçüm kullanıcısı bağlandı. Kayıplı iki senaryoda 242–246 kullanıcı 4 saniyede DL veri aldı;
  eski TA ve yalnız dikey desen 255–256 idi. Bu, tek başına kalıcı kapsama kesintisi kanıtı değildir.
- Bina kaybı yalnız ölçüm kullanıcılarına, dikey desen tüm eNB–UE bağlantılarına DL/UL uygulanır.
  Kodun 12 küçük kontrolü ve etkiler kapalı eski TA koşusu karşılaştırması geçti.
- Çıktılar/kanıtlar: `SONUCLAR.md`, `comparison.json`, `result.json`, `regression.json`.
  WSL onarımının tek kullanımlık betiği/günlüğü `logs/` altında; hizmet tekrar başlatılmayacak.
- Sonuç: Bina/eğim etkilerinin gerçekten bulunmadığı değil, bu basit ortak varsayımın genel çözüm
  sağlamadığı gösterildi. Saatlik ortalama TA ve rastgele yönler gerçek kullanıcı konumlarını vermez.

## 13. Deney 17 — hocanın tam gruplaması tamamlandı

Klasör: `deneyler/17_saha440_gruplama_2026-11-16/`. Adı ilk 440 incelemesinden kalmıştır;
son kapsam yalnız 440 değil, mevcut bölgenin bütün strong sahalarıdır. Yeni klasör/rapor kopyası açılmadı.

- Güncel `all_sites_cell_layers_v2.xlsx` esas: **198 (3+3+3), 220 (4+3+4), 224 (3+4+3), 440 (3+3+3)**.
  Diğer 20 saha tek B3, üç sektör. Dört sektörlü bloklar gerçekten dört ayrı yönle kuruldu.
- Her strong sahada blokların Experia TA medyanı sırası: en yüksek→B20, orta→B3, en düşük→B1.
  Bu, hocanın izin verdiği senaryo varsayımıdır; gerçek bant eşleşmesi doğrulanmadı.
- B3: EARFCN1300/1815 MHz/20 MHz; B20: 6400/816 MHz/10 MHz; B1: 100/2120 MHz/20 MHz.
  Her hücre 49 dBm, 15 dBi kazanç, 120° yatay genişlik. Üçlü blokta yön aralığı 120°, dörtlüde 90°.
- 99 hücre = 72 B3 + 14 B20 + 13 B1. 256 ölçüm + 99 yük = 355 kullanıcı.
  Ölçüm kullanıcılarının S0 konumları ve eski 72 B3 yük kullanıcısı aynen korundu.
- S0 analitik B3 hesabında strong sahaya bağlanacak ölçüm kullanıcıları kimlik sırasıyla üç banda
  dengeli atandı; diğerleri B3 kaldı. Gerçek bant kullanıcı payları bilinmiyor. Otomatik inter-frequency
  seçim, CA veya handover iddiası yok. Eşleme ayrıntısı `plan.json/runtime/block_band_mapping` içindedir.
- 27 yeni yük kullanıcısı 800 m boresight'a kondu. İlk yük kuralı `(1,47/0,233)*(100/RB)` ms;
  dar B20 taşıyıcısına yarı paket hızı. Toplam sunulan yük trafiği %27,8, hücre/güç sayısı %37,5 arttı.
  Yalnız frekans etkisi olarak yorumlanamaz.
- Üç koşu bitti. Kontrol MAE RSRP/SINR **2,64/3,61 dB**, S0 **1,72/2,15 dB**. 440'taki ortalama
  işaretli RSRP farkı +0,08→+3,31 dB; diğer yedi değerlendirme sahasının RSRP'si aynı kaldı.
- B20 PRB hedefi .233 iken .093 kaldı; bu yük farkı Deney 18'de düzeltildi. Sonuçlar hocanın
  gruplamasının yanlış olduğunu kanıtlamaz; bant, güç ve kullanıcı payı varsayımları belirsizdir.
- Teknik düzeltme: Dört sektörde 360°'yi aşan yönler modulo 360'a çevrildi. Bilimsel girdiler değişmedi;
  kaynak değişikliği plan'a kaydedildi. Son kaynakla S0 ve üç koşu tekrarlandı; 20 kod kontrolü geçti.
  İlk başarılı 703'ün altı CSV'si düzeltme sonrası da birebir aynıydı.
- Kanıtlar: `SONUCLAR.md`, `comparison.json`, `result.json`, `regression.json`. Bütün koşular tamamlandı.

CellMapper ve kaynak sürümleri:

- Kullanıcı 440/206/224 koordinatlarında kule göremedi. Bu, gerçek kule yokluğu kanıtı değil.
  300 m çevrenin ayrıca sistematik tarandığı kesinleşmedi; hedef bant alanları boş bırakıldı.
- Güncel v2'de 206 **moderate**, 3+3+3+3. Eski şablonda 4+4+4 ve farklı p-değeri var.
  440'ın güncel p=.017 değeriyle eski şablon p=.055 aynı sürüm değil.
- Tarayıcı bağlantı hizmeti kullanılamadı; yerel arayüz aracı URL'yi güvenilir belirleyemediği için durdu.
  Kullanıcı ekran görüntüleriyle elle ilerledi. Kontrol engeli aşılmaya veya toplu veri çekmeye çalışılmadı.
- Kullanıcı yol üzerindeki **kule13062** panelini paylaştı: 286/1, Region6163, MACRO.
  B20 6400/816 MHz, B3 1651/1850,1 MHz, B1 100/2120 MHz ve eski alternatif kanal kayıtları var.
  B3/B20 bazı kayıtları Haziran2026, B1 kayıtları 2024, bazı alternatifler 2021'de kalıyor.
  Bu liste aynı anda aktif sekiz hücre veya kesin üç sektör kanıtı değil. Kule hedef sahalara eşleşmedi.
  900 MHz bu örnekte gözlenmedi. Ham kullanıcı aktarımı aynı Deney 17 rapor/planında kayıtlı.

## 14. Deney 18 — yalnız B20 yük eşlemesi tamamlandı

Klasör: `deneyler/18_tasiyici_yuk_esleme_2026-11-16/`; 16 Kasım'da başlayıp 17 Kasım'da tamamlandı.

- C++ kaynak, binary, RF ayarları, hücreler ve tüm kullanıcı konumları Deney 17 ile aynı.
  Hash'lerle doğrulandı. Kod değişmediği için pahalı S0 tekrar koşusu yapılmadı; 20 küçük kontrol tekrarlandı.
- **Yalnız 14 B20 yük kullanıcısının `udp_interval_ms` alanı değişti.** B1 zaten hedef aralığındaydı;
  B1/B3 ve ölçüm kullanıcılarının trafiği değiştirilmedi. Kaynak/girdi fark kontrolü tam 14 alanı doğruladı.
- Hedef PRB .233. 701'de bütün B20 hücrelerinin yalnız benzetim PRB ortalaması kullanıldı;
  440 yük sayacı dahil, fakat hiçbir Experia RSRP/SINR hatası ayar seçimine girmedi.
- İki yeni pilot: 6,309013 ms→.18544; **5,021216 ms→.227017**. İkinci pilot önceden yazılan ±%5
  aralığına girince sabitlendi. 701 yeniden çalıştırılmadı; aynı aralık 702/703'e uygulandı.
- Nihai B20 PRB: **.227017/.226103/.224960**. Üç örnekte B20/B1 hedef ±%10 ve ağ PRB farkı S0'a
  göre ≤.03 kontrolleri geçti. 702/703 görüldükten sonra yeniden ayar yapılmadı.
- B20 ortalaması .093→.226; ağ ortalaması .224→.243 (S0 .254). RSRP en büyük değişimi **0 dB**;
  hücre yapısı ve taşıyıcı atamaları korundu. Bağlanan ölçüm kullanıcıları 256/256/256, DL alan 255/256/256.
- Kontrol RSRP MAE **2,64 dB**, SINR **3,44 dB** (önce3,61); S0 hâlâ1,72/2,15 dB ile daha yakın.
  Yük eşleme görevi geçti; bu, gerçek RF konfigürasyonunun doğrulandığı veya S0'ın değiştirildiği anlamına gelmez.
- Kanıtlar: `SONUCLAR.md`, `calibration.json`, `comparison.json`, `result.json`, `verification.json`.
  `load_matching_passed=true`, `load_only_invariants_passed=true`. Aktif koşu yok.

## 15. Deney 19 — S0 handover tamamlandı; bundan sonra buradan ilerlenir

Klasör: `deneyler/19_s0_handover_2026-11-17/`.

- Kaynak temiz S0/Deney14 kopyasıdır. `handover-support.h` ve isteğe bağlı X2+A3, waypoint hareketi,
  olay/zaman çizgisi/paket alış kaydı eklendi. Bina kaybı veya Deney17'nin çok taşıyıcılı değişiklikleri yok.
- `--handover 1`: A3 RSRP, **3 dB histerezis, 256 ms TTT**. Varsayılan kapalı; bu durumda kurulu
  ns-3.44'ün NoOp algoritması değiştirilmez. Aynı frekansta handover doğrulandı; çok taşıyıcılı HO girdisi reddedilir.
- X2 tam ağda 72 mantıksal sektör eNB'si arasında tam bağlıdır (2556 bağlantı). Bu bir yazılım senaryosu;
  gerçek operatörün X2 topolojisi bilinmiyor. Mevcut ideal RRC modeli korunur.
- **Kapalı eski S0 kontrolü geçti:** 701'de altı CSV yalnız CRLF→LF sonrası birebir aynı.
- **Altı hareket kontrolü geçti:** 441/443 gerçek konumları izole edildi; altı sektör eNB, bir kullanıcı,
  15 m/s hız, hattın %15'inden %85'ine hareket, uçlarda2s bekleme; toplam102,409s, 10ms/512bayt trafik.
  Üç anten yönü örneğinde açık/kapalı çiftler kullanıldı. Bu, tam72hücreli hareket/afet deneyi değil.
- A3 açık her örnekte **otomatik tek 441→443 handover**, eşleşen UE/eNB olayları, sıfır hata,
  hedefte bağlantı ve geçişten sonra veri doğrulandı. Elle HandoverRequest/target attach yapılmadı.
  Kapalı üç kontrolde0handover; kullanıcı441'de kaldı.
- UE olay başlangıç/bitiş farkı yaklaşık **4,213ms**, geçiş çevresindeki en büyük paket alış aralığı
  **120ms**. Bunlar farklı ölçülerdir;4ms gerçek veri kesintisi veya operatör gecikmesi diye sunulmaz.
- **Üç tam sabit S0 A3 testi geçti:** 256/256 ölçüm kullanıcısı bağlandı ve veri aldı;
  328/328 toplam kullanıcının hizmet hücresi korundu, RSRP en büyük değişimi0dB, gereksiz HO yok.
- `comparison.json`: **integration_passed=true**; `result.json`: completed=true. Kaynak/girdi hash'leri
  doğrulandı. Aktif koşu yok; aynı kontrolleri yeni oturum açıldı diye yeniden başlatmayın.

Yeniden kullanırken:

- Yeni deney yeni klasörde olsun; gerekliyse Deney19 `simulation/` kodunu kopyalayın. Kaynak ve başlık
  hash'leri aynıysa mevcut doğrulama kanıtını kullanın. C++/başlık değişecekse gerekli değişiklikleri
  topluca yapıp tek anlamlı davranış koruma kontrolü planlayın.
- Çalıştırıcı varsayılanları küçük tanı senaryosudur; yalnız `--handover 1` yazmak tam S0 kurmaz.
  S0 için siteler/UE dosyaları ve bütün radyo/yük seçenekleri açık verilmeli. Doğru komut örnekleri
  `simulation/results/S0_A3_draw701/result.json/command` ve plan.json içindedir.
- Hareket için `--waypoints <csv>`; alanlar `ue_id,time_s,x_m,y_m,z_m`. İlk nokta t=0'da UE başlangıç
  konumuna eşit, zamanlar artan olmalı. Noktası olmayan UE sabit kalır. Hareket analizi eski metrics()
  ile yalnız son hücreye indirgenmemeli.
- `handover_events.csv`: UE/eNB başlangıç, bitiş, hata; `serving_timeline.csv`:100ms konum/hücre/durum;
  `packet_rx.csv`: waypoint'li koşuda paket alışları. Bunlar gerçek ağ uçtan uca gecikme/kapasite
  doğrulaması değildir. Tam ağ hareket, saha kesintisi, UAV ve inter-frequency HO henüz açık işler.
- Raporu yeniden yazmak gerekiyorsa `study.py --summarize` yalnız mevcut sonuçları okur. `prepare.py`
  tekrar çalıştırılmaz. Bütün kampanyayı sırf rapor görmek için yeniden başlatmayın.

## 16. Bu devir sırasında yapılan son kontrol

17 Kasım'da Deney16–19 `result.json` dosyalarında completed=true; Deney19 integration_passed=true
olduğu kontrol edildi. Raporlar mevcut. Git durumunda README/DEVAM_NOTU/CALISTIRMA_REHBERI değişik ve Deney16–19
henüz eklenmemiş. Commit/push yapılmadı. Bir sonraki AI aynı çalışma klasöründen devam etmeli.
