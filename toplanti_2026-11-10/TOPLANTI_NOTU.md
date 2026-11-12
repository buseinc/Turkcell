# Sındırgı LTE — 10 Kasım 2026 toplantı notu

> **11 Kasım güncel durum:** [Proje durumu, hocanın beklentileri ve yapılacaklar](../toplanti_2026-11-11/PROJE_DURUMU_VE_PLAN.md). Bu dosya tarihsel deney akışını korur; aşağıdaki ilk açılış metni ve eski metrikler son seçilen ayarı anlatmaz. Toplantıya güncel durum notundan başlayın.

Amaç: mevcut başlangıç senaryosunu, ölçümlerle uyumunu ve açık kararları 5–8 dakikada anlatmak.

**Toplantıda önce açılacak güncel dosya:** [Hocaya kısa özet](HOCAYA_KISA_OZET.md).
Son kullanıcı/yayılım/güç araştırmasının seçilen adayı, bağımsız kullanıcı
örneklemi ve komşu kontrolleri bu kısa özette birlikte veriliyor.

**Öne çıkan bulgu:** Aynı düşük yüklü şebekede kontrol yerine mixed CQI
kullanılınca üç kontrol sahasındaki SINR hatası **9,97 → 1,56 dB** oldu.
RSRP, RSRQ ve bağımsız kontrol SINR'si değişmedi. Bu, yöntem tanımının
etkisini gösteriyor; Experia ile eşdeğerlik henüz doğrulanmadı. Önce
[07 numaralı görsel](07_kontrol_mixed_karsilastirma.png) ve aşağıdaki
“Ek deney: kontrol ve mixed SINR/CQI” bölümünü göstermek faydalı olabilir.

## Açılışta söylenecek

“İstediğiniz sırayla koordinatları kontrol ettik, ns-3 üzerinde LTE/EPC şebekesini
çalıştırdık ve Experia ile radyo karşılaştırması yaptık. Dokuz aday arasında
yalnız eğitim sahalarının RSRP hatasına göre seçim yaptık. RSRP başlangıç
hedefini sağladık. Ek tanıda mixed yöntemin düşük yükte SINR karşılaştırmasını
belirgin değiştirdiğini gördük; RSRQ farkı ve ölçüm eşdeğerliği sorusu devam
ediyor. Komşu saha etkisini sınadık ve senaryoyu bu bilgisayarda yeniden çalıştırdık.
Bugün açık veri sorularını ve yük aşamasına geçişteki önceliği netleştirmek istiyoruz.”

## Dört görselle anlatım

1. [Konum kontrolü](01_konum_kontrolu.png)

   “Hocanın ilk seçimi 8 ana + 8 komşu saha. İlk 16'nın 13'ü ana envanterle
   örtüşüyor. 554 ana saha; 553 ve 555 komşu saha. Bu üçünün koordinatları
   seçim dosyasında var, ana envanterde yok. Kaynağını soracağız.”

   Not: Bu görsel ilk 16 seçimin kontrolüdür; son 24 sahanın haritası değildir.
   İşaretler istasyon konumudur, kapsama veya hasar sınırı değildir.

2. [Dokuz yerleşim/yayılım adayı](02_dokuz_senaryo.png)

   “Gerçek kullanıcı konumları ve yayılım koşulları bilinmediği için üç
   varsayımsal kullanıcı yerleşimini üç yayılım seçeneğiyle karşılaştırdık.
   Beş saha ayar seçimi, üç saha kontrol için ayrıldı. Seçilen aday,
   sahaların 1–4 km çevresindeki kullanıcı kümeleri ve üs 3 log-distance modeli.”

   Not: En düşük hata, bu adaylar ve bu örneklem içindir. Gerçek kullanıcı
   dağılımını bulduğumuz anlamına gelmez. Kontrol sahaları ilk S0 analizinde
   daha önce görüldü; tamamen kör dış doğrulama değildir.

3. [Ölçüm–simülasyon karşılaştırması](03_olcum_simulasyon.png)

   “RSRP ortalama mutlak hatası eğitimde 3,92 dB, kontrolde 3,86 dB.
   Önceden belirlenen 5 dB ortalama hata hedefi sağlandı. Tek sahadaki
   en büyük hata 7,57 dB. Kontrolde SINR/RSRQ hataları 9,97/5,42 dB;
   bu iki metrikte uyumu henüz gösteremedik.”

   Basit açıklama: RSRP konuşanın ses gücü; SINR, çevredeki sesler arasında
   konuşanın ne kadar ayırt edilebildiği gibidir. Gücün uyuşması, kalitenin
   de uyuşacağını garanti etmez. Ölçüm tanımlarının eşdeğerliği belirsizdir.

4. [Komşu saha kontrolü](04_komsu_saha_kontrolu.png)

   “Ana sekiz sahayı, kullanıcıları ve ortak anten yönlerini sabit tutup
   komşu sayısını artırdık. Son seçim 8 ana + 16 komşu = 24 saha.
   Daha fazla komşu ekleyince sonuçların az değiştiğini kontrol ettik.”

   Dikkat: Grafikteki 8, 16, 24, 40 sayıları KOMŞU sayısıdır; toplam sayılar
   sırasıyla 16, 24, 32, 48'dir. 16'dan 24 toplam sahaya geçişte RSRP
   değişmedi; SINR'de %95 mutlak değişim yaklaşık 1,001 dB oldu ve 1 dB
   sınırını çok az aştı. Sonraki iki genişletmede 0,164 ve 0,288 dB çıktı;
   hizmet sektörü eşleşmesi %100 kaldı. Bu nedenle seçilen koşullarda
   toplam 24 saha yeterli kabul edildi. Bu, ölçümlerle uyumun iyileştiğini
   gösteren bir sonuç değildir.

## Mevcut senaryo ve bu bilgisayar

- 24 saha, saha başına 3 varsayımsal sektör, toplam 72 sektör ve 64 sabit sanal kullanıcı.
- Tek taşıyıcı; anten, güç, yayılım ve kullanıcı yerleşimi açık varsayımlardır.
- Son 4 saniyelik koşuda 64 kullanıcı bağlandı, 60'ı veri aldı. Bu kısa prob,
  gerçek yük deneyi veya hizmet kesintisi tespiti değildir.
- Bu bilgisayarda ayrı Python ortamı ve ns-3.44 hazırlandı. Son senaryo
  yeniden çalıştırıldı; karşılaştırılan 64 kullanıcının sektör, RSRP, SINR,
  RSRQ, bağlantı ve alınan veri değerleri eski sonuçlarla aynı çıktı.
- 12 ana Excel yeniden tarandı: 851.003 radyo kaydı ve 5.694.304 KPI kaydı.
  Temel özet tablolar önceki sonuçlarla uyuştu. Harita çevrimdışı test edildi.
- Tam tarihsel deney kampanyası bu PC'de yeniden koşturulmadı; son senaryo
  ve küçük çalışma testleri yeniden koşturuldu.

## Hocaya sorulacaklar

| Öncelik | Soru | Neyi etkiliyor? |
|---|---|---|
| 1 | 553/554/555 koordinatları ve hücre–saha bağlantıları hangi kaynaktan alındı? | Biri ana saha; üç konumu çıkarmanın RSRP etkisi önemli. |
| 2 | Biz kontrol kanalı SINR'si ölçüyoruz. Experia SINR/RSRQ hangi kanal, örneklem ve ortalama tanımıyla üretiliyor? | Aynı tanımları karşılaştırıp karşılaştırmadığımızı belirlemek. |
| 3 | İlk seçimdeki ölçüm özetleri hangi dönem/filtreyle üretildi? Anonim hücre kimlikleri dosyalar ve yıllar arasında ortak mı? | Seçim özetindeki kayıt farkı ve kaynakları ilişkilendirmek. |
| 4 | TAAVG, throughput, trafik hacmi ve aktif kullanıcı alanlarının tam birim/tanımları nedir? Ek anten/taşıyıcı bilgisi alınabilir mi? | Mesafe yorumu, radyo varsayımları ve sonraki yük modeli. |

Not: 2025 KPI ile 2026 Experia eşzamanlı gözlemler gibi birleştirilmedi.
Seçim dosyası aynı 96 hücre için 11.312, tam Experia dönemi 14.363 kayıt
içeriyor. Bu, dönem/filtre sorusudur; doğrudan hata kanıtı değildir.

## Toplantıdan çıkarmak istediğimiz karar

Önerimiz: RSRP sonucu kabul edilebilir bir başlangıç olarak korunurken,
SINR/RSRQ tanımları ve sektör/taşıyıcı varsayımlarının etkisi incelensin.
KPI birimleri netleşirken seçilen bölgenin trafik profili de hazırlansın.

Hocayla netleştirilecek üç karar:

1. Bir sonraki öncelik radyo kalitesi farkını açıklamak mı, mevcut varsayımlarla
   sınırlı bir yük pilotuna başlamak mı?
2. İki hücre gözlenen sahalarda 1–2 sektör pilotu tamamlandı (aşağıda).
   Sonraki radyo deneyi farklı kalan anten yönleri veya taşıyıcı alternatifleri mi olsun?
3. İlk 1×/10× sentetik yük duyarlılığı pilotu, üç anten genişliğiyle altı
   koşulda tamamlandı (aşağıda). Gerçek KPI profiline uyarlama, daha uzun
   süreler ve hız/gecikme/paket teslimi kabul ölçütleri nasıl belirlensin?
   Bunlar henüz tamamlanmış bir yük veya stres doğrulaması değildir.

Sonraki adımlar: yük pilotu → kademeli stres → ayrı istasyon kesintisi
deneyleri → öncelikli bölgeler ve UAV/rota çalışmaları.

## Toplantı öncesi ek deney: iki sahada sektör sayısı

[Yeni görsel](05_sektor_sayisi_pilotu.png) —
[Yöntem, sınırlar ve ayrıntılı sonuçlar](../experiments/sector_sensitivity_2026-11-10/SONUCLAR.md).

Hocanın kırmızı notundaki üç sektör varsayımını incelemek için yalnız
`SITE_000482` ve `SITE_000554` sahalarında üç, iki ve bir etkin sektör denendi.
Diğer 22 saha ve aynı 64 kullanıcı korundu. Kalan antenler aynı yön, güç ve
65° genişlikte tutuldu. Önce yeni kodun üç sektörlü durumu eski sonuçlarla
64 kullanıcıda sıfır farkla yeniden ürettiği doğrulandı.

| 482 ve 554'te sektör sayısı | Aynı 64 UE'de ortalama SINR değişimi | Kontrol sahaları SINR MAE | Sonuç üreten ana saha | Kısa koşuda DL alan UE |
|---|---:|---:|---:|---:|
| 3 — başlangıç | 0 dB | 9,97 dB | 8/8 | 60/64 |
| 2 | −0,50 dB | 10,57 dB | 8/8 | 57/64 |
| 1 | −0,69 dB | 10,39 dB | 7/8 | 57/64 |

**Bulgu:** Bu pilot sektör azaltmayı bir iyileştirme olarak benimsemek için
destek vermedi. Aynı kullanıcıların ortalama SINR'si düştü ve kontrol
sahalarındaki hata büyüdü. Başlangıçta bu iki sahadan hizmet alan aynı
15 kullanıcıda ortalama SINR değişimi sırasıyla −2,64 ve −4,98 dB oldu.

Bir sektörlü durumda 554 sahasına hiç kullanıcı bağlanmadı. Bu durumda
bütün mevcut sahaların ortalama hatasının düşmesi, daha iyi model kurulduğu
anlamına gelmiyor: zor bir saha ortalamadan çıkıyor ve kullanıcılar başka
sahalara geçiyor. Bu yüzden aynı kullanıcı konumlarını ayrıca karşılaştırdık.

Toplantıda söylenecek: “İki hücreli sahalardaki sektör varsayımını da
kontrol ettik. Bu belirli sektör kaldırma düzeni kalite sorununu çözmedi;
ortalama hata yanında kullanıcıların hangi sahaya geçtiğini de izlemek gerekiyor.”

Sınır: Yalnız bir kalan yön düzeni ve mevcut 24 saha denendi; tek sektör
tek bir yönlü antendir. Gerçek anten düzeni veya çok taşıyıcılı yapı doğrulanmadı.
Başlangıç senaryosu değiştirilmedi.

## Ek araştırma: SINR'de sinyal, girişim ve gürültü ayrımı

[Yeni görsel](06_sinyal_girisim_gurultu.png) —
[Basit sonuç anlatımı](../experiments/sinr_diagnostics_2026-11-10/TANI_SONUCLARI.md) —
[Teknik kaynak incelemesi](../experiments/sinr_diagnostics_2026-11-10/OLCUM_HESABI.md).

Mevcut senaryoya pasif gözlemciler ekleyerek S (istenen sinyal), I (girişim)
ve N (alıcı gürültüsü) ayrı çıkarıldı. Eklenen izler başlangıç sonuçlarını
değiştirmedi. Isınma sonrası 1.984 örnekte bileşenlerden hesaplanan RSRP/SINR,
yerel izlerle sayısal hassasiyet düzeyinde uyuştu; RSRQ da bağımsız yeniden üretildi.

- **64/64 kullanıcıda girişim gürültüden büyük.**
- **30/64 kullanıcıda SINR < 0 dB**; bu 30 kullanıcının hepsinde istenen sinyal
  gürültüden büyük, fakat girişim+gürültü toplamından küçük.
- **61/64 kullanıcıda girişimin çoğu başka sahalardan geliyor.** Anten ve
  yayılım formülüyle hesaplanan sektör güç toplamı doğrudan gözlemle doğrulandı.
- Kullanıcılar arası medyan S/N **10,99 dB**, medyan SINR **0,63 dB**.
  S/N, girişimi kapatıp koşturulan başka bir şebeke değil, aynı sinyalin yalnız
  gürültüye oranıdır. Sıfır dB bir hizmet kabul eşiği olarak kullanılmadı.

Somut örnek: 444 sahasına bağlı sanal kullanıcı 7'de S/N **11,37 dB**, SINR
**0,71 dB**; en güçlü girişim kaynağı 480 sahası.

**Ölçüm tanımı:** Kaydettiğimiz SINR, kontrol kanalı sinyali ve kontrol
kanalı girişimini kullanıyor. ns-3'ün bu yöntemi komşuların veri yükünden
bağımsız kontrol girişimini içeriyor. Experia'nın aynı tanımı kullandığını
bilmiyoruz. İncelenen birim dönüşümlerinde hata bulunmadı; gerçek ağla eşdeğerlik
kanıtlanmadı. Bütün sektörlerin aynı taşıyıcıda olması hâlâ varsayım.

Toplantıda söylenecek: “SINR farkını yalnız sayı olarak bırakmadık; kendi
simülasyonumuzda nereden geldiğini ayırdık. Seçtiğimiz aynı frekanslı kontrol
kanalı senaryosunda girişim baskın. Experia'daki SINR ile hangi tanım ve
taşıyıcı varsayımı üzerinden karşılaştırma yapmamız gerektiğini netleştirmek istiyoruz.”

## Ek deney: kontrol ve mixed SINR/CQI

[Yeni görsel](07_kontrol_mixed_karsilastirma.png) —
[Ayrıntılı sonuç ve sınırlar](../experiments/mixed_cqi_2026-11-10/SONUCLAR.md).

Aynı 24 saha, 72 sektör, 64 kullanıcı ve düşük UDP yükünde yalnız CQI
yöntemi değiştirildi. Ek pasif izlerle her iki koşuda kontrol SINR'si de
bağımsız kaydedildi. Yeni kontrol kodu eski sonucu sıfır farkla yeniden üretti.

| Gösterge | Kontrol | Mixed |
|---|---:|---:|
| 3 kontrol sahası SINR MAE | **9,97 dB** | **1,56 dB** |
| 3 kontrol sahası RSRQ MAE | 5,42 dB | 5,42 dB |
| Kullanıcılar arası medyan raporlanan SINR | 0,63 dB | 9,74 dB |
| Pasif kontrol SINR medyanı | 0,63 dB | 0,63 dB |
| Kısa koşuda DL alan kullanıcı | 60/64 | 64/64 |

RSRP/RSRQ ve hizmet saha/sektörleri aynı kaldı. Kontrol girişimi fiziksel
olarak azalmadı. Mixed, veri kanalı girişimini kullanan farklı bir hesap;
CQI geri bildirimi değiştiği için zamanlayıcı kararları da etkilenebilir.

Mixed örneklerinin %88,46'sında yeni veri girişim güncellemesi yoktu;
bu çağrılarda ns-3 yalnız gürültüyü kullandı. Bu, düşük yükteki yakınlığın
yorumlanması için kritik. Bütün şebekenin zamanın bu oranında boş olduğu
sonucu çıkarılmadı. Daha yüksek yük denenmedi.

**Güncel bulgu:** Ölçüm yöntemi, SINR karşılaştırmasını belirgin etkiliyor.
Mixed bu koşuda Experia'ya daha yakın; ölçüm eşdeğerliği hâlâ belirsiz,
RSRQ farkı devam ediyor. Yeni bir kör kontrol veya operatör doğrulaması değil.
Başlangıç senaryosu korundu, mixed ayrı bir alternatif olarak kaydedildi.

Hocaya soru: “Experia'nın SINR'si hangi kanal ve örneklem üzerinden hesaplanıyor;
bizim kontrol veya mixed çıktımızla karşılaştırılması uygun mu?”

## Ek tarama: üç metriğe birlikte yaklaşan bir aday

[Saha karşılaştırması](08_ortak_radyo_taramasi.png) —
[Altı koşulun puanları](09_tarama_puanlari.png) —
[Tam sonuçlar](../experiments/radio_joint_search_2026-11-10/SONUCLAR.md).

Mixed yöntemde anten genişliği 65°/90°/120° ve sentetik sunulan yük 1×/10×
olarak altı koşul denendi. Aynı 24 saha ve 64 kullanıcı korundu. Seçim kuralı
koşulardan önce yazıldı: beş eğitim sahasında üç metrik MAE'sinin eşit ağırlıklı
ortalaması; eksik sahaya ceza. Kontrol sahaları sıralamaya alınmadı.

Eğitim puanı 65° düşük yükte **3,702**, 90° düşük yükte **3,540**, 120° düşük
yükte **3,492** oldu. Bu kurala göre 120° düşük yük seçildi; toplam puandaki
azalma yaklaşık **%5,7** ve mütevazı. Üç düşük yük adayı arasındaki kontrol
sonuçları:

| Kontrol sahalarında MAE | 65° başlangıç mixed | 90° düşük yük | 120° düşük yük — eğitimden seçilen |
|---|---:|---:|---:|
| RSRP | 3,86 dB | 2,49 dB | **2,24 dB** |
| SINR | **1,56 dB** | 2,29 dB | 3,09 dB |
| RSRQ | 5,42 dB | 4,99 dB | **4,62 dB** |

**Yorum:** Daha geniş anten RSRP/RSRQ karşılaştırmasını biraz iyileştirdi;
SINR karşılaştırması kötüleşti. Yükü 10 kat artırmak her üç anten genişliğinde
ortak eğitim puanını kötüleştirdi. Altı koşulun tamamında 64 kullanıcı bağlandı
ve veri aldı; bu kısa süreli pilot gerçek hizmet kapasitesi doğrulaması değildir.

Bu, “tek doğru konfigürasyonu bulduk” sonucu değil. Ölçümlere yaklaşan birkaç
aday ve aralarındaki ödünleşim elde edildi. Özgün başlangıç korundu; yeni aday
ayrı `selected_candidate.json` dosyasında saklandı. Yeni kullanıcı/azimut
örnekleri ve komşu yakınsaması seçilen adayda yeniden sınanmadı.

## Son araştırma: kullanıcı dağılımı, yayılım ve güç

[Yeni karşılaştırma](10_kullanici_yayilim_arastirmasi.png) —
[Sabit sahalar ve varsayımsal kullanıcı örneklemleri](11_kullanici_yerlesimleri.png) —
[Tam sonuçlar](../experiments/placement_propagation_2026-11-10/SONUCLAR.md).

135 olasılık analitik olarak ön elendi; bunlar gerçek ns-3 koşusu sayılmadı.
Ön eleme hesabının RSRP/RSRQ'su önceki native sonuçla yaklaşık 10⁻⁹ dB
düzeyinde uyuşuyor, SINR ön elemesi ise yalnız S/N yaklaşımı. Ardından beş
gerçek seçim koşusu ve üç takip koşusu yapıldı.

Verideki saha konumları, eşlemeler ve hedef ölçümler korundu. Yalnız bilinmeyen
kullanıcı yerleşimi, anten, yayın gücü ve yayılım hipotezleri değiştirildi.
Seçim yine yalnız beş eğitim sahasının üç metrik puanıyla yapıldı.

Seçilen aday: **kullanıcılar ana saha çapaları çevresinde 2–6 km kümelerde,
120° anten, sektör başına 49 dBm, log-distance üs 3, mixed ve düşük UDP yükü**.
Bu gerçek kullanıcı konumlarının veya operatör ayarlarının bulunduğu anlamına gelmez.

| Kontrol sahalarında MAE | Önceki 120° / 46 dBm aday | Yeni aday | Aynı yeni ayar, farklı kullanıcı örneklemi |
|---|---:|---:|---:|
| RSRP | 2,24 dB | 3,55 dB | 3,78 dB |
| SINR | 3,09 dB | 1,82 dB | 1,47 dB |
| RSRQ | 4,62 dB | 3,23 dB | 3,77 dB |

Eğitim puanları **3,492 ve 3,484**; fark çok küçük. Bu nedenle önceki ve yeni
aday arasında güçlü bir üstünlük iddiası kurulmadı. Yeni adayın RSRQ/SINR
kontrol karşılaştırması daha yakın, RSRP karşılaştırması daha uzak.
Yeni kullanıcı örneklemi yeniden ayar yapılmadan test edildi; sekiz saha
karşılaştırmada kaldı. Ortalamalar tek tek bütün sahaların yakın olduğunu göstermez.

Komşularla 24 → 32 → 48 toplam saha kontrolleri geçti: %95 mutlak SINR
değişimi 0,243 ve 0,364 dB; RSRP değişimi sıfır, hizmet sektörü eşleşmesi %100.
Tanısal RSRQ değişimleri de 0,139 ve 0,156 dB oldu.

Seçilen adayın ayar ve girdileri ayrı
[`selected_scenario/`](../experiments/placement_propagation_2026-11-10/selected_scenario/configuration.json)
altında korundu. Özgün başlangıç değiştirilmedi. Sonuçlar kısa/düşük yükte
temsili radyo senaryosudur; gerçek kapasite, arıza veya tam ağ doğrulaması değildir.

## Ayrıntıya ihtiyaç olursa

- [Mevcut radyo raporu](../turkcell_tam_paket_2026-11-10/05_RADYO_DENEYLERI_VE_SONUCLAR.md)
- [Saha bazında sayısal sonuçlar](../turkcell_tam_paket_2026-11-10/analysis/sindirgi/radio_study/final_site_comparison.csv)
- [Bu PC'nin doğrulama kaydı](../pc_validation/20261110_pc/verification.json)
- [Çalıştırma rehberi](../BU_PCDE_CALISTIRMA.md)

## Genişletilmiş araştırma: gerçek tarama ve ortak tekrarlar

51 gerçek tarama koşusu (49 geçerli; iki Band 8 koşusu genişlik uyumsuzluğu nedeniyle çıkarılıp yeniden çalıştırıldı), 12 ortak tekrar ve 3 uzun/komşu kontrolü tamamlandı. Yazılım doğrulaması ayrıca 2 LTE koşusu içerir. Dokuz değişken ailesi tarandı; analitik ön eleme sayıları gerçek koşulara eklenmedi. Önerilen **reference**; ayar: 2–6 km kümeler; 120°; n=3.0; 49 dBm; NF=9.0 dB; gölge σ=0.0 dB; DL EARFCN=1300; UDP=50 ms; sektör=three.

| Aday | Eğitim puanı ort. ± std | Sağlamlık puanı | Eğitim MAE RSRP / SINR / RSRQ | Kontrol MAE RSRP / SINR / RSRQ |
|---|---:|---:|---:|---:|
| reference (önerilen) | 3.143 ± 0.118 | 3.202 | 3.52 / 3.32 / 2.59 | 2.96 / 3.64 / 4.08 |
| model_02 | 3.288 ± 0.372 | 3.474 | 3.74 / 3.00 / 3.12 | 2.63 / 2.86 / 4.54 |
| model_01 | 3.207 ± 0.553 | 3.484 | 3.42 / 3.49 / 2.71 | 4.09 / 3.70 / 3.97 |
| model_03 | 3.628 ± 0.374 | 3.815 | 4.19 / 3.17 / 3.52 | 2.89 / 2.62 / 4.70 |

Kontrol sütunu seçimde kullanılmadı; bu üç saha geçmişte görüldüğünden kör test değildir. Üç tekrar ortalamaları 8 s tek örnek sonucundan ayrıdır. 8 s tek örnekte kontrol MAE RSRP / SINR / RSRQ: 2.14 / 5.20 / 3.80 dB. En büyük saha hataları: 7.58 / 10.06 / 4.39 dB.

24→32→48 kontrolü: geçti; 4→8 s: geçti. Koordinatlar/ham veri/ölçüm hedefleri ve özgün başlangıç korunur.

[49 koşulun en iyi 20'si](12_genis_tarama.png) — [Ortak tekrarlar](13_ortak_tekrarlar.png) — [Saha karşılaştırması](14_son_saha_karsilastirmasi.png) — [Tam sonuçlar](../experiments/extended_radio_2026-11-10/SONUCLAR.md) — [Güncel kısa özet](HOCAYA_KISA_OZET.md).
