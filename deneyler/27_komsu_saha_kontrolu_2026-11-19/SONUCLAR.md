# Komşu saha kontrolü — 19 Kasım 2026

**Soru:** Hoca "seçtiğimiz tüm siteleri denediniz mi" diye sordu. Şimdiye kadar yalnızca 8 ana sahayı ölçümle
karşılaştırmıştık. 26. deneydeki model, hiç karşılaştırmadığımız komşu sahalarda da benzer sonuç veriyor mu?

**Durum: Eski sonuçla kontrol geçti ([regression.json](regression.json)), 3/3 koşu tamamlandı. Bütün ölçüm
kullanıcıları (352/352) bağlandı.**

## Kurulum

- Model 26. deneyle birebir aynı; hiçbir değer değişmedi.
- Sahalar koşudan önce, yalnızca hücre sayısına göre seçildi: hocanın 8 komşu sahasından en çok Experia
  hücresi olan üçü, **200 (12 hücre), 224 (10), 206 (9)**. 506, 475 ve 480'de 1–2 hücre var; 553 ve 555'in
  ölçüm verisi yok.
- Her sahanın çevresine, ana sahalardaki gibi TA mesafesine göre 32'şer ölçüm kullanıcısı eklendi. 224'ün
  kullanıcıları kuleden ortalama 9–10 km uzakta.
- Ölçüm hedefleri ana sahalarla aynı yöntemle hesaplandı (hücre başına saatlik ortalama, sonra saha
  ortalaması; yöntem ana sahaların hedeflerini birebir veriyor).
- **Not:** Bu sahaların hücreleri, mesafe düzeltmesinin hesaplandığı 5.812 hücrenin içindeydi (yaklaşık
  %0,5). Bu yüzden "tam" değil, "neredeyse" bağımsız sayılmalı.

Kurallar koşudan önce [prepare.py](prepare.py) içine yazıldı.

## Sonuç

Saha bazında fark (model − Experia, dB, üç anten yönü çekilişinin ortalaması):

| Saha | Grup | Hücre | RSRP farkı | SINR farkı |
|---|---|---:|---:|---:|
| 200 | komşu | 12 | +5,4 | +2,5 |
| 224 | komşu | 10 | +8,0 | +6,2 |
| 206 | komşu | 9 | +3,6 | −0,6 |
| **Komşu ortalama (mutlak)** | | | **5,7** | **3,1** |
| Test sahaları (440, 441, 443), 26. deney | | | 4,8 | 2,6 |

Çekilişlere göre RSRP farkı: 200 → 9,8 / 4,9 / 1,5; 224 → 8,0 / 12,2 / 3,8; 206 → 3,4 / 4,6 / 2,8 dB.

## Bu ne demek

1. **Komşu sahalarda da sonuç ana sahalara yakın.** Sinyal kalitesinde ortalama fark 3,1 dB (ana test
   sahalarında 2,6), sinyal gücünde 5,7 dB (ana test sahalarında 4,8). 206 ve 200 iyi tutuyor.
2. **224 ana sahalardaki 444 ve 440 gibi davranıyor.** Bu üç sahanın ortak noktası, gerçek sinyalin zayıf
   olması (−112 ile −115 dBm) ve kullanıcıların kuleden uzak olması. Model bu sahalarda sinyali 6–11 dB fazla
   güçlü veriyor. Yani zayıf ve uzak sahalarda model sistematik olarak iyimser. Bölge geneli için tek bir
   mesafe düzeltmesi kullandığımız için bu sahalara özel etkiyi yakalayamıyoruz.
3. **Saha sonuçları hangi kullanıcıların sayıldığına duyarlı.** Komşu sahalara kullanıcı eklemek, bazı ana
   sahaların sonucunu da 4 dB'ye kadar değiştirdi (yeni kullanıcıların bir kısmı ana sahalara bağlandı).
   Örneğin 441'in RSRP farkı 1,4'ten 5,4 dB'ye çıktı, 443'ünkü 4,8'den 1,7 dB'ye indi. Yani tek tek
   sahalardaki farklarda birkaç dB'lik bir belirsizlik payı var; ortalamalar daha güvenilir.

| Ana saha (26 → 27) | 130 | 296 | 440 | 441 | 443 | 444 | 482 | 554 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RSRP farkı | 0,8 → 2,2 | 9,9 → 10,4 | 7,4 → 6,3 | 1,4 → 5,4 | 4,8 → 1,7 | 8,3 → 11,1 | 2,5 → 3,3 | 3,7 → 7,1 |

## Sınırlar

- Yalnızca 3 komşu saha; seçim hücre sayısına göre.
- Komşu sahaların hücreleri mesafe düzeltmesinin hesabına küçük bir oranla girdi.
- 224'ün kullanıcılarının çoğu 5 km'den uzak; kırsal yayılım modelinin geçerli olduğu aralığın dışında.

[Hazırlık](prepare.py) — [Koşu](study.py) — [Karşılaştırma](summarize.py) — [Sayılar](comparison.json)
