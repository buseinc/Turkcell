# Deney 43: Şehirde kesinti, sonuçlar (26 Kasım)

Kurallar `KURALLAR.md`. Kod `hizli43.py`, sayılar `hizli43.json`. Şimdilik yalnız hızlı model (3 saat × 10 anten çekilişi). ns-3 koşuları henüz yapılmadı.

Tablolarda önce 10 çekilişin ortalaması, köşeli parantezde en düşüğü–en yükseği.

## Kesinti yokken (C0)

| Saat | Kullanıcı | Ortalama hücre doluluğu (KPI hedefi) | Servis yok (bütün bölge) | Dolu hücre |
|---|---|---|---|---|
| 08:45 | 4.321 | %18,4 (%18) | %6,9 | 0 |
| 15:30 | 6.244 | %28,5 (%28) | %6,0 | 0–1 |
| 21:15 | 4.730 | %34,5 (%35) | %5,9 | 0–1 |

## Etkilenen kullanıcılar (kapanan hücrelere bağlı olanlar)

| Durum | Saat | Kişi | Servis yok: önce → sonra | Zayıf sinyal (sonra) | Aldığı veri (önceye göre) |
|---|---|---|---|---|---|
| **C1: 195** | 08:45 | 42 [35–55] | %3,6 → %8,4 [0–15] | %19 | %95 |
| | 15:30 | 56 [48–68] | %2,7 → %9,7 [6–19] | %19 | %93 |
| | 21:15 | 62 [51–70] | %3,7 → %8,7 [3–14] | %19 | %95 |
| **C2: 087 + 108** | 08:45 | 103 [90–108] | %2,6 → %5,9 [2–14] | %14 | %97 |
| | 15:30 | 204 [180–226] | %1,7 → %5,7 [4–11] | %12 | %97 |
| | 21:15 | 142 [132–148] | %1,7 → %7,4 [5–10] | %15 | %95 |
| **C3: 116'nın 2 yönü** (3 seçenek) | 08:45 | 14–18 | %2–7 → %8–9 | %10 | %92–97 |
| | 15:30 | 23–31 | %1–3 → %2–4 | %4–6 | %99 |
| | 21:15 | 25–31 | %2–5 → %3–6 | %5–11 | %98–99 |

## Devralan komşu hücreler

| Durum | Saat | Devralan hücre | Doluluk: önce → sonra | En dolu devralan hücre (sonra) | Eski kullanıcılarının verisi |
|---|---|---|---|---|---|
| C1 | 08:45 | 18 | %16 → %19 | %30 | değişmiyor |
| | 15:30 | 22 | %27 → %30 | %60 | değişmiyor |
| | 21:15 | 24 | %41 → %45 | %68 | değişmiyor |
| C2 | 08:45 | 28 | %18 → %20 | %35 | değişmiyor |
| | 15:30 | 36 | %33 → %37 | %78 | değişmiyor |
| | 21:15 | 33 | %38 → %43 | %65 | değişmiyor |
| C3 | üç saat | 9–15 | 1–2 puan artış | %25–66 | değişmiyor |

Hiçbir durumda bölgede yeni dolu hücre çıkmıyor.

## Ne anlama geliyor

- **Şehirde komşular yükü kaldırıyor.** Kapanan sahanın kullanıcıları 18–36 komşu hücreye dağılıyor; her birinin doluluğu yalnız 2–5 puan artıyor. En dolu devralan hücre bile %84'ü geçmiyor.
- **Kayıp küçük ama sıfır değil.** Etkilenenlerin %6–10'u servissiz kalıyor (kesinti yokken %2–4). Bunlar komşu sahaya uzak duranlar. Aldıkları veri ortalama %3–7 düşüyor.
- **Komşuların kendi kullanıcıları etkilenmiyor.**
- **Saat farkı:** Etkilenen kişi sayısı en çok 15:30'da; komşular en çok 21:15'te zorlanıyor. Yine de hiçbir saatte hücre dolmuyor.
- **116'nın kısmi kesintisi** en hafif durum: az kişi etkileniyor, sahanın açık kalan yönü ve komşular kapatıyor.
- **Sındırgı ile fark:** Kırsalda sorun sinyalin ulaşmamasıydı. Şehirde sinyal büyük ölçüde ulaşıyor ve kapasite de yetiyor.

## Sınırlar

- **Yük ayarı bazı hücrelerde tutmadı.** Ortalama doluluk KPI'daki hedefe eşit (yukarıdaki ilk tablo). Ama bazı çekilişlerde tek tek hücrelerde hedeften fark 0,2–0,7'ye çıkıyor (deney 42'de en çok 0,09'du). 15:30, çekiliş 42 incelendi (`hazirla43.py`, `inputs/cells_43.csv`): 282 hücreden 11'i hedeften 0,01'den fazla sapıyor, 10'unda sapma en çok 0,035. Asıl sapan tek hücre: 134'ün 0 numaralı hücresi, 4 kullanıcısı var, hedef %52, modelde %75 (yani olduğundan dolu, kötümser yönde). 087 + 108'i devralan 42 hücreden 4'ü sapanlar arasında.
- **Modelde sahada 3 hücre ve tek frekans var**; gerçekte ortalama 11 hücre. Kullanıcı sayısı bir katmanın kullanıcıları. Bu yüzden "kişi" sütunu gerçek etkilenen insan sayısı değil, bir katmandaki sayı.
- **Sinyal kalitesi modelde ölçümden 2–3 dB kötü** (deney 40). Servis yok payları bu yönden biraz kötümser olabilir.
- Kesintiler gerçekte başka saatlerde oldu; burada "bu saatte olsaydı" sorusuna bakılıyor.
- Bunlar hızlı model sonuçları. Ana sonuçlar ns-3'ten gelecek.
