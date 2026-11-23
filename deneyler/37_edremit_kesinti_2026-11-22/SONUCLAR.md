# Deney 37: Edremit kıyısında saha kesintisi — sonuçlar

Kurallar `KURALLAR.md` dosyasında. Girdiler `hazirla.py` ile üretildi; özetleri `plan.json` dosyasında.

## Girdiler

- **Kullanıcılar:** İç 24 sahada 27 Ekim deprem yüküyle 655 kullanıcı, yalnız karaya yerleştirildi. Buna ek olarak dış 24 sahanın 72 hücresinde birer yük kullanıcısı var.
- **Trafik:** Ortak paket aralığı 21,4 ms. Hızlı modelle, kesinti yokken ana hücrelerin PRB'si 0,18 olacak şekilde ayarlandı.

## Hızlı modelle ön bakış (`onizleme.json`; 3 anten çekilişinin ortalaması, f = 0,03)

| Durum | Kapanan sahanın kullanıcılarında servis yok | zayıf sinyal | Bütün bölgede servis yok | Ana hücre PRB | Dolu hücre |
|---|---|---|---|---|---|
| E0 kesinti yok | – | – | %2,5 | 0,16 | 1,7 |
| E1 529 kapalı | **%2,6** | %5,2 | %2,7 | 0,16 | 1,7 |
| E2 105 kapalı | **%6,8** | %11,1 | %2,7 | 0,17 | 1,7 |

**Karşılaştırma:** Sındırgı'da, aynı hızlı modelle ve aynı ölçütle, kapanan sahanın çevresinde servisi olmayan pay %22–28'di (deney 36). ns-3'te %15–18'di (deney 33). Edremit'te bu pay %3–7.

**Dikkat:**
- Bu tablo ön bakış; ana sonuç ns-3'ten gelecek.
- "Dolu hücre" sütunu kesinti olmadan da ~2 hücre gösteriyor. Hangi hücreler olduğuna ns-3 sonucundan sonra bakılacak.
- Bölgenin genelinde servis yok oranı (%2,5) Sındırgı'dakinden (%0,8) yüksek. Sık ağda hücre kenarlarında girişim fazla.

## ns-3 deneme koşusu (E0, 1,5 s)

- **Süre:** 2.005 s (~33 dakika). 144 hücre olduğu için Sındırgı'nın iki katına yakın. Sındırgı'daki orana göre tam koşu (4 s) koşu başına ~1,8 saat sürer.
- **Bağlantı:** 727 kullanıcının 726'sı bağlandı.
- **Sinyal kalitesi:** Deprem kullanıcılarında ortanca 14,3 dB. Experia'daki saha değerleri 13,8–15,6 dB. ns-3, f = 0,03 ile gerçek ölçüme oturuyor.
- **Yük:**
  - Ana hücrelerin PRB'si 0,142, hedef 0,18.
  - Sındırgı'da da deneme koşusunda hedefin altında kalmıştı (0,16 / 0,23). Orada yeniden ayar yapılmadı; aynı yöntemi korumak için burada da yapılmıyor.
  - Deney 36, kesinti sonucunun yükteki bu kadar farka duyarlı olmadığını gösteriyor.
- **Dolu görünen hücreler:**
  - Biri dış sahada (267). Yalnız kendi yük kullanıcısı var ve onun sinyali zayıf olduğu için bütün kaynakları kullanıyor.
  - Biri komşu sahada (004, 0,91). Oraya dış sahaların iki yük kullanıcısı da bağlanmış.
  - Bunlar yük kullanıcısı yönteminin yan etkisi; ana sahalarda değil. Sonuçta not edilecek.

## ns-3 tam koşular (E0, E1, E2; 4 s, 22 Kasım)

Süre: koşu başına ~1,7 saat (paralel). Ölçütler KURALLAR.md'deki gibi; puanlama `analiz37.py`, sayılar `analiz.json`.

| Durum | Kapanan sahanın çevresi: servis yok | Aynı kullanıcılar, saha açıkken | Bölge geneli: servis yok | Ana hücre PRB | Dolan ana hücre |
|---|---|---|---|---|---|
| E0 kesinti yok | – | – | %1,5 | 0,15 | 0 |
| E1 529 kapalı | **%0** (64 kişiden 0) | %0 | %1,8 | 0,16 | 0 |
| E2 105 kapalı | **%5,1** (39 kişiden 2) | %2,6 (1 kişi) | %2,0 | 0,16 | 0 |

**Sındırgı ile karşılaştırma (deney 33, ns-3):** kapanan sahanın çevresinde servis yok %15–18. Edremit'te %0–5.

**Sonuç:** Sık kıyı bölgesinde bir saha çökünce komşular boşluğu büyük ölçüde dolduruyor. Kullanıcılar bağlı kalıyor, sinyal kalitesi biraz düşüyor (ortanca 15,6 → 14,5 dB ve 15,4 → 15,2 dB). 105 çökünce zayıf sinyalli kullanıcı payı artıyor (%15 → %21), ama servis neredeyse korunuyor. Hiçbir ana hücre dolmuyor; yük kesintiyle yalnızca 0,15'ten 0,16'ya çıkıyor.

**Hızlı modelle uyum:** Ön bakış %2,6 ve %6,8 demişti; ns-3 %0 ve %5,1 verdi. Sıralama ve büyüklük aynı.

**Dikkat:**
- Çevredeki kullanıcı sayısı küçük (64 ve 39). %5,1, 2 kişi demek; 1-2 kişilik fark rakamı birkaç puan oynatır. Ama Sındırgı ile fark (%15–18'e karşı %0–5) bundan çok büyük.
- Dolu görünen iki hücre (004 ve 267) üç koşuda da aynı ve kesinti olmadan da var. Deneme koşusunda görülen yük kullanıcısı yan etkisi; ana sahalarda değil.
- Ana hücre PRB'si hedefin (0,18) altında kaldı (0,15). Sındırgı'daki gibi yeniden ayar yapılmadı.
- Bölge geneli servis yok oranı kesinti yokken de %1,5 (Sındırgı %0,07). Sık ağda hücre kenarlarında girişim fazla; kesintiden kaynaklanmıyor.
