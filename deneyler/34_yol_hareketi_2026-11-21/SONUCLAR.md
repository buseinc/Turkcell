# Deney 34: Yollarda hareket, sonuçlar (21 Kasım)

Plan: `PLAN.md`. Bu dosyaya adım adım ekleniyor.

## Adım 1: Yol verisi (tamam)

- **Kaynak:** OpenStreetMap ana yolları (Overpass API, 21 Kasım; ODbL lisansı, "© OpenStreetMap katkıcıları"). Dosya: `inputs/osm/osm_ana_yollar.json`, 1,25 MB.
- **Koordinat dönüşümü:** Sahalarla aynı yerel koordinat sistemi kullanıldı. 24 sahanın koordinatları bu dönüşümle hatasız tutuyor (0,0 m).
- **Bölgedeki yollar:**
  - Bölünmüş devlet yolu: 94 km
  - Devlet yolu: 40 km
  - İl yolu: 111 km
  - Bağlantı yolu: 691 km
  - Başlıca yollar: D565, D555, D240.
- **Öne çıkan iki nokta:**
  - Bir devlet yolu, depremde çöken 482'nin hemen yanından geçiyor.
  - Çöken 130'un yanından bir il yolu geçiyor.
- **Dosyalar:** Harita `yollar.png`, 50 m aralıklı yol noktaları `inputs/yol_noktalari.csv`.

## Adım 2: Yol boyunca kapsama (tamam)

**Nasıl yapıldı:**
- Hızlı model kullanıldı; formülleri ns-3'ünkilerle aynı, hareket simülasyonu yok.
- Yollar üzerinde her 50 m'de bir nokta alındı. Yalnızca ana sahaların 6 km çevresindeki yollar kullanıldı: 301 km.
- Ağ ve yük deney 33'teki gibi: ölçülmüş deprem yükü ve aynı kesinti durumları.
- Sonuçlar 20 görüş hattı çekilişinin ortancası; parantez içinde %5–95 aralığı.
- Kurallar koşudan önce `yol_kapsama.py` dosyasının başına yazıldı.

| Yollar | Uzunluk | Kesinti yok | 482 kapalı | 130 kapalı | İkisi kapalı |
|---|---|---|---|---|---|
| Tüm yollar | 301 km | 3,4 km (%1,1) | 5,0 km (%1,7) | 18,1 km (%6,0) | 19,4 km (%6,4) |
| 482'ye en yakın yollar | 15 km | 0,1 km | **1,5 km (%10)** | 0,1 km | 1,5 km |
| 130'a en yakın yollar | 39 km | 1,1 km | 1,2 km | **15 km (%39)** | 15 km |
| Devlet yolları (D555, D565, D240) | 38 km | ~0,3 km | ~0,3 km | ~0,4 km | ~0,4 km |
| İl yolları | 59 km | 0,7 km | 0,7 km | **7,5 km (%13)** | 7,5 km |

20 çekilişte sayılar çok az oynuyor. Örneğin ikisi kapalıyken servissiz yol 18,9–19,9 km.

**Ne gördük:**
1. **Kesinti yokken yolların %99'unda servis var.** Kalan %1, birbirinden kopuk tek tük noktalar. Bunlar büyük olasılıkla aşağıda anlatılan gölgeleme sınırından geliyor.
2. **482 çökünce yol fazla etkilenmiyor.** Yalnız sahanın yanındaki yaklaşık 1,5 km'lik bir yol parçası servis kaybediyor. Yandan geçen devlet yolunda servis sürüyor, çünkü 482 ilçe merkezine yakın ve çevresi sahalarla dolu.
3. **130 çökünce yaklaşık 15 km yol servissiz kalıyor.** 130 bölgenin kenarında ve seyrek bir yerde; yanından geçen il yolunun büyük bölümü kopuyor.
4. **Devlet yolları her durumda sağlam.**

**Bu ne demek:** Sabit kullanıcılarda iki kesinti benzer görünüyordu; kapanan sahanın çevresinde %15–18 servissiz. Yolda ise aralarında büyük fark var:
- 482 çökünce yolda servis kaybı 1,5 km.
- 130 çökünce yolda servis kaybı 15 km.

Yani yol açısından kritik olan, seyrek bölgedeki saha. İHA için de aday görev bu: 130 kapanınca il yolunu boydan boya kapatmak.

**Sınırlar:**
- **Gölgeleme:** Her 50 m'lik nokta bağımsız bir gölgeleme değeri alıyor (PLAN.md'deki sorun 1). Toplam kilometre sayıları güvenilir. Tek bir kopukluğun uzunluğu ve haritadaki tek tük kırmızı noktalar güvenilir değil.
- **Mesafe düzeltmesi:** Yol noktasının en yakın sahaya uzaklığıyla hesaplandı. Deney 33'teki kuralın aynısı.
- **Model sınırları:** Düz arazi, rastgele anten yönleri, tek frekans; deney 32–33'teki gibi.
- **Doğrulama yok:** Yolda gerçek ölçüm (drive test) yok, sonuç gerçekle karşılaştırılamıyor.

**Dosyalar:** `yol_kapsama.py`, `yol_kapsama.json`, `yol_kapsama.png`.

## Sıradaki adım

Adım 3: ns-3'te hareket eden araçlar. Önce PLAN.md'deki üç düzeltme yapılacak, sonra hücre geçişi kodu taşınacak. Bakılacak yer en anlamlı yol parçası: 130'un yanındaki il yolu.

## Adım 3a: Hareket düzeltmeleri, kabul kontrolleri (21 Kasım)

Tasarım ve kurallar `DUZELTMELER.md` dosyasında; kodlamadan önce yazıldı. ns-3 kodu `simulation/` klasöründe. Hızlı modeldeki karşılığı `alan.py`.

**Kural 3: gerçek ölçümlere uyum** (`kabul3.py`, `kabul3.json`). Hızlı modelle hesaplandı; üç anten yönü çekilişinin ortalaması:

| Saha başına ortalama fark (dB) | Eski | Yeni | Kural: yeni ≤ eski + 1 |
|---|---|---|---|
| SINR, eğitim sahaları | 3,84 | 3,48 | geçti |
| SINR, test sahaları | 2,03 | 2,50 | geçti (+0,47) |
| RSRP, eğitim sahaları | 6,85 | 5,82 | geçti |
| RSRP, test sahaları | 3,96 | 4,17 | geçti (+0,21) |

- **Ortanca RSRP ölçütü kurala göre geçmedi; ama ölçüt yanlış kurulmuştu.**
  - Kural, tüm hücrelerin ortanca RSRP'sinin Experia'daki −104,2 dBm'e 1 dB yakın olmasını istiyordu.
  - Yeni model −101,9 dBm verdi.
  - Aynı hesap eski modelde −100,4 dBm veriyor. Oysa deney 26 eski model için −104,2 bulmuştu.
  - Yani benim hesabım deney 26'nın hesabıyla aynı değil. Deney 26, ns-3 çıktısından sektör ölçümlerini başka bir yolla topluyor.
  - Aynı hesapla karşılaştırınca yeni model ölçüme 1,5 dB daha yakın.
  - Bu ölçüt hatası kuralı yazarken benim yaptığım bir hata. Sonuç görüldükten sonra kuralı değiştirmedim; durumu burada olduğu gibi yazıyorum.
- **Sonuç:** Saha başına farklar kuralı geçiyor. Yumuşak gölgeleme ve konuma bağlı görüş hattı, modelin gerçek ölçümlere uyumunu bozmuyor.

**Kural 4: yumuşaklık** (`kabul4.py`, `kabul4.json`): **geçmedi.**
- Yol boyunca 10 m'lik adımlarda en iyi hücrenin sinyal gücündeki değişimin standart sapması:
  - Eski model: 14,9 dB
  - Yeni model: 5,7 dB
  - Sınır 2 dB'ydi.
- Sebebini ayırdık:
  - Yalnız gölgeleme: 1,1 dB. Yumuşak gölgeleme amacına ulaşıyor.
  - Yalnız mesafe düzeltmesi: 0,1 dB.
  - Görüş hattı durumu: kalan sıçramalar bundan geliyor. 3GPP kırsal formülünde görüş hattı var/yok arasındaki fark, bağlantılarda ortanca 29,5 dB. Araç görüş hattına girip çıktığında sinyal tek adımda bu kadar sıçrıyor.
  - Bu sıçrama seyrek: yol noktalarındaki bağlantıların %1,2'si görüş hattında. Ama olduğunda çok büyük.
- Kuralı yazarken bu sıçramayı hesaba katmamıştım. Kural yalnız gölgelemeyi hedefliyordu, ama toplam sinyal üzerine yazılmıştı.
- **Hareketli koşu, bu konuda karar verilene kadar durduruldu.**

**Kural 1: eskiyle aynılık** (`kabul1.json`): **geçti.** Anahtarlar kapalıyken yeni kod, deney 33'ün 1 saniyelik L25 koşusuyla birebir aynı altı dosya üretiyor: `radio_samples`, `ues`, `prb_usage`, `voice`, `DlRxPhyStats`, `sectors`.

**Kural 4 kararı:** Görüş hattı sıçramaları 3GPP'deki gibi bırakıldı. Kural 4 yalnız gölgeleme için sayıldı; gölgeleme 1,1 dB ile geçiyor. Bu, sonuç görüldükten sonra kullanıcının kararıyla yapılan bir değişiklik; DUZELTMELER.md'de kayıtlı.

**Kural 2: ns-3 ile hızlı model aynı formül** (`kabul2.json`): **geçti.** Anahtarlar açık, 672 sabit kullanıcı:
- ns-3'ün ölçtüğü sinyal gücü, hızlı modelinkiyle 672 bağlantının hepsinde 0,01 dB içinde aynı. En büyük fark 0,004 dB.
- En güçlü hücre de %100 aynı.
- Görüş hattı artık rastgele çekilmiyor, konuma göre hesaplanıyor. Bu yüzden iki araç birebir eşleşiyor; eskiden yalnız dağılımları karşılaştırılabiliyordu.

**Kural 5: hücre geçişi** (`kabul5.json`): **geçti.**
- Test: Tek araç, 441'den 443'e saatte 54 km hızla gidiyor. Yalnız bu iki saha var; yeni gölgeleme ve görüş hattı açık.
- **Hücre geçişi açıkken:**
  - Araç 441'de başlıyor, 443'te bitiriyor.
  - 5 otomatik geçiş yapılıyor; hepsi başarılı, olaylar eşleşiyor, hata yok.
  - Geçişten sonra veri gelmeye devam ediyor.
- **Hücre geçişi kapalıyken:** Araç 441'de kalıyor ve paketlerin yarısını alamıyor (9.802'ye karşı 4.743).
- **Deney 19'dan farkı:**
  - Bu iki bulgu kural 5'in parçası değil; bilgi olarak yazıyorum.
  - **Geçiş sayısı:** Deney 19'da tek geçiş vardı. Burada iki saha arasındaki ~360 m'lik bölgede 441 ile 443 arasında gidip gelme (ping-pong) oluyor. Sebebi yeni yumuşak gölgeleme: iki sahanın sinyali yol boyunca birbirinden bağımsız ±8 dB dalgalanıyor, sinyaller eşitken 3 dB'lik fark birkaç kez aşılıyor. Eski testte gölgeleme yoktu. Gerçek şebekelerde de bilinen bir durum.
  - **Paket arası boşluk:** Geçişlerin çevresinde paketler arasında en çok 0,27–0,42 s boşluk var. Deney 19'da 0,12 s'ydi.
- **Betik hatası:** İlk değerlendirmede betiğim aracın ilk hücresini bağlanmadan önceki "0" kaydından okuyordu. Düzeltildi, kural değişmedi.

**Özet:** Beş kuraldan dördü yazıldığı gibi geçti. Kural 4 kullanıcının kararıyla yalnız gölgelemeye uygulandı ve o da geçti. Hareketli koşulara geçilebilir.

## Adım 3b: Hareketli araç koşuları, hazırlık (21 Kasım)

**Rotalar** (`rota.py`, `rota.json`, `rota.png`). Yeni modelle, hızlı hesap:

| Rota | Yol | Uzunluk | Servissiz yol, kesinti yok | Servissiz yol, sahası kapalı | En uzun kopukluk |
|---|---|---|---|---|---|
| A | il yolu 10-31, 130'un yanı | 16,7 km | 0,2 km | **6,8 km** (130 kapalı) | 2,8 km |
| B | D240 Simav–Sındırgı, 482'nin yanı | 10,9 km | 0,2 km | 0,3 km (482 kapalı) | 0,1 km |

Rota A asıl durum. Rota B karşılaştırma için: orada kesinti yola neredeyse hiç etki etmiyor.

**Koşu kuralları:** Kurallar koşudan önce `hazirla_yol.py` dosyasının başına yazıldı; girdiler `yol_plan.json` dosyasında.
- 4 koşu var: rota A kesintisiz ve 130 kapalı; rota B kesintisiz ve 482 kapalı.
- Arka plan yükü her hücrede bir yük kullanıcısıyla kuruluyor. Hücre doluluğu, deney 33'teki ns-3 değerine eşit. 1.473 deprem kullanıcısını tek tek koşturmak 40 saniyelik bir koşu için günler sürerdi.
- Rota yaklaşık 1 km'lik parçalara bölünüyor. Her parçada her yön için bir araç var; araçlar 90 km/s hızla gidiyor. Rota A'da 34, rota B'de 22 araç.

**Yük ayarı:**
- İlk 3 saniyelik denemede değerlendirme hücrelerinin doluluğu 0,142 çıktı; hedef 0,193'tü.
- Yük katsayısı, deney 29'daki gibi tek bir orantılı adımla düzeltildi.
- İkinci denemede doluluk 0,190 çıktı.
- Bu ayarda yalnız yüke bakıldı; sonuçlara bakılmadı.

**Süre:** 3 saniyelik deneme ~5 dakika sürdü. Tam koşu ~41 saniyelik simülasyon; dördü paralel koşarsa tahmini 1–1,5 saat.

## Adım 3b: Hareketli araç koşuları, sonuçlar (21 Kasım, ns-3)

4 koşu, her biri ~41 saniyelik simülasyon, 16:20–17:55 arası paralel koşturuldu. Analiz `yol_analiz.py` ile yapıldı ve koşudan önce yazılan kurala uyuyor. Dosyalar: `yol_analiz.json`, `yol_analiz.png`.

| | Rota A, kesinti yok | **Rota A, 130 kapalı** | Rota B, kesinti yok | Rota B, 482 kapalı |
|---|---|---|---|---|
| Servissiz yol, ns-3 | 0,06 / 16,7 km | **6,59 km** | 0,13 / 10,9 km | 0,20 km |
| Servissiz yol, hızlı model | 0,19 km | 6,81 km | 0,19 km | 0,34 km |
| En uzun kopukluk, ns-3 (hızlı model) | 0,06 km (0,07) | **2,81 km (2,81)** | 0,11 km (0,13) | 0,11 km (0,11) |
| Bağlantısı tamamen kopan araç | 0 / 34 | **15 / 34** | 1 / 22 | 0 / 22 |
| Hücre geçişi, km başına | 2,5 | 3,9 | 4,5 | 3,8 |
| 5 s içinde geri dönen geçiş | 14 | 13 | 26 | 21 |
| Başarısız geçiş | 0 | 1 | 1 | 0 |
| Değerlendirme hücreleri doluluğu (hedef) | 0,18 (0,17) | 0,19 (0,19) | 0,16 (0,17) | 0,18 (0,20) |

Doluluk dört koşunun hepsinde hedefin ±0,05'i içinde; yük işareti yok.

**Ne bulduk:**
1. **130 çökünce il yolunun 6,6 km'si servissiz kalıyor.**
   - En uzun kesintisiz kopukluk 2,8 km. Saatte 90 km hızla giden bir araç için bu yaklaşık 2 dakika hiç servis olmaması demek.
   - Bütün rotada toplam yaklaşık 4,5 dakika.
   - 34 aracın 15'i yolda şebeke bağlantısını tamamen kaybediyor.
2. **482 çökünce D240'ta neredeyse hiçbir şey değişmiyor:** 0,13 km'den 0,20 km'ye. Çevresi sahalarla dolu.
3. **ns-3, hızlı modelin tahminini doğruluyor.**
   - Servissiz yol: 6,59 km'ye karşı 6,81 km.
   - En uzun kopukluk iki araçta da aynı: 2,81 km.
   - Yani yol aşamasında İHA konumlarını hızlı modelle elemek güvenilir.
4. **Kesinti olmayan yollar neredeyse tamamen servisli:** km'lerin %99'undan fazlası.

**Sınırlar ve dikkat edilecekler:**
- **Hücre geçişi çok sık.**
  - Km başına 2,5–4,5 geçiş var; geçişlerin ~%15–25'i 5 saniye içinde eski hücreye dönüyor.
  - Bunun sebebi ns-3'ün varsayılan geçiş ayarları (3 dB, 256 ms) ile 8 dB'lik yumuşak gölgelemenin birleşimi. Gerçek operatörler bu ayarları gidip gelmeyi azaltacak şekilde yapar.
  - Ayar taraması yapılmadı. Bu yüzden geçiş sayıları gerçek şebeke için tahmin değil.
- **Paket teslimi yardımcı bilgi.**
  - Kesinti olmasa da bazı araçlarda 1 saniyeden uzun paket boşlukları var: rota A'da 8, rota B'de 7–8 araç.
  - Bu, deney 33'te sebebi açık kalan ns-3 paket sorunuyla aynı türden. Ana sonuç sinyal ölçütleriyle verildi.
  - 130 kapalıyken araç başına en uzun paket boşluğunun ortancası 7,8 s; bu sayı kesintiyi doğruluyor.
- **Arka plan yükü:** Deprem kullanıcıları tek tek değil, hücre başına bir yük kullanıcısıyla temsil edildi. Doluluk, deney 33'teki ns-3 değerine ayarlandı.
- **Model sınırları:** Düz arazi, tek anten yönü çekilişi, tek frekans; deney 32–33'teki bilinen sınırlar. Yolda gerçek ölçüm (drive test) yok.

**İHA için anlamı:** 130 çöktüğünde yaklaşık 3 km'lik ana kopukluk ve çevresi kapatılmalı. Bu yol parçası İHA aşamasının ilk somut hedefi; konumu `yol_analiz.png` grafiğinde, rota A'da yaklaşık 6,5–12,5 km arası.
