# Deney 36: Hep yayında olan pay (f) ns-3'te — kurallar

22 Kasım'da, kod yazılmadan önce yazıldı.

## Ne ekleniyor

- **Ne:** Deney 35'te hızlı modelde ayarlanan katsayı (f = 0,03) ns-3'e ekleniyor. Fiziksel bir pay değil, **ayarlanmış bir katsayı**.
- **Nerede:** Özel LTE kütüphanesine 4. yama olarak, `lte-ue-phy.cc` içindeki `GenerateMixedCqiReport` fonksiyonuna. Telefonun bildirdiği sinyal kalitesi (CQI ve `radio_samples` SINR) burada hesaplanıyor.
- **Formül (kaynak bloğu başına):**
  - SINR = S / [(1 − f)·(I_veri + N) + f·(I_tam + N)]
  - I_tam + N, kontrol sinyalinin girişimi. Kontrol sinyali ns-3'te her alt çerçevede bütün komşular tarafından bütün banda yayılıyor. Bu değer kontrol SINR'ından geri hesaplanıyor: S/SINR_kontrol − EVM²·S.
  - Sonra EVM, bugünkü gibi ekleniyor. Bu, hızlı modeldeki `sinamalar.sinr_on` formülüyle aynı.
- **Neyi değiştirmiyor:** Verinin çözülmesi ve hata modeli. Gerçek veri girişimi aynen kalıyor. Yalnız bildirilen kalite ve ona bağlı olarak seçilen kodlama değişiyor.
- **Anahtar:** `g_lteAlwaysOn`, varsayılan 0. Senaryoda `--alwaysOn` seçeneğiyle açılıyor.

## Kabul

1. **Eskiyle aynılık:** f = 0 iken deney 34'ün `R1_regresyon` koşusuyla (L25 girdileri, 1 s, bütün yeni anahtarlar kapalı) altı dosya birebir aynı olmalı.
2. **Formül eşleşmesi:**
   - Koşu: f = 0,03; deney 34'ün `R2_alan` girdileri (sabit kullanıcılar, yumuşak gölgeleme ve görüş hattı açık, 1 s).
   - Hesaplanan: ns-3'ün bildirdiği SINR (kullanıcı başına zaman ortalaması) ile hızlı modelin `sinr_on` formülü. Formülde ns-3'ün kendi bağlı hücreleri ve kendi ölçtüğü hücre PRB'leri kullanılıyor. Bu, deney 31'deki "formül" testi.
   - Şart (a): Ana sahalarda saha başına ortalama mutlak fark ≤ 1,5 dB. Deney 31'deki sınır.
   - Şart (b): f = 0 ile f = 0,03 arasındaki ns-3 düşüşü, hızlı modelin aynı girdilerle öngördüğü düşüşe ±0,5 dB içinde eşit olmalı. Ana saha kullanıcılarının ortalaması alınıyor. f = 0 koşusu olarak deney 34'ün `R2_alan` sonucu kullanılıyor.

## Düzeltme (sonuç görülmeden önce)

- **Sorun:** 1 saniyelik koşularda ns-3 hücre yükünü ölçmüyor. Yük 1. saniyeden sonra sayılıyor ve deney 34'ün `R2_alan` koşusunda bütün hücreler 0 çıkıyor. Bu yüzden kontrol 2 yazıldığı gibi yapılamıyor.
- **Kontrol 2'nin yeni hâli:**
  - Aynı girdilerle iki **2 saniyelik** koşu yapılıyor: `R2b_f0` (f = 0) ve `R2b_f003` (f = 0,03).
  - SINR örnekleri ve hücre yükü 1–2. saniye arasından alınıyor.
  - Şart (a) ve (b) aynen geçerli. Şart (b)'deki f = 0 karşılaştırması `R2b_f0` ile yapılıyor.
- **Bekleyen 1 saniyelik koşu:** Çalışmakta olan `R2_f003` kontrol için kullanılmıyor.

## Sındırgı kesinti sonucu katsayıyla değişiyor mu? (hızlı model, sonuç görülmeden yazıldı)

- **Girdiler:** Deney 33'ün kullanıcıları (`ues_quake_42.csv`), K0–K3 durumları ve deney 32'deki ölçütler. Servis yok = planlanan bloklardaki SINR'a göre CQI 0. Zayıf = RSRP < −121,8 dBm.
- **Model:** Deney 34'teki yumuşak gölgeleme ve konuma bağlı görüş hattı.
- **Hesap:** f = 0 ve f = 0,03 ile servisi olmayan payı:
  - kapanan sahanın kullanıcıları arasında,
  - bütün bölgede.
- Hücre yükü f = 0 ile çözülüyor. f'nin yük üzerindeki etkisi ayrıca raporlanıyor: f = 0,03 ile bloklar başına kaynak ihtiyacından yeniden hesaplanan yük.
- **Karar:**
  - Kapanan sahaların çevresinde servisi olmayan pay 3 yüzde puanından fazla değişirse, deney 33'ün K koşuları ns-3'te f = 0,03 ile tekrarlanacak.
  - Değişmezse deney 33'ün ns-3 sonuçları geçerli kalacak; bu kontrol ek bilgi olarak yazılacak.
