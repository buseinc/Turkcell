# Deney 43: Şehirde kesinti, kurallar (25 Kasım)

Hiçbir kesinti sonucu görülmeden yazıldı. Görülen tek şey KPI'daki kesinti kayıtları (aşağıda).

## Soru

Balıkesir merkezde bir saha, iki komşu saha ya da bir sahanın çoğu çökünce kaç kişi servissiz kalır, komşu sahalar yükü kaldırır mı? Aynı kesinti günün farklı saatlerinde ne kadar farklı sonuç verir?

## Kesintiler (KPI'daki gerçek arızalar, 10 gün)

| Durum | Kapanan | KPI'da ne oldu |
|---|---|---|
| **C0** | Hiçbiri | Normal gün |
| **C1** | 195 (bütün saha) | 3 Kasım 00:15, 13 hücrenin hepsi, 2,5 saat, arıza |
| **C2** | 087 ve 108 (bütün sahalar, aralarında 536 m) | 10 Ağustos 13:15, ikisi aynı anda, 1,8 saat, arıza |
| **C3** | 116'nın 3 sektöründen 2'si | 10 Ağustos 18:00, 11 hücreden 8'i, 4,8 saat, arıza |

- Şehirde depremden sonra başlayan bir arıza yok; bu kesintiler depremle ilgili değil. Soru "şehirde bir saha çökerse" olarak kuruluyor.
- **C3:** Gerçek hücrelerin hangi yöne baktığı bilinmiyor. ns-3'te açık kalan sektör 0 numaralı sektör. Hızlı modelde 3 seçeneğin üçü de hesaplanıp aradaki fark yazılıyor.

## Saatler

08:45 (sabah gidişi), 15:30 (en kalabalık), 21:15 (kapasite zirvesi), deney 39'dan. Kesintiler gerçekte başka saatlerde oldu; burada "aynı kesinti bu saatte olsaydı" sorusuna bakılıyor.

## Model

Deney 42'nin ns-3 şehir modeli (deney 40'ın ayarları): 94 saha, kullanıcının yerine göre UMa/RMa, standarttaki bina/araba kaybı, gölgeleme şehirde 7 dB, kırsalda 4/8 dB, 25 m kule, anten 36.814, EVM %8, sürekli yayın %4,8, kuyruğa göre kaynak veren PF. Anten yönleri: çekiliş 42. Mesafe düzeltmesi yok.

## Kullanıcılar ve yük (gerçek sayı)

- **Sayı:** Her ana sahaya, o sahanın gerçek hücrelerinin o saatteki ortalama KPI kullanıcısı × 3 (modelde sahada 3 hücre, tek frekans). 15:30'da toplam ~6.100, 08:45'te ~4.200, 21:15'te ~5.000.
- **Yer:** Deney 40'taki gibi. Uzaklık Experia'da o sahanın o saatteki TA kayıtlarından; yön, kendi sahasının en iyi olduğu ilk yön (12 deneme).
- **Trafik:** 512 baytlık paketler. Her hücrenin kullanıcılarına ortak paket aralığı, kesinti yokken (C0) hücre KPI'daki o saatin PRB'si kadar meşgul olacak şekilde, hızlı modelle (deney 42'deki yöntem: 1 ms altına inmiyor, servis alamayan saniyede 1 paket).
- **Kesintide:** Aynı kullanıcılar aynı yerde, aynı paket aralığıyla. Kapanan sahanın kullanıcıları komşulara bağlanıyor ya da servis alamıyor.
- **11 komşu saha:** Kullanıcı yok; her hücreye bir yük kullanıcısı (deney 42'deki gibi).

## Ölçütler

- **Servis yok:** SINR < −6,7 dB (CQI 0); deney 32'nin tanımı.
- **Zayıf:** RSRP < −121,8 dBm; deney 32'nin tanımı.
- **Dolu hücre:** PRB ≥ 0,95.
- **Etkilenen kullanıcılar:** C0'da (kesinti yokken) kapanan hücrelere bağlı olanlar. Üç durumda da aynı tanım.
- **Devralan hücreler:** Kesintide etkilenen kullanıcıları alan hücreler.
- **Raporlanan** her durum ve saat için:
  - etkilenen kullanıcılar arasında servis yok ve zayıf payı,
  - bütün bölgede servis yok payı,
  - devralan hücrelerin PRB'si (önce/sonra), bütün bölgede dolu hücre sayısı,
  - etkilenen kullanıcıların ve devralan hücrelerin eski kullanıcılarının aldığı veri (önce/sonra).

## Araçlar ve sıra

1. **Hızlı model:** 3 saat × 4 durum, anten yönleri için 10 çekiliş. Aralıkları gösteriyor; C3'ün 3 seçeneği burada.
2. **ns-3:** Önce 15:30'da C0 deneme koşusu (1 s) ile süre ölçülüyor ve kullanıcıya bildiriliyor. Ana sonuçlar ns-3'ten; kaç saat/durum koşulacağı süreye göre kullanıcıyla kararlaştırılıyor.

Hiçbir sayı ölçüme göre ayarlanmıyor.
