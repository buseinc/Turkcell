# Denenenler: neyi denedik, ne çıktı, neden bıraktık

Bilgi amaçlı. Güncel ayarlar ve sonuçlar her deneyin kendi `KURALLAR.md` / `SONUCLAR.md` dosyasında; bu dosya yalnız geçmişte denenen yolları ve neden bırakıldıklarını tutar. Yeni bir yol denenince ya da bırakılınca buraya bir satır eklenir.

## Sinyal modeli (yayılım, anten, düzeltmeler)

| Denenen | Deney | Ne çıktı | Durum |
|---|---|---|---|
| Ayarlanmış temel model S0 (log-mesafe, 120° anten, taramayla seçilmiş) | 4–7 | Ölçüme uyuyordu ama değerler taramayla seçilmişti | Bırakıldı: kaynağı yok |
| Kaynaklı değerler: COST-231 Hata, 65° anten, 6° eğim, 8 dB gölge, 1850 MHz | 20 | Sinyal ölçümden 12–17 dB zayıf | Bırakıldı |
| Kırsal 3GPP RMa | 21 | Medyan tuttu; yakın sahalar 11–18 dB güçlü, uzaklar 6–7 dB zayıf | Sındırgı'da kullanıldı |
| Bina kaybı / dikey desen (9 koşu) | 16 | Kabul ölçütleri geçmedi | Bırakıldı |
| Veriden mesafe düzeltmesi (k0 + k1·log d) | 22 | RSRP dağılımı tuttu, SINR 8 dB yüksek | Sındırgı/Edremit'te kullanıldı; **24 Kasım'da hocanın kararıyla kaldırıldı** |
| 3GPP TR 36.814 anten deseni | 23 | Saha sıralaması tuttu, SINR düşmedi | Kullanılıyor |
| Yükü KPI PRB'sine göre kalibre etmek | 24 | SINR yalnız 0,3 dB değişti | Kullanılıyor |
| Verici kusuru (EVM %8, 3GPP TS 36.104) | 25–26 | SINR farkı 2,3–2,8 dB'ye indi | Kullanılıyor |
| Mesafe düzeltmesinin kesintide uygulanışı: ev sahasına göre (A), bağlı hücreye göre (S), bağlantı başına (C) | 38 | Seyrek bölgede kesinti etkisi %0–28 arası, veriden ayrılamadı | Düzeltme kaldırıldığı için konu kapandı |
| Boş hücrenin sürekli yayını, ölçüme uydurulmuş %3 | 35–36 | Kesinti sonucunu değiştirmedi | Bırakıldı: ölçüme uydurulmuş sayı |
| Boş hücrenin sürekli yayını, fiziksel %4,8 (referans sinyali payı) | 40 | %0 ile kalite farkı 0,8 dB değişiyor | Kullanılıyor |

## Şehir modeli (Balıkesir merkez, deney 40, 24 Kasım)

Hepsi hızlı modelle, 94 saha, ölçümle aynı saatte. Fark = saha başına ortalama mutlak fark (sınır kalite 3 dB, güç 5 dB).

| Sıra | Denenen | Kalite farkı | Güç farkı | Neden değişti |
|---|---|---|---|---|
| 1 | Bütün bölge şehir (UMa), %80 bina içi (yarı eski yarı yeni bina), rastgele yön | 5,7 | 8,6 | Hata şehrin kenarında: kırsal sahalara şehir modeli |
| 2 | Saha başına şehir/kırsal, formül **kulenin** yerine göre | 2,1 | 9,2 | Şehirdeki kullanıcıların %35'i uzak kırsal kulelere bağlanıyordu |
| 3 | Formül **kullanıcının** yerine göre | 2,6 | 7,7 | Kullanıcıların çoğu yerleştirildiği sahaya bağlanmıyordu |
| 4 | Kullanıcı kendi sahasının en iyi olduğu yöne | 3,0 | 7,5 | Standardın metni okundu: bizim durum için başka bina modeli öngörülüyor |
| 5 | Standarda uygun: şehirde 20 dB + iç mesafe, gölge 7 dB; kırsalda %50 bina, %50 araba | 3,5 | 6,0 | Güncel ana model; ortalama güç farkı 1–1,6 dB |

Yan denemeler (hepsi bırakıldı, ana modelin yerine geçmedi): bina kaybı yok (kalite 1,9 / güç 19,5), bütün bölge kırsal (2,5 / 21,9), anten eğimi 10° (5,0 / 6,4), sürekli yayın %9,5 (4,6 / 6,0).

## Frekans ve taşıyıcı

| Denenen | Deney | Ne çıktı | Durum |
|---|---|---|---|
| Çok taşıyıcı S2 (800 MHz ek katman) | 14 | Ölçüme daha iyi uymadı | Bırakıldı |
| Hocanın sektör/taşıyıcı grupları | 17–18 | Bantlar TA'ya göre varsayım; yük eşlemesi tuttu (bkz. deney 17–18) | Ana modelde yok |
| CellMapper bantları (1, 3, 7, 20) | 35 | Hücre–bant eşleşmesi, güç ve kullanıcı payı yok; toplu çekme yasak | Bırakıldı; tek frekans kaldı |

## Kullanıcılar ve yük

| Denenen | Deney | Ne çıktı | Durum |
|---|---|---|---|
| 64 / 128 / 256 kullanıcı, toplam yük sabit | 8 | Örneklem duyarlılığı (bkz. deney 8) | Şehir modelinde saha başına 32 |
| TA'ya göre yerleştirme, rastgele yön | 15 | Uyum bozuldu, açıklaması kanıtlanamadı | Yön 24 Kasım'da değişti |
| Kendi sahasının en iyi olduğu yöne yerleştirme | 40 | Kullanıcıların üçte biri için hiçbir yönde kendi sahası en iyi değil (gerçek hücreler daha uzağa hizmet veriyor) | Kullanılıyor |
| Günlük ortalama yük; deprem yükü (KPI × 2) | 9, 32 | Deprem yükü ağı tıkamıyor | Sındırgı'da kullanıldı |
| Gün içi saatler: kurala göre "akşam zirvesi" 19:00 | 39 | Bağlı kişide ayrı akşam zirvesi yok | Değişti: 08:45, 15:30, kapasite zirvesi (~21:00) |
| Trend için modeldeki 24 saha | 39 | Az veri | Değişti: bütün ilçe |

## Bölge

| Denenen | Deney | Durum |
|---|---|---|
| Sındırgı 24 saha (hocanın 8 + 8 + yakın 8) | 7 | Kırsal bölge |
| Edremit 24 / 48 saha | 35, 37 | 24 → 48'de sinyal kalitesi 0,8 dB değişti (sınır 0,5) |
| Balıkesir merkez 24 / 48 saha (merkezin 1,7 km'si) | 35 | Şehir için az; bırakıldı |
| Balıkesir merkez 94 saha, amaca göre (8 km + 4 km komşu kuşağı) | 40 | Kullanılıyor |

## Zamanlayıcı ve kapasite

| Denenen | Deney | Ne çıktı | Durum |
|---|---|---|---|
| ns-3 varsayılan PF | 28 | Tek ses paketi bütün bandı alıyor, hücreler dolu görünüyor | Bırakıldı |
| Kuyruğa göre kaynak veren PF | 29 | Hücre başına 200 görüşmede gecikme 14 ms, tıkanma yok | Kullanılıyor |

## Kesinti

| Denenen | Deney | Ne çıktı | Durum |
|---|---|---|---|
| 130 ve 482 kapatma (ns-3, deprem yükü) | 33 | Çevrenin %15–18'i servissiz (mesafe düzeltmesiyle) | Düzeltmesiz yeniden yapılacak |
| Yollarda hareketli araçlar | 34 | 130 kapanınca il yolunun 6,6 km'si servissiz (mesafe düzeltmesiyle) | Düzeltmesiz yeniden yapılacak |
| Gerçek 200 kesintisiyle karşılaştırma | 38 | Kullanıcıların ~%67'si en yakın 6 sahada; model ~%88 | Bilgi |
| Kesinti türü (otomatik / elle) | 41 | 482 gerçek arıza, 130 yarım saatlik elle kapatma, 200 elle (depremden önce) | Bilgi |
