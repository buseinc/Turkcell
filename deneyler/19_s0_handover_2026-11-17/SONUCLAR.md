# Deney 19 — S0 için handover

**Durum: Handover doğrulaması tamamlandı. Tüm kabul ölçütleri geçti.**

S0’a isteğe bağlı X2 + A3 RSRP handover eklenir. Kapalıyken ns-3.44’ün eski NoOp davranışı aynen bırakılır. S0 radyo ayarları, 256 ölçüm + 72 yük kullanıcısı ve sabit konumlar korunur.

Histerezis 3 dB, komşunun üstünlüğünü sürdürme süresi 256 ms: kurulu ns-3.44 A3 varsayımları. Değer taraması yapılmayacak. X2, mantıksal sektör eNB düğümleri arasında tam bağlı kurulur; gerçek operatör komşuluk topolojisi iddiası yok.

Önce eski S0 kapalı koşusu altı CSV’de yalnız satır sonu normalizasyonuyla birebir tekrarlanacak. Sonra üç S0 örneğinde handover açıkken sabit kullanıcıların bağlantısı, hücresi ve sinyal gücünün korunduğu kontrol edilecek.

Pozitif/negatif hareket testi: S0’ın 441 ve 443 sahaları tek başına, aynı üç anten yönü örneğiyle kullanılır. Bir kullanıcı iki saha arasında 15 m/s hızla gider; iki uçta 2 saniye bekler. 10 ms aralıklı 512 bayt trafik veri sürekliliğini izler. Bu küçük test, tam ağın hareket veya deprem performansı iddiası değildir.

Her rotada handover kapalı ve açık koşulur. Açıkken 441→443 otomatik A3 geçişi, UE/eNB olaylarının eşleşmesi, hedefte bağlantı ve geçişten sonra veri beklenir. Kapalı koşuda handover olayı beklenmez; son bağlantı kaybı varsa açıkça raporlanır. Elle handover emri veya hedefe zorunlu bağlantı kullanılmaz.

Handover olayları, 100 ms hücre/konum zaman çizgisi ve hareket testinin paket alış zamanları kaydedilir. Son hücreye göre filtreleyen eski metrics() hareket testine uygulanmaz; bütün geçiş öncesi/sonrası veriler değerlendirilir.

Geçiş süresi ≤100 ms, geçiş çevresinde paket aralığı ≤250 ms tanısal kabul sınırlarıdır. Mevcut ideal RRC modeli gerçek şebekenin kesinti süresini ölçmez. Tüm karar kuralları koşudan önce plan.json dosyasına yazıldı.

## Doğrulama sonuçları

Handover kapalı tam S0 koşusunun altı CSV dosyası eski sonuçla aynı içerikte çıktı; yalnız CRLF/LF biçimi normalize edildi.

| Hareketli örnek | Handover | İlk saha | Son saha | Başlayan / biten | Geçiş süresi (ms) | Geçiş çevresinde en büyük paket aralığı (ms) | Kontrol |
|---|---|---|---|---|---:|---:|---|
| 701 | Kapalı | SITE_000441 | SITE_000441 | 0/0 | — | — | Geçti |
| 701 | A3 açık | SITE_000441 | SITE_000443 | 1/1 | 4.213 | 120.000 | Geçti |
| 702 | Kapalı | SITE_000441 | SITE_000441 | 0/0 | — | — | Geçti |
| 702 | A3 açık | SITE_000441 | SITE_000443 | 1/1 | 4.213 | 120.000 | Geçti |
| 703 | Kapalı | SITE_000441 | SITE_000441 | 0/0 | — | — | Geçti |
| 703 | A3 açık | SITE_000441 | SITE_000443 | 1/1 | 4.213 | 120.000 | Geçti |

| Tam S0, A3 açık | Bağlanan ölçüm kullanıcısı | Veri alan | Hücresi korunan toplam kullanıcı | En büyük RSRP değişimi (dB) | Kontrol |
|---|---:|---:|---:|---:|---|
| 701 | 256/256 | 256/256 | 328/328 | 0.00000000 | Geçti |
| 702 | 256/256 | 256/256 | 328/328 | 0.00000000 | Geçti |
| 703 | 256/256 | 256/256 | 328/328 | 0.00000000 | Geçti |

**Sonuç: S0 için isteğe bağlı X2 + A3 RSRP handover doğrulandı.**

Hareket testinde geçiş emri verilmedi; A3 algoritması ölçüm koşuluyla otomatik karar verdi. UE ve eNB başlangıç/bitiş olayları, hedef hücre, paket alışları ve son bağlantı birlikte kontrol edildi.

Kaydedilen süreler mevcut ideal RRC modeline aittir; gerçek operatör gecikmesi veya deprem altında başarı oranı değildir. İki sahalık testte diğer 22 saha ve yük kullanıcıları yoktur. Tam S0 testleri sabit kullanıcılıdır; bu deney, tam ağda hareket/arıza/UAV performansını ayrıca kanıtlamaz. Frekanslar arası handover eklenmedi.

Yeni özellik varsayılan olarak kapalıdır; kaynak S0 ve eski deney dosyaları değiştirilmedi. Ayrıntılı olaylar simulation/results altındaki handover_events.csv, serving_timeline.csv ve hareket koşularının packet_rx.csv dosyalarındadır.
