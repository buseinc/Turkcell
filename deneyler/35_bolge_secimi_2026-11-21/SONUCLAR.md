# Deney 35: İkinci bölge için veri kapsamı (21 Kasım)

Betik: `veri_kapsami.py`. Yalnız yerel dosyalar okundu, ham veri kopyalanmadı. Çıktı: `veri_kapsami.csv` (sayılar), `veri_kapsami.log`.

## Ne var

- **Tek il:** Experia'daki bütün kayıtlar tek bir ile ait (`CITY_001`), 20 ilçe.
- **Adlar gizli:** İl ve ilçe adları gizlenmiş (`DISTRICT_0001` … `DISTRICT_0020`).
- **KPI kapsamı:** Bütün ilçelerde hücrelerin %85–100'ü KPI'da da var. Yani yük ve deprem anı verisi her ilçe için mevcut.
- **Deprem günleri:** KPI aynı günleri (10 Ağustos, 27 Ekim depremleri) bütün ilde kapsıyor. Bu, deprem anındaki yükü yeni bölgede de ölçebileceğimiz anlamına geliyor.

## İlçeler (konumlarından tahmin edilen adlarla)

İlçe adlarını ortalama saha koordinatlarına bakarak tahmin ettim; **resmî eşleşme değil**. Sındırgı eşleşmesi kendi bölgemizle tutuyor: `DISTRICT_0019`, 39,24 K 28,26 D.

| Kod | Tahmini ilçe | Tür | Saha | Hücre | En yakın saha (ort.) | 100 km²'de saha |
|---|---|---|---|---|---|---|
| 0008 | Edremit (Akçay–Altınoluk) | sahil | 82 | 1.098 | 0,8 km | 33,9 |
| 0002 | Ayvalık | sahil | 60 | 765 | 1,0 km | 18,9 |
| 0006 | Burhaniye | sahil | 30 | 380 | 1,8 km | 14,4 |
| 0010 | Gömeç | sahil (küçük) | 12 | 172 | 1,6 km | 32,2 |
| 0004 | Bandırma | sahil + şehir | 43 | 475 | 1,9 km | 6,8 |
| 0009 | Erdek | sahil | 27 | 318 | 2,1 km | 8,6 |
| 0001 + 0014 | Balıkesir merkez (Altıeylül + Karesi) | şehir merkezi | 72 + 46 | 686 + 507 | 1,6–1,7 km | 9,5–12,0 |
| 0019 | **Sındırgı (bizim bölge)** | kırsal | 20 | 98 | **5,2 km** | 2,5 |

## Yorum

- Sahil ilçelerinde sahalar Sındırgı'dakinden 3–6 kat daha sık. Edremit'te en yakın saha ortalama 0,8 km, Sındırgı'da 5,2 km.
- Sındırgı'daki ana bulgumuz şuydu: kesintide sorun, seyrek bölgede sinyalin ulaşmaması. Sık sahalı bir bölge bu bulguyu sınamak için doğru karşılaştırma. Komşu sahalar boşluğu dolduruyor mu? Kullanıcı yoğun olduğu için bu sefer kapasite mi sorun oluyor?

## Adım 1–2: Edremit kıyısında 24 saha ve veri (21 Kasım)

Kural koşudan önce `secim.py` dosyasının başına yazıldı. Çıktılar: `inputs/sites_edremit.csv`, `secim.json`, `secim.png`. Ham veri süzmeleri (`*.csv.gz`) yalnız yerelde; `.gitignore`'a eklendi.

- **Merkez:** Edremit ilçesindeki 82 sahanın ortası, 39,585 K 26,897 D, Akçay kıyısı. Bu 82 sahanın 78'inde yeterli Experia verisi var.
- **Seçilen sahalar:** 8 ana saha ve 16 komşu saha. Hepsi 7 km × 4,6 km'lik bir alanda. Sındırgı'da 24 saha yaklaşık 35 km × 35 km'ye yayılıyordu.
- **Çıkarılan veri:** 42.803 saatlik Experia kaydı ve 331.634 adet 15 dakikalık KPI kaydı. 10 KPI gününün hepsi var, iki deprem günü dahil.

| | Edremit kıyısı | Sındırgı |
|---|---|---|
| Saha başına hücre (ortalama) | ~15 (7–28) | 2–14 |
| Hücre başına bağlı kullanıcı (KPI ortalaması) | 11,5 | 21,2 |
| Hücre kapasite kullanımı (PRB, ortalama) | 0,21 | 0,26 |

**Dikkat edilmesi gerekenler (adım 3'ten önce):**
1. **Deniz:** Sahalar kıyı boyunca bir şerit hâlinde ve güneyleri deniz. Sındırgı'daki yerleştirme kuralı kullanıcıları sahanın çevresine her yöne eşit dağıtıyordu; burada kullanıcıların bir kısmı denize düşer. Kullanıcıları yalnız karaya yerleştirmek için kıyı çizgisi gerekiyor. OpenStreetMap'te var; indirmek için izin gerekir.
2. **Çok frekans:** Saha başına ~15 hücre var. Bu, birden çok frekansın kesin olarak kullanıldığını gösteriyor. Tek frekans varsayımı burada Sındırgı'dakinden daha zayıf; girişimi abartır. Model doğrulamasında bunu göreceğiz.
3. **Küçük alan:** Bölge çok küçük ve sahalar çok sık. 24 sahanın sınır etkisi için yeterli olup olmadığı hızlı modelle yeniden kontrol edilecek.
4. **Mevsim:** Ağustos KPI günleri turizm sezonuna denk geliyor. Kıyıda yük Ekim'den farklı olabilir; ikisi ayrı ayrı bakılacak.

## Kıyı çizgisi (21 Kasım)

- **Kaynak:** OpenStreetMap kıyı çizgisi (Overpass, ODbL), 145 KB. Dosya: `inputs/osm/osm_kiyi.json`. Bölge: enlem 39,38–39,79, boylam 26,64–27,16.
- **Kara/deniz testi** (`kiyi.py`):
  - OpenStreetMap kuralına göre kara, kıyı çizgisinin yönünün solunda kalıyor. Bir nokta, kendisine en yakın kıyı parçasının solundaysa karada sayılıyor.
  - Kontrol: 24 sahanın 24'ü karada çıktı.
- **Harita:** `kiyi.png`. Sahalar Edremit Körfezi'nin kuzey kıyısında, deniz kenarında sıralanıyor. Her sahanın çevresinin yaklaşık yarısı deniz.
- **Sonuç:** Adım 3'te kullanıcılar Experia'daki uzaklıklarla, ama yalnız karaya yerleştirilecek. Denize düşen nokta atılıp yeniden çekilecek. Kural adım 3'ün planına yazılacak.

## Adım 3: Model kurma ve doğrulama, hızlı modelle (21 Kasım)

Kurallar `ADIM3_KURALLAR.md` dosyasında; sonuç görülmeden yazıldı. Betik `model35.py`, çıktılar `adim3.json` (24 saha), `adim3_48.json` (48 saha) ve aynı adlı `.png` dosyaları.

- **Eğitim ve test:** 8 ana sahanın 3'ü test için ayrıldı: 005, 007, 507.
- **Mesafe düzeltmesi:** Merkeze 15 km içindeki 1.181 Experia hücresinden çıkarıldı: −72,6 − 9,0·log10 d. İl genelindeki eğri −68,3 − 10,6·log10 d; ikisi birbirine yakın.

| Saha başına ortalama fark (3 çekiliş) | RMa, 24 saha | UMa, 24 saha | RMa, 48 saha | UMa, 48 saha |
|---|---|---|---|---|
| SINR, eğitim sahaları | 2,79 | 3,02 | 3,22 | 3,09 |
| RSRP, eğitim sahaları | 3,95 | 4,99 | 3,72 | 4,73 |
| **SINR, test sahaları (sınır 3)** | **3,80** | 3,52 | **4,11** | 3,70 |
| RSRP, test sahaları (sınır 5) | 3,29 | 4,71 | 3,87 | 5,66 |

- **Seçim:** Kurala göre iki ağda da kırsal model (RMa) seçildi.
- **Kabul geçmedi:** RMa'nın test sahalarındaki SINR farkı 24 sahada 3,8 dB, 48 sahada 4,1 dB; sınır 3 dB.
- **Sinyal gücü (RSRP) tuttu:** 3,3–3,9 dB, Sındırgı'dakiyle aynı düzeyde.
- **Sınır etkisi:** 24 sahadan 48 sahaya geçince ana sahalardaki SINR ortalama 0,84 dB değişiyor; sınır 0,5 dB. Kural gereği değerlendirme 48 sahayla tekrarlandı. Sonuç değişmedi; kabul yine geçmedi.

**Hatanın yönü tek taraflı:**
- Model sinyal kalitesini her sahada 1–5 dB fazla iyi gösteriyor: model ortalaması 17,6 dB, Experia 14,5 dB.
- Experia'da sekiz sahanın hepsinin SINR'ı birbirine çok yakın, 13,8–15,6 dB arası.

**Tanı hesabı** (kural değil, sebebi anlamak için):
- Komşuların bütün kaynak bloklarında yayın yaptığı varsayılınca, yani tam girişimde, model SINR'ı 4,5 dB'ye düşüyor. Bu sefer de 10 dB fazla kötü.
- Gerçek, iki ucun arasında kalıyor.
- Sındırgı'da sahalar seyrek olduğu için girişim azdı ve sinyal kalitesini daha çok gürültü belirliyordu; bu varsayım sonucu pek etkilemiyordu.
- Edremit'te sahalar 0,8 km arayla sık. Sinyal kalitesini komşuların girişimi belirliyor, bu yüzden komşuların ne kadar ve hangi frekansta yayın yaptığı sonucu doğrudan değiştiriyor.
- Burada saha başına ~15 hücre var, yani birden çok frekans katmanı. Tek frekanslı model bu girişimi doğru temsil edemiyor:
  - KPI yüküyle, ns-3'ün kaynak bloklarını baştan doldurma davranışında girişim az kalıyor.
  - Tam yükte ise girişim çok fazla oluyor.
- Bu bir açıklama önerisi; kanıtlanmadı.

**Sonuç (kurala göre):** Model bu bölgede sinyal gücü için uyuyor, sinyal kalitesi için yeterince uymuyor. Kesinti ve yol adımlarına geçilmedi. ns-3 kontrol koşusu da yapılmadı, çünkü kabul geçmeden gerek yok.

## Balıkesir merkez: adım 1–3 (21 Kasım)

Kurallar `ADIM3_KURALLAR.md` dosyasının ekinde; Edremit'tekilerle aynı. Çıktılar: `secim_balikesir.*`, `adim3_balikesir.json`, `adim3_balikesir_48.json` ve aynı adlı `.png` dosyaları. Ham süzmeler yalnız yerelde.

- **Bölge:** İki ilçede 118 saha var, 117'sinde veri var. Merkez 39,636 K 27,885 D.
- **Seçilen 24 saha:** Merkeze en fazla 1,7 km uzakta. Ağ Edremit'tekinden de sık.
- **Test sahaları:** 089, 121, 244.

| Saha başına ortalama fark (3 çekiliş) | RMa, 24 saha | UMa, 24 saha | RMa, 48 saha | UMa, 48 saha |
|---|---|---|---|---|
| SINR, eğitim | 4,34 | 4,77 | 4,72 | 4,73 |
| RSRP, eğitim | 4,52 | 7,12 | 4,14 | 6,68 |
| **SINR, test (sınır 3)** | **5,42** | 5,01 | **5,20** | 4,88 |
| **RSRP, test (sınır 5)** | **5,94** | 7,41 | 4,75 | 7,20 |

- **Seçilen model:** Kurala göre iki ağda da kırsal model (RMa).
- **Kabul geçmedi:**
  - SINR farkı 5,2–5,4 dB, sınırın çok üstünde.
  - RSRP 24 sahada geçmedi (5,9 dB), 48 sahada geçti (4,75 dB).
  - Sınır etkisi 0,77 dB çıktı; bu yüzden 48 saha da hesaplandı.
- **Hatanın yönü yine tek taraflı:**
  - Model sinyal kalitesini her sahada 3,6–6,4 dB fazla iyi gösteriyor: ortalama 18,3 dB, Experia 13,6 dB.
  - Model sinyal gücünü de her sahada 1,4–7,8 dB fazla güçlü gösteriyor: ortalama −95,9 dBm, Experia −100,4 dBm.
  - Sinyal gücündeki fark, şehir merkezinde kullanıcıların çoğunun bina içinde olmasıyla uyumlu. Modelde bina kaybı yok. Bu bir açıklama önerisi.

## Üç bölgenin karşılaştırması

| | Sındırgı (kırsal) | Edremit kıyısı | Balıkesir merkez |
|---|---|---|---|
| 24 sahanın yayıldığı alan | ~35 × 35 km | 7 × 4,6 km | ~3,4 km çaplı |
| Model SINR − Experia SINR (ortalama) | ±, işaretsiz ~2–2,5 dB | **+3,1 dB** | **+4,7 dB** |
| Model RSRP − Experia RSRP | işaretsiz ~4 dB | +2,7 dB | **+4,5 dB** |
| Kabul | geçti | geçmedi (SINR) | geçmedi (SINR, RSRP) |

**Bulgu:**
- Yöntem seyrek, kırsal bölgede gerçek ölçümlere uyuyor.
- Ağ sıklaştıkça model sinyal kalitesini giderek daha fazla iyi gösteriyor. Şehir merkezinde sinyal gücünü de fazla güçlü gösteriyor.
- Muhtemel sebepler, ikisi de verimizde yok:
  1. Sık ağda sinyal kalitesini komşu girişimi belirliyor. Gerçek ağ çok frekanslı (saha başına 11–16 hücre), model ise tek frekanslı.
  2. Şehirde kullanıcılar bina içinde.
- Bu iki bölgede kesinti ve yol sonuçları güvenilir olmaz; o adımlara geçilmedi.

## CellMapper'da Edremit'in 8 ana sahası (22 Kasım, elle bakış)

**Nasıl bakıldı:**
- Kullanıcının izniyle CellMapper kullanım koşulları kabul edildi. Konum izni verilmedi.
- Turkcell LTE haritası, Akçay kıyısında iki görünümde elle incelendi. Toplu veri çekilmedi.
- Eşleştirme konuma göre yapıldı. Bizim saha koordinatımıza en yakın CellMapper kulesi alındı. CellMapper'daki kule konumları kullanıcı ölçümlerinden tahmin edildiği için eşleştirme yaklaşık.

| Saha | CellMapper kulesi | Görünen bantlar | Verimizdeki hücre sayısı | Not |
|---|---|---|---|---|
| 370 | 53834 | 1, 3, 7, 20 | 14 | yakın, güvenilir |
| 105 | 10133 | 1, 3, 7, 20 | 23 | yakın |
| 507 | 172981 | 1, 3, 7 | 25 | yakında 54271 de var (1, 3, 7, 20); belirsiz |
| 529 | 59646 | 1, 7 | 7 | yakın |
| 006 | 57451 | 1, 20 | 9 | yakın |
| 007 | 25735 | 1 | 14 | yakın; ama 14 hücreye karşı tek bant, CellMapper eksik |
| 016 | — | — | 8 | yakınında kule yok |
| 005 | — | — | 21 | ~500 m içinde kule yok |

**Ne öğrendik:**
- Turkcell bu bölgede LTE'de dört bant kullanıyor: **Band 1 (2100 MHz), Band 3 (1800 MHz), Band 7 (2600 MHz), Band 20 (800 MHz)**.
- Bu, "saha başına çok hücre = çok frekans" tahminimizi doğruluyor. Modelimiz yalnız 1800 MHz kullanıyor.
- Band 1 neredeyse her kulede var.
- CellMapper eksik: 8 sahanın 2'sinde kule yok. 007'de 14 hücreye karşı tek bant görünüyor. Yani CellMapper hangi bantların **en azından** var olduğunu söylüyor; tam listeyi vermiyor.
- **Hangi hücrenin hangi bantta olduğu CellMapper'dan çıkmıyor.**

## A ve B sınamaları (22 Kasım, hızlı model)

Kurallar `ADIM3_KURALLAR.md` dosyasındaki Ek 2'de; koşudan önce yazıldı. Betik `sinamalar.py`, çıktılar `sinama_edremit.json` ve `sinama_balikesir.json`.

| Saha başına fark (3 çekiliş) | Taban (tek bant) | A1 (4 bant) | A2 (CellMapper bantları) | B (hep yayında sinyaller) | A1+B |
|---|---|---|---|---|---|
| **Edremit**, SINR test (sınır 3) | 3,81 | 3,77 | **3,01** | 5,05 | 5,02 |
| Edremit, RSRP test (sınır 5) | 3,29 | 3,79 | 2,05 | 3,29 | 3,79 |
| Edremit, SINR yönü (model − Experia) | +3,1 | +3,1 | +2,5 | **−5,2** | −5,1 |
| **Balıkesir**, SINR test (sınır 3) | 5,43 | 5,34 | — | 5,66 | 5,56 |
| Balıkesir, RSRP test (sınır 5) | 5,94 | 6,54 | — | 5,94 | 6,54 |
| Balıkesir, SINR yönü | +4,7 | +4,7 | — | **−5,8** | −5,7 |

- **Seçim (kurala göre):** Edremit'te A2, Balıkesir'de taban.
- **Kabul geçmedi:**
  - Edremit A2: test sahalarında SINR farkı 3,01 dB. Sınır 3 dB; 0,01 dB farkla da olsa kural gereği geçmedi.
  - Balıkesir: hem SINR hem RSRP sınırın üstünde.
- B seçilmediği için Sındırgı kontrolüne gerek kalmadı.

**Ne öğrendik:**
1. **Dört bandın hepsini her sahaya koymak (A1) sonucu değiştirmiyor.** Önceden tahmin edildiği gibi, yük hücre başına verildiği için her bant kendi içinde aynı girişimi görüyor.
2. **CellMapper'daki gerçek bant dağılımı (A2) Edremit'te biraz iyileştiriyor.** SINR 3,8'den 3,0 dB'ye, RSRP 3,3'ten 2,0 dB'ye iniyor. Ama CellMapper eksik olduğu için bu bilgi kısmi.
3. **Komşuların hep yayında olan sinyallerini saymak (B) ters yöne çok fazla itiyor.** Model, 3–5 dB fazla iyiyken 5–6 dB fazla kötü oluyor.
4. **Gerçek bu iki ucun arasında.** Telefonun ölçtüğü sinyal kalitesindeki girişim, yalnız veri girişiminden fazla, ama komşuların bütün kontrol ve referans sinyallerinden az. Aradaki doğru payı veri olmadan bilemiyoruz. Bunun için ya Experia'nın SINR'ı nasıl ölçtüğü, ya da hücrelerin bant ve PCI bilgisi gerekiyor. PCI, referans sinyallerinin çakışıp çakışmadığını belirler.

**Sonuç:** Hiçbir sınama sık bölgedeki sapmayı kurallara göre düzeltmedi. Yöntem kırsal ve seyrek bölgede gerçek ölçümlere uyuyor. Sık bölgede ise sinyal kalitesi, elimizde olmayan bir bilgiye bağlı: telefonun ölçtüğü girişimin ne kadarının komşuların hep yayında olan sinyallerinden geldiği.

## Hep yayında olan payın ayarlanması (22 Kasım, hızlı model)

Kurallar `ADIM3_KURALLAR.md` dosyasındaki Ek 3'te; koşudan önce yazıldı. Betik `kalibrasyon.py`, çıktılar `kalibrasyon.json` ve `kalibrasyon.png`.

**Ayar:** Tek bir katsayı f, iki bölgenin yalnız eğitim sahalarına bakılarak seçildi: **f = 0,03**. Yani komşu hücreler, veri yükünden bağımsız olarak, kaynak bloklarının %3'ünde hep yayında sayılıyor. Kuralda bunun bir üst sınırı da vardı: tam LTE payı olan 0,214. Seçilen değer bunun yaklaşık yedide biri.

| Saha başına SINR farkı (dB) | f = 0 (önceki) | **f = 0,03** | Sınır |
|---|---|---|---|
| Edremit, eğitim | 2,80 | 1,26 | — |
| **Edremit, test** | 3,81 | **0,71** | 3 ✅ |
| Balıkesir, eğitim | 4,34 | 1,32 | — |
| **Balıkesir, test** | 5,43 | **1,36** | 3 ✅ |
| **Sındırgı, eğitim** (ayarda kullanılmadı) | 3,48 | **2,63** | eskisi + 1 ✅ |
| **Sındırgı, test** (ayarda kullanılmadı) | 2,50 | **1,95** | eskisi + 1 ✅ |

**Kabul:** Dört kontrolün dördü de geçti.

**Ne anlama geliyor:**
- Yalnız eğitim sahalarına bakılarak seçilen tek bir sayı, iki bölgenin hiç bakılmamış test sahalarında SINR farkını 3,8 ve 5,4 dB'den 0,7 ve 1,4 dB'ye indiriyor.
- Aynı sayı, ayarda hiç kullanılmayan Sındırgı'yı da iyileştiriyor: 3,5'ten 2,6 dB'ye ve 2,5'ten 1,9 dB'ye. Yani bu düzeltme yalnız sık bölgeye özel değil, üç bölgede de aynı yönde çalışıyor.
- **f fiziksel bir pay değil, ayarlanmış bir katsayı.** Neden %3 olduğunu açıklamıyor. Muhtemel bir yorum şu: telefonun ölçtüğü girişimin küçük bir kısmı komşuların her zaman yayında olan sinyallerinden geliyor. Bunu doğrulamak için Experia'nın SINR tanımı gerekiyor.

**Bölgelerin durumu:**
- **Edremit kıyısı:** Model artık iki ölçütte de kabulü geçiyor. SINR farkı 0,7 dB, RSRP farkı 3,3 dB.
- **Balıkesir merkez:** SINR geçiyor, ama RSRP geçmiyor (5,9 dB, sınır 5). Muhtemel sebep bina içi kullanıcılar; bu ayar onu çözmüyor.

**ns-3 için anlamı:**
- Bu katsayı şimdilik yalnız hızlı modelde var. ns-3'te kullanmak için, EVM'deki gibi, girişim hesabına küçük bir ekleme yapmak gerekir.
- Ekleme kapalıyken ns-3'ün eski sonuçları birebir aynı kalmalı. Açıkken ns-3 ile hızlı model aynı sonucu vermeli.
- f sinyal kalitesini biraz düşürdüğü için, Sındırgı'daki kapasite ve kesinti sonuçları ns-3'te yeniden koşturulursa biraz değişebilir. Yön: biraz daha kötü kalite, biraz daha fazla kaynak kullanımı.

## Katsayı PCI planlamasından türetilebilir mi? (22 Kasım)

Kural `ADIM3_KURALLAR.md` dosyasındaki Ek 4'te; hesaptan önce yazıldı. Betik `pci_payi.py`, çıktı `pci_payi.json`. Ayar yapılmadı.

Soru şu: kullanıcıların gördüğü komşu gücünün ne kadarı, referans sinyalleri çakışan komşulardan geliyor?

| Bölge | P1: yaygın kural (k. sektör → k. grup), ortalama | ortanca | P2: rastgele gruplar, ortalama |
|---|---|---|---|
| Sındırgı | 0,22 | 0,09 | 0,20 |
| Edremit | 0,33 | 0,20 | 0,26 |
| Balıkesir | 0,31 | 0,23 | 0,29 |
| **Üç bölge ortalaması (P1)** | **0,29** | | |

- **Sonuç:** Açıklama bu haliyle desteklenmedi. Türetilen pay 0,29, ayarlanan katsayı ise 0,03; yaklaşık 10 kat büyük. Kural, 0,015–0,06 aralığını istiyordu.
- **Neden böyle olabilir:**
  - Modelde anten yönleri rastgele. Bu yüzden "aynı sektör numarası" kuralı, rastgele PCI dağıtımından (P2) pek farklı çıkmıyor. Gerçek ağda PCI'lar, gerçek anten yönlerine göre en güçlü komşular çakışmasın diye planlanır.
  - Çakışan payın 10 kat düşük olması için planlamanın neredeyse kusursuz olması gerekir. Bunu verimizle gösteremiyoruz.
  - Experia'nın sinyal kalitesini gerçekten referans sinyalleri üzerinden mi ölçtüğünü de bilmiyoruz. Başka bir tanımla ölçülüyorsa bu açıklama zaten geçersiz olur.
- **Karar:** f = 0,03, **ölçüme uydurulmuş bir katsayı** olarak kalıyor. Eğitim sahalarında ayarlandı; test sahalarında ve ayarda kullanılmayan Sındırgı'da tuttu. Fiziksel açıklaması açık bir soru.
- **Kalıcı sınır:** Experia'daki SINR'ın tanımı, hücrelerin PCI'ları ve anten yönleri verimizde yok ve gelmeyecek. Bu yüzden katsayının fiziksel açıklaması kapatılamıyor. Katsayı, eğitim sahalarında ayarlanıp bakılmayan sahalarda sınanmış bir düzeltme olarak kullanılıyor ve böyle raporlanıyor.
