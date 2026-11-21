# Deney 33: ns-3 ile deprem anında saha kesintisi (21 Kasım)

## Ne yaptık

ns-3 modelinin kendisini (deney 29) değiştirmeden dört durumu koşturduk:

- **Kullanıcılar:** 27 Ekim 2025 depremindeki ölçülmüş yük, yani 1.473 kullanıcı.
- **Durumlar:**
  - K0: kesinti yok
  - K1: 482 sahası kapalı
  - K2: 130 sahası kapalı
  - K3: ikisi birden kapalı
- **Koşu:** Her biri 4 saniye; dört durumda da kullanıcılar aynı.

Ölçütleri koşudan önce `prepare.py` dosyasına yazdık:

- **Servis yok:** Telefon şebekeye bağlanamıyor ya da sinyal kalitesi (SINR) −6,7 dB'nin altında. Bu, CQI 0 demek.
- **Zayıf sinyal:** Alınan sinyal −121,8 dBm'in altında (TS 36.101).
- **Dolu hücre:** Hücrenin kaynak kullanımı (PRB) %95 veya üstü.

Paket kaybına göre değerlendirme yapmadık, çünkü ns-3'ün bu konuda güvenilmez olduğunu deney 29'da gördük.

**Yük kontrolü:** Kesinti yokken değerlendirme hücrelerinin ortalama doluluğu 0,17 çıktı. Hedef 0,23'tü; baştan kabul ettiğimiz aralık 0,15–0,35. Yük kabul edildi, ama ns-3'te ağ hedefe göre biraz hafif.

## Sonuç

| Durum | Servisi olmayan (tüm bölge) | Zayıf sinyal (tüm bölge) | Kapanan sahanın kullanıcılarında servisi olmayan | Kapanan sahanın kullanıcılarında zayıf sinyal | En dolu hücre | Dolu hücre |
|---|---|---|---|---|---|---|
| K0 kesinti yok | %0,1 | %3,1 | – | – | 0,33 | 0 |
| K1 482 kapalı | %1,1 | %4,7 | **%18** (81 kişiden) | %28 | 0,44 | 0 |
| K2 130 kapalı | %0,5 | %3,7 | **%15** (40 kişiden) | %38 | 0,32 | 0 |
| K3 ikisi kapalı | %1,6 | %5,0 | **%17** (121 kişiden) | %28 | 0,43 | 0 |

Sonuçları üç maddede özetleyebiliriz:

1. **Kapasite sorunu yok.** Bir ya da iki saha kapandığında da hiçbir hücre dolmuyor. En dolu hücre yarı dolu bile değil (0,44). 482'nin komşusu 443'ün doluluğu 0,29'dan 0,36'ya çıkıyor.
2. **Sorun kapsama.** Kapanan sahanın çevresindeki kullanıcıların yaklaşık altıda biri servis alamıyor. Bunun nedeni komşu sahaların sinyalinin oraya yeterince ulaşmaması.
3. **Etki kapanan sahanın çevresiyle sınırlı.** Bölgenin tamamında servisi olmayanların oranı %0,1'den %1–1,6'ya çıkıyor.

**Aynı kullanıcılar, sahalar açıkken (K0):**

| Kullanıcılar | Servisi olmayan, saha açık | Servisi olmayan, saha kapalı | Ortanca sinyal kalitesi, açık → kapalı |
|---|---|---|---|
| 482'nin 81 kullanıcısı | %0 | %18,5 | 18,9 → 6,0 dB |
| 130'un 40 kullanıcısı | %0 | %15 | 8,3 → 2,4 dB |

Saha açıkken bu kullanıcıların hiçbiri servissiz değil. Yani tablodaki servissizlik tamamen kesintiden geliyor.

## Hızlı modelle karşılaştırma

Hızlı modeli aynı kullanıcılarla, 20 farklı rastgele görüş hattı çekilişiyle çalıştırdık. Tabloda bu 20 çekilişin %5–%95 aralığı var:

| Durum | Kapanan sahanın kullanıcılarında servisi olmayan: ns-3 | Hızlı model | Zayıf sinyal: ns-3 | Hızlı model |
|---|---|---|---|---|
| K1 | %18 | %18–23 | %28 | %33–41 |
| K2 | %15 | %25 | %38 | %40 |
| K3 | %17 | %21–24 | %28 | %36–41 |

- **Servis yok:** İki araç aynı büyüklüğü veriyor. ns-3 aralığın alt ucunda ya da biraz altında; hızlı model biraz kötümser.
- **K2'deki fark:** K2'de yalnızca 40 kullanıcı var. Fark 4 kişiye denk geliyor.
- **Hiçbir hücre dolmuyor:** Bu sonuç iki araçta da aynı.
- **Uyuşmayan nokta:** Saha kapandığında ns-3'te komşu hücrelerin doluluğu artıyor (0,17'den 0,22'ye). Hızlı modelde ise biraz azalıyor (0,23'ten 0,21'e). Muhtemel neden şu: hızlı model servis alamayan kullanıcıların hiç kaynak kullanmadığını varsayıyor; ns-3'te ise bu kullanıcılar kötü sinyalle de olsa kaynak harcıyor. Bu nedeni henüz doğrulamadım. Sonucu değiştirmiyor; bunu not olarak düşüyoruz.

## L25: "yüzde 15–20'si konuşamıyor" sonucunun kodlama kontrolü

- **Kontrol 1 tuttu.** İzleme anahtarı açıkken `voice.csv` deney 29'dakiyle bayt bayt aynı çıktı. Yani bu anahtar sonucu değiştirmiyor.
- **Kontrol 2 yapılamadı. Bu benim hatam.** Kodda `EnableDlPhyTraces` çağırmışım. Bu çağrı yalnızca RSRP/SINR dosyasını yazıyor. Hangi veri bloğunun hatalı alındığını gösteren dosya (`DlRxPhyStats.txt`) ise ayrı bir çağrıyla açılıyor: `EnableDlRxPhyTraces`. Kısa deneme koşusunda bu dosyanın oluşup oluşmadığına bakmadım.
- **Düzeltme:** Kodda tek satırı değiştirip L25'i tek başına yeniden koşturmak yeterli; yaklaşık 1 saat sürer. K0–K3 sonuçları bu hatadan etkilenmiyor, çünkü onlarda bu anahtar kapalıydı.
- **21 Kasım, düzeltme yapıldı:**
  - Satır `EnableDlRxPhyTraces` olarak düzeltildi; değişiklik `plan.json` içinde `amendment_21Nov` başlığıyla kayıtlı.
  - İlk L25 `L25_v1_yanlis_iz` klasöründe saklandı.
  - 1 saniyelik deneme koşusunda dosya oluştu.
  - Bu kısa denemede ilk ön bulgu: sinyali iyi (>3 dB) konuşma kullanıcılarının ilk gönderimlerinin %14'ü hatalı. Hedef %10'du.

### L25 sonucu (4 saniyelik koşu, 21 Kasım)

- **Kontrol 1 yeniden tuttu.** `voice.csv`, deney 29 ile bayt bayt aynı.
- **Kontrol 2: açıklama ana sebep olarak tutmadı.**
  - Sinyali iyi (>3 dB) 552 konuşma kullanıcısında ilk gönderimlerin %13,6'sı bozuk. Bu, 100.192 veri bloğu üzerinden hesaplandı.
  - ns-3'ün hedefi %10. Önceden yazdığımız kurala göre, açıklama doğru olsaydı bu oran %10'un çok üstünde çıkmalıydı.
  - Hedefin biraz üstünde; uyuşmazlık var ama küçük.

Aynı 552 kullanıcı, veri bloklarının bozulma oranına göre ve ITU ölçütüne göre:

| İlk gönderimde bozulma oranı | Kullanıcı | Konuşabilen | Konuşamayan |
|---|---|---|---|
| %20'den az | 469 | 420 | 49 |
| %20–50 | 31 | 26 | 5 |
| %50'den çok | 52 | 38 | 14 |

- **Konuşamayanların çoğunda bloklar bozulmuyor.** Konuşamayan 68 kişinin 49'u bu durumda.
- **Blokları çok bozulanların çoğu yine konuşabiliyor.** Yeniden gönderim, paketi 50 ms içinde kurtarıyor.
- **Konuşamayanlarda asıl sorun gecikme ve kayıp.** Blokları bozulmayan 49 kişide ortalama gecikme 41 ms, en uzun gecikme 114 ms, paketlerin ~%9'u kayıp.
- **Yükle ilgisi yok.** Bu kişiler 31 farklı hücreye dağılmış; hücrelerin doluluğu konuşabilenlerinkiyle aynı (0,18).
- **Sebep henüz bilinmiyor.** "Komşular susarken ölçülen kalite" açıklaması deney 29'da güncellendi. Normal günde "%15–20 konuşamıyor" sonucunun gerçek mi yoksa ns-3'ün bir davranışı mı olduğu açık kaldı. Bu, kesinti sonuçlarını (K0–K3) etkilemiyor, çünkü onları paket teslimine göre değil, sinyal ölçütleriyle değerlendirdik.
- **Dosyalar:** `l25_kontrol.py`, `l25_kontrol.json`, `simulation/results/L25`.

## Sınırlar

- **Tek çekiliş:** Tek anten yönü çekilişi ve tek görüş hattı çekilişi var. Bu yüzden kapanan sahanın çevresindeki oranlar birkaç puan oynayabilir; hızlı modeldeki aralık bunu gösteriyor.
- **Deney 32'deki bilinen sınırlar geçerli:**
  - tek taşıyıcı
  - 24 saha
  - düz arazi
  - 482'nin kendi sahasındaki kalan hücrenin kullanıcıları gerçekte almaması

## Dosyalar

- `analiz.py` ve `analiz.json`
- ns-3 çıktıları: `simulation/results/K0..K3` ve `L25`
