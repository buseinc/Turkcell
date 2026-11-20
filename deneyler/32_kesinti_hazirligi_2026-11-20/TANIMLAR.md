# 32 — Kesinti senaryolarından önce sabitlenen tanımlar

Bu dosya kesinti senaryoları (K1 / K2 / K3) koşulmadan **önce** yazıldı. Sonuçlar görüldükten sonra buradaki eşikler değiştirilmeyecek. Değişirse ayrı bir duyarlılık çalışması olarak raporlanacak.

Araç: deney 31'in hızlı modeli (`31_hizli_model_2026-11-20/hizli_model.py`). Her senaryo en az 20 rastgele çekilişle koşulacak; sonuçlar ortalama ve aralık olarak verilecek.

## Adım 1 — "Servis yok" ve "zayıf servis" (tamam)

| Durum | Tanım | Kaynak |
|---|---|---|
| **Servis yok** | Kullanıcının sinyal kalitesi, en düşük kodlamayla bile veri gönderilemeyecek kadar kötü (CQI = 0). Modelde SINR < −6,7 dB. | 3GPP TS 36.213, Tablo 7.2.3-1: CQI 0 "out of range", yani en düşük kodlamada bile blok hata oranı %10'un altına inmiyor. Eşik değeri −6,7 dB yaygın kullanılan bağlantı seviyesi sonucu (hizli_model.py, CQI_DB). |
| **Zayıf servis** | Sinyal gücü (RSRP) −121,8 dBm'nin altında. | 3GPP TS 36.101, Tablo 7.3.1-1: Band 3, 20 MHz için telefonun en az veri hızının %95'ini alabilmesi gereken en düşük güç (REFSENS) −91 dBm. Bu, 1200 alt taşıyıcıya bölününce kaynak elemanı başına −91 − 10·log10(1200) = −121,8 dBm eder. |
| **Hücre aşırı yüklü** | Hücredeki kullanıcıların istediği kaynak blokları bandın tamamından fazla (talep ≥ 1). | Deney 31'deki doluluk hesabı. |
| **Aşırı yüklü hücrede hizmet alan pay** | Talep 1'den büyükse kullanıcıların ancak 1/talep kadarı hizmet alabiliyor sayılır. | Varsayım: kaynaklar kullanıcılar arasında eşit paylaştırılıyor. |

**Neden bu eşikler:**
- "Servis yok" için girişimi de hesaba katan bir ölçüt gerekiyor. Saha çökünce kullanıcılar uzaktaki hücrelere bağlanacak; sinyal hem zayıflayacak hem de girişime daha açık hale gelecek. CQI 0 bunların ikisini birden kapsıyor.
- REFSENS bir "servis yok" sınırı değil. Telefon bunun altında da bağlı kalabilir. Bu yüzden ayrı bir "zayıf servis" sınıfı olarak kullanılıyor.
- Operatörün hücreye bağlanma eşiği (Qrxlevmin, TS 36.331'de −140 ile −44 dBm arasında ayarlanabiliyor) bilinmiyor. Bu yüzden kullanılmadı.

**Normal günde kontrol** (deney 29'un 3 yerleşimi, ölçüm kullanıcıları, 20 çekiliş):

| Yerleşim | Servis yok (hızlı model) | Zayıf servis (hızlı model) | Zayıf servis (ns-3) |
|---|---|---|---|
| 1 | %0,2 | %4,3 | %3,5 |
| 2 | %1,0 | %4,5 | %5,1 |
| 3 | %0,3 | %5,5 | %5,5 |

Normal bir günde servissiz kullanıcı neredeyse yok, ~%5'i zayıf. Kırsal bir bölge için akla yatkın. Hızlı model ile ns-3 bu konuda da tutuyor.

**Hızlı modelin ölçmediği:** Paket gecikmesi. "Kaç kişi konuşabiliyor" sorusu doğrudan cevaplanmıyor. Deney 29'da deprem yükünde gecikmenin sorun olmadığı ns-3 ile gösterildi.

## Adım 2 — Deprem anındaki yük (tamam; `deprem_yuku.py`, `deprem_yuku.json`)

Daha önce deprem yükü "normal günün 2 katı kullanıcı" diye **varsayılmıştı**. Şimdi KPI'dan doğrudan ölçüldü.
- **Pencere:** depremden ilk saha kesintisine kadar. 10 Ağustos'ta 19:53–21:30, 27 Ekim'de 22:48–01:15.
- **Karşılaştırma:** önceki 7 günün aynı saatleri.

| Saha | Hücre başına bağlı kullanıcı, normal → deprem (en yoğun 15 dk) | Hücre doluluğu, normal → deprem |
|---|---|---|
| 443 | 47 → 91 (101) / 31 → 71 (94) | 0,51 → 0,46 / 0,47 → 0,42 |
| 441 | 30 → 61 (68) / 21 → 47 (62) | 0,43 → 0,41 / 0,47 → 0,46 |
| 482 | 64 → 68 (91) / 25 → 27 (33) | 0,62 → 0,25 / 0,40 → 0,16 |
| 440 | 26 → 42 (50) / 14 → 26 (30) | 0,33 → 0,35 / 0,31 → 0,34 |
| 130 | 13 → 24 (28) / 9 → 13 (17) | 0,20 → 0,20 / 0,17 → 0,21 |
| 296 | 10 → 18 (22) / 10 → 17 (22) | 0,13 → 0,13 / 0,21 → 0,16 |
| 444 | 4 → 7 (8) / 4 → 6 (7) | 0,06 → 0,06 / 0,07 → 0,06 |
| 554 | veri yok / 4 → 9 (13) | – / 0,02 → 0,04 |

(Her hücrede ilk sayı 10 Ağustos, ikincisi 27 Ekim depremi.)

**Ne öğrendik:**
- **Bağlı kullanıcı sayısı 1,6–1,85 katına çıkıyor**; tam 2 kat değil. Sahaya göre 1,1 ile 2,3 kat arasında değişiyor.
- **Hücre doluluğu artmıyor, hatta biraz düşüyor** (0,82–0,87 kat). Kullanıcı başına veri yarıya iniyor. İnsanlar arıyor ve mesajlaşıyor, büyük veri kullanmıyor. Deney 09 da bunu görmüştü.
- **Eski sonuçta düzeltme:** En yoğun hücre (443) deprem anında ortalama ~91, en yoğun 15 dakikada ~101 bağlı kullanıcı taşıdı. Daha önce "en fazla ~69" demiştik; o sayı ×2 varsayımından geliyordu. 101 de ns-3'te sorunsuz taşınan 200'ün yarısı. Sonuç değişmiyor, ama doğru sayı bu.

**Kesinti senaryolarında yük şöyle kurulacak:**
- Her hücredeki kullanıcı sayısı = o sahanın deprem penceresindeki ortalaması (KPI). En kötü durum için ayrıca en yoğun 15 dakika.
- Kullanıcı başına veri tek bir değer olacak. Kesinti yokken modelin değerlendirme hücrelerindeki ortalama doluluğu, KPI'daki deprem doluluğunu verecek şekilde seçilecek (10 Ağustos: 0,27; 27 Ekim: 0,23).
- Bir saha kapanınca kullanıcıları yerinde kalıyor ve kalan en güçlü hücreye bağlanıyor. Veri talepleri değişmiyor.
- Komşu sahaların (tampon) deprem yükü de KPI'dan aynı şekilde alınacak.

## Adım 3 — Kullanıcı yerleştirmesinin etkisi (tamam; `senaryo.py`, `yerlesim.py`, `yerlesim.json`)

Üç kural karşılaştırıldı. Kural, sonuca bakılarak **seçilmedi**; bu baştan yazıldı. A ana kural olarak kalıyor, çünkü Experia'ya karşı doğrulanan o. B ve C, K senaryolarında duyarlılık aralığı olarak verilecek.
- **A:** Experia'daki saatlik uzaklık kayıtlarından rastgele seçim (şimdiye kadarki kural).
- **B:** Aynı kayıtlar, ama yoğun saatlerin kayıtları daha sık seçiliyor (KPI'daki saatlik kullanıcı sayısına göre).
- **C:** Kişiler saatlik ortalamalardan daha dağınık; sahaya göre ortalama uzaklıkta üstel dağılım.

Her kural için 3 anten yönü × 3 yerleştirme × 10 çekiliş yapıldı. Yük 27 Ekim deprem anındaki yük.

| | A | B | C |
|---|---|---|---|
| Sahadan 5 km'den uzak kullanıcı | %30 | %26 | %25 |
| Kesinti yok: servis yok / zayıf | %0,5 / %2,9 | %0,5 / %3,2 | %0,6 / %3,4 |
| 482 kapalı, 482 çevresindeki kullanıcılar: servis yok | **%23** (17–31) | **%22** (14–31) | **%32** (24–41) |
| 482 kapalı, 482 çevresindeki kullanıcılar: zayıf | %38 | %37 | %46 |
| 482 kapalı, bütün bölge: servis yok | %1,7 | %1,8 | %2,3 |
| 482 kapalı, aşırı yüklenen hücre | 0 | 0 | 0 |

**Ne öğrendik:**
- A ile B neredeyse aynı. Yoğun saatleri ağırlıklandırmak sonucu değiştirmiyor.
- C (daha dağınık kullanıcılar) sahası kapanan kullanıcılar için ~10 puan daha kötü sonuç veriyor. Yerleştirme sonucu orta derecede etkiliyor. Bu yüzden K senaryolarında A ile C arası aralık olarak verilecek.
- "Kullanıcıların üçte biri 5 km'den uzakta" endişesi büyük ölçüde boşa çıktı. Saatlik ortalamalar kişilerin uzaklıklarından **daha dar** dağılır; gerçekte bazı kullanıcılar daha da uzakta olabilir. C kuralı bunu temsil ediyor.
- **İlk bakış (K1'in ön sonucu):** 482 kapanınca o sahanın çevresindeki kullanıcıların yaklaşık **dörtte biri ile üçte biri** servissiz kalıyor. Komşu hücreler kayan yükü rahatça taşıyor; hiçbiri aşırı yüklenmiyor. Yani saha kaybında sorun **kapasite değil, kapsama**. Bu, İHA'nın görevinin "kapsama boşluğunu doldurmak" olacağını gösteriyor.

## Adım 4 — Gerçek 482 kesintisi ile karşılaştırma (tamam; `gercek_kesinti.py`, `gercek_kesinti.json`)

**KPI'da ne oldu** (28 Ekim, 08:00–22:00, önceki normal günlerin aynı saatleriyle karşılaştırıldı):
- KPI'da 482'nin **2 hücresi** var. Biri (6252) bütün gün kapalıydı, diğeri (6253) açıktı.
- Kapanan hücre normalde ~41 kullanıcı taşıyordu.
- Açık kalan hücre normal gününden **fazla kullanıcı almadı** (54 → 49). Yani aynı sahanın diğer hücresi kayan kullanıcıları üstlenmedi.
- 443 ve 441 sahalarında kullanıcı sayısı normalin 1,31 katına çıktı (+245 kişi). Diğer değerlendirme sahaları tamamen normaldi (358 → 356).
- 443/441'deki artış, 482'den kaybolan 41 kişinin 6 katı. Bu yüzden artışın çoğu başka bir sebepten geliyor; büyük ihtimalle deprem sonrası ilçe merkezinde toplanma. **482'nin kullanıcılarının nereye gittiği KPI'dan ayrıştırılamıyor.**

**Model ne diyor** (482'nin 3 sektöründen biri kapatıldığında, o sektörün kullanıcıları):

| Nereye gidiyor | Model (ortalama, %5–95 aralığı) | KPI |
|---|---|---|
| Aynı sahanın başka sektörü | %48 (33–65) | ~%0 |
| Başka bir saha | %49 (32–63) | ayrıştırılamıyor |
| Servis yok | %3 (0–9) | ayrıştırılamıyor |

**Sonuç: model burada gerçekle uyuşmuyor.** Modelde kullanıcıların yarısı aynı sahanın komşu sektörüne geçiyor; gerçekte geçmedi. Muhtemel sebep: modelde 482 üç sektörlü ve sektörler 120° arayla; KPI'da ise 482'nin 2 hücresi var. Deney 13'te 554 için de 2 sektör çıkmıştı. Gerçek ağda 482'nin iki hücresi birbirinden uzağa bakıyor olabilir.

**Ek sınama:** 482 iki sektörlü ve sektörler ters yönlere bakıyor varsayılınca da model kullanıcıların %39'unu aynı sahanın diğer sektörüne gönderiyor (başka saha %54, servis yok %7). Yani sektör sayısı uyuşmazlığı tek başına açıklamıyor. Olası diğer sebepler veriden ayrılamıyor: kesinti günü 482 çevresindeki insanların bölgeden ayrılması, ya da hücrelerin KPI'da görünmeyen başka bir frekans katmanına geçmesi. Deney 13'e göre 482'nin hücrelerinden birinde frekanslar arası geçiş raporlanıyor.

**Kesinti senaryolarına etkisi:** K1 ve K3'te sahanın **tamamı** kapatılıyor. Bu durumda sektörler arasındaki paylaşım önemli değil, çünkü hepsi kapalı. Yani bu uyuşmazlık K senaryolarını doğrudan bozmuyor. Ama tek bir hücrenin kapandığı bir senaryo kurulursa model güvenilir değil. Bu bir sınır olarak not edildi.

**Bu adımın gösterdiği:** KPI tek başına modeli kesinti anında doğrulamaya yetmiyor. Deprem sonrası insanların yer değiştirmesi, kesintinin etkisini maskeliyor.

## Önceki deneylerden bilinen ve kesinti sonuçlarını etkileyecek sınırlar

Eski deneylerin notları tarandı. Kesinti senaryolarında önemli olanlar:

| Sınır | Nereden | Kesinti sonucuna etkisi |
|---|---|---|
| Bütün sahalar tek taşıyıcıda (1800 MHz). Gerçek ağda 800 / 2100 MHz katmanları da var. | Deney 10, 11, 13, 14 | 800 MHz daha uzağa ulaşır. Modelde saha çökünce açılan boşluk gerçekte olduğundan **büyük** görünebilir. Ayrıca girişim fazla hesaplanıyor. |
| Modelde 24 saha var; KPI'da 47. | Deney 09, 30 | Modelin kenarındaki kullanıcılar gerçekte dışarıdaki sahalara bağlanabilir. Kenar sonuçları kötümser. |
| Anten yönleri bilinmiyor (3 farklı yön çekilişi). | Deney 10, 26 | Sonuçlar 3 yön çekilişinde de verilecek. |
| Kullanıcı uzaklıkları saatlik hücre ortalamalarından (TA). | Deney 15, 26 | Adım 3'te sınanacak. |
| Bir bağlantının açık görüş olup olmadığı rastgele; tek çekilişte kullanıcıların %40'ının hücresi değişiyor. | Deney 31 | En az 20 çekiliş zorunlu. |
| 554 sahası büyük ihtimalle 2 sektörlü. | Deney 13 | 482 ve 130'a uzak; etkisi küçük. |
| Düz zemin; arazi ve binalar yok (8 dB gölgeleme bunların yerini tutuyor). | Deney 10, 20 | Gerçek kapsama daha parçalı. |

## Sıradaki adımlar

- Adım 2: Deprem anındaki yük (KPI'dan).
- Adım 3: Kullanıcı yerleştirmesinin sonuca etkisi.
- Adım 4: Hızlı modeli 28 Ekim'deki gerçek 482 kesintisiyle karşılaştırma.
