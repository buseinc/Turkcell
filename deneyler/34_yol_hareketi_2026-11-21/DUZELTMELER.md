# Hareket için model düzeltmeleri: tasarım ve kabul kuralları

Bu dosya kod yazılmadan önce, 21 Kasım'da yazıldı. Kurallar sonuca bakılarak değiştirilmeyecek.

## Neden

Mevcut model sabit kullanıcılar için kuruldu. Hareket eden bir kullanıcıda üç yerde yanlış çalışıyor (PLAN.md). Üç düzeltme de bir anahtarla açılıp kapanacak. Anahtarlar kapalıyken model eskisiyle birebir aynı çalışmalı.

## Düzeltme 1: Gölgeleme konuma göre yavaş değişsin

- **Bugünkü durum:** Gölgeleme, kullanıcının tam koordinatına bağlı rastgele bir değer. 1 mm ötede tamamen yeni bir değer geliyor.
- **Yenisi:** Her saha için harita üzerinde 120 m aralıklı bir ızgara kurulur.
  - Her ızgara düğümüne sabit bir rastgele değer verilir: ortalama 0, standart sapma 1. Değer saha konumu, düğüm ve tohumdan hesaplanır, yani tekrarlanabilir.
  - Kullanıcının değeri, çevresindeki 4 düğümden ağırlıklı ortalamayla bulunur.
  - Sonuç, standart sapması her noktada yine 1 olacak şekilde ölçeklenir, sonra 8 dB ile çarpılır.
- **Sonuç:** Gölgelemenin büyüklüğü aynı kalıyor (8 dB), ama değer konumla yumuşak değişiyor. Yaklaşık 120 m ötede artık bağımsız.
- **Neden 120 m:** 3GPP TR 38.901 Tablo 7.5-6, kırsal alanda (RMa) gölgelemenin benzer kaldığı mesafeyi görüş hattı varken 37 m, yokken 120 m veriyor. Bizim mesafelerde bağlantıların büyük çoğunluğunda görüş hattı yok, bu yüzden 120 m.
- **Paylaşım:** Aynı sahanın sektörleri aynı değeri paylaşıyor; bugünkü gibi.

## Düzeltme 2: Görüş hattı durumu konuma göre değişsin

- **Bugünkü durum:** Her bağlantının görüş hattı var/yok durumu koşu başında bir kez çekiliyor, sonra hiç değişmiyor. Aynı sahanın sektörleri birbirinden bağımsız çekiliyor.
- **Yenisi:** Düzeltme 1'deki gibi saha başına ikinci bir yumuşak alan kuruluyor; ızgara aralığı 60 m.
  - Alan değeri 0–1 arasında eşit dağılımlı bir sayıya çevriliyor.
  - Bu sayı görüş hattı olasılığından küçükse görüş hattı var sayılıyor. Olasılık formülü 3GPP'deki gibi, değişmedi: exp(−(d−10)/1000).
- **Neden 60 m:** 3GPP TR 38.901 bölüm 7.6.3.3, kırsal alanda görüş hattı durumunun benzer kaldığı mesafe olarak 60 m veriyor.
- **Değişen bir şey:** Aynı sahanın sektörleri artık aynı görüş hattı durumunu paylaşıyor. Fiziksel olarak doğrusu bu, çünkü aynı direkteler. Eskiden bağımsızdı.

## Düzeltme 3: Hareket eden kullanıcıda mesafe düzeltmesi güncellensin

- **Sabit kullanıcılar:** Hiçbir şey değişmiyor. Dosyadaki değer kullanılıyor.
- **Hareket eden kullanıcılar:** Düzeltme her an yeniden hesaplanıyor.
  - Formül deney 26'dakiyle aynı: k0 + k1·log10(d).
  - d, kullanıcının o anki konumunun 24 sahalık tam ağdaki en yakın sahaya uzaklığı; 100–15000 m arasına sınırlanıyor.
  - Bu, yol kapsaması adımındaki ve deney 33'teki kuralın aynısı: kapanan saha da sayılıyor.

## Hücre geçişi

- Deney 19'daki X2 + A3 hücre geçişi şimdiki koda taşınıyor.
- Ayarlar aynı: 3 dB fark, 256 ms bekleme. Değer taraması yok.
- Deney 19'daki yol noktası (waypoint) dosyası biçimi aynen kullanılıyor.

## Kabul kuralları (her biri geçmeden bir sonrakine geçilmez)

1. **Eskiyle aynılık:** Anahtarlar kapalıyken yeni kod, eski kodla aynı sonucu vermeli. Kısa bir koşuda `radio_samples.csv`, `ues.csv` ve `prb_usage.csv` aynı içerikte olmalı.
2. **ns-3 ile hızlı model aynı formül:** Düzeltme 1 ve 2 hızlı modele de aynen yazılıyor. Anahtarlar açıkken, sabit kullanıcılarda ns-3'ün sinyal gücü hızlı modelinkiyle kullanıcıların en az %99'unda 0,01 dB içinde aynı çıkmalı. Görüş hattı artık rastgele değil hesaplanıyor; bu yüzden birebir eşleşme bekleniyor.
3. **Gerçek ölçümlere uyum bozulmamalı:**
   - Düzeltme 1 ve 2 sabit kullanıcıların değerlerini de değiştiriyor; yalnız rastgele çekiliş değişiyor, dağılım aynı.
   - Hızlı modelle deney 29'un üç doğrulama durumu (normal yük, üç anten yönü) eski ve yeni gölgeleme/görüş hattıyla hesaplanıyor.
   - Ölçütler deney 31'dekiler: Experia'ya göre saha başına SINR farkı (eğitim ve test sahaları) ve saha başına RSRP farkı.
   - **Kabul:** Yeni hâlin her ölçütü eskisinden en fazla 1 dB kötü olmalı ve tüm hücrelerin ortanca RSRP'si ölçümden en fazla 1 dB farklı olmalı.
   - Tutmazsa durulur ve hareketli koşu yapılmaz.
4. **Yumuşaklık:** Yol boyunca 10 m'de bir hesaplanan sinyal gücünde ardışık iki nokta arasındaki farkın standart sapması 2 dB'den küçük olmalı. Bugünkü modelde bu fark ~11 dB, çünkü her noktada yeni bir 8 dB değer çekiliyor.
5. **Hücre geçişi:** Deney 19'daki iki sahalık hareket testi yeni kodda da geçmeli: otomatik A3 geçişi, eşleşen olaylar, hedefte bağlantı ve geçişten sonra veri.

## İddia etmeyeceklerimiz

- Yumuşak alan, gerçek arazinin (tepe, bina) gölgesi değil; aynı istatistikle üretilmiş rastgele bir alan.
- 120 m ve 60 m değerleri 3GPP'nin genel kırsal değerleri; bu bölge için ölçülmüş değil.

## Değişiklik (21 Kasım, sonuç görüldükten sonra; kullanıcının kararıyla)

- **Kural 4 geçmedi.** Yol boyunca 10 m'lik adımlarda toplam sinyal değişiminin standart sapması 5,7 dB çıktı.
  - Gölgeleme tek başına 1,1 dB.
  - Kalan sıçramalar görüş hattına girip çıkmaktan geliyor. 3GPP RMa'da görüş hattı var/yok arasındaki fark ~30 dB.
- **Karar:** Görüş hattı sıçramaları 3GPP'deki gibi bırakılıyor.
  - Kural 4 yalnız gölgeleme için geçerli sayılıyor; gölgeleme bu kuralı geçiyor.
  - Hareketli koşularda, görüş hattı değişiminin tetiklediği hücre geçişleri ayrıca sayılıp raporlanacak.
