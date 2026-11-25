# Deney 40: Balıkesir merkez şehir modeli, sonuçlar (25 Kasım)

Kurallar `KURALLAR.md`. Kod: `hazirla40.py` (girdiler), `model40.py` (hızlı model), `analiz40.py` (tablo, şekil). Sayılar `model40.json`, `analiz40.json`; şekil `sehir_modeli.png`. Ölçüm ve kullanıcı dosyaları (`*.csv.gz`) yalnız yerelde.

Hızlı model, 94 saha (83 ana + 11 komşu). Her ana sahada 100 ölçüm noktası; her saat için 10 anten çekilişi. Karşılaştırma Experia gibi: önce hücre başına ortanca, sonra saha. Ölçüm: Experia 22–26 Haziran 2026 hafta içi, aynı saat. Hiçbir sayı ölçüme göre ayarlanmadı; mesafe düzeltmesi yok.

## Ana model

Ayarlar 3GPP TR 38.901 V19.5.0'ın metninden kontrol edildi (KURALLAR.md).
- Her sahaya sahaların sıklığına göre şehir ya da kırsal ortam (56 şehir, 38 kırsal).
- Kullanıcının bütün bağlantıları bulunduğu yerin ortamının standardıyla:
  - **Şehir:** UMa, gölgeleme 7 dB, %80 bina içi. Bina kaybı 20 dB + iç mesafe U(0,25) m × 0,5 dB/m (standardın 6 GHz altı tek frekanslı şehir simülasyonları için öngördüğü model).
  - **Kırsal:** RMa, %50 bina içi (düşük kayıplı model), %50 arabada (9 ± 5 dB).
- Kullanıcılar ölçümdeki uzaklıkta, kendi sahasının en iyi sinyali verdiği yönlere konuyor.

| Saat | Sinyal kalitesi farkı (sınır 3 dB) | Sinyal gücü farkı (sınır 5 dB) | Ortalama yön | Normal günde servis yok |
|---|---|---|---|---|
| 08:45 | 2,5 | 7,1 | kalite 1,7 dB düşük, güç 0,8 dB fazla | %5 |
| 15:30 | 3,0 | 7,3 | 2,3 dB düşük, 0,6 dB fazla | %4 |
| 21:15 | 3,4 | 7,0 | 2,9 dB düşük, 0,2 dB eksik | %5 |

- **Sinyal gücü ortalamada tutuyor:** model ölçümden ortalama 1 dB'den az farklı (15:30'da ortanca ikisinde de −99,6 dBm).
- **Saha saha güç farkı 7 dB.** Bu şans değil: aynı sahada anten çekilişleri arası oynama 2,9 dB, sahalar arası fark 8,9 dB. Yani bazı sahalarda model sürekli güçlü, bazılarında sürekli zayıf. Sahaların %35–45'i iki sınırın birden içinde.
- **Sinyal kalitesi** modelde ortalama 2–3 dB düşük; sabah ve öğleden sonra sınırın içinde, akşam sınırın biraz dışında. Model kaliteyi gerçekten kötü gösteriyor; kesinti sonuçları bu yönden ihtiyatlı (kötümser) olur.
- Güç sınırı geçilmiyor. Kurala göre bu model kullanılıyor, farklar açıkça yazılıyor.

## Fark nerede toplanıyor (15:30)

| Bölge | Saha | Güç farkı (ortanca) | Kalite farkı (ortanca) |
|---|---|---|---|
| Merkeze 0–2 km | 35 | −1,8 dB | −2,6 dB |
| 2–4 km | 25 | −3,3 dB | −1,9 dB |
| 4–8 km (şehrin kenarı) | 22 | +4,4 dB | −0,2 dB |

- Kuleye çok yakında (100–200 m) model 7,7 dB güçlü, çok uzakta (5–15 km) 9,7 dB zayıf. Ölçümde sinyal uzaklıkla modelden daha yavaş düşüyor.
- Servissiz kalanlar uzakta: kuleye 1 km içinde %1, 2 km'den uzakta %17 (kullanıcıların %21'i 2 km'den uzakta). Bina içinde %6, dışarıda %1,5.

## Kullanıcıların yeri: modelde hücreler gerçekten daha küçük

- Kullanıcıların **%33–37'si** için, ölçümdeki uzaklıkta denenen 12 yönün hiçbirinde kendi sahası en iyi saha olmuyor. Bunlar kurala göre ilk yönde bırakıldı.
- Eşleşmeyenler uzaktaki kullanıcılar. Yani gerçek hücreler modeldekinden daha uzağa hizmet veriyor. Olası sebepler: tepedeki sahalar, 800 MHz gibi uzağa giden katmanlar, gerçek anten eğimleri, ya da Experia'daki TA'nın kullanıcı başına değil hücre ortalaması olması. Veri bunları ayırmıyor.
- Yalnız eşleşen kullanıcılarla karşılaştırınca kalite farkı 3,2–3,9 dB, güç farkı 9,0–9,4 dB.

## Yan denemeler

Ana modelin seçiminde bakıldı; eski karşılaştırmayla (sahada 32 nokta, 3 çekiliş, ortalama) hesaplandı, yenisiyle tekrarlanmadı. Ana modelin aynı eski karşılaştırmayla sonucu: kalite 3,5, güç 6,0.

| Hâl | Kalite farkı | Güç farkı |
|---|---|---|
| Bütün bölge şehir | 7,7 | 10,4 |
| Bütün bölge kırsal | 2,5 | 21,9 |
| Bina içi ve araba kaybı yok | 1,9 | 19,5 |
| Şehirde yarı eski yarı yeni bina (Tablo 7.4.3-2) | 3,1 | 6,5 |
| Sürekli yayın %0 | 2,8 | 6,0 |
| Sürekli yayın %9,5 | 4,6 | 6,0 |
| Anten eğimi 10° | 5,0 | 6,4 |

Hiçbir hâl iki sınırı birden geçmiyor. Kalite farkını en çok kaybı kaldırmak azaltıyor, ama o zaman güç 19 dB fazla.

## Kalan farklar nereden gelebilir (kanıtlanmadı)

- Saha saha 7 dB'lik güç farkı: anten yönleri, gerçek eğim, yükseklik ve arazi bilinmiyor.
- Kalitenin 2–3 dB düşük çıkması: modelde bütün komşular aynı frekansta; gerçekte trafik birden çok frekans katmanına dağılıyor. Sürekli yayın %0 iken kalite farkı 0,7 dB azalıyor.
- Ölçüm haziranda, yük ekimde.

Bunların hiçbiri ölçüme göre ayarlanmadı.

## Sınırlar

- Experia'daki TA hücre ortalaması; modelde kullanıcı uzaklıkları gerçekte olduğundan daha toplu olabilir.
- Anten yönleri bilinmiyor (10 çekiliş).
- Hızlı model; ana sonuçlar ns-3'e taşındıktan sonra oradan alınacak.
