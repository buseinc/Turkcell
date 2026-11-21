# Deney 34: Gerçek yollarda hareket eden kullanıcılar (plan, 21 Kasım)

## Amaç

Şimdiye kadar bütün kullanıcılar sabitti. Hocanın önerisi: kullanıcılar araziye uygun hareket etsin, yani araçlar gerçek yollarda gitsin. Ana yol bunun için en kolay başlangıç.

Sorduğumuz soru: **Bir saha çökünce, yoldan geçen araçlar yolun neresinde ve ne kadar süre servis kaybediyor?**

- Bu, sabit kullanıcılarla bulduğumuz "kapanan sahanın çevresinde %15–18 servissiz" sonucunun yoldaki karşılığı.
- İHA aşamasına da doğrudan girdi verir: yolun hangi parçası, kaç kilometresi kapatılmalı?

Hocanın "şimdilik Sındırgı ile başlayalım" sözüne uygun olarak bölge değişmiyor: deney 29 modeli, 24 saha.

## Neyi gerçek veriyle, neyi varsayımla yapıyoruz

| | Kaynak |
|---|---|
| Yolların güzergâhı | OpenStreetMap (herkese açık, gerçek) |
| Yolun türü ve hız sınırı | OpenStreetMap; hız etiketi yoksa Türkiye'deki yasal sınırlar (şehir dışı tek yol 90 km/s) |
| Kesinti senaryosu | Gerçekte çöken 482 (28 Ekim) ve 130 (10 Ağustos) |
| Arka plandaki sabit kullanıcılar | Deney 33'teki ölçülmüş deprem yükü |
| Yoldaki araç sayısı | **Varsayım.** Trafik sayımı verimiz yok; araç sayısı bir test ayarı, gerçek trafik iddiası değil. |
| Anten yönleri, tek frekans, düz arazi | Deney 32–33'teki bilinen sınırlar aynen geçerli |

## Adımlar

**Adım 1: Yol verisi.** OpenStreetMap'ten 24 sahalık bölgedeki ana yolları (otoyol, devlet yolu, il yolu) indiriyoruz. Bölge: enlem 39,09–39,45, boylam 27,90–28,38. İndirme için kullanıcının izni gerekiyor. Yolları modelin koordinat sistemine çeviriyoruz ve haritada sahalarla birlikte gösteriyoruz.

**Adım 2: Yol boyunca kapsama.** Hareket simülasyonu yok; hızlı model ve ns-3 formülleri kullanılıyor.
- Yol boyunca her 50 m'de bir noktada sinyal gücü ve sinyal kalitesi hesaplanıyor. Durumlar: K0 kesinti yok, K1 482 kapalı, K2 130 kapalı, K3 ikisi kapalı.
- Çıktı: yolun hangi kilometrelerinde servis yok. Ölçütler deney 32'dekilerle aynı: sinyal kalitesi −6,7 dB altı ya da sinyal gücü −121,8 dBm altı.
- Bu adım ucuz ve asıl soruya ilk cevabı verir. ns-3'ün yerine geçmez; ns-3 koşusunda hangi yol parçasına bakacağımızı seçer.

**Adım 3: ns-3'te hareket eden araçlar.** Seçilen yol parçasında araçlar gidip geliyor. Hücreler arası geçiş açık (deney 19'daki X2 + A3). Sabit deprem yükü arka planda duruyor. Durumlar: K0 ve K1.
- Ölçülenler: yol boyunca servis kesintisinin yeri ve süresi, geçiş sayısı ve başarısı, paket kaybı.
- Paket teslimi yalnızca yardımcı bilgi olarak raporlanacak. Deney 33'teki L25 kontrolünde ns-3'ün paket kaybının sebebi açık kaldı.

## Hareket başlamadan önce düzeltilmesi gereken bilinen sınırlar

Mevcut ns-3 modeli sabit kullanıcılar için kuruldu. Hareket eden bir kullanıcıda üç yeri yanlış çalışır. Bunları düzeltmeden koşu yapmak anlamsız olur.

1. **Gölgeleme her adımda yeniden çekiliyor.**
   - Sorun: Şu anki 8 dB gölgeleme, kullanıcının tam koordinatına bağlı. Araç 1 milimetre bile ilerlese yeni ve bağımsız bir değer geliyor. Hareket eden araç her an rastgele ±8 dB sıçrayan bir sinyal görür; bu da sahte, sürekli hücre geçişleri demek.
   - Gerçekte: Gölgeleme bir bina ya da tepe kadar sürer. 3GPP TR 38.901 Tablo 7.5-6'ya göre kırsal alanda yaklaşık 37 m (görüş hattı var) ve 120 m (görüş hattı yok) boyunca benzer kalır.
   - Düzeltme: Bu mesafelerle uyumlu, uzayda yumuşak değişen bir gölgeleme.

2. **Görüş hattı durumu hiç değişmiyor.** Her bağlantının görüş hattı var/yok durumu bir kez çekilip koşu boyunca sabit kalıyor. Araç 10 km gitse de değişmiyor. Bu durum, araç ilerledikçe bölgeden bölgeye değişmeli.

3. **Mesafe düzeltmesi kullanıcıya sabitlenmiş.** Gerçek ölçümlerden çıkardığımız "uzaklığa göre sinyal düzeltmesi" (deney 26) şu an kullanıcının başlangıçtaki sahaya uzaklığından bir kez hesaplanıyor. Hareket eden araçta bu, o anki uzaklığa göre güncellenmeli.

Ayrıca deney 19'daki hücre geçişi kodu, şimdiki model koduna (deney 29/33) taşınmadı; taşınması gerekiyor.

**Her düzeltmeden sonra kontrol:**
- Sabit kullanıcılarla model hâlâ gerçek ölçümlere aynı yakınlıkta mı? Deney 26'daki karşılaştırma hızlı modelle tekrarlanır.
- Gölgeleme düzeltmesi sabit kullanıcıların değerlerini de değiştirecek. Bu yüzden doğrulama tekrarı zorunlu; tutmazsa koşu yok.

## İddia etmeyeceklerimiz

- Gerçek trafik yoğunluğu ya da gerçek araç sayısı.
- Gerçek bir sürüş testinin sonucu. Elimizde yol üzerinde ölçüm (drive test) yok, bu yüzden yoldaki sonuçlar gerçekle doğrudan karşılaştırılamaz.
- Arazinin (dağ, tepe) etkisi. Model düz arazi varsayıyor.
