# Deney 40: Balıkesir merkez şehir modeli, sonuçlar (24 Kasım)

Kurallar `KURALLAR.md`. Kod: `hazirla40.py` (girdiler), `model40.py` (hızlı model), `analiz40.py` (tablo, şekil). Sayılar `model40.json`, `analiz40.json`; şekil `sehir_modeli.png`. Ölçüm ve kullanıcı dosyaları (`*.csv.gz`) yalnız yerelde.

Hızlı model, 94 saha (83 ana + 11 komşu), 3 saat × 3 anten çekilişi, her hâl için 9 hesap (hesap başına ~17 s). Ölçüm: Experia 22–26 Haziran 2026 hafta içi, aynı saat. Hiçbir sayı ölçüme göre ayarlanmadı; mesafe düzeltmesi yok.

## Ana model

Ayarlar 3GPP TR 38.901 V19.5.0'ın metninden kontrol edildi (KURALLAR.md).
- Her sahaya sahaların sıklığına göre şehir ya da kırsal ortam (56 şehir, 38 kırsal).
- Kullanıcının bütün bağlantıları bulunduğu yerin ortamının standardıyla:
  - **Şehir:** UMa, gölgeleme 7 dB, %80 bina içi. Bina kaybı 20 dB + iç mesafe U(0,25) m × 0,5 dB/m; bu, standardın 6 GHz altı tek frekanslı şehir simülasyonları için öngördüğü model.
  - **Kırsal:** RMa, %50 bina içi (düşük kayıplı model), %50 arabada (9 ± 5 dB).
- Kullanıcılar ölçümdeki uzaklıkta, kendi sahasının en iyi sinyali verdiği yönlere konuyor.

| Saat | Sinyal kalitesi farkı (sınır 3 dB) | Sinyal gücü farkı (sınır 5 dB) | Ortalama yön | Normal günde servis yok |
|---|---|---|---|---|
| 08:45 | 3,1 | 6,0 | kalite 2,7 dB düşük, güç 1,6 dB fazla | %4 |
| 15:30 | 3,5 | 6,1 | 3,2 dB düşük, 1,6 dB fazla | %4 |
| 21:15 | 4,0 | 5,7 | 3,8 dB düşük, 0,8 dB fazla | %5 |

- **Sinyal gücü ortalamada tutuyor:** model ölçümden ortalama yalnız 1–1,6 dB güçlü (15:30'da model ortancası −100,0, ölçüm −99,6 dBm). Saha saha fark ise 6 dB civarında; yani tek tek sahalarda model kimi zaman güçlü kimi zaman zayıf. Bilinmeyen anten yönleri bunun bir sebebi.
- **Sinyal kalitesi** modelde ortalama 3–4 dB düşük. Yani model sinyal kalitesini gerçekten **kötü** gösteriyor; kesinti sonuçları bu yönden ihtiyatlı (kötümser) olur.
- İki sınır da tam geçilmiyor. Kurala göre bu model kullanılıyor, farklar açıkça yazılıyor.

## Kullanıcıların yeri: modelde hücreler gerçekten daha küçük

- Kullanıcıların **%32–36'sı** için, ölçümdeki uzaklıkta denenen 12 yönün hiçbirinde kendi sahası en iyi saha olmuyor. Bunlar kurala göre ilk yönde bırakıldı.
- Eşleşmeyenler uzaktaki kullanıcılar: kuleye 300 m içinde %98'i eşleşiyor, 2–5 km'de yalnız %33'ü. Uzaklığı komşu sahalara uzaklığın 2–5 katı olanların %20'si eşleşiyor.
- Yani gerçek hücreler, modeldekinden daha uzağa hizmet veriyor. Olası sebepler: tepedeki sahalar, 800 MHz gibi uzağa giden katmanlar, gerçek anten eğimleri, ya da Experia'daki TA'nın kullanıcı başına değil hücre ortalaması olması. Veri bunları ayırmıyor.
- Yalnız eşleşen kullanıcılarla karşılaştırınca kalite farkı 3,5–4,2 dB, güç farkı 8–9 dB.

## İlk denemeyle karşılaştırma (bütün bölge şehir)

| | Kalite farkı | Güç farkı | Şehrin kenarında (4–8 km) güç | Servis yok |
|---|---|---|---|---|
| Bütün bölge şehir | 7,7 | 10,4 | −20,3 dB (çok zayıf) | %16–17 |
| Ana model | 3,5 | 6,0 | +4,9 dB | %4–5 |

- İlk denemede hata şehrin kenarında toplanıyordu: kırsal karakterli kenar sahalara şehir modeli uygulanmıştı. Saha başına ortam bu yüzden eklendi; sınır standardın saha aralıklarından, ölçüme bakılmadan.
- Formülün kulenin yerine değil kullanıcının yerine göre seçilmesi ve kullanıcıların kendi sahasının alanına konması, modelin kendi içine bakılarak düzeltildi.
- Bina kaybı modeli ve kırsaldaki araba kaybı, standardın metni okunduktan sonra standardın bu durum için öngördüğü hâle getirildi. Önceki hâlde (yarı eski yarı yeni bina) model ortalamada 4–5 dB güçlüydü.

## Kuleye uzaklığa göre (şekil, orta panel)

- Ana model 300 m–2 km arasında ölçüme yakın; kuleye çok yakında (100–200 m) 9 dB güçlü, uzakta (5–15 km) 8 dB zayıf.
- Ölçümde sinyal uzaklıkla modelden daha yavaş düşüyor. Herkes dışarıdayken model 20–26 dB güçlü; bina kaybı farkın büyük kısmını kapatıyor.

## Yan denemeler (3 saatin ortalaması)

| Hâl | Kalite farkı | Güç farkı |
|---|---|---|
| Ana model | 3,5 | 6,0 |
| Bütün bölge şehir | 7,7 | 10,4 |
| Bütün bölge kırsal | 2,5 | 21,9 |
| Bina içi ve araba kaybı yok | 1,9 | 19,5 |
| Şehirde yarı eski yarı yeni bina (Tablo 7.4.3-2) | 3,1 | 6,5 |
| Sürekli yayın %0 | 2,8 | 6,0 |
| Sürekli yayın %9,5 | 4,6 | 6,0 |
| Anten eğimi 10° | 5,0 | 6,4 |

Hiçbir hâl iki sınırı birden geçmiyor. Kalite farkını en çok kaybı kaldırmak azaltıyor, ama o zaman güç 19 dB fazla.

## Kalan farklar nereden gelebilir (kanıtlanmadı)

- Saha saha 6 dB'lik güç farkı: anten yönleri, gerçek eğim ve yükseklik bilinmiyor.
- Kalitenin 3–4 dB düşük çıkması: modelde bütün komşular aynı frekansta ve sürekli yayın payı açık; gerçekte trafik birden çok frekans katmanına dağılıyor. Sürekli yayın %0 iken kalite farkı 2,8 dB.
- Ölçüm haziranda, yük ekimde.

Bunların hiçbiri ölçüme göre ayarlanmadı.

## Sınırlar

- Experia'daki TA hücre ortalaması; modelde kullanıcı uzaklıkları gerçekte olduğundan daha toplu olabilir.
- Anten yönleri bilinmiyor (3 çekiliş).
