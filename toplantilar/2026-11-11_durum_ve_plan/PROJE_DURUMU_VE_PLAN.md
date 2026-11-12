# Proje durumu ve hocayla görüşme — 11 Kasım 2026

> **12 Kasım güncel sonuç:** Hocanın 8 ana + 8 komşu sahası güncel envanterle doğrulandı ve korundu. Yeni yakın sahalarla yedi simülasyon koşusu tamamlandı; komşu genişletmeleri ve üç kullanıcı örneğinin eski–yeni kontrolleri geçti. Güncel 24 sahada kontrol MAE: RSRP 2,96 / SINR 3,63 / RSRQ 4,07 dB. [Sonuçlar ve grafik](../../deneyler/07_guncel_envanter_kontrolu_2026-11-12/SONUCLAR.md) — [Hocaya güncel mesaj](../2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/HOCAYA_MESAJ.md). Aşağıdaki 516 saha/eksik koordinat ifadeleri ve eski tablolar tarihsel sürümdür; güncel envanter 563 saha / 6.475 hücredir.

**Neredeyiz?** Sındırgı için bu PC'de çalışan, saha konumlarına dayanan ve Experia radyo ölçümleriyle karşılaştırılan bir LTE/EPC başlangıcı var. Bilinmeyen ayarlar için geniş bir tarama ve tekrar çalışmaları tamamlandı. Seçilen ayar kayıtlı. Gerçek KPI ile yük modeli, hizmet yetersizliği/stres, öncelikli bölge ve rota aşamaları henüz tamamlanmadı. Radyo başlangıcının bu aşamalara geçiş için yeterliliğini hocayla değerlendireceğiz.

Bu not 10 Kasım'da tamamlanan deneyleri bir araya getirir; 11 Kasım'da yeni simülasyon koşusu yapılmış gibi sunulmaz.

## Hocanın istediği ve karşılığı

Doğrudan kaynak: [advisors notes.txt](../../ana_proje/advisors%20notes.txt). Hoca, taslağı ChatGPT ile hazırlattığını ve kendi notlarını kırmızı yazdığını söylüyor. Bu nedenle taslaktaki bütün örnek değerleri hocanın kesin şartı saymıyoruz.

Hocanın iki kısa ifadesi: “once baseline bir calissin”; “koordinatlari cekip harita uzerine yerlestirin net gorelim”. Ağ kurulduktan sonra yük üretimi, stres, öncelikli bölge ve rota atamasına ilerlemeyi tarif ediyor. Gerçek konfigürasyon paylaşılmadığı için varsayımlar ve deneme yanılma bekliyor.

| Beklenti | Yaptığımız | Durum / açık kalan |
|---|---|---|
| Seçilen koordinatları kontrol et | Ana envanter ve ilk 16 saha seçimi karşılaştırıldı, metre cinsinden yerel koordinatlara çevrildi ve haritalandı | İlk 16'nın 13'ü ana envanterde; 553/554/555 yalnız seçim eklerinde. Kaynak teyidi açık |
| ns-3 sürümü ve LTE ağını çalıştır | ns-3.44 klasik LTE/EPC, otomatik ilk hücre seçimi ve veri akışı çalıştı; bu PC'de yeniden üretim kontrolü geçti | Çalışan başlangıç var |
| RSRP vb. çıktıları Experia ile karşılaştır | Saha bazında RSRP/SINR/RSRQ hedefleri ve hatalar hesaplandı | Karşılaştırma var; tüm sahalarda/metriklerde uyum sağlanmadı; ölçüm tanımları açık |
| Bilinmeyen ayarlar için alternatif dene | Kullanıcı, anten, güç, yayılım, gölgeleme, alıcı gürültüsü, trafik, sektör ve taşıyıcı alternatifleri tarandı | Geniş pilot tamamlandı; gerçek sektör/taşıyıcı konfigürasyonu tespit edilmiş değil |
| Komşu sınırının etkisini kontrol et | 24→32→48 toplam saha, aynı kullanıcı/ortak anten örneğiyle karşılaştırıldı | Seçilen düşük yük koşulunda kontroller geçti |
| Yük üretimi ve stres | Kısa sentetik UDP yük duyarlılığı denemeleri yapıldı | KPI ile yük kalibrasyonu ve kapsamlı stres/hizmet değerlendirmesi yapılmadı |
| Öncelikli bölgeler, rota, sonraki senaryolar | Çalışma sırası taslakta var | Henüz uygulanmadı; şehir merkezi/deniz kenarı ve UAV ile hizmet iyileştirme ileriki aşama |

## Elimizdeki somut çıktılar

1. **Denetlenmiş veri özeti:** 516 saha / 5.721 hücre koordinat envanteri; 851.003 Experia kaydı; 5.694.304 KPI kaydı. Experia Haziran 2026, KPI 2025'teki günler: eşzamanlı radyo–trafik verisi olarak birleştirmiyoruz. [Veri özeti](../../ana_proje/01_VERI_VE_PROJE_OZETI.md).
2. **Konum karşılaştırması:** [harita görseli](../2026-11-10_toplanti_sunumu/01_konum_kontrolu.png). Bu görsel hocanın ilk 16 saha seçimini gösterir; son 24 sahanın tamamı değildir. 554 değerlendirme, 553 ve 555 komşu sahadır. Bu üç konum seçim dosyasında mevcut; özgün kaynağının teyidi eksik.
3. **Çalışan ve kayıtlı senaryo:** 8 değerlendirme + 16 komşu = 24 saha; 72 varsayımsal sektör; 64 sabit sanal kullanıcı. Seçilen radyo ayarları: 2–6 km kullanıcı kümeleri, 120° yatay anten genişliği, sektör başına 49 dBm, log-distance üs 3, NF 9 dB, gölgeleme kapalı, Band 3 / 20 MHz, mixed CQI, kullanıcı başına 50 ms UDP aralığı. [Seçilen senaryo ve girdiler](../../deneyler/06_genis_tarama_secilen_ayar_2026-11-10/selected_scenario/configuration.json).
4. **Deney karşılaştırması:** son kampanyada 51 tarama çalıştırması, bunlardan 49 geçerli koşul; 4 aday × 3 ortak tekrar; 3 uzun/komşu doğrulaması. İki Band 8 koşusu genişlik hatası nedeniyle elendi ve doğru genişlikle yeniden çalıştırıldı. Yazılım/tanı kontrolleri de eklenince toplam 70 çalıştırma; bu, 70 ayrı model alternatifi demek değildir. Önceki 135 analitik ön eleme bu sayıya eklenmedi. [Deney raporu](../../deneyler/06_genis_tarama_secilen_ayar_2026-11-10/SONUCLAR.md).
5. **Bu PC'de çalışma kanıtı:** ana veri özetleri ve önceki senaryonun karşılaştırılan çıktıları yeniden üretildi; son geniş kampanya da bu PC'de tamamlandı. [PC kontrolü](../../pc_validation/20261110_pc/verification.json), [son kampanya kontrolleri](../../deneyler/06_genis_tarama_secilen_ayar_2026-11-10/checks.json), [çalıştırma rehberi](../../CALISTIRMA_REHBERI.md).

Kaynak Excel'ler ve özgün başlangıç C++ kodu korunuyor. Son seçilen deney, `deneyler/06_genis_tarama_secilen_ayar_2026-11-10/` altında ayrı kayıtlı; eski ana paket raporları tarihsel sonuçları anlatır.

## Denemelerden ne öğrendik?

**Önceki aday, üç ortak tekrarda eğitim hatası ve oynaklık birlikte değerlendirildiğinde ilk sırada kaldı.** Yeni seçenekleri denemek ayarı mutlaka değiştirmek anlamına gelmedi; ayarın alternatifler karşısındaki davranışını görmüş olduk.

Örnek: 4 dB gölgeleme eklenen aday ilk kısa taramada çok iyi çıktı. Üç yeni örnekte eğitim puanı ortalaması 3,21, standart sapması 0,55 oldu. Önceki adayda bunlar 3,14 ve 0,12 oldu. İlk güzel denemeyi seçmek yerine ortak tekrarlardaki davranışı kullandık. Bu yalnız denenen koşullar için bir seçimdir; bütün olası modellerin en iyisi olduğu iddiası yok.

Seçim beş eğitim sahasında yapıldı; kalan üç saha kontrol karşılaştırmasında kullanıldı. Bu üç saha daha önce görüldüğünden kör doğrulama değildir. Eğitim puanı, üç metrik MAE'sinin ortalaması ve eksik saha cezasıdır; son seçim ayrıca tekrarlar arası oynaklığı dikkate alır.

| Kontrol sahalarındaki hata (dB; düşük daha yakın) | Üç tekrarın ortalaması ± std | Önceden seçilen ilk örnekte 8 s |
|---|---:|---:|
| RSRP — sinyal gücü | 2,96 ± 0,83 | 2,14 |
| SINR — girişim/gürültüye göre sinyal | 3,64 ± 1,38 | 5,20 |
| RSRQ — alınan sinyal kalitesi | 4,08 ± 0,21 | 3,80 |

± değerleri yalnız üç tekrarın standart sapması; güven aralığı değildir. 8 s sütunu ayrı bir örnektir. Sekiz saha içindeki en büyük mutlak hatalar bu uzun koşuda RSRP/SINR/RSRQ için 7,58 / 10,06 / 4,39 dB: özellikle SINR'de bazı sahalar uzak kalıyor. “Bütün sahalar yakın” diyemeyiz.

64 kullanıcının tamamı seçilen adayın tekrarlarında ve son uzun koşularda bağlanıp veri aldı. 24→32 ve 32→48 saha genişletmelerinde kullanıcı başına mutlak SINR değişiminin %95 yüzdeliği 0,192 ve 0,145 dB; RSRP değişimi sıfır; aynı hizmet sektörü %100. 4→8 s kontrolü de geçti. Bunlar seçilen düşük yük koşulunun sayısal kararlılığını destekler; gerçek kapasiteyi veya bütün yüklerde yeterliliği kanıtlamaz.

## Açık kalanlar ve önemleri

- **Üç ek koordinatın kaynağı:** 553/554/555 konumlarını kullandık; ana envanterden doğrulayamıyoruz. Hocadan özgün kaynak istenecek.
- **Sektör ve taşıyıcı ayrımı:** gözlenen hücre sayısı doğrudan anten yönü sayısı değildir. Bir/iki sektör alternatifleri ve farklı ortak frekanslar denendi; aynı anda çok taşıyıcılı gerçek ağ temsili henüz yapılmadı.
- **Experia ölçüm tanımı:** mixed seçimi SINR karşılaştırmasını değiştirdi. Bu yalnız açıklanmamış fiziksel girişim farkı değildir; ölçülen/raporlanan SINR türü de değişiyor. İlk tek koşudaki 1,56 dB SINR hatası güncel genel sonuç olarak sunulmamalı.
- **Kullanıcı örneklemi:** 64 sanal kullanıcı bazı sahalarda yalnız 1–2 örnek bırakıyor. Saha ortalamaları yerleşime duyarlı; daha yoğun örneklem sınanmalı. Sürekli ve doğrulanmış gerçek kapsama sınırları çıkarılmış değil.
- **TAAVG ve KPI tanımları:** TAAVG açıklanmadan mesafeye çevrilmedi. Throughput, trafik hacmi, kullanıcı ve PRB alanlarının birimleri/ortalamaları yük modelinde dikkatle ele alınmalı. Taşınan trafik, sunulan talebin tamamı değildir.
- **Başarı ölçütü:** önceki 5 dB RSRP ve komşu değişimi eşikleri çalışma içi tanı ölçütleridir; hocanın/operatörün onayı değildir. Sonraki aşamaya geçiş için hangi hata ve duyarlılığın yeterli olduğu netleşmeli.

## Yapılacaklar — önerilen sıra

Bu sıra çalışma önerimizdir; hocanın henüz verilmemiş bir kararı gibi sunulmaz.

- [x] Veri/konum denetimi ve uyuşmazlık listesi.
- [x] Bu PC'de çalışan LTE/EPC başlangıcı ve yeniden üretim kayıtları.
- [x] Experia ile radyo karşılaştırması, alternatif ayarlar ve ortak tekrarlar.
- [x] Seçilen ayarın komşu/süre kontrolleri, ayar ve girdilerin saklanması.
- [x] Güncel durumu hocanın beklentileriyle eşleyen bu not.
- [ ] **Yakın teknik adım:** aynı seçilen ayarda 64→128→256 kullanıcı örneklemini, toplam sunulan yük sabit kalacak biçimde sınamak; saha başına örnek sayısını, metrik değişimini ve çalışma süresini raporlamak. Her basamak uygun küçük testle başlatılmalı. Amaç, bir sahadaki sonucun az sayıda kullanıcıya bağımlı olup olmadığını görmek.
- [ ] **Yük aşamasının hazırlığı:** seçilen bölgenin KPI trafik/kullanıcı/PRB profillerini birim ve dönem notlarıyla çıkarmak. Mevcut genel veri denetimi bunu tamamlanmış bir yük modeli yapmaz.
- [ ] **Hocayla geçiş kararı:** radyo başlangıcını açık sınırlamalarıyla sabitleyip yük pilotuna geçmek için kabul ölçütlerini belirlemek. Gerekiyorsa yalnız en etkili radyo eksiğine odaklanmak.
- [ ] **Yük pilotu:** belirlenmiş temel yük ve artan yük düzeylerinde throughput, gecikme, paket teslimi/kaybı ve PRB kullanımını ölçmek; tohum, süre ve servis ölçütlerini önceden yazmak.
- [ ] **Sonraki araştırma:** kontrollü saha kesintisi veya kapasite sınırı altında hizmet açığı haritası; ardından öncelikli bölge ve rota/UAV ile iyileştirme. Genel `region.yaml` arayüzüyle farklı bölgelerde tekrar kullanılabilir üretici de henüz tamamlandı sayılmamalı.

## Hocaya 1 dakikalık anlatım

“İstediğiniz gibi önce saha koordinatlarını kontrol ettik ve bu bilgisayarda çalışan LTE/EPC başlangıcını kurduk. İlk seçimin üç sahasının konumu ek dosyada var ama ana envanterde yok; bunların kaynağını netleştirmek istiyoruz. Bilinmeyen radyo ve kullanıcı koşulları için dokuz başlıkta 49 geçerli tarama yaptık, öne çıkan dört ayarı üçer farklı örnekte karşılaştırdık. Önceki ayar daha tutarlı kaldı. Seçilen ayarda komşu ve süre kontrolleri geçti; Experia'ya göre kontrol hataları üç tekrar ortalamasında RSRP 2,96, SINR 3,64 ve RSRQ 4,08 dB. Bazı sahalarda SINR farkı belirgin. Şimdi kullanıcı örneklemi duyarlılığını tamamlayıp bu başlangıçla yük pilotuna geçmenin uygunluğunu konuşmak istiyoruz.”

## Toplantıda gösterilecek üç görsel

1. [İlk saha seçimi / koordinat kontrolü](../2026-11-10_toplanti_sunumu/01_konum_kontrolu.png): bilinen coğrafya ve üç kaynak sorusu.
2. [Adayların ortak tekrar karşılaştırması](../../deneyler/06_genis_tarama_secilen_ayar_2026-11-10/robustness_comparison.png): neden önceki ayarın korunduğu ve metrikler arasındaki ödünleşim.
3. [Saha bazında Experia karşılaştırması](../../deneyler/06_genis_tarama_secilen_ayar_2026-11-10/final_site_comparison.png): ortalamaların arkasındaki saha farkları.

Toplantıda netleştirilecekler: üç konumun özgün kaynağı; Experia SINR/RSRQ ile TAAVG/KPI tanımları; mevcut radyo başlangıcının yeterlilik ölçütü ve yük pilotunun kapsamı. Yöntem taslağı: [main.tex](../../ana_proje/main.tex).
