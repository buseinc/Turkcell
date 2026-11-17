# Sındırgı LTE başlangıç senaryosu — ilk aşama özeti (15 Kasım 2026)

> Terimler yabancı geliyorsa önce [basit anlatım](BASIT_ANLATIM.md) belgesini okuyun.

Bu belge, 10–15 Kasım arasında yapılan bütün çalışmayı tek yerde toplar. Ayrıntılar her başlıktaki
bağlantılarda. Eski belgelerdeki sayılar, o günün senaryosuna aittir; **güncel sayılar bu belgededir.**

## 1. Projenin amacı (kısaca)

Turkcell'in saha koordinatları, Experia radyo ölçümleri ve LTE KPI verileriyle Sındırgı bölgesinin mobil
ağını ns-3'te temsili olarak kurmak. Sonraki aşamalarda deprem anı yükü, stres testi, öncelikli bölgeler ve
UAV ile hizmet iyileştirme bu ağ üzerinde çalışılacak. Anten yönü, güç, frekans ve kullanıcı konumları
paylaşılmadığı için hedef **birebir kopya değil, ölçümlere dayanan temsili bir ağ.**

## 2. Hoca ne istedi, biz ne yaptık

Kaynak: [hocanın notları](../../ana_proje/advisors%20notes.txt) ve yöntem taslağı (main.tex).

| Hocanın isteği | Yapılan | Durum |
|---|---|---|
| Koordinatları çek, haritaya koy, ChatGPT'nin seçtiği sahaları doğrula, kartezyen koordinata çevir | 8 ana + 8 komşu saha güncel envanterle (563 saha / 6 475 hücre) doğrulandı; 96 hücrenin 96'sı doğru sahada. Yerel metre koordinatları, haritalar. [Koordinat raporu](../2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/KOORDINAT_GUNCELLEME_SONUCU.md) | ✅ |
| ns-3 sürümü ve LTE yığınını netleştir | ns-3.44 klasik LTE/EPC (5G-LENA değil). Otomatik hücre seçimi, EPC, veri trafiği çalışıyor; iki bilgisayarda yeniden üretildi. | ✅ |
| Varsayılan değerler + rastgele kullanıcılarla RSRP vb. ölç, Experia ile karşılaştır | Saha bazında RSRP/SINR/RSRQ karşılaştırması; 5 eğitim, 3 kontrol sahası. | ✅ |
| "Tx power ve anten bilgisi olmadan hücre sınırları anlaşılmıyor; deneme yanılma" | 9 başlıkta 49 geçerli tarama, tekrarlı karşılaştırma; ayar seçildi. Izgara kapsama haritaları. | ✅ |
| "Önce bir coverage belli olsun" | Bölge geneli RSRP, hizmet alanı ve SINR sınır haritaları; etkileşimli harita. | ✅ |
| Sektör/taşıyıcı kombinasyonlarını dene (tek taşıyıcı, çok taşıyıcı…) | S0 (3 sektör, tek frekans), S1 (az sektör), S2 (çok frekans) denendi; hangi sahaların çok frekanslı olduğu KPI'dan çıkarıldı. | ✅ |
| TAAVG'yi kullan | Birim belirsiz olduğu için mesafeye çevrilmedi; yalnız göreli sıralama için kullanıldı. | ⏳ Turkcell teyidi bekleniyor |
| Normal gün ve deprem anı yükü | KPI'dan yük profili çıkarıldı; iki deprem KPI'da tespit edildi. Simülasyona KPI yükü verildi. | ✅ profil — stres testi sonraki aşama |
| Statik kullanıcıyla başla | Bütün çalışmalar sabit kullanıcılarla. | ✅ |

## 3. Şu anki başlangıç senaryosu (S0) — tam tanım

Karşılaştırmalarda kullanılan standart budur.

| Başlık | Değer | Nereden geldi |
|---|---|---|
| Sahalar | 24: hocanın 8 ana + 8 komşu sahası + güncel envanterde en yakın 8 saha | Komşu sayısı 16→24→32→48 kontrolüyle |
| Sektör / taşıyıcı | Saha başına 3 sektör, tek taşıyıcı: Band 3, 1 815 MHz, 20 MHz | Varsayım (S0) |
| Güç / anten | Sektör başına 49 dBm; 120° yatay genişlik, 15 dBi; anten yükseklik 30 m | Taramayla seçildi |
| Yayılım | Log-distance, üs 3; gölgeleme yok; alıcı gürültü faktörü 9 dB | Taramayla seçildi |
| Zamanlayıcı / CQI | Proportional fair; mixed CQI | ns-3 seçenekleri |
| Ölçüm kullanıcıları | 256; ana sahaların 2–6 km çevresinde kümeler | Örneklem çalışması (64 yetersiz çıktı) |
| Yük | Her hücreye bir yük kullanıcısı; KPI normal gün ortalaması DL PRB 0,233; trafik rastgele anlarda başlıyor | KPI yük profili |
| Tekrar | 3 azimut/kullanıcı örneği | Sağlamlık için |
| Süre | 4 s, ilk 1 s ısınma | — |

## 4. Ana sonuçlar (güncel standartla)

Kaynak: [S0/S2 karşılaştırması](../../deneyler/14_temel_s0_ve_cok_tasiyici_s2_2026-11-15/SONUCLAR.md).

| Gösterge | Değer | Yorum |
|---|---:|---|
| Kontrol sahaları RSRP hatası | 1,72 ± 0,54 dB | İyi |
| Kontrol sahaları SINR hatası | 2,15 ± 1,13 dB | Makul; ölçüm tanımı belirsiz |
| Kontrol sahaları RSRQ hatası | 4,30 ± 0,39 dB | ns-3 RSRQ tanımı farklı; karşılaştırma anlamlı değil |
| Sahaların RSRP sıralaması (Experia ile) | Spearman 0,79–0,95 | İyi: güçlü/zayıf sahalar doğru |
| Hücre RSRP medyanı | −111,7 dBm (Experia −104,2) | Gerçek ağdaki güçlü hücreler eksik |
| CQI (KPI ile eşzamanlı) | KPI'dan 1,1 birim düşük | Girişim biraz fazla |
| Kapsama | Değerlendirme alanının %99,8'inde RSRP ≥ −120 dBm | Bölgede kapsama boşluğu yok |

**Bir cümleyle:** Başlangıç senaryosu kapsama ve sahaların göreli durumu için güvenilir. Sinyal kalitesi
makul düzeyde. Ama gerçek ağın hücre çeşitliliği ve çok frekanslı yapısı tam temsil edilmiyor.

## 5. Bu süreçte öğrendiklerimiz

1. **64 sanal kullanıcı yetersizdi.** Saha ortalamaları kullanıcıların nereye düştüğüne bağlıydı; 256
   kullanıcıya geçildi. [Örneklem](../../deneyler/08_kullanici_orneklemi_2026-11-12/SONUCLAR.md)
2. **Önceki simülasyon ağı gerçeğe göre 7–10 kat boş çalıştırıyordu.** KPI'da PRB normal gün %23, akşam
   yoğun saat %36; simülasyonda %3. Yük verilince SINR iyimserliği büyük ölçüde kayboldu. [Yük profili](../../deneyler/09_kpi_yuk_profili_2026-11-12/SONUCLAR.md)
3. **Deprem anı KPI'da açıkça görülüyor.** 10 Ağustos ve 27 Ekim 2025 depremlerinde aynı anda bağlı
   kullanıcı ilk yarım saatte ≈2 katına çıkıyor, veri hacmi ve PRB düşüyor, bağlantı düşmeleri artıyor.
   Deprem yükü "daha çok veri" değil, "aynı anda çok daha fazla kişi". Stres testi buna göre kurulmalı.
4. **ns-3'ün raporladığı SINR'nin yaklaşık üçte ikisi girişimsiz örneklerden oluşuyor.** Bu bir model
   davranışı. Ayrıca ilk yük denemelerinde yük trafiği eşzamanlıydı; bu düzeltildi. Bu yüzden SINR
   sayılarını "Experia ile eşleşti" diye sunmuyoruz. [Kapsama haritaları](../../deneyler/10_kapsama_haritalari_2026-11-15/SONUCLAR.md)
5. **Tek frekans varsayımı girişimi abartıyor.** KPI CQI'sıyla eşzamanlı karşılaştırma ve hücre dağılımları
   bunu gösterdi. [CQI](../../deneyler/11_cqi_karsilastirmasi_2026-11-15/SONUCLAR.md),
   [dağılım](../../deneyler/12_dagilim_karsilastirmasi_2026-11-15/SONUCLAR.md)
6. **Ana sahaların beşi (130, 296, 440, 441, 443) ve komşuların çoğu çok frekanslı;** 444 ve 554 tek frekans
   görünüyor. Bu, KPI'daki frekanslar arası handover kayıtlarından çıkarıldı. [Hücre imzası](../../deneyler/13_hucre_imzasi_2026-11-15/SONUCLAR.md)
7. **Çok taşıyıcılı senaryo (S2) karışık sonuç verdi.** Hücre RSRP düzeyi ve CQI gerçeğe yaklaştı, ama saha
   hataları büyüdü. Sebep, doğrulanamayan iki varsayım: 800 MHz gücü ve kullanıcıların katmanlara atanması.
   S0 başlangıç olarak korunuyor. Yük deneylerinde S0 (girişim fazla) ve S2 (girişim az) iki uç olarak
   birlikte kullanılabilir.

## 6. Sınırlar — ne iddia etmiyoruz

- Gerçek anten yönleri, güçleri, frekansları ve kullanıcı konumları bilinmiyor. Seçilen değerler ölçümlere
  en yakın sonucu veren varsayımlardır, Turkcell'in gerçek ayarları değil.
- Experia (Haziran 2026) ve KPI (2025) farklı dönemlere ait; eşzamanlı gözlem gibi birleştirilmedi.
- Kontrol sahaları ayar seçiminde kullanılmadı, ama önceki çalışmalarda görülmüştü; kör doğrulama değil.
- Arazi ve bina modeli yok; koşular kısa (4 s) ve kullanıcılar sabit.
- Haritalar varsayımsal senaryonun çıktısıdır, operatör kapsama haritası değildir.

## 7. Hocaya/Turkcell'e sorulacaklar

1. **Hücrelerin bandı/EARFCN'i ve taşıyıcı başına güç.** Hangi hücrelerin aynı sektörde olduğu. (S2'yi
   tahminden veriye taşır.)
2. **Experia SINR ve RSRQ'nun tanımı:** Hangi kanal, hangi ortalama?
3. **KPI tanımları:** CQI tablosu (64QAM mı 256QAM mı), throughput ve trafik hacmi birimleri, TAAVG birimi.
4. **Deprem saatleri ve KPI saat dilimi:** Veride görülen sıçramalar 10 Ağustos 19:45 ve 27 Ekim 22:45
   dilimlerinde. Kamuya açık deprem saatleriyle uyumlu, ama KPI'nın yerel saat olduğu teyit edilmeli.
5. **İlk aşamanın yeterliliği:** Bu başlangıç senaryosu sınırlarıyla birlikte yük/stres aşamasına geçmek
   için yeterli mi? Hangi hata düzeyi kabul edilebilir?

## 8. Önerilen sonraki adım

Stres pilotu, yoğun saat yükünden başlayarak:
- (a) PRB yükünü kademeli artırmak,
- (b) deprem anını temsil etmek için eşzamanlı kullanıcı sayısını artırmak.

Her ikisi S0 ve S2'de koşulacak. Başarı ölçütleri (throughput, gecikme, paket kaybı, bağlanamayan kullanıcı)
koşulardan önce yazılacak.

## Bütün çalışmalar

| # | Çalışma | Ana sonuç |
|---|---|---|
| 01–07 | [10–12 Kasım çalışmaları](../2026-11-11_durum_ve_plan/PROJE_DURUMU_VE_PLAN.md) | Ayar taraması, seçilen ayar, koordinat doğrulama |
| 08 | [Kullanıcı örneklemi](../../deneyler/08_kullanici_orneklemi_2026-11-12/SONUCLAR.md) | 64 kullanıcı yetersiz → 256 |
| 09 | [KPI yük profili](../../deneyler/09_kpi_yuk_profili_2026-11-12/SONUCLAR.md) | Ağ 7–10 kat boştu; deprem anı yükü |
| 10 | [Kapsama haritaları](../../deneyler/10_kapsama_haritalari_2026-11-15/SONUCLAR.md) | Kapsama boşluğu yok; ns-3 SINR davranışı |
| 11 | [CQI karşılaştırması](../../deneyler/11_cqi_karsilastirmasi_2026-11-15/SONUCLAR.md) | Tek frekans girişimi abartıyor |
| 12 | [Dağılım karşılaştırması](../../deneyler/12_dagilim_karsilastirmasi_2026-11-15/SONUCLAR.md) | Sıralama iyi, hücre çeşitliliği eksik |
| 13 | [Hücre imzası](../../deneyler/13_hucre_imzasi_2026-11-15/SONUCLAR.md) | 5 ana saha çok frekanslı |
| 14 | [Çok taşıyıcı (S2)](../../deneyler/14_temel_s0_ve_cok_tasiyici_s2_2026-11-15/SONUCLAR.md) | Karışık; S0 korunuyor |

Etkileşimli kapsama haritası: [kapsama_haritasi.html](../../deneyler/10_kapsama_haritalari_2026-11-15/kapsama_haritasi.html)
