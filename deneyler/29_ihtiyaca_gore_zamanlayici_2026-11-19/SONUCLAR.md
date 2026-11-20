# 29 — Zamanlayıcı düzeltmesi ve ses kapasitesi

**Neden bu deney:** ns-3'ün PF zamanlayıcısı, verisi olan her kullanıcıya bütün boş kaynak bloklarını veriyordu (deney 28).

**Düzeltme:** Özel `libns3-lte` kopyasına bir ayar eklendi (`build_private_lte.py`, 3. yama, `--pf-buffer-aware 1`). Bu ayar açıkken bir kullanıcı, kuyruğundaki veri aldığı bloklara sığdığı anda o milisaniye (TTI) için başka blok almıyor. Kimsenin ihtiyaç duymadığı bloklar boş kalıyor; o bloklarda yayın ve girişim olmuyor.

Bunun dışında model, deney 26'daki yeni modelin aynısı.

## 1. Kontrol: eski sonuçlar aynen çıkıyor mu

Düzeltme kapalıyken simülasyon, deney 16'nın sonuç dosyalarını bayt bayt aynı üretti (6/6 dosya). Ayrıntı `regression.json`'da.

## 2. Yük ayarı (`calibration/calibration.json`)

| Deneme | Yük katsayısı | Hücre doluluğu (hedef 0,233) |
|---|---|---|
| 1 (deney 26'nın katsayısı) | 1,243 | 0,034 |
| 2 | 0,182 | 0,307 |
| 3 | 0,239 | 0,254 |
| 4 (sabitlendi) | **0,261** | **0,228** (hedeften %2 sapma) |

- Deney 26'daki arka plan trafiği, düzeltilmiş zamanlayıcıyla hücreleri sadece %3,4 dolduruyor. Yani eski zamanlayıcı aynı trafiği yaklaşık 7 kat fazla yer kaplıyormuş gibi gösteriyordu.
- KPI'daki doluluğa ulaşmak için arka plan trafiğini yaklaşık 4,8 kat artırmak gerekti.

## 3. Test sahalarında doğruluk (3 anten yönü çekilişi; 256 kullanıcının hepsi bağlandı)

Tablodaki değerler ortalama mutlak hatadır (MAE), dB cinsinden.

| | Deney 26 (eski zamanlayıcı) | Deney 29 (düzeltilmiş) |
|---|---|---|
| Test sahası SINR hatası | 2,6 dB | **1,9 dB** (1,2 / 2,3 / 2,2) |
| Test sahası RSRP hatası | 4,8 dB | 4,8 dB (2,8 / 4,1 / 7,5) |
| Ayar sahası SINR hatası | – | 2,9 dB (2,5 / 2,9 / 3,1) |

- SINR biraz iyileşti.
- RSRP değişmedi. Bu beklenen bir sonuç: RSRP zamanlayıcıdan bağımsız.
- Bu yüzden deney 29 modeli yeni başvuru modeli olarak kullanılıyor.

## 4. Ses kapasitesi

Kullanıcılar deney 28'dekilerle aynı yerlerde. Kurulum aynı:
- Görüşmeler AMR 12,2 kbps.
- Bir kullanıcı "konuşabiliyor" sayılır: paketlerinin en az %99'u 100 ms içinde ulaşıyorsa.

| Hücre başına görüşme | Konuşabilen (28 → 29) | Ortanca gecikme (28 → 29) | Hücre doluluğu (28 → 29) |
|---|---|---|---|
| 25 | %84 → %79 | 27 → 14 ms | %93 → %26 |
| 50 | %86 → %81 | 38 → 14 ms | %99 → %36 |
| 100 | %34 → **%82** | 61 → 14 ms | %100 → %48 |
| 200 | – → **%84** | – → 14 ms | – → **%72** |
| 300 | – | – | – (durduruldu, aşağıya bakın) |

Bütün adımlarda bütün kullanıcılar şebekeye bağlandı.

**Okuma:**
- Düzeltilmiş zamanlayıcıyla 200 görüşmede bile şebeke tıkanmıyor: gecikme 14 ms'de sabit, konuşabilenlerin oranı düşmüyor (%84).
- Ama hücreler dolmaya başlıyor: doluluk 100'de %48, 200'de %72. En dolu hücreler (443 ve 444 sahaları) %84–87'de. Sınır büyük ihtimalle hücre başına 250–300 görüşme civarında.
- 200'de sinyal kalitesi de düşüyor: ortanca SINR 14 dB'den 9 dB'ye iniyor, çünkü dolu hücreler komşulara daha çok girişim yapıyor. Buna rağmen gecikme ve konuşabilenler değişmedi.
- 300'lük adım başlatıldı ama yaklaşık 18 saat sürecekti; bilgisayarın kapatılması gerektiği için 8 saat sonra durduruldu ve yarım kalan dosyaları silindi. Sınırı tam görmek için 300 daha hızlı derlenmiş bir ns-3 ile tekrar koşulacak.
- Depremde hücre başına en yüksek yük: ×2 varsayımıyla ~69 kullanıcı bulunmuştu. KPI'dan doğrudan ölçülünce (deney 32) en yoğun hücre 443'te ortalama ~91, en yoğun 15 dakikada ~101 bağlı kullanıcı çıktı. Bu da 200'ün yaklaşık yarısı.
- Konuşamayan yaklaşık %20'lik pay yükle değişmiyor. Bu kullanıcılar, deney 26/28 yerleşimiyle sahadan uzağa (TA'ya göre 15 km'ye kadar) düşen ve sinyali zayıf olanlar.
- V25 için sinyal kalitesine göre konuşabilenler:

| Sinyal kalitesi (SINR) | Konuşabilen |
|---|---|
| 0 dB altı | %0 |
| 0–3 dB | %35 |
| 3–10 dB | %69 |
| 10 dB üstü | %90 |

- Yani bu sonuç bir kapasite sınırı değil, kapsama sınırı.
- Modelde sinyali 0 dB'nin altında kalan görüşmeci oranı %4. Experia saatlik kayıtlarında bu oran yaklaşık %1, ama bu bir alt sınır. Yani model bu açıdan gerçeğe yakın.

**Açık noktalar ve sonradan yapılan inceleme (20 Kasım):**

*Ölçütün kaynağı bulundu.* ITU-R M.2135-1 (IMT-Advanced değerlendirme kılavuzu), §7.1.3:
- 12,2 kbit/s kodek, %50 konuşma payı.
- Paketlerinin %98'inden azı 50 ms içinde ulaşan kullanıcı "kesintide" sayılır.
- Kesintideki kullanıcılar %2'den az olmalı.

Bizim ölçütümüz bundan biraz farklıydı: %99 ve 100 ms. ITU ölçütüyle yeniden puanlanınca konuşabilenler %79–83'ten %79–86'ya çıkıyor; sonuç pek değişmiyor. (`voice.csv` 50 ms sınırını doğrudan vermiyor; bu yüzden alt ve üst sınır hesaplandı.) Ayrıca bizim modelde konuşma payı %100, yani ITU'nun iki katı trafik var. Bu, kapasite sonucunu daha da kötümser yapıyor.

*Konuşamayanlar neden konuşamıyor?*

| Sinyal kalitesi (SINR) | Konuşamayan, 25 görüşme | Konuşamayan, 200 görüşme |
|---|---|---|
| 0 dB altı | %93 | %78 |
| 0–3 dB | %64 | %23 |
| 3–10 dB | %27 | %5 |
| 10 dB üstü | %8 | %1 |

- Başarısızlıkların çoğu paket kaybı. Kaybeden kullanıcılar paketlerinin ortanca %7–9'unu kaybediyor; en uzun gecikme ~150 ms.
- **Sinyali iyi olanlar ağ boşken daha çok başarısız oluyor.** Bu fiziksel olarak beklenen bir şey değil.
- Muhtemel sebep şu. Ağ boşken komşu hücreler çoğu zaman susuyor. Telefon sinyal kalitesini bu sessiz anlarda ölçüp iyi bildiriyor ve baz istasyonu hızlı bir kodlama seçiyor. Ama veri gönderildiği anda komşular da aynı kaynak bloklarında gönderiyor (ns-3 zamanlayıcısı blokları hep bandın başından dolduruyor). Paket bozuluyor; birkaç yeniden gönderimden sonra kayboluyor. Ağ doluyken girişim sürekli olduğu için ölçüm ile gerçek tutuyor.
- Gerçek baz istasyonları bunu bir düzeltme döngüsüyle önler (outer-loop link adaptation): paketler bozuldukça seçilen kodlamayı otomatik olarak düşürür. ns-3.44'ün LTE modülünde böyle bir döngü yok; kaynak kodunda arandı, bulunamadı.
- **Sonuç:** Normal günde görülen "%15–20 konuşamıyor" sonucunun önemli bir kısmı büyük ihtimalle ns-3'ün bu eksikliğinden geliyor, gerçek bir kapsama sorunundan değil. SINR'ı 0 dB altında olanların başarısız olması ise gerçek bir kapsama sınırı.
- Bu açıklama henüz doğrudan kanıtlanmadı. ns-3'ün fiziksel katman kayıtlarıyla (her paket için seçilen kodlama ve bozulup bozulmadığı) kısa bir koşuda sınanabilir.

*Hiç paket almayanlar:* 25 görüşmede 10 kullanıcı (ortanca SINR 1,8 dB, RSRP −120 dBm), 200 görüşmede 41 kullanıcı (ortanca SINR −6 dB, RSRP −129 dBm). 200'dekiler kapsama dışı. 25'tekiler sınırda; bunlar da aynı kodlama uyuşmazlığından etkileniyor olabilir.
