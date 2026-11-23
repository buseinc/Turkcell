# Deney 36: Hep yayında olan pay (f = 0,03) ns-3'te — sonuçlar

Kurallar `KURALLAR.md` dosyasında; hesaplardan önce yazıldı. Bir düzeltme var: 1 saniyelik koşularda hücre yükü ölçülmediği için kontrol 2, 2 saniyelik iki koşuyla yapılıyor. Düzeltme de sonuç görülmeden yazıldı.

## Kontrol 1: anahtar kapalıyken eskisiyle aynı mı? **Geçti.**

f = 0 ve bütün yeni anahtarlar kapalıyken, yeni kütüphane deney 34'ün `R1_regresyon` koşusuyla birebir aynı altı dosyayı üretti: `radio_samples`, `ues`, `prb_usage`, `voice`, `DlRxPhyStats`, `sectors` (`kontrol1.json`). Yama, açılmadıkça hiçbir şeyi değiştirmiyor.

## Sındırgı kesinti sonucu katsayıyla değişiyor mu? **Değişmiyor.**

Hızlı modelle, deney 33'ün kullanıcıları ve K0–K3 durumlarıyla hesaplandı (`sindirgi_f.py`, `sindirgi_f.json`).

| Durum | Kapanan sahanın çevresinde servissiz, f = 0 | f = 0,03 | Bütün bölgede servissiz, f = 0 → 0,03 | Hücre yükü, f = 0 → 0,03 |
|---|---|---|---|---|
| K0 kesinti yok | – | – | %0,81 → %0,81 | 0,235 → 0,238 |
| K1 482 kapalı | %28,4 | %28,4 | %2,4 → %2,4 | 0,262 → 0,264 |
| K2 130 kapalı | %22,5 | %22,5 | %1,1 → %1,1 | 0,254 → 0,258 |
| K3 ikisi kapalı | %25,6 | %25,6 | %2,6 → %2,6 | 0,287 → 0,290 |

- **Servis yok sayısı:** Katsayı servisi olmayan kullanıcıların sayısını hiç değiştirmiyor. Bunlar zaten sinyalin çok zayıf olduğu kullanıcılar ve %3'lük ek girişim onları etkilemiyor. Yük ise yalnız ~0,003 artıyor.
- **Karar (kurala göre):** Değişim 3 puandan az, yani 0. Deney 33'ün ns-3 kesinti sonuçları geçerli kalıyor; yeniden koşturmaya gerek yok.
- **Bu tablodaki oranlar ns-3 sonuçlarıyla karşılaştırılmamalı.** Hızlı model burada deney 34'ün yeni gölgeleme ve görüş hattıyla, tek bir çekilişle hesaplandı. Kapanan sahanın çevresindeki oran (%22–28), deney 33'ün ns-3 sonucundan (%15–18) farklı çıkıyor. Bu tablo yalnız f'nin etkisini ölçmek için; iki sütun arasındaki farka bakılmalı, oranların kendisine değil.

## Kontrol 2: anahtar açıkken ns-3 ile hızlı model aynı mı? **Geçti.**

İki 2 saniyelik ns-3 koşusu yapıldı (`R2b_f0`, `R2b_f003`): 672 sabit kullanıcı, yumuşak gölgeleme ve görüş hattı açık. Sonuçlar `kontrol2.json` dosyasında.

| | f = 0 | f = 0,03 |
|---|---|---|
| ns-3, ana saha kullanıcılarının ortalama SINR'ı | 13,88 dB | 12,61 dB |
| Hızlı model, aynı hücreler ve ns-3'ün ölçtüğü yükle | 14,10 dB | 12,77 dB |
| Saha başına ortalama fark (sınır 1,5 dB) | 0,20 dB | **0,14 dB** ✅ |

- **Katsayının etkisi:** SINR'ı ns-3'te 1,27 dB, hızlı modelde 1,33 dB düşürüyor. Fark 0,05 dB; sınır 0,5 dB ✅.
- **Hücre yükü:** İki koşuda da aynı (0,226 ve 0,227).

## Sonuç

- **Katsayı artık ns-3'te var.** Varsayılan değeri kapalı; `--alwaysOn 0.03` ile açılıyor.
- **Kapalıyken:** Eski sonuçlar birebir aynı.
- **Açıkken:** ns-3 ve hızlı model aynı formülü uyguluyor.
- **Sındırgı:** Kesinti sonuçlarını değiştirmiyor.
- **Bundan sonra:** Sık bölge (Edremit) koşuları bu katsayı açık olarak yapılacak.
