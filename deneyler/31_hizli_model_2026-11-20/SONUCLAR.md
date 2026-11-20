# 31 — Hızlı model: ns-3'ün yerine geçebilir mi?

**Neden:** ns-3 her paketi tek tek canlandırıyor. Hücre başına 200 görüşmelik tek bir senaryo 9 saat sürdü. Kesinti senaryoları ve İHA yerleşimi için yüzlerce, binlerce senaryo denememiz gerekiyor. Bu hızla imkânsız.

**Hızlı model ne yapıyor** (`hizli_model.py`)?
- Paket yok, zaman yok. Ağın tek bir "fotoğrafı" çekiliyor.
- Sinyal hesabı ns-3'teki formüllerin bire bir aynısı:
  - yol kaybı (3GPP kırsal model),
  - anten deseni,
  - kullanıcı başına gölgeleme (ns-3 ile aynı rastgele değerler),
  - mesafe düzeltmesi,
  - verici bozulması (EVM),
  - gürültü.
- Hücre doluluğu tahminle bulunuyor. Her kullanıcının paketinin kaç kaynak bloğu tuttuğu, ns-3'ün kendi kodlama tablolarıyla hesaplanıyor.
- Sinyal kalitesi ile doluluk birbirine bağlı (dolu komşu, daha çok girişim demek). İkisi birlikte çözülüyor.

**Hız:** Hücre başına 200 görüşmelik senaryo ns-3'te 9 saat, hızlı modelde **1 saniyeden az** sürüyor.

## ns-3 ile karşılaştırma (`dogrula.py`, `dogrulama.json`)

Deney 29'un 7 ns-3 koşusu kullanıldı: normal yükte 3 farklı yerleşim ve hücre başına 25 / 50 / 100 / 200 görüşme. Hızlı modelin sayıları 20 rastgele çekilişin ortalaması. Başarı ölçütleri koşudan önce dosyanın başına yazıldı.

| Senaryo | Değerlendirme hücrelerinin doluluğu (ns-3 → hızlı) | Saha başına SINR farkı | Ortanca SINR (ns-3 → hızlı) | SINR'ı 0 dB altında olanlar (ns-3 → hızlı) |
|---|---|---|---|---|
| Normal yük, yerleşim 1 | 0,22 → 0,18 | 0,8 dB | 15,6 → 17,2 dB | %3 → %3 |
| Normal yük, yerleşim 2 | 0,18 → 0,21 | 1,3 dB | 15,7 → 16,9 dB | %3 → %3 |
| Normal yük, yerleşim 3 | 0,22 → 0,20 | 1,3 dB | 14,9 → 16,8 dB | %5 → %4 |
| 25 görüşme | 0,26 → 0,25 | 0,5 dB | 15,0 → 16,2 dB | %4 → %4 |
| 50 görüşme | 0,36 → 0,35 | 0,4 dB | 14,4 → 15,1 dB | %4 → %4 |
| 100 görüşme | 0,48 → 0,52 | 0,4 dB | 13,5 → 13,8 dB | %5 → %5 |
| 200 görüşme | 0,72 → 0,81 | 0,5 dB | 8,6 → 8,4 dB | %11 → %14 |

**Ölçütler:**

| Ölçüt | Sonuç |
|---|---|
| 1. Sinyal gücü (RSRP) her kullanıcıda ns-3 ile aynı mı? | **Geçti.** Bütün kullanıcılarda; en büyük fark 0,004 dB. |
| 3a. Ortalama doluluk her senaryoda ±0,05 içinde mi? | **Kaldı.** 6 senaryoda tuttu. 200 görüşmede +0,09: hızlı model doluluğu biraz fazla gösteriyor. |
| 3b. Tek tek hücrelerde doluluk farkı 0,10'dan küçük mü? | **Kaldı.** Fark 0,13–0,17. Sebebi aşağıda; ölçüt baştan yanlış seçilmiş. |
| 4a. Saha başına SINR farkı 1,5 dB'den küçük mü? | **Geçti.** 0,4–1,3 dB. |
| 4b. Experia'ya göre hata ns-3'ünkinden en fazla 1 dB kötü mü? | **Geçti.** Test sahalarında hızlı model 1,84 dB, ns-3 1,87 dB. Ayar sahalarında hızlı model 3,8 dB, ns-3 2,9 dB. |

**Formül tek başına da sınandı:** ns-3'ün kendi hücre atamaları ve doluluk değerleri hızlı modele verildiğinde, saha başına SINR farkı yalnızca 0,3–0,7 dB çıkıyor. Yani kalan farkın çoğu formülden değil, rastgelelikten geliyor.

## Önemli bir bulgu: tek koşu yanıltıcı

Modelde bir bağlantının açık görüş (LOS) olup olmadığına yazı-tura gibi rastgele karar veriliyor. ns-3 de böyle yapıyor. Bunun etkisi beklenenden büyük:
- Yazı-tura yeniden atıldığında kullanıcıların **%40'ı başka bir hücreye** bağlanıyor.
- Tek tek hücrelerin doluluğu da bu yüzden ortalama 0,13–0,19 değişiyor (`rastgelelik_tabani.json`).

Hızlı model ile ns-3 arasındaki hücre farkı (0,13–0,17) ve aynı hücreye bağlananların oranı (%57–63), hızlı modelin kendi iki çekilişi arasındaki farkla aynı. Yani ns-3 koşusu, hızlı modelin üreteceği çekilişlerden biri gibi davranıyor.

Bundan çıkan iki sonuç:
- **3b ölçütü ulaşılamaz bir ölçüttü.** ns-3'ü başka bir rastgele çekilişle tekrar koşsaydık, kendisiyle bile bu ölçütü sağlayamazdı. Bunu ölçütü yazarken düşünmemiştim. Ölçüt geriye dönük olarak değiştirilmedi; "kaldı" olarak duruyor.
- **Şimdiye kadarki ns-3 sonuçlarının hepsi tek bir çekilişe dayanıyor.** Tek bir hücre ya da saha hakkındaki sonuçlar şansa bağlı olabilir. Hızlı modelle her senaryoyu onlarca çekilişle koşup hata payı verebiliriz.

## Hızlı modelin sınırları

- Paket gecikmesi ve kuyruklar yok. "Kaç kişi konuşabiliyor" sorusunu doğrudan cevaplamıyor. Gecikmenin deprem yükünde sorun olmadığı deney 29'da ns-3 ile zaten gösterildi.
- Sinyal kalitesinden kodlama seviyesine geçişte ns-3'ün ayrıntılı hata modeli yerine yaygın kullanılan eşik tablosu kullanılıyor.
- Çok yüksek yükte (hücre başına 200 görüşme) doluluğu %10 kadar fazla gösteriyor.
- Ayar sahalarında Experia'ya göre hatası ns-3'ünkinden ~1 dB büyük. Test sahalarında ise aynı.

## Yol boyunca düzeltilen iki hata

1. **Saha koordinatları:** ns-3'ün `sectors.csv` dosyası koordinatları 12 haneyle yazıyor. Gölgeleme değeri ise koordinatın tam haline bakılarak hesaplanıyor. Kullanıcıların %10'unda sinyal gücü bu yüzden tutmadı. Koordinatlar girdi dosyasından alınınca hepsi tuttu.
2. **Karşılaştırma yöntemi:** İlk sürümde ns-3'ün seçtiği hücrenin açık görüş durumu sabit tutulup diğer bağlantılar yeniden çekiliyordu. Bu, hızlı modele daha güçlü bir hücre bulmak için ikinci bir şans veriyordu ve SINR'ı ~1,4 dB yüksek gösteriyordu. Son karşılaştırmada bütün bağlantılar baştan çekildi.

Ayrıca ilk sürüm, komşu hücrelerin kaynak bloklarını rastgele kullandığını varsayıyordu. ns-3'ün zamanlayıcısı ise blokları hep bandın başından dolduruyor (`pf-ff-mac-scheduler.cc`). Model buna göre düzeltildi. Bu düzeltmeden sonra az yükteki doluluk farkı kapandı.

## Karar

Hızlı model kesinti ve İHA senaryolarında ana araç olarak kullanılabilir:
- Sinyal gücü birebir aynı.
- Sinyal kalitesi saha başına 1,3 dB içinde.
- Experia'ya göre doğruluğu test sahalarında ns-3 kadar iyi.
- Ortalama doluluk, en yüksek yük dışında tutuyor.

ns-3 yalnızca sonunda seçilecek birkaç durumu doğrulamak için kullanılacak.

**Sıradaki adım:** Kesinti senaryoları K1 / K2 / K3 (deney 30), her biri onlarca çekilişle.

## Ek: ses kapasitesinin sınırı (`kapasite_siniri.py`, `kapasite_siniri.json`)

Deney 29'un 300'lük adımı ns-3'te bitirilemedi. Aynı kurulum hızlı modelle 500'e kadar koşuldu (her adım 20 çekiliş). Değerlendirme hücreleri 24 tane.

| Hücre başına görüşme | Ortalama hücre doluluğu | Bandı tamamen dolan hücre (24'ten) |
|---|---|---|
| 100 | %53 | 0,3 |
| 200 | %81 | 7 |
| 250 | %90 | 14 |
| 300 | %93 | 17 |
| 400 | %97 | 21 |
| 500 | %98 | 22 |

**Dikkat:** 200'de ns-3'te hiçbir hücre dolmadı (en dolu hücre %87, gecikme 14 ms). Hızlı model ise 7 hücreyi dolu gösteriyor. Yani hızlı model yüksek yükte, özellikle en kalabalık hücrelerde, fazla kötümser. Ortalama doluluğu ns-3'ten %12 fazla buluyordu, en dolu hücrelerde fark daha büyük. Bu yüzden buradaki sınır güvenli tarafta, yani gerçekte daha yüksek.

**Sonuç:** Ortalama bir hücre hücre başına yaklaşık **250–300 görüşmede** doluyor. En kalabalık hücreler daha erken doluyor. ns-3, 200'de hâlâ tıkanma olmadığını gösteriyor. Deprem anında en yoğun hücre (443) en yoğun 15 dakikada ~101 bağlı kullanıcı taşıdı (deney 32, KPI'dan ölçüldü). Bu, sınırın yaklaşık üçte biri.
