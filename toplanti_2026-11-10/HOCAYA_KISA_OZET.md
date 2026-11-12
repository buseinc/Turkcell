# Hocaya kısa özet — 10 Kasım 2026

> **12 Kasım güncel sonuç:** Hocanın 8 ana + 8 komşu sahası güncel envanterle doğrulandı ve korundu. Yeni yakın sahalarla yedi simülasyon koşusu tamamlandı; komşu genişletmeleri ve üç kullanıcı örneğinin eski–yeni kontrolleri geçti. Güncel 24 sahada kontrol MAE: RSRP 2,96 / SINR 3,63 / RSRQ 4,07 dB. [Sonuçlar ve grafik](../experiments/inventory_refresh_2026-11-12/SONUCLAR.md) — [Hocaya güncel mesaj](../review_2026-11-12/HOCAYA_MESAJ.md). Aşağıdaki 516 saha/eksik koordinat ifadeleri ve eski tablolar tarihsel sürümdür; güncel envanter 563 saha / 6.475 hücredir.

> [11 Kasım: hocanın beklentileriyle eşleştirilmiş güncel durum ve yapılacaklar](../toplanti_2026-11-11/PROJE_DURUMU_VE_PLAN.md). Aşağıdaki sayılar 10 Kasım'da tamamlanan son deney kampanyasına aittir.

Amaç, verideki saha konumlarını koruyup bilinmeyen radyo ve kullanıcı koşullarını açık varsayımlarla deneyerek Experia'ya yakın, temsili bir LTE başlangıcı kurmak.

**Bu bilgisayarda çalışıyor.** Son genişletmede **51 gerçek ns-3 tarama koşusu** (49 geçerli; iki hatalı Band 8 koşusu çıkarılıp uygun genişlikle yeniden çalıştırıldı), **4 aday × 3 ortak tekrar** ve **3 uzun/komşu kontrolü** tamamlandı. Bunlara ek 2 yazılım testi ve 2 pasif tanı tekrarı yapıldı; bunlar yeni model alternatifi sayılmadı. Önceki analitik ön elemeler bu gerçek koşu sayısına dahil değil.

Dokuz başlık denendi: kullanıcı dağılımı, gölgeleme, alıcı gürültüsü, yayılım, güç, trafik, sektör sayısı, anten yönü ve taşıyıcı. Koordinatlar ve ölçüm hedefleri değiştirilmedi.

**Öneri: reference.** 2–6 km kümeler; 120°; n=3.0; 49 dBm; NF=9.0 dB; gölge σ=0.0 dB; DL EARFCN=1300; UDP=50 ms; sektör=three. Önceki aday ortak tekrarların sağlamlık sıralamasında doğrudan ilk sırada kaldı. 

| Kontrol hatası: üç tekrar ort. ± std | Korunan önceki aday | En yakın eğitim alternatifi (model_02) |
|---|---:|---:|
| RSRP | 2.96 ± 0.83 dB | 2.63 ± 1.12 dB |
| SINR | 3.64 ± 1.38 dB | 2.86 ± 0.65 dB |
| RSRQ | 4.08 ± 0.21 dB | 4.54 ± 0.21 dB |

Düşük daha yakın. Seçim yalnız beş eğitim sahasında, ortalama hata ve tekrarlar arası oynaklıkla yapıldı. Tekrarları dikkate alan eğitim puanı: seçilen 3.202, en yakın alternatif 3.474. ± değerleri üç tekrarın standart sapmasıdır, güven aralığı değildir. Tekrarlarda eğitim 15/15, kontrol 9/9 saha-gözlemi; en az 64/64 kullanıcı bağlı, 64/64 kullanıcı veri aldı.

Kapsam sınırı: bazı tekrar/sahalarda yalnız 1–2 sanal kullanıcı vardır. Bir sonraki duyarlılık kontrolü, toplam sunulan yükü koruyarak kullanıcı örneklemini artırmak olmalı; bu kampanyada henüz yapılmadı.

Önceden seçilen ilk kullanıcı örneğinde 8 s kontrol hataları RSRP / SINR / RSRQ **2.14 / 5.20 / 3.80 dB**. Sekiz sahanın en büyük mutlak hataları **7.58 / 10.06 / 4.39 dB**; bazı sahalarda fark devam ediyor. 24→32→48 saha kontrolü **geçti**; 4→8 s kontrolü **geçti**.

Hocaya söylenecek: “Yalnız birkaç ayar denemedik; farklı açıklamaları tarayıp iyi görünenleri farklı kullanıcı/anten örneklerinde tekrar sınadık. Seçtiğimiz ayar ölçümlere yakın bir başlangıç; gerçek ağın birebir konfigürasyonu olduğunu iddia etmiyoruz.”

Üç kontrol sahası önceki çalışmalarda görüldü; yeni kör doğrulama değildir. Bütün koşullar kısa süreli, düşük sentetik yükte çalışır. Yakınlık gerçek operatör ayarlarının bulunduğunu göstermez; kapasite doğrulaması yapılmadı.

Hocadan netleştirilecek üç konu:

1. 553/554/555 konumları ve hücre–saha bağlantılarının özgün kaynağı.
2. Experia SINR/RSRQ kanal ve ortalama tanımları; mixed çıktıyla karşılaştırma uygunluğu.
3. Temsili başlangıcın yeterlilik ölçütü ve KPI ile yük aşamasına geçiş.

[Son deneyin tam sonuçları](../experiments/extended_radio_2026-11-10/SONUCLAR.md) — [Seçilen senaryo](../experiments/extended_radio_2026-11-10/selected_scenario/configuration.json)
