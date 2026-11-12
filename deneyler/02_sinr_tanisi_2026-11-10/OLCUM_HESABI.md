# ns-3.44 ölçüm hesabının denetimi

İncelenen durum: sabitlenen 24 saha, 72 aynı frekanslı sektör, 64 sabit kullanıcı;
`UsePdschForCqiGeneration=false`, düz zemin, log-distance üs 3, shadowing/fading kapalı.
Bu belge bu durumun hesabını açıklar. Experia ölçüm tanımı henüz bilinmiyor.

## Kodda hangi değer nereden geliyor?

| Alan | ns-3 kaynağı | Birim ve işlem |
|---|---|---|
| Radyo izindeki RSRP | `LteUePhy::GenerateCqiRsrpRsrq` | RB'lerin ortalama alınan PSD'si × 15.000 Hz; watt olarak izlenir. Biz `10 log10(W)+30` ile dBm'e çeviriyoruz. |
| Radyo izindeki SINR | `GenerateCtrlCqiReport` → `GenerateCqiRsrpRsrq` | Her RB'de S/(I+N), önce doğrusal RB ortalaması; biz `10 log10` ile dB'ye çeviriyoruz. |
| Ölçüm izindeki RSRP | `ReceivePss` → `ReportUeMeasurements` | PSS PSD'sinden aynı referans güç dönüşümü; dBm örnekler ölçüm penceresinde aritmetik ortalanır. |
| Ölçüm izindeki RSRQ | `GenerateCqiRsrpRsrq` → `ReportUeMeasurements` | PSS gücü, toplam kontrol sinyali+girişim+gürültüye göre normalize edilir; dB örnekler ortalanır. |

Radyo izi örnekleme sayacı 97 alt çerçeve; UE ölçüm raporu varsayılan filtre
penceresi 200 ms. Bunlar ayrı izlerdir. Analizde bağlantı kurulduktan sonraki
ve en az 1. saniyedeki, son hizmet hücresiyle eşleşen geçerli örnekler kullanılır.

Projenin saha özetleme sırası: zaman örnekleri → UE ortalaması → bağlı UE'lerin
sektör ortalaması → geçerli sektörlerin eşit ağırlıklı saha ortalaması.
Experia'da mevcut hücre zaman ortalamaları sahada eşit hücre ağırlığıyla birleştirilir.
Bu iki örneklem aynı kullanıcıları veya aynı gerçek sektörleri temsil etmiyor.

## Sinyal, girişim ve gürültü

`LteInterference::ConditionallyEvaluateChunk` şu hesabı yapar:

```text
I+N = bütün alınan sinyaller − istenen sinyal + alıcı gürültüsü
SINR = istenen sinyal / (I+N)
```

`ReportInterference` adıyla iletilen değer **yalnız girişim değildir; gürültüyü de içerir.**
Bu tanıda gürültüyü bir kez çıkararak I'yi bulduk. Ana projenin mevcut SINR izinde
bu değer elle bölünmediğinden, önceki SINR hesabına ek gürültü koyma/çıkarma hatası yoktur.

Gerçek UE özelliği `GetNoiseFigure()` ile 9 dB olarak okundu.
Kurulu yardımcı sınıfın hesabı:

```text
Gürültü PSD = 10^((-174 + 9 − 30)/10) W/Hz
             = −165 dBm/Hz
Bir referans elemanı (15 kHz) için: −123,239 dBm
100 RB × 180 kHz = 18 MHz üzerinde: −92,447 dBm
```

20 MHz nominal LTE taşıyıcısı ile 100 RB'nin toplam 18 MHz kaynak genişliği
aynı kavram değildir. RSRP'yi 18 MHz toplam gürültüyle doğrudan karşılaştırmak
yanlış olur; güçler aynı bant/genişlik tanımına getirilmelidir.

Kontrol yöntemi, komşuların veri yükünden bağımsız kontrol sinyallerini girişim
olarak içerir. ns-3'te ayrıca PDSCH girişimine dayanan bir mixed CQI yöntemi vardır.
Bu çalışmada moda geçiş yapılmadı. [Resmî ns-3.44 model belgesi](https://www2.nsnam.org/docs/release/3.44/models/singlehtml/index.html).

## RSRQ ile SINR ilişkisi

Bu sabit ve RB'ler arasında düz kontrol spektrumlu senaryoda, kaynak kodundaki
RSRQ hesabı şu ilişkiye indirgeniyor:

```text
RSRQ(dB) = 10 log10[S / (2 × (S + I + N))]
         = −10 log10[2 × (1 + 1/SINR_linear)]
```

Bu ilişkinin bileşenlerden üretilen RSRQ'su, yerel UE ölçüm iziyle karşılaştırıldı.
En büyük kullanıcı ortalaması farkı yaklaşık 4,13×10⁻¹² dB bulundu.
Bu, seçilen ns-3 hesabının iç tutarlılığıdır; gerçek LTE ölçümlerinin veya
Experia'daki farklı örneklem ortalamalarının aynı formüle uyması gerektiği iddiası değildir.

## İz eklemenin ve bağımsız hesabın kontrolü

- Yeni gözlemciler sinyal ve I+N PSD'lerini aynı simülasyon zamanında okur.
  Zaman hizası uyuşmazsa koşu hata verir. Şebeke ayarlarını değiştirmez.
- Orijinal 64 kullanıcının hizmet saha/sektörü, bağlantısı ve alınan baytları
  aynıdır; RSRP/SINR/RSRQ farkı sayısal hassasiyet düzeyindedir.
- Isınma sonrası 1.984 örnekte RSRP ve SINR bileşenlerden yeniden hesaplandı.
- Her sektörün alınan gücü ayrıca koordinat, 3B uzaklık, anten deseni ve
  log-distance formülüyle hesaplandı. İstenen güç ve diğer sektörlerin güç toplamı
  gözlenen değerlerle yaklaşık 10⁻⁹ dB düzeyinde uyuştu. Girişimi sahalara
  ayırırken bu bağımsız hesap kullanıldı.
- Kontroller: [checks.json](checks.json). Kurulu kaynak hash'leri:
  [source_manifest.json](source_manifest.json).

## İncelenen birincil kaynaklar

- [lte-ue-phy.cc](sources/src/lte/model/lte-ue-phy.cc): `GenerateCqiRsrpRsrq`, `ReceivePss`, `ReportUeMeasurements`, gürültü katsayısı.
- [lte-helper.cc](sources/src/lte/helper/lte-helper.cc): kontrol ve mixed CQI bağlantıları.
- [lte-interference.cc](sources/src/lte/model/lte-interference.cc): S/(I+N), zaman parçaları ve gözlemci çağrı sırası.
- [lte-chunk-processor.cc](sources/src/lte/model/lte-chunk-processor.cc): zaman ağırlıklı PSD/SINR birleştirmesi.
- [lte-spectrum-value-helper.cc](sources/src/lte/model/lte-spectrum-value-helper.cc): watt/PSD ve gürültü hesabı.
- [lte-enb-phy.cc](sources/src/lte/model/lte-enb-phy.cc): tam RB genişliğinde kontrol yayını.
- [cosine-antenna-model.cc](sources/src/antenna/model/cosine-antenna-model.cc) ve
  [propagation-loss-model.cc](sources/src/propagation/model/propagation-loss-model.cc): bağımsız güç hesabı.
