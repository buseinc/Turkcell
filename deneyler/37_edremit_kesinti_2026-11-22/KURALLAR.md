# Deney 37: Edremit kıyısında saha kesintisi — kurallar

22 Kasım'da, hiçbir kesinti sonucu görülmeden yazıldı. Görülen tek şey KPI'daki kesinti kayıtları ve deprem anı yükü (aşağıda).

## Amaç

Sındırgı'da (seyrek, kırsal) bir saha çökünce çevresindeki kullanıcıların %15–18'i servis alamıyordu (deney 33). Sık sahalı Edremit kıyısında aynı şey olunca komşular boşluğu dolduruyor mu?

## KPI'dan görülenler (girdi)

- **Deprem anlarında kesinti yok.** Edremit'in 24 sahasında yalnız iki kısa site kesintisi var:
  - 011: 11 Ağustos 19:45, 30 dakika.
  - 529 (ana saha): 28 Ekim 14:15, 45 dakika.
- **Deprem yükü:**
  - 27 Ekim (22:45–01:15): hücre başına kullanıcı 9,4 (bir hafta önce aynı saatlerde 6,9), PRB 0,18 (0,14).
  - 10 Ağustos (19:45–21:30): kullanıcı 29,0 (20,0), PRB 0,39 (0,35).

## Ağ ve model

- **Saha sayısı:** Deney 35'teki 48 sahalık ağ. Sınır etkisi kuralı 24 sahanın yetmediğini göstermişti.
- **Model:** Kırsal yayılım (RMa), adım 3'te seçildiği gibi. Deney 33'ün radyo ayarları. Yumuşak gölgeleme ve konuma bağlı görüş hattı açık.
- **Hep yayında olan pay:** f = 0,03 (deney 35'te ayarlandı, deney 36'da ns-3'e eklendi).
- **Mesafe düzeltmesi:** Deney 35'teki Edremit RMa düzeltmesi.
- **Anten yönü:** Tohum 42 çekilişi.

## Kullanıcılar ve yük (27 Ekim depremi; Sındırgı'daki deney 33 ile aynı deprem)

- **Kullanıcı sayısı:** İç 24 sahada her sahaya, o sahanın deprem penceresindeki hücre başına ortalama KPI kullanıcısı × 3 kullanıcı. Sındırgı'daki kural; modeldeki tek taşıyıcı katmanını temsil ediyor.
- **Yerleştirme:** Kural A. Uzaklık sahanın Experia TA kayıtlarından seçiliyor, yön rastgele, yalnız karaya.
- **Trafik:** Her kullanıcı 512 baytlık paketler alıyor. Paket aralığı ortak ve hızlı modelle ayarlanıyor. Hedef: kesinti yokken ana hücrelerin ortalama PRB'si KPI deprem değeri 0,18 olsun.
- **Dış 24 saha:** Kullanıcı konmuyor. Her hücreye bir yük kullanıcısı konuyor: 800 m'de, anten yönünde. O nokta denizdeyse sırayla 600, 400, 200 m deneniyor; hiçbiri karada değilse yön ±30°, ±60° döndürülüyor. Yük kullanıcısının hedef PRB'si 0,18. Paket aralığı deney 34'teki gibi hesaplanıyor: katsayı / hedef PRB.

## Kesinti durumları

| Durum | Kapalı | Neden |
|---|---|---|
| E0 | hiçbiri | karşılaştırma |
| E1 | 529 | gerçekte kesinti yaşamış tek ana saha (28 Ekim) |
| E2 | 105 | deprem anında en kalabalık ana sahalardan biri (27 Ekim'de 13,1 kullanıcı/hücre) |

Bütün durumlarda kullanıcılar aynı.

## Ölçütler (deney 32 ve 33'teki gibi)

- **Servis yok:** Telefon bağlanamıyor ya da ortalama bildirilen SINR < −6,7 dB.
- **Zayıf:** RSRP < −121,8 dBm.
- **Dolu hücre:** PRB ≥ 0,95.
- **Raporlanan:** Bütün kullanıcılar için ve kapanan sahanın kullanıcıları için. Karşılaştırma deney 33'le (Sındırgı) yapılıyor.

## Sıra

1. **Hızlı modelle ön bakış:** E0–E2, 3 anten çekilişi.
2. **ns-3 deneme koşusu:** 1,5 s; süre ve yük kontrolü.
3. **ns-3 tam koşu:** 4 s, E0–E2 paralel. Süre deneme koşusundan sonra kullanıcıya bildirilecek.

## Yaz yükü (yalnız hızlı model, bilgi için)

10 Ağustos deprem yüküyle aynı hesap yapılacak: kullanıcı ve PRB 0,39. Hücrelerin dolup dolmadığına bakılacak.
