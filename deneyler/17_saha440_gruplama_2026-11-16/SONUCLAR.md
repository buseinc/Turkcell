# Deney 17 — hocanın hücre ve taşıyıcı gruplaması

**Durum: 3/3 yeni koşu ve eski sonuçla kontrol tamamlandı. Kabul ölçütleri geçmedi; S0 temel kalıyor.**

## Kaynaklardan öğrendiklerimiz

Hocanın güncel v2 gruplamasında SITE_000440, 9 hücreden oluşan 3 üçlü blok içeriyor. Gruplama güçlü olarak işaretli (p=0,017). Bu istatistiksel destek, frekansların doğrulandığı anlamına gelmiyor.

| Blok | Hücreler | Üç hücrenin TA medyanlarının medyanı | Dosyadaki bant hipotezi |
|---|---|---:|---|
| 1 | 006021, 006022, 006023 | 7.85 km | 800/900 MHz? |
| 2 | 006024, 006025, 006026 | 10.53 km | 800/900 MHz? |
| 3 | 006027, 006028, 006029 | 6.50 km | 800/900/1800 MHz? |

İlk iki blok aynı uzun menzil grubunda. Üçüncü blokta sinyal daha zayıf; tüm ağ analizinin yöntem notu, bu iki menzil sınıfının uzaklıklarının benzer olduğunu ve tek kapsama grubu gibi okunması gerektiğini belirtiyor. Bu nedenle bloklara yalnız TA sırasına bakarak kesin 800/900/1800 MHz atamak desteklenmiyor.

Blok içindeki hücre sırası anten yönünü göstermiyor. Yeni bant/EARFCN, bant genişliği ve azimut alanları inputs/cell_groups_440.csv içinde boş bırakıldı. Kaynak Excel dosyaları değiştirilmedi.

Kontrol şablonunda eski p=0,055 değeri var; güncel v2 değeri p=0,017. Yeni gruplama esas alındı.

## CellMapper kontrolü

[440 koordinatında Turkcell LTE haritası](https://www.cellmapper.net/map?MCC=286&MNC=1&type=LTE&latitude=39.21265&longitude=28.09685&zoom=16)

Koordinat: 39.21265 K, 28.09685 D. Yaklaşık 300 m içindeki aday kulelerde bant/EARFCN, bant başına hücre sayısı ve varsa anten yönleri incelenecek. Daha uzak kuleyle eşleşme belirsiz sayılacak.

Erişim denendi: tarayıcı bağlantı sunucusu kullanılamadı; yerel arayüz aracı adresi güvenilir biçimde belirleyemediği için durdu. Web okuyucu da etkileşimli haritayı açamadı. Kule ve bant gözlemi yok; bu, o konumda kule olmadığı anlamına gelmez. Toplu veri çekilmedi.

## Tek yeni senaryonun sınırı

24 sahalık bölgede strong 198, 220, 224 ve 440'ın yapısı güncel v2 dosyasındaki gibi kurulacak.
Kalan 20 saha tek taşıyıcı, 3 sektör, 1800 MHz kalacak. 220 ve 224'ün dört sektörlü blokları korunacak.
S0 ölçüm kullanıcılarının konumları ve temel radyo ayarları korunacak; Deney 16’daki bina kaybı
eklenmeyecek. Üç anten/kullanıcı örneği kullanılacak. Klasör adı ilk 440 incelemesinden kalmıştır;
aynı deney genişletildi, yeni deney/rapor kopyası oluşturulmadı.

Koşudan önce frekanslar, bant genişlikleri, güçler, taşıyıcıya kullanıcı atama kuralı ve yeni hücrelerin yükü açıkça sabitlenecek. Doğrulanamayan bilgi varsayım diye işaretlenecek; 3 taşıyıcıyı doldurmak için veri uydurulmayacak. Karşılaştırma ve kabul kuralları plan.json içinde kayıtlı.

440 ayarlamada kullanılmayan saha olarak kalır; buradaki sinyal sonuçlarına bakarak güç/frekans seçilmez. Gerçek yapı bilgisi modele girdi olarak kullanılabilir.

**Bant doğrulaması için eksik bilgi:** Aday CellMapper kulesinin koordinatı ve görünen LTE bant/EARFCN listesi. Üç gerçek hücre bloğunun bantlarla birebir eşlemesi ayrıca belirsizdir; kamu haritası bunu her zaman sağlayamaz.

## Hocanın mesajlarıyla netleşen uygulama

Hoca, güçlü grupların önerildiği gibi kurulmasına; diğer sahaların tek taşıyıcı, 3 sektör, 1800 MHz kalmasına izin veriyor. Çok taşıyıcılı sahalarda yüksek TA’ya düşük frekans atanması deneme varsayımı olarak kullanılabilir. CellMapper gözlemi varsa tercih edilir; yokluğu bütün simülasyonu durdurma gerekçesi değildir.

Mevcut 24 sahalık bölgenin güncel v2 dosyasında güçlü sahalar: **198 (3+3+3), 220 (4+3+4), 224 (3+4+3), 440 (3+3+3)**. Bunlardan yalnız 440 ana değerlendirme sahasıdır; diğer üçü komşu girişim sahalarıdır. Bütün 24 saha için yalnız 440’ın güçlü olduğunu söylemek doğru değildir.

206 elle kontrol önceliğinde kalır; güncel v2 dosyasında güveni moderate, gruplaması 3+3+3+3’tür. Eski şablondaki 4+4+4 ve p-değeri güncel v2 ile aynı değildir.

Son görüşmede kapsam sadeleştirildi: ayrı bir 440 pilotu yerine, hocanın tarif ettiği güçlü grupların tamamını içeren tek yeni senaryo hazırlanacak. Dört sektörlü bloklar üçe yuvarlanmaz. Yukarıdaki yalnız 440 ile ilgili ilk taslak bu kapsam kararıyla genişletilmiştir; henüz yeni koşu başlatılmadı.

| Elle kontrol | Enlem | Boylam | Güncel v2 güveni |
|---|---:|---:|---|
| [SITE_000440](https://www.cellmapper.net/map?MCC=286&MNC=1&type=LTE&latitude=39.21265&longitude=28.09685&zoom=16) | 39.21265 | 28.09685 | strong |
| [SITE_000206](https://www.cellmapper.net/map?MCC=286&MNC=1&type=LTE&latitude=39.39445&longitude=28.1325&zoom=16) | 39.39445 | 28.1325 | moderate |
| [SITE_000224](https://www.cellmapper.net/map?MCC=286&MNC=1&type=LTE&latitude=39.37625&longitude=28.19365&zoom=16) | 39.37625 | 28.19365 | strong |

## Kullanıcının elle kontrolü ve alternatif bölge

Kullanıcı 440, 206 ve 224 koordinatlarında kule görünmediğini bildirdi. Paylaşılan operatör ekranında Turkcell, 4G-LTE ve All bant seçimi doğrulandı. Bu, kulelerin gerçekte bulunmadığını göstermez. Yaklaşık 300 m yarıçapın ayrıca sistematik tarandığı doğrulanmadı.

Hocanın açıklamasına göre hedefin yaklaşık 300 m çevresinde kayıt aranır; veri yetmezse ölçümün bol olduğu ana arter/otoyollardaki kuleler incelenir. Uzak kuleler hedef sahayla eşleştirilmez; bant, EARFCN ve bant başına hücre sayısı için bölgesel örüntü sağlar. Hedeflerin doğrulanmış RF alanları boş kalır.

## Kullanıcının paylaştığı CellMapper örneği — kule 13062

Kaynak: Kullanıcının haritadan seçerek aktardığı kule paneli; Turkcell 286/1, Region 6163, MACRO.
Haritada Kırkağaç yönünde seçilen örnektir; 440/206/224 sahalarına eşleştirilmedi. Kesin kule
koordinatı ve hedeflere mesafe henüz paylaşılmadı. Panelde son görülme 17 Haziran 2026, oluşturulma
25 Haziran 2026 yazıyor. Aşağıdaki tarih ve eksik alanlar kullanıcı aktarımından aynen ayrıldı.

| Cell | Cell Identifier | PCI | Bant | EARFCN | DL / UL (MHz) | Bant genişliği | Panelde yön | Son görülme |
|---|---:|---:|---|---:|---|---|---|---|
| 11 | 3343883 | 322 | B20 | 6400 | 816 / 857 | Belirtilmemiş | 0° | 17.06.2026 |
| 12 | 3343884 | 322 | B3 | 1651 | 1850,1 / 1755,1 | 20 MHz | 178° | 17.06.2026 |
| 17 | 3343889 | 322 | B1 | 100 | 2120 / 1930 | 20 MHz | 179° | 09.05.2024 |
| 21 | 3343893 | 279 | B20 | 6400 | 816 / 857 | 10 MHz | 175° | 09.05.2024 |
| 22 | 3343894 | 279 | B3 | 1651 | 1850,1 / 1755,1 | 20 MHz | 176° | 17.06.2026 |
| 23 | 3343895 | 279 | B3 | 1795 | 1864,5 / 1769,5 | Belirtilmemiş | 179° | 29.05.2021 |
| 26 | 3343898 | 279 | B1 | 50 | 2115 / 1925 | Belirtilmemiş | 176° | 29.05.2021 |
| 27 | 3343899 | 279 | B1 | 100 | 2120 / 1930 | 20 MHz | Belirtilmemiş | 09.05.2024 |

Bu örnek, operatörün daha geniş bölgede 800 MHz sınıfı B20, 1800 MHz sınıfı B3 ve 2100 MHz sınıfı
B1 kayıtlarını birlikte barındıran çok bantlı makro sahalarına örnek sağlar. Bant sınıfı ile gerçek
taşıyıcı merkez frekansı ayrıdır: paneldeki merkezler sırasıyla 816, 1850,1 ve 2120 MHz'tir.

Sekiz tarihsel hücre kaydı, aynı anda sekiz aktif hücre veya kesin 3 taşıyıcı × 3 sektör demek değildir.
B1'in paylaşılan son kayıtları 2024'te, alternatif B3 EARFCN 1795 ve B1 EARFCN 50 kayıtları 2021'de
kalıyor. Bunların 2025 KPI veya 2026 Experia döneminde aktif olup olmadığı bu panelden belirlenemez.

Panel yönleri de doğrudan anten ayarı olarak alınmayacak: örneğin aynı PCI 322 için Cell 11'de 0°,
Cell 12/17'de yaklaşık 178–179° yazıyor. Aynı PCI tek başına aynı fiziksel sektörü kanıtlamaz.
CELL_006021 vb. anonim proje kimlikleriyle kamu haritasındaki bu kimlikler eşleştirilmedi.

Bu gözlem 800/1800/2100 MHz sınıflarını bölgesel senaryo adayı olarak destekler; 440'ın gerçek
bantlarını veya TA bloklarıyla bant eşlemesini doğrulamaz. 900 MHz bu paylaşılan örnekte gözlenmedi.
Örneği tamamlamak için kule koordinatı ve varsa kalan hücre kayıtları gerekir.

## Koşudan önce sabitlenen senaryo

Dört güçlü sahanın blokları TA medyanına göre sıralandı: en yüksek TA → B20 (816 MHz), orta → B3 (1815 MHz), en düşük → B1 (2120 MHz). Bunlar hedef sahaların doğrulanmış bantları değil, hocanın izin verdiği varsayımlardır. B1 bölgesel örnekte tarihsel kayıttır. B3 merkezi S0 ile aynı tutuldu.

| Saha | Kaynak blok | Sektör sayısı | TA medyanı (km) | Varsayılan bant |
|---|---:|---:|---:|---|
| SITE_000198 | 1 | 3 | 2.680 | B3 |
| SITE_000198 | 2 | 3 | 2.490 | B1 |
| SITE_000198 | 3 | 3 | 6.690 | B20 |
| SITE_000220 | 1 | 4 | 9.445 | B20 |
| SITE_000220 | 2 | 3 | 5.760 | B3 |
| SITE_000220 | 3 | 4 | 1.915 | B1 |
| SITE_000224 | 1 | 3 | 7.560 | B1 |
| SITE_000224 | 2 | 4 | 11.110 | B20 |
| SITE_000224 | 3 | 3 | 8.890 | B3 |
| SITE_000440 | 1 | 3 | 7.850 | B3 |
| SITE_000440 | 2 | 3 | 10.530 | B20 |
| SITE_000440 | 3 | 3 | 6.500 | B1 |

B3/B1 genişliği 20 MHz, B20 10 MHz; her hücre 49 dBm. Anten kazancı 15 dBi, yatay genişlik tümünde 120°. Dört sektörlü katmanda yön aralığı 90°, üçlüde 120° varsayıldı. Bina kaybı, dikey desen veya yeni handover eklenmedi.

256 ölçüm kullanıcısının konumu aynen korundu. Önceki B3 sinyal hesabında güçlü sahaya bağlanacak kullanıcılar, kimlik sırasıyla üç taşıyıcıya dengeli dağıtıldı; diğerleri B3 kaldı. Gerçek taşıyıcı kullanıcı payları bilinmiyor, bu dağılım varsayım. ns-3 otomatik frekanslar arası seçim yaptığı iddia edilmiyor.

72 eski yük kullanıcısı aynen korundu; 27 yeni hücreye birer yük kullanıcısı eklendi. 10 MHz B20 hücrelerinin paket aralığı 20 MHz hücrelerin iki katı seçildi; böylece dar taşıyıcıya bant genişliğiyle orantılı trafik verildi. Hedef PRB 0,233 ve eski 1,47 katsayısı korundu; sonuçlara bakarak ayar yapılmayacak. Toplam 99 hücre ve 355 kullanıcı var. Toplam yük trafiği yaklaşık %27,8, hücre sayısı ve toplam yapılandırılmış güç %37,5 artıyor. Gerçekleşen PRB ayrıca kontrol edilecek; sonuç yalnız frekans etkisi diye yorumlanmayacak.

Önce yeni bant ve sektör kodu kendi kontrollerinden geçecek; sonra S0 tek taşıyıcılı tam koşusu eski altı CSV ile yalnız CRLF/LF normalizasyonu sonrası birebir karşılaştırılacak. Geçmeden yeni üç koşu başlamayacak. Eşikler önceden plan.json içinde yazılı; sonuçlara bakarak ayar seçilmeyecek.

## ns-3 çalışma durumu ve sonuçları

Eski tek taşıyıcılı S0 koşusu içerik olarak birebir tekrarlandı (yalnız CRLF/LF normalize edildi). Yeni bant/sektör kodunun küçük kontrolleri ve üç tam koşu tamamlandı.

| Senaryo | Ayarda RSRP farkı | Kontrolde RSRP farkı | Kontrolde SINR farkı | Ortalama PRB |
|---|---:|---:|---:|---:|
| S0 | 3.59 | 1.72 | 2.15 | 0.254 |
| G17 | 3.59 | 2.64 | 3.61 | 0.224 |

Farklar dB; küçük değer daha iyi. Kontrol sahaları 440/441/443; hiçbir RF ayarı bunların sonuçlarına göre seçilmedi.

**Karar: Önceden yazılan kabul ölçütleri geçmedi; S0 temel kalıyor.**

| Kontrol | Sonuç |
|---|---|
| 8 sahanın sonuçları var | Geçti |
| Kontrol RSRP farkı en az 0,5 dB azaldı | Geçmedi |
| Kontrol SINR farkı en fazla 0,5 dB kötüleşti | Geçmedi |
| 440 dışındaki sahalarda RSRP farkı en fazla 1 dB kötüleşti | Geçti |
| Her koşuda 256 ölçüm kullanıcısı bağlandı | Geçti |
| Her koşuda 256 ölçüm kullanıcısı veri aldı | Geçmedi |
| Her örnekte ortalama PRB farkı en fazla 0,03 | Geçmedi |
| Hücre yapısı, frekans ve kullanıcı taşıyıcı ataması doğru uygulandı | Geçti |
| Yeni bantların RSRP hesabı analitik bütçeyle uyuştu | Geçti |

| Örnek | Bağlanan / 256 | Veri alan / 256 | Yük kullanıcısı hedef hücrede / 99 | B3/B20/B1 ölçüm kullanıcısı |
|---|---:|---:|---:|---|
| 701 | 256 | 255 | 94 | 232/13/11 |
| 702 | 256 | 256 | 95 | 230/14/12 |
| 703 | 256 | 256 | 95 | 236/11/9 |

Eski S0’da da hedef hücreye bağlı yük kullanıcısı sayısı 67/72, 68/72 ve 68/72 idi. Yeni koşularda buna 27 yeni yük kullanıcısının tamamı eklendi; 94/99, 95/99 ve 95/99 değerleri bu nedenle yeni katmanlara ait bir hedefleme hatası göstermez.

RSRP değişimi 440 sahasında yoğunlaştı: ortalama işaretli fark yaklaşık +0,08 → +3,31 dB oldu; modelin sinyali bu sahada ölçümden daha güçlü çıktı. Diğer yedi değerlendirme sahasının RSRP değerleri S0 ile aynı kaldı. Bu, yeni bant ve kullanıcı atamasının etkisinin nerede oluştuğunu gösterir; hocanın gruplamasının yanlış olduğunu kanıtlamaz.

Yük eşitliği tam sağlanmadı. B20 ortalama PRB yaklaşık 0.093 oldu; hedef 0,233 idi. Bant genişliğiyle orantılı trafik vermek, aynı PRB’yi garanti etmedi. Bu yüzden SINR farkı, yalnız yeni hücre yapısının etkisi olarak yorumlanamaz. Sonuçlara göre yük katsayısı veya güç yeniden ayarlanmadı.

Teknik düzeltme: İlk denemede iki dört-sektörlü yerleşimde 360° üstüne çıkan yönler anten modelinin aralık kontrolüne takıldı. Yönler modulo 360 ile aynı fiziksel yöne çevrildi; girdi konumları, güç, bant, yük ve kabul ölçütleri değiştirilmedi. Düzeltilen kaynakla S0 kontrolü ve üç koşu yeniden tamamlandı. Yeni kodun 20 küçük kontrolü geçti.

Bantlar ve taşıyıcı kullanıcı payları senaryo varsayımlarıdır; bu sonuçlar gerçek saha konfigürasyonunu doğrulamaz. B1 için bölgesel CellMapper kaydı tarihsel; hedef sahalara eşleşme yok. Toplam sunulan trafik %27,8, yapılandırılmış toplam güç/hücre sayısı %37,5 arttığı için fark yalnız frekans etkisi diye yorumlanamaz. Kısa koşuda veri alamama kalıcı kesinti kanıtı değildir. Mixed SINR tanımı ve S0 kullanıcı mesafelerinin sınırlamaları devam ediyor.

Ayrıntılı saha hataları ve bütün kontroller comparison.json içinde. Sonuç görüldükten sonra ayar değiştirilmedi.
