# 3. aşama: radyo karşılaştırması ve duyarlılık kontrolü

Bu aşamadaki deneyler tamamlandı. Bu, gerçek operatör ağının doğrulandığı anlamına gelmez; aşağıda ölçülen uyum ve sınırlar ayrı verilir.

## Ne yapıldı?

- Konumları sabit tutulan 64 kullanıcı cihazıyla (UE) deneyler yapıldı. Üç farklı cihaz yerleşiminin her biri, üç farklı sinyal yayılım modeliyle denendi. Böylece toplam dokuz senaryo karşılaştırıldı.
- 5 saha ayar seçimi, 3 saha son kontrol için ayrıldı. Seçim yalnız eğitim RSRP hatasını kullandı; SINR ve RSRQ ayarlanmadı. İlk S0 analizinde bütün sahalar görülmüştü; bu kontrol yeni arama için ayrılmıştır, kör dış doğrulama değildir.
- Anten yönleri için 42/7/99 örneklemeleri karşılaştırıldı. Komşu eklerken aynı UE konumları ve ortak sahaların anten yönleri korundu. 0,5–2 km ve 1–4 km kümeler ile ana sahaların dışbükey zarfında uniform yerleşim kullanıldı; bunlar gerçek UE dağılımı değildir.
- Komşu saha sayısı artırıldı; son koşu 2 yerine 4 saniye ve küçük UDP trafiğiyle tekrarlandı. Ana envanterde bulunmayan 553/554/555 konumlarını çıkarmanın etkisi ayrıca ölçüldü.
- İki yerel RSRP izi karşılaştırıldı; %95 fark 0.000000 dB. RSRQ ve ölçülen en güçlü hücreye göre hizmet hücresi farkı da kaydedildi.

## Saha ortalamaları nasıl hesaplandı?

Simülasyonda önce her cihazın zaman içindeki geçerli RSRP, SINR ve RSRQ değerlerinin ortalaması alındı. Daha sonra aynı sektöre bağlanan cihazların ortalamaları, her cihaza eşit ağırlık verilerek birleştirildi. Buradaki sektör, simülasyonda sahanın belirli bir yöne hizmet vermesi için oluşturduğumuz anten bölümüdür; gerçek verideki bir hücreyle bire bir eşleştirilmiş değildir.

Sahanın sonucunu bulmak için o sahadaki sektör ortalamalarının ortalaması alındı. Yalnızca cihaz bağlanan ve ilgili metrik için geçerli sonuç üreten sektörler hesaba katıldı. Her sektör saha ortalamasına eşit katkı yaptı. Örneğin bir sektöre iki, diğerine on cihaz bağlansa bile bu iki sektörün ortalamaları saha hesabında eşit ağırlık taşıdı. Cihaz bağlanmayan sektörlere sıfır değeri verilmedi.

Experia verisinde ise önce her hücrenin mevcut saatlik kayıtlarının ortalaması alındı. Ardından aynı sahaya ait hücre ortalamaları, her hücreye eşit ağırlık verilerek birleştirildi. Daha fazla saatlik kaydı bulunan bir hücre, sırf bu nedenle saha ortalamasında daha fazla ağırlık almadı.

Karşılaştırmada bu iki yöntemle hesaplanan saha ortalamaları kullanıldı. Ancak simülasyondaki cihaz konumları varsayımsaldır; Experia kayıtlarının kaç kullanıcıyı ve hangi kullanıcı konumlarını temsil ettiğini bilmiyoruz. Bu nedenle ortalamaların yakın çıkması, gerçek kullanıcıların tamamının aynı sinyal koşullarını yaşadığını göstermez.

## Sonuç

| Gösterge | Sonuç |
|---|---|
| Eğitimden seçilen yerleşim / model | wide-clusters / log3 |
| Son topoloji | 8 ana + 16 komşu saha; saha başına 3 sentetik sektör |
| Eğitim RSRP saha MAE | 3.92 dB |
| Ayrılmış kontrol RSRP saha MAE | 3.86 dB |
| Ayrılmış kontrol SINR / RSRQ saha MAE | 9.97 / 5.42 dB; bu metriklerde uyum doğrulanmadı |
| Bütün sahalarda en büyük mutlak RSRP hatası | 7.57 dB; 5 dB hedefi tek tek saha değil ortalama hata içindir |
| Kapsanan eğitim / kontrol sahası | 5/5 ve 3/3 |
| Önceden yazılan 5 dB kontrol hedefi | geçti |
| Son koşuda bağlanan / DL alan UE | 64/64 ve 60/64 |
| 4 saniyelik koşunun gerçek çalışma süresi | 72.8 saniye |
| Buffer kontrolü | iki ardışık genişletmede eşikler sağlandı |
| Yalnız süre: 2 saniyeden 4 saniyeye uzatma | RSRP %95 değişim 0.000 dB; SINR 0.000 dB |
| Yalnız UDP probu: aynı 4 s | RSRP %95 değişim 0.000 dB; SINR 0.000 dB |
| Belirsiz 3 konum çıkarıldığında | RSRP %95 değişim 8.003 dB; aynı hizmet sektörü %87.5 |

5 dB hedefi bir mühendislik tanı eşiğidir; operatör onayı değildir. Buffer için %95 mutlak RSRP/SINR değişimi ≤1 dB ve aynı hizmet sektörü oranı ≥%95 şartları iki ardışık genişletmede arandı. Yakınsama yalnız seçilen model, UE yerleşimi ve azimut örneklemesi için kontrol edildi; yük/konfigürasyon değişirse yeniden sınanmalı. [Deney planı](experiment_plan.json) koşulardan önce yazıldı; süre ve UDP etkisini ayıran ek kontrol sonradan ayrıca belirtildi. [Tam sonuç](study_result.json) hesapları içerir.

## Görseller ve tablolar

- [Yerleşim / model taraması](training_comparison.png), [aday sonuçları](training_candidates.csv).
- [Saha bazında RSRP, SINR, RSRQ](final_site_comparison.png), [sayısal karşılaştırma](final_site_comparison.csv).
- [Buffer yakınsaması](buffer_convergence.png), [tablosu](buffer_convergence.csv), [azimut grafiği](azimuth_sensitivity.png), [azimut tablosu](azimuth_sensitivity.csv).
- [UE noktalarındaki radyo haritası](final_ue_map.png), [UE sonuçları](final_ue_metrics.csv).
- [Dondurulan yapılandırma](frozen/configuration.json), [sahalar](frozen/sites.csv), [UE konumları](frozen/ues.csv).

## Sınırlar ve kullanım

Üç sektör/tek taşıyıcı politikası, düz zemin, bilinmeyen UE örneklemi, anten gücü ve açıları varsayımdır. Shadowing/fading yoktur. COST231 seçeneği kurulu OkumuraHata modelinin 1,5 GHz üstü MediumCity dalıdır; kırsal arazi modeli sayılmaz, kısa/çok uzun bağlantılarda model aralığının dışına taşabilir. SINR kontrol kanalı girişiminden, RSRQ yerel UE ölçüm izinden alınır; Experia'nın kanal/örnekleme tanımlarıyla eşdeğerlik doğrulanmadı. TAAVG mesafeye çevrilmedi, 2025 trafik dönemiyle 2026 radyo dönemi birleştirilmedi.

Kaynakları belirsiz üç koordinatın etkisi raporlandı; bu konumların doğruluğu kanıtlanmış olmadı. Gerçek hücre sınırları veya arızalar çıkarılmadı. Başlangıç senaryosu ve belirsizlik aralığı sonraki kontrollü deneylere girdi sağlar; kalan tanım/envanter soruları hocaya sorulacak.

## Tekrar üretim

Windows Python: `python analysis/prepare_radio_study.py`. İlk derleme: `simulation/run_baseline.py --name stage3/smoke` WSL altında. Ardından WSL Python ile `simulation/run_radio_study.py`; mevcut geçerli sonuçları tekrar kullanır. Son olarak Windows Python: `python analysis/report_radio_study.py`. WSL yolları [simülasyon notunda](../../../simulation/README.md). Plan, girdiler, kaynak hash'leri ve arşivlenen C++ dosyası korunur. Eski S0 sonuçları ayrıca saklandı.
