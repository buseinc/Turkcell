# Deney 40: Balıkesir merkez şehir modeli, kurallar

24 Kasım. Hocanın kararı: mesafe düzeltmesi yok, önce sık şehir bölgesi. Bölge, sabit bir saha sayısına göre değil, amaca göre seçiliyor. Başka bölgelerle karşılaştırma amacı yok.

## Bölgenin amacı

Model şunları içermeli:
1. Şehrin ortasındaki konut bölgesi (deney 39'da akşam kalabalık sahalar).
2. Çevresindeki gündüz halkası (gündüz kalabalık sahalar: iş, okul, sanayi). Sabah ve akşam insanlar bu ikisi arasında kayıyor.
3. 15:30'daki bağlı kullanıcıların büyük çoğunluğu.
4. Kenarda eksik komşu yüzünden sinyal kalitesi bozulmasın diye çevresinde bir kuşak komşu saha.

## Seçim

- **Merkez:** 15:30'daki bağlı kullanıcı sayısıyla ağırlıklı saha ortası: 39,6395 K, 27,8916 D.
- **Ana bölge:** merkeze 8 km içindeki bütün sahalar, hangi ilçede olursa olsun: **83 saha**.
  - Balıkesir merkezdeki 15:30 kullanıcılarının %84'ü bu alanda.
  - Gündüz kalabalık 35 sahanın 29'u, akşam kalabalık 23 sahanın 23'ü bu alanda.
  - 8 km'den sonra her km yalnız birkaç saha ve kullanıcı ekliyor.
- **Komşu kuşağı:** 8–12 km arasındaki bütün sahalar: **11 saha**. Bunlar yayın yapıyor ve KPI yüküyle dolu, ama sonuçlar bu sahalarda değerlendirilmiyor.
- **Toplam:** 94 saha, sahada 3 hücreyle 282 hücre.

## Nasıl çalıştırılıyor

- **Tarama hızlı modelle:** ölçümle karşılaştırma, ayar denemeleri, kesinti ve İHA yerleşimi taraması.
- **ns-3'te yalnız seçilmiş birkaç durum** (normal gün, en kötü kesinti, en iyi İHA yerleşimi; üç saatte). Ana sonuçlar bunlardan.
- ns-3 koşularından önce 94 sahayla kısa bir süre denemesi yapılır. Tam koşu 6 saati geçecekse ana bölge 5 km'ye inilir (66 saha, kullanıcıların %71'i), komşu kuşağı 5–9 km olur.

## Model ayarları

Hiçbir değer ölçüme bakılarak ayarlanmıyor. Her değer veriden, bir standarttan ya da açıkça "bilinmiyor" denip birkaç olasılıkla deneniyor.

| Ayar | Ana model | Kaynak |
|---|---|---|
| Saha konumları | Turkcell koordinatları | veri |
| Frekans, bant | 1850 MHz (Band 3), 20 MHz, tek katman | veri (CellMapper) |
| Sahada hücre | 3 | varsayım |
| Güç | 49 dBm | 3GPP TR 36.814 |
| Anten | 3GPP deseni, 65°, 15 dBi, dikey genişlik 10° | 3GPP TR 36.814 / 36.942 |
| Anten eğimi | 6° | hocanın taslağı; gerçek değer bilinmiyor |
| Anten yönleri | rastgele; ana modelde 10, yan denemelerde 3 çekiliş | bilinmiyor |
| Kule / telefon yüksekliği | 25 m / 1,5 m | 3GPP TR 38.901 şehir formülünün varsayımı |
| Yayılım | şehir sahasında UMa, kırsal sahada RMa (aşağıda "Saha başına ortam"); görüş hattı olasılığı formülün kendisinden | standart (3GPP TR 38.901) |
| Gölgeleme | şehirde 7 dB (TR 38.901 Tablo 7.4.3-3, tek frekanslı 6 GHz altı şehir simülasyonu), kırsalda 4 / 8 dB (görüş hattı / engelli, Tablo 7.4.1-1) | standart |
| Bina içi | şehirde kullanıcıların %80'i içeride (Tablo 7.2-1); duvar kaybı sabit 20 dB + iç mesafe U(0,25) m × 0,5 dB/m, dalgalanma yok (Tablo 7.4.3-3: 6 GHz altı tek frekanslı şehir simülasyonlarında kullanılması öngörülen model). Kırsal için aşağıya bakın. Kayıp kullanıcıya ait, bütün bağlantılarda aynı. | standart (3GPP TR 38.901, 7.4.3) |
| Mesafe düzeltmesi | yok | hocanın kararı |
| Verici kusuru | %8 | 3GPP verici kalitesi sınırı |
| Boş hücrenin sürekli yayını | %4,8 (tek anten portunda referans sinyalinin payı, 168 kaynak öğesinin 8'i) | LTE yapısı (3GPP TS 36.211) |
| Kullanıcı sayısı | her model hücresine bir gerçek hücrenin KPI yükü | veri |
| Saatler | 08:45, 15:30, kapasite zirvesi (21:15) | veri (deney 39) |
| Kullanıcıların yeri | Experia'daki kuleye uzaklık (TA) dağılımı | veri |
| Trafik | hücre doluluğu o saatin KPI değerini tutana kadar | veri |

**Standardın metninden kontrol edildi** (TR 38.901 V19.5.0): şehirde %80 içeride (Tablo 7.2-1); kırsalda %50 içeride, %50 arabada (Tablo 7.2-3); kırsalda yalnız düşük kayıplı bina modeli ve iç mesafe min(U(0,10), U(0,10)) m (Tablo 7.4.3-2); araba kaybı N(9, 5) dB (7.4.3.2). Eski/yeni tip binanın yarı yarıya oranı yalnız 6–70 GHz kalibrasyon tablosunda geçiyor (Tablo 7.8-1) ve standart bu oranı kullanıcıya bırakıyor; bu yüzden ana modelde değil, yan denemede.
- ns-3'teki hazır bina içi kayıp kodu dalgalanmayı standarttan küçük kuruyor (4,4 ve 6,5'i sapma değil varyans olarak veriyor). Bu yüzden bina içi kayıp ns-3'ün hazır kodu yerine, mesafe düzeltmesinin kullandığı "kullanıcı başına ek kayıp" yapısıyla, standarttaki sapmalarla eklenecek.

## Saha başına ortam: şehir ya da kırsal

Bölge yalnız şehir değil; 8 km içinde şehrin kenarı kırsala geçiyor. Bu yüzden her sahaya kendi ortamının standardı uygulanıyor. Atama ölçüme bakmadan, yalnız sahaların sıklığından yapılıyor.

- **Ölçü:** sahanın en yakın 3 sahaya ortalama uzaklığı (bütün envanter).
- **Sınır: 931 m.** 3GPP'nin şehir senaryosundaki saha aralığı 500 m, kırsal senaryodaki 1.732 m (TR 38.901 değerlendirme ayarları); sınır ikisinin geometrik ortası.
- Sonuç: 56 saha şehir, 38 saha kırsal (ana bölgede 56 / 27, komşu kuşağında 0 / 11). Merkeze 0–2 km'de 35 şehir / 1 kırsal, 4–8 km'de 3 şehir / 19 kırsal.

| | Şehir sahası | Kırsal saha |
|---|---|---|
| Yayılım formülü (kullanıcının bütün bağlantıları; kullanıcının bulunduğu yerin ortamına göre, yani yerleştirildiği sahanın ortamı) | UMa | RMa |
| Gölgeleme (görüş hattı / engelli) | 7 dB | 4 / 8 dB |
| Görüş hattı olasılığı | UMa formülü | RMa formülü |
| Kullanıcının kaybı (yerleştirildiği sahanın ortamına göre) | %80 içeride: 20 dB + U(0,25) m × 0,5 dB/m; %20 dışarıda: 0 | %50 içeride: düşük kayıplı bina modeli, iç mesafe min(U(0,10), U(0,10)) m, dalgalanma 4,4 dB; %50 arabada: N(9, 5) dB |

- Formülü kulenin yeri değil kullanıcının yeri belirliyor: şehirdeki kullanıcının sinyalini çevresindeki şehir yapıları zayıflatıyor, sinyal hangi kuleden gelirse gelsin.
- Kule yüksekliği iki ortamda da 25 m (aynı kuleler).
- Bu atama, ilk denemede (bütün bölge şehir) hatanın şehrin kenarında toplandığı görüldükten sonra eklendi. Sınır ise ölçüme göre değil, standardın saha aralıklarından seçildi.

## Karşılaştırma için yan denemeler (yalnız hızlı model)

0. Bütün bölge şehir (ilk deneme).

Ana model önceden belli; yan denemeler sonucu nasıl değiştirdiğini göstermek için, ana modelin yerine geçmez.

1. Bina içi ve araba kaybı yok (herkes dışarıda).
2. Şehirde Tablo 7.4.3-2 modeli: içeridekilerin yarısı eski tip (düşük kayıp), yarısı yeni tip (yüksek kayıp) bina; şehir gölgelemesi 4 / 6 dB.
3. Boş hücrenin sürekli yayını %0 ve %9,5 (iki anten portu).
4. Anten eğimi 10°.
5. Bütün bölge kırsal formül (RMa).

## Yük ve ölçüm kullanıcıları (ölçümle karşılaştırma adımı)

- Şehirde bir sahada ortalama 10 gerçek hücre var, modelde 3. Sahanın 3 model hücresinin her birinin doluluğu, o sahanın gerçek hücrelerinin o saatteki ortalama doluluğu (DL PRB; üç pazartesinin ortalaması, deney 39). KPI'sı olmayan sahalara bölgenin o saatteki ortalaması.
- Bu adımda yük, kullanıcılardan hesaplanmıyor; hücre doluluğu doğrudan KPI'dan giriliyor (girişim bundan geliyor). Binlerce kullanıcı ancak kesinti adımında gerekiyor.
- Ölçüm kullanıcıları (yalnız sinyali ölçen noktalar; yükü değiştirmez): Experia verisi olan her ana sahaya 100 kullanıcı, o sahanın hücrelerinin aynı saatteki TA uzaklıklarından çekilerek. TA birimi 4,88 m, uzaklık 100 m–15 km arasına sınırlanıyor (önceki deneylerle aynı).
- **Yön:** TA, telefonun bağlı olduğu kuleye uzaklık. Bu yüzden kullanıcı yalnız yerleştirildiği sahanın en iyi sinyali verdiği yönlere konuyor ("en iyi sunucu alanı"): her kullanıcı için 12 rastgele yön deneniyor, yerleştirildiği sahanın bir hücresine bağlandığı ilk yön seçiliyor. Hiçbir yönde bağlanmıyorsa ilk yön kalıyor ve bu kullanıcıların payı raporlanıyor. Yön seçimi her hâlin kendi modeliyle yapılıyor.
- Experia'daki TA, hücreye o saatte bağlı telefonların ortalaması; tek tek kullanıcıların uzaklığı değil. Bu yüzden modelde uzaklıklar gerçekte olduğundan daha toplu olabilir (sınır).
- Saat eşleşmesi: modelin 1 saatlik penceresinin ortası hangi Experia saatine düşüyorsa (08:45 → saat 9, 15:30 → saat 16, 21:15 → saat 21).
- Bir hücre, o saat için hafta içi en az 3 Experia kaydı varsa kullanılıyor; saha değeri hücre değerlerinin ortalaması.

## Ölçümle karşılaştırma

- Hiçbir şey ayarlanmadığı için sahalar eğitim/test diye ayrılmıyor; ana bölgedeki Experia verisi yeterli bütün sahalar kullanılıyor.
- Her saatin modeli Experia'nın aynı saatteki ölçümleriyle karşılaştırılıyor (`HOUR_ID`).
- Experia yalnız 22–28 Haziran 2026 haftasını kapsıyor; KPI ise 2025 Ağustos ve Ekim–Kasım günleri. Okullar haziranın sonunda kapalı. Bu yüzden yalnız Experia'nın hafta içi günleri (22–26 Haziran) kullanılıyor ve dönem farkı sınır olarak yazılıyor.
- Ölçü: Experia her hücre ve saat için ortanca veriyor; modelde de her hücrenin kullanıcılarının ortancası alınıyor, saha değeri hücrelerin ortalaması. Saha başına sinyal gücü (RSRP) ve sinyal kalitesi (SINR) farkı, anten çekilişlerinin ortalaması.
- Sınırlar: SINR farkı ≤ 3 dB, RSRP farkı ≤ 5 dB.
- **Geçmezse de ana model kullanılır**, farklar açıkça yazılır. Kuleye yakın kullanıcılardaki fark ayrıca gösterilir.
