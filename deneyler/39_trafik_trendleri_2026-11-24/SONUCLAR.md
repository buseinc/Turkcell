# Deney 39: Gün içi trafik trendleri, sonuçlar (24 Kasım)

Kurallar `KURALLAR.md`, ilçe seçimi `ilce_secimi.md`. Kod: `suz.py` (KPI süzme), `trend.py` (hesap ve şekil). Sayılar `trend_sehir.json`, şekil `trend_sehir.png`. Ham süzme ve hücre başına yük dosyaları (`*.csv.gz`) yalnız yerelde.

İlk bölgeler: **Balıkesir merkez** (2 ilçe, 1.153 hücre) ve **Bandırma** (429 hücre). Bütün ilçe kullanıldı, yalnız modeldeki sahalar değil.

## Önceden konan şartlar

| Şart | Balıkesir merkez | Bandırma | Sonuç |
|---|---|---|---|
| Üç pazartesi birbirine benziyor mu (sınır 0,2) | en büyük fark 0,13 | en büyük fark 0,08 | geçti, ortalama "tipik pazartesi" olarak kullanılabilir |
| 17 Ağustos öbür yaz günlerine benziyor mu (sınır 0,2) | 0,09 | 0,06 | geçti, yaz hafta sonu grubuna girdi |

## Ne çıktı

Sayılar hücre başına ortalama bağlı kullanıcı. İlk sayı Balıkesir merkez, ikincisi Bandırma.

**Hafta içi (pazartesi, okul açık):**
- **Gece** en sakin: 03:00–05:00 arası 7,1 / 9,3 kişi. En düşük nokta 05:00–05:30.
- **Sabah gidiş** çok belirgin: 06:30'dan sonra hızla artıyor. 07:00 ile 09:00 arasındaki artış günlük ortalamanın %45'i / %41'i. Hafta sonunda bu artış yalnız %27 / %22 ve daha geç başlıyor.
- **Mesai / okul** saatlerinde (09:00–16:00) gece seviyesinin 2,8 / 2,3 katı.
- **Günün en kalabalık saati 15:30**, iki şehirde de aynı: 22,9 / 24,4 kişi. 15:00–15:30 arasında ani bir sıçrama var. Okul çıkışı ya da vardiya değişimi olabilir, veri sebebini söylemiyor.
- **Akşam**: 16:00'dan sonra bağlı kişi sayısı yavaş yavaş azalıyor. **Bağlı kişi sayısında ayrı bir akşam zirvesi yok.**
- **Ama kapasite kullanımı akşam en yüksek**: 21:15 / 20:45. Yani akşam daha az kişi bağlı ama kişi başına daha çok veri kullanılıyor. Evde video izleme olabilir, bu bir tahmin.

**Hafta sonu:** Seviye daha düşük (gün ortalaması 13,6 / 15,5 kişi; hafta içi 15,7 / 17,4). Sabah artışı yavaş, öğleden gece 22:00'ye kadar düz.

**Yaz ile okul dönemi (yalnız hafta sonu karşılaştırılabildi):** İki şehirde de biçim neredeyse aynı (fark 0,10 / 0,06). Şehirde yazın büyük bir değişiklik yok. Edremit gibi turistik yerde farklı çıkması beklenir, henüz bakılmadı.

**Deprem sonrası:** 10 Ağustos depreminin olduğu 20:00 diliminde ani sıçrama, sonra yavaş düşüş. Bu grup farklı gün ve saatlerin karışımı, yalnız karşılaştırma için.

**Gündüz ve akşam hücreleri (hafta içi):**

| | Balıkesir merkez | Bandırma |
|---|---|---|
| Gündüz hücresi (mesai ≥ 1,2 × akşam) | %33 | %34 |
| Akşam hücresi (mesai < 0,8 × akşam) | %35 | %29 |
| Karışık | %33 | %37 |

Haritada her daire bir saha. Rengi, o sahanın hücrelerinin ortalama gündüz/akşam oranından geliyor; tablodaki yüzdeler ise hücre bazında. Eksenler, ilçedeki sahaların ortasından km cinsinden uzaklık.
- **Balıkesir merkez:** Şehrin ortasındaki sahalar çoğunlukla akşam kalabalık (mavi), yani konut. Hemen çevrelerindeki halka, özellikle güney ve doğu tarafı, gündüz kalabalık (kırmızı), yani gündüz insanların gittiği yerler. Uzak kırsal sahalarda ikisi yakın (gri).
- **Bandırma:** Merkez akşam kalabalık ya da karışık. Merkezin batısı ve güneydoğuya uzanan hat gündüz kalabalık.
- Kırmızı bölgelerin sanayi, üniversite ya da yol olduğu tahmin. Haritada yer adı yok ve veri bunu tek başına söylemiyor.

## Simülasyon için saatler

Hücre başına yük, üç pazartesinin ortalaması:

| Saat | Balıkesir merkez: bağlı kişi / kapasite kullanımı | Bandırma: bağlı kişi / kapasite kullanımı |
|---|---|---|
| Sabah gidiş, 08:45 | 16,1 / %18 | 17,6 / %19 |
| En kalabalık saat, 15:30 | 22,9 / %28 | 24,3 / %30 |
| Kapasite zirvesi (21:15 / 20:45) | 18,3 / %35 | 19,4 / %38 |

- Normal bir pazartesi bile bazı hücreler bu saatlerde neredeyse dolu: en yoğun hücrede kapasite kullanımı %94–97. Şehirde kapasite sorunu Sındırgı'dakinden daha yakın olabilir. Bu, kesinti ve İHA denemelerinde önemli.
- Hücre başına yükler `yuk_saatleri_sehir_*.csv.gz` dosyalarında (yalnız yerelde).

## Sınırlar

- Hafta içi yalnız pazartesi (3 gün). Salı–cuma farklı olabilir.
- Okul açık hafta sonu tek gün (26 Ekim).
- Yaz hafta içi yok, yaz etkisi yalnız hafta sonunda görülebildi.
- KPI bağlı telefonu sayıyor, konuşan veya veri kullanan kişiyi değil.
- 15:30 sıçramasının ve akşam veri artışının sebebi tahmin.
