# Deney 42: Şehir modeli ns-3'te, kurallar (25 Kasım)

Kullanıcıyla 25 Kasım'da kararlaştırıldı.

## Amaç

Deney 40'taki şehir modelini (Balıkesir merkez, 94 saha) ns-3'e taşımak. Aynı kullanıcılarla, aynı yükte, ns-3 ile hızlı modelin aynı sonucu verdiğini göstermek. Bu bir sınama; modele yeni bir şey eklenmiyor, ölçüme göre hiçbir şey ayarlanmıyor.

## Ayarlar: hızlı modelde ne var, ns-3'te nasıl olacak

| Ayar | Hızlı model (deney 40) | ns-3'te | Kaynak | Yeni kod mu |
|---|---|---|---|---|
| Yol kaybı | Kullanıcının yerine göre UMa ya da RMa | ns-3'ün kendi `ThreeGppUma` ve `ThreeGppRma` sınıfları; her kullanıcının bütün bağlantıları onun ortamının sınıfıyla. Küçük bir seçici sınıf | TR 38.901 | Evet, küçük |
| Görüş hattı (LOS) | Yumuşak alan; olasılık ortama göre (UMa: 18/d + e^(−d/63)(1 − 18/d), RMa) | Deney 34'teki yumuşak LOS sınıfına UMa olasılığı ekleniyor | TR 38.901 Tablo 7.4.2-1 | Evet, küçük |
| Gölgeleme | Yumuşak alan; σ ortama ve LOS'a göre (şehir 7/7, kırsal 4/8 dB) | Deney 34'teki yumuşak gölge alanı; σ bağlantı başına seçiliyor | TR 38.901 Tablo 7.4.1-1, 7.4.3-3 | Evet, küçük |
| Bina içi / araba kaybı | Kullanıcı başına çekiliyor | Python'da aynı kuralla çekilip kullanıcı dosyasında `extra_loss_db` olarak veriliyor. ns-3'ün kendi bina kaybı kapalı (varyans hatası var) | TR 38.901 7.4.3 | Hayır, var |
| Kule yüksekliği | 25 m | 25 m (`--enbHeight`; eski koşularda 30 m) | UMa standardı; gerçek yükseklik bilinmiyor | Evet, ayar |
| Anten | 36.814 deseni, 6° eğim, yönler 10 çekilişten | Aynı | TR 36.814 | Hayır, var |
| Verici kusuru | EVM %8 | Aynı | TS 36.104 | Hayır, var |
| Sürekli yayın | %4,8 | `--always-on 0.048` | Referans sinyali payı 8/168 | Hayır, var |
| Zamanlayıcı | Yalnız yük olarak | Kuyruğa göre kaynak veren PF | Deney 29 | Hayır, var |
| Kullanıcı yerleri | Ölçümdeki TA uzaklığı, kendi sahasının en iyi olduğu yön | Hızlı modelin ürettiği yerler aynen dosyadan | Deney 40 | Hayır |

Yüklü ns-3'e (`/home/umut/ns-allinone-3.44/ns-3.44`) dokunulmuyor; yeni kod senaryo dosyasına ve özel kütüphaneye giriyor.

## Sınama sırası

1. **Eskiyle aynılık:** Yeni ayarlar kapalıyken eski bir koşu (deney 34, `R5_ho_kapali`) birebir aynı sonucu vermeli.
2. **Sinyal gücü (K1):**
   - Kısa koşu, trafik yok; 15:30, çekiliş 42, deney 40'ın kullanıcıları.
   - ns-3'ün ölçtüğü RSRP ile hızlı modelin RSRP'si kullanıcı başına karşılaştırılıyor.
   - Şart: saha başına ortalama mutlak fark ≤ 0,5 dB.
3. **Sinyal kalitesi ayrıca sınanmıyor:**
   - Kalite, ns-3'ün bu deneyde değişmeyen parçalarıyla hesaplanıyor: parazit, verici kusuru, sürekli yayın payı, zamanlayıcı. Bunların hızlı modelle aynı hesabı yaptığı deney 31 ve 36'da gösterildi.
   - Kaliteye giren bütün sinyal güçleri, K1'de sınanan aynı formülden geçiyor.
   - Trafikli koşu şehir büyüklüğünde saatler sürüyor ve yeni bilgi vermesi beklenmiyor. Bu yüzden yapılmıyor.
4. **Ölçümle karşılaştırma** hızlı modelden alınıyor (deney 40); ns-3'te tekrarlanmıyor.

Bir sınama geçmezse sebep bulunuyor. Hiçbir sayı ölçüme ya da hızlı modele uydurulmuyor.

## Kullanıcılar ve yük

Bu deney iki modelin aynı hesabı yaptığını sınıyor; gerçek kalabalık gerekmiyor.
- **Kullanıcılar:** Her ana sahada 32 kullanıcı, deney 40'ın 15:30 yerlerinden (ilk 32): ölçümdeki uzaklıkta, kendi sahasının en iyi olduğu yönde.
- **Yük:** Yükü bu kullanıcıların kendisi taşıyor (Sındırgı'daki gibi). Her hücrenin kullanıcılarının paket aralığı, hücre KPI'daki 15:30 PRB'si kadar meşgul olacak şekilde seçiliyor. Hangi kullanıcının hangi hücreye bağlandığı hızlı modelden alınıyor.
- **Paketler:** 512 bayt. Paket aralığı 1 ms'nin (bir alt çerçeve) altına inmiyor; bir hücrenin hedefi için daha sık paket gerekiyorsa paket büyüyor (17 kullanıcı, en çok 1.723 bayt).
- **Servis alamayan kullanıcılar** (hızlı modelde CQI 0, 134 kişi): Saniyede bir paket alıyorlar, yük ayarına katılmıyorlar.
- **Servis alabilen kullanıcısı olmayan hücreler** (11 komşu saha ve birkaç hücre, toplam 14): Her birine bir yük kullanıcısı. Antenin baktığı yönde, 100 m'den başlayarak 50 m adımlarla, kendi hücresinin en iyi olduğu ilk noktada.
- **Sonuç** (`hazirla42.py`, `plan42.json`): 2.624 kullanıcı ve 14 yük kullanıcısı. Hızlı modelde hücre yükünün hedeften ortalama farkı 0,002; 20 hücrede fark 0,01'den büyük, en çok 0,09. Kalite sınaması ns-3'ün kendi ölçtüğü yükle yapıldığı için bu fark sınamayı etkilemiyor.
- **Yerleşimin aynılığı:** Deney 40'ın yerleşimi aynı rastgele sayılarla yeniden üretiliyor; kaydedilen kullanıcıların RSRP'siyle fark 0,0 dB.

Kesinti ve İHA senaryolarında ise gerçek sayı kullanılacak: model hücresine, gerçek hücrelerin KPI ortalaması kadar kullanıcı (15:30'da hücre başına ~25, ana 83 sahada ~6.100). Gerçekte sahada ortalama 11 hücre var, modelde 3 ve tek frekans; bu yüzden sahanın bütün kullanıcıları değil, bir katmanın kullanıcıları konuyor.

## Süre

- Edremit (144 hücre) 1,5 s'lik koşuda 33 dakika sürmüştü.
- Burada 282 hücre ve 2.638 kullanıcı var. Trafiksiz koşuda yalnız ilk 0,3 s (bağlanma) 29 dakika sürdü.
