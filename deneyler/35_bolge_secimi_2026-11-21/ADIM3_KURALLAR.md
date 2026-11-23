# Edremit kıyısı, adım 3: model kurma ve doğrulama kuralları

21 Kasım'da, hiçbir model sonucu görülmeden yazıldı. Hesaplar hızlı modelle yapılıyor (formülleri ns-3'ünkilerle aynı). Sonunda tek bir kısa ns-3 koşusuyla iki modelin bu bölgede de aynı sonucu verdiği kontrol edilecek.

## Sabit kalanlar (Sındırgı'daki son modelle aynı)

- **Verici:** 49 dBm, 20 MHz, 1800 MHz bandı (EARFCN 1651).
- **Anten:** 15 dBi, 3GPP deseni, 6° eğim, 30 m yükseklik.
- **Diğer:** %8 verici kusuru (EVM), 9 dB alıcı gürültüsü, her sahada 3 sektör ve tek frekans.
- **Gölgeleme ve görüş hattı:** Deney 34'teki yumuşak gölgeleme ve konuma göre değişen görüş hattı.
- **Anten yönleri:** Bilinmiyor. Üç çekiliş yapılıyor (tohum 42, 7, 99): saha kimliklerine göre sıralanmış her saha için 0–120° arası rastgele bir açı. Sektörler bu açı, +120° ve +240°.

## Kullanıcılar

- **Ölçüm kullanıcıları:** Her ana sahanın çevresine 32 kullanıcı; toplam 256.
- **Uzaklık:** O sahanın Experia saatlik TA kayıtlarından rastgele bir kayıt seçilir (TA × 4,88 m, 100 m–15 km arasına sınırlı). Bu, Sındırgı'daki kural A.
- **Yön:** Rastgele seçilir. Nokta denize düşerse yön en çok 50 kez yeniden çekilir; yine olmazsa uzaklık da yeniden çekilir.
- **Kara/deniz:** `kiyi.py` testine göre.
- **Hücre yükü:** Her sektörün kapasite kullanımı, o sahanın KPI'daki ortalama PRB'si alınır. Deprem günleri (10 Ağustos, 27–28 Ekim) hariç tutulur. Yük kullanıcısı kullanılmıyor; yük doğrudan ölçümden geliyor.

## Hedef değerler (Experia)

- **Hücre seçimi:** Ana sahaların en az 100 saatlik kaydı olan hücreleri.
- **Saha hedefi:** Hücre ortalamalarının ortalaması alınır; sinyal gücü (RSRP) ve sinyal kalitesi (SINR) için ayrı ayrı. Sındırgı'daki gibi.
- **Eğitim ve test:** 8 ana saha, kimliğe göre sıralanıp 3'ü test için ayrılır. Seçim `numpy.random.default_rng(35).choice(8, 3, replace=False)` ile yapılır. Test sahalarına model seçiminde hiç bakılmaz.

## Mesafe düzeltmesi (Sındırgı'daki deney 22 ve 26 yöntemi)

Düzeltme = model sinyal gücü eğrisi − Experia sinyal gücü eğrisi. İki eğri de a + b·log10(d) biçiminde uydurulur.

- **Experia eğrisi:** Bölge merkezine 15 km içindeki sahaların hücreleri kullanılır; 8 ana sahanın hücreleri hariç. Hücre ortalama RSRP'si, hücre ortalama TA uzaklığına göre uydurulur (`ana_proje/analysis/radio_cell_summary.csv`). Karşılaştırma için il geneli eğri de raporlanır (Sındırgı'da kullanılan, −68,3 − 10,6·log10 d).
- **Model eğrisi:** Düzeltmesiz model sinyal gücü, ölçüm kullanıcılarının bağlı olduğu sahaya uzaklığına göre uydurulur. Üç anten çekilişi birlikte kullanılır. Her yayılım modeli için ayrı hesaplanır.

## Yayılım modeli seçimi: kırsal (RMa) mı, şehir (UMa) mı

- **Kırsal (RMa):** Sındırgı'daki model. Gölgeleme 8 dB; gölgelemenin benzer kaldığı mesafe 120 m, görüş hattınınki 60 m.
- **Şehir (UMa):** 3GPP TR 38.901, ns-3'teki formüller.
  - Gölgeleme 6 dB (UMa'da görüş hattı yokken).
  - Gölgelemenin benzer kaldığı mesafe 50 m (TR 38.901 Tablo 7.5-6), görüş hattınınki 50 m (bölüm 7.6.3.3).
  - Görüş hattı olasılığı UMa formülüyle hesaplanır.
- **Seçim kuralı:** Eğitim sahalarında saha başına SINR farkı (üç çekilişin ortalaması) küçük olan model seçilir. Fark 0,3 dB'den azsa, RSRP farkı küçük olan seçilir.

## Kabul

Seçilen modelin test sahalarındaki saha başına farkı (üç çekilişin ortalaması):
- SINR farkı ≤ 3 dB (Sındırgı'da hızlı modelle 2,0–2,5 dB)
- RSRP farkı ≤ 5 dB (Sındırgı'da ~4 dB)

Tutmazsa şöyle yazılır: "Model bu bölgede yeterince uymuyor." Kesinti ve yol adımlarına geçilmez.

## Sınır etkisi

- 24 sahalık ağ, 48 sahalık ağla karşılaştırılır. Ek 24 saha, merkeze en yakın sonraki sahalar; yükleri 0,21 (bölge KPI ortalaması).
- Ana sahalarda saha başına SINR'deki ortalama değişim < 0,5 dB olmalı. Olmazsa 48 saha kullanılır.

## ns-3 kontrolü

- Seçilen modelle bir anten çekilişi, sabit kullanıcılar, 1 saniyelik koşu.
- ns-3 ile hızlı modelin sinyal gücü, kullanıcıların ≥ %99'unda 0,01 dB içinde aynı olmalı. Bu, deney 34'teki kural 2.
- UMa seçilirse, ns-3'teki konuma bağlı görüş hattı modeline UMa olasılığı eklenir.

## Ek: Balıkesir merkez (21 Kasım, Edremit sonucu görüldükten sonra, kullanıcının kararıyla)

- **Bölge:** DISTRICT_0001 ve DISTRICT_0014. Konumdan yapılan tahmine göre Altıeylül ve Karesi.
- **Merkez:** İki ilçenin bütün sahalarının ortalama koordinatı.
- **Kurallar:** Saha seçimi, veri çıkarma ve yukarıdaki adım 3 kuralları aynen geçerli. Sınırlar da aynı: test sahalarında SINR ≤ 3 dB, RSRP ≤ 5 dB; sınır etkisi < 0,5 dB.
- **Tek fark:** Bölge karada; kara/deniz testi uygulanmıyor.
- **Edremit'ten bilinen risk:** Sık ve çok frekanslı ağda sinyal kalitesinin fazla iyi çıkması. Burada sahalar Edremit'in yaklaşık iki katı aralıklı (1,6 km). Kurallar bu riske göre değiştirilmedi.

## Ek 2: Sinyal kalitesi sapması için iki sınama (22 Kasım, Edremit ve Balıkesir sonuçları görüldükten sonra)

**Amaç:** Sık bölgelerde model sinyal kalitesini 3–5 dB fazla iyi gösteriyor. Sebep olarak iki açıklama öneriliyor; ikisi de hızlı modelle sınanacak. Sayılar sonuca bakılarak değiştirilmeyecek.

**Taban:** Adım 3'teki kırsal model (RMa) ve 24 sahalık ağ. Kullanıcılar, mesafe düzeltmesi, anten çekilişleri ve yük aynen kalıyor. Kaydedilmiş girdi dosyaları kullanılıyor.

**A, çok bant:**
- **Bantlar ve frekanslar:** Band 20 (806 MHz), Band 3 (1850,1 MHz), Band 1 (2140 MHz), Band 7 (2655 MHz). Hepsinde her sahada aynı 3 sektör ve aynı anten yönü var.
- **Ortak olanlar:** Güç yoğunluğu (kaynak bloğu başına güç) aynı. Gölgeleme ve görüş hattı aynı; aynı sahadan çıkıyorlar. Yol kaybı her bandın kendi frekansıyla hesaplanıyor (RMa).
- **Girişim:** Her bant yalnız kendi bandındaki hücrelerden girişim alıyor.
- **Yük:** Her hücrenin yükü, sahasının KPI'daki hücre başına ortalama PRB'si.
- **Ölçüm:** Her kullanıcı her bantta o bandın en güçlü hücresine göre ölçülüyor. Saha değeri, sahanın bütün (bant, sektör) hücrelerinin kullanıcı ortalamalarının ortalaması. Bu, Experia'daki "hücre ortalamalarının ortalaması" ile aynı biçim.
- **A1:** Her sahada dört bant.
- **A2:** CellMapper'da eşleşen 6 ana sahada yalnız görünen bantlar: 370 ve 105'te {1, 3, 7, 20}, 507'de {1, 3, 7}, 529'da {1, 7}, 006'da {1, 20}, 007'de {1}. Diğer sahalarda dört bant. Yalnız Edremit için.

**B, komşuların hep yayında olan sinyalleri:**
- **Gerekçe:** Gerçek telefon kaliteyi referans sinyalleri üzerinden ölçer. Komşu hücrelerin kontrol bölgesi ve referans sinyalleri yükten bağımsız olarak hep yayındadır.
- **Hep yayında olan pay** (TS 36.211'deki tipik LTE yapısı; varsayım):
  - Kontrol bölgesi: 14 sembolün 2'si → 2/14.
  - İki anten portu: kaynak bloğu başına 16 referans sinyali hücresi var; bunların 12'si kontrol bölgesinin dışında → 12/168.
  - Toplam f = 2/14 + 12/168 = 0,214.
- **Hesap:** Komşu hücrenin bir kaynak bloğundaki etkinliği f + (1 − f) × (veri yükü). Veri yükü bugünkü gibi; kaynak blokları baştan dolduruluyor.
- Yalnız bildirilen sinyal kalitesi değişiyor; sinyal gücü değişmiyor.

**Seçim ve kabul:**
- **Seçim:** Taban, A1, A2, B ve A1+B arasından, eğitim sahalarında SINR farkı en küçük olan seçiliyor. Fark 0,3 dB'den azsa RSRP farkı küçük olan seçiliyor.
- **Kabul:** Adım 3'teki sınırlar aynen geçerli. Test sahalarında SINR ≤ 3 dB, RSRP ≤ 5 dB.
- **Balıkesir merkez:** Aynı yöntem uygulanıyor; A2 yok.
- **Sındırgı kontrolü:** B veya A1+B seçilirse, B Sındırgı'ya da uygulanıyor. Sındırgı'nın üç doğrulama durumunda saha başına SINR farkı eskisinden en fazla 1 dB kötü olmalı; yöntem deney 34'teki `kabul3.py` ile aynı. Tutmazsa B, Sındırgı'da çalışan modeli bozuyor demektir; yalnız sık bölgeye özel bir düzeltme olarak kabul edilmez.

## Ek 3: Hep yayında olan payın ayarlanması (22 Kasım, kullanıcının kararıyla)

- **Ne yapılıyor:** Komşu hücrenin bir kaynak bloğundaki etkinliği f + (1 − f) × (veri yükü) olarak hesaplanıyor. f fiziksel bir değer olarak değil, **ayarlanan bir katsayı** olarak ele alınıyor; yük katsayısı gibi. Sonuçlarda da böyle yazılacak.
- **Taban model:** Tek bant (B3), RMa, 24 saha, adım 3'teki girdiler.
- **Ayar:**
  - Tek bir f, iki bölge için ortak.
  - f, 0 ile 0,214 arasında 0,005 adımla taranıyor. 0,214, B sınamasındaki tam pay.
  - Seçilen f, Edremit ve Balıkesir'in **eğitim sahalarında** saha başına ortalama mutlak SINR farkını (3 çekilişin ortalaması) en küçük yapan değer. Test sahalarına ayar sırasında bakılmıyor.
- **Kabul:**
  1. **Test sahaları:** Her iki bölgede SINR farkı ≤ 3 dB. RSRP f'ten etkilenmiyor; adım 3'teki sonuçları aynen geçerli. Balıkesir'de RSRP zaten geçmemişti.
  2. **Sındırgı:** Aynı f Sındırgı'nın üç doğrulama durumuna uygulanıyor (deney 34'teki `kabul3.py` yöntemi, yeni gölgeleme ve görüş hattı). Eğitim ve test sahalarında SINR farkı, f = 0 hâlinden en fazla 1 dB kötü olmalı. Yük, f = 0 ile çözülen hücre yükü olarak alınıyor; f'nin yük üzerindeki ikinci derece etkisi ihmal ediliyor.
- Ayar tek bir sayı. Bu yüzden test sahalarında tutması, modelin bu bölgelerde kullanılabileceğini gösterir; sapmanın sebebini açıklamaz.

## Ek 4: Katsayının PCI planlamasından türetilmesi (22 Kasım, f = 0,03 görüldükten sonra)

**Açıklama:**
- Telefon kaliteyi referans sinyali hücrelerinde ölçer (RS-SINR).
- İki anten portunda, iki hücrenin PCI'sının 3'e bölümünden kalan aynıysa referans sinyalleri aynı yere düşer; bu girişim yükten bağımsız olarak hep vardır.
- Kalanlar farklıysa ölçüm noktalarına komşunun veri yayını düşer; o da yüke bağlıdır.
- Bu durumda hep var olan girişim c × (toplam komşu gücü) olur. c, çakışan komşuların toplam komşu gücündeki payıdır. Yani modeldeki f yerine c gelir.

**Hesap (ayar yok):**
- Her kullanıcı için c hesaplanıyor: bağlı olduğu hücreyle aynı PCI grubundaki komşuların gücü / bütün komşuların gücü (bağlı hücre hariç).
- Hesap hızlı modelde yapılıyor, adım 3'teki kullanıcılar ve anten çekilişleriyle: Edremit ve Balıkesir'de 24 saha RMa, Sındırgı'da deney 29'un üç doğrulama durumu (deney 34 modeli).
- **P1, yaygın kural:** Her sahada k. sektörün PCI grubu k (k = 0, 1, 2). Aynı sahanın sektörleri hiç çakışmıyor.
- **P2, karşılaştırma için:** PCI grupları rastgele. Çakışma olasılığı 1/3; aynı sahanın sektörleri yine farklı gruplarda.

**Karar:**
- P1'de üç bölgenin kullanıcı ortalaması c, 0,015–0,06 arasında çıkarsa (0,03'ün yarısı ile iki katı), açıklama destekleniyor sayılır.
- Dışında çıkarsa açıklama bu haliyle tutmuyor demektir.
- **Bilinen sınır:** Anten yönleri rastgele seçildiği için, P1'deki "aynı sektör numarası" gerçek ağdaki planlı komşuluğu temsil etmeyebilir. Gerçek planlama, en güçlü komşuları özellikle çakıştırmamaya çalışır.
