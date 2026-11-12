# Genişletilmiş gerçek ns-3 denemeleri — 10 Kasım 2026

**Sonuç:** 51 gerçek tarama koşusu (49 geçerli koşul; 2 reddedilmiş Band 8 tanı koşusu), 4 adayda 12 ortak tekrar ve 3 uzun/komşu doğrulaması tamamlandı. Önerilen aday: **reference**. Önceki aday ortak tekrarların sağlamlık sıralamasında doğrudan ilk sırada kaldı. 

## Kaç ve ne çeşit deneme yaptık?

Tarama: önce **49**, ardından **2 düzeltme** ile **51 gerçek koşu**; sıralamada **49 geçerli koşul**. Rastgele anten örneklerini aynı yapısal model sayarsak **46** geçerli farklı yapısal ayar. Her tarama 2 s, ilk 1 s ısınma. Bunlar analitik kestirim değil, gerçek LTE/EPC ns-3 çalıştırmalarıdır.

**Kaydedilmiş düzeltme:** İlk iki Band 8 denemesinde 100 RB / 20 MHz kalmıştı. [ETSI TS 136 101 Tablo 5.6.1-1](https://www.etsi.org/deliver/etsi_ts/136100_136199/136101/18.05.00_60/ts_136101v180500p.pdf) Band 8 için bu genişliği desteklemez. `screen_015` ve `screen_031` aday sıralamasından çıkarıldı, kayıtları silinmedi; aynı girdilerle 50 RB / 10 MHz'de iki yeni koşu yapıldı. Düzeltme geçerli ilk üç yapısal adayı değiştirmedi; rapor bunu ayrıca doğrular. Diğer koşuların kaynakları değiştirilmedi. [Düzeltme kuralı](band8_amendment.json), [düzeltilen sonuçlar](band8_correction.json). Aşağıdaki aile sayıları yalnız geçerli taramaları içerir.

| Değişken ailesi | Atanan tarama sayısı |
|---|---:|
| Kullanıcı dağılımı | 14 |
| Sabit gölgeleme | 6 |
| Alıcı gürültüsü | 6 |
| Yayılım kaybı | 6 |
| Yayın gücü | 4 |
| Taşıyıcı | 4 |
| Sunulan yük | 3 |
| Sektör düzeni | 3 |
| Anten yönü | 3 |

Kullanıcılar: 0,5–2 km / 1–4 km / 2–6 km kümeler, bölge içinde uniform ve yakın–uzak karışık; anten 65°/120°; yayılım üsleri yaklaşık 2,55–3,15; güç 40–49 dBm; alıcı NF 6/9/12 dB; gölge σ 0/4/8 dB; UDP 20/50 ms; anten yön örnekleri; 482/554 için iki veya üç sektör; ortak Band 3/8/1 taşıyıcı hipotezleri. Bu bir tam faktöriyel tarama değildir: üç başlangıç profili çevresinde tek-değişken denemeleri yapılmıştır. Tüm olası etkileşimleri tükettiğimiz iddia edilmez.

Toplam **70 native LTE çalıştırması** = 51 tarama + 12 tekrar + 3 doğrulama + 2 yazılım testi + 2 pasif tanı tekrarı. Son ikisi yeni model alternatifi sayılmaz: 10 MHz'de native mixed SINR'nin kaynak-grubu kenar RB ortalamasını kontrol hesabına ekleyerek aynı iki modeli yeniden çalıştırdık. Native radyo, ölçüm, sektör ve UE CSV özetleri önceki 10 MHz koşularıyla birebir aynı; yalnız pasif tanı hesabı düzeldi. İlk kayıtlar `band8_10mhz/`, son doğrulanmış kayıtlar `band8_10mhz_v2/` altında. Önceki 135 analitik ön eleme bu sayıya dahil değildir. Ayrı küçük gölgeleme birim kontrolü LTE koşusu sayılmadı.

## Seçimi nasıl yaptık?

Basit örnek: saha yerini haritada sabit tutuyoruz. O sahanın 1 km çevresindeki kullanıcılarla 5 km çevresindeki kullanıcıların göreceği sinyal aynı olmayabilir. Kullanıcı dağılımı denemesi bunu değiştiriyor. Gölgeleme denemesinde ise aynı uzaklıktaki bağlantıların ek kaybının farklı olabileceğini varsayıyoruz; bunu gerçek bina haritasından çıkarmıyoruz. Alıcı gürültüsü denemesi de telefonun zayıf sinyali ne kadar temiz duyabildiğiyle ilgili. Bunlar ölçülmemiş koşullar için alternatiflerdir; saha konumları için alternatif üretmiyoruz.

Beş eğitim sahasında RSRP/SINR/RSRQ mutlak hatalarının eşit ağırlıklı ortalaması; eksik eğitim sahası başına 10 dB ceza. Taramanın ilk üç farklı yapısal modeli ve önceki referans, aynı üç kullanıcı/anten/gölgeleme örneğinde 4 s çalıştırıldı. Rastgele örnekler önceden yazıldı; en güzel sonuç veren örnek seçilmedi.

Son puan = üç tekrarın eğitim puanı ortalaması + 0,5 × standart sapması. Önceki referans minimuma 0,10 dB içinde kalırsa daha basit referans önerilir. Kontrol hataları bu seçim dondurulduktan sonra hesaplandı. Üç tekrarın standart sapması belirsizliğin sınırlı bir göstergesidir; güven aralığı değildir. Tarama ve tekrarlar aynı beş eğitim sahasını kullandığı için eğitim kazanımı genelleme kanıtı değildir.

| Aday | Eğitim puanı ort. ± std | Sağlamlık puanı | Eğitim MAE RSRP / SINR / RSRQ | Kontrol MAE RSRP / SINR / RSRQ |
|---|---:|---:|---:|---:|
| reference (önerilen) | 3.143 ± 0.118 | 3.202 | 3.52 / 3.32 / 2.59 | 2.96 / 3.64 / 4.08 |
| model_02 | 3.288 ± 0.372 | 3.474 | 3.74 / 3.00 / 3.12 | 2.63 / 2.86 / 4.54 |
| model_01 | 3.207 ± 0.553 | 3.484 | 3.42 / 3.49 / 2.71 | 4.09 / 3.70 / 3.97 |
| model_03 | 3.628 ± 0.374 | 3.815 | 4.19 / 3.17 / 3.52 | 2.89 / 2.62 / 4.70 |

Tablodaki MAE'ler dB; düşük daha yakın. Kontrol MAE standart sapmaları, önerilende RSRP / SINR / RSRQ: **0.83 / 1.38 / 0.21 dB**. Tekrarlarda eğitim 15/15, kontrol 9/9 saha-gözlemi; en az 64/64 kullanıcı bağlı, 64/64 kullanıcı veri aldı.

- **model_01**, tarama kaynağı screen_005: 2–6 km kümeler; 120°; n=3.0; 49 dBm; NF=9.0 dB; gölge σ=4.0 dB; DL EARFCN=1300; UDP=50 ms; sektör=three.
- **model_02**, tarama kaynağı screen_041: 2–6 km kümeler; 65°; n=2.7; 43 dBm; NF=12.0 dB; gölge σ=0.0 dB; DL EARFCN=1300; UDP=50 ms; sektör=three.
- **model_03**, tarama kaynağı screen_024: 1–4 km kümeler; 120°; n=3.0; 46 dBm; NF=12.0 dB; gölge σ=0.0 dB; DL EARFCN=1300; UDP=50 ms; sektör=three.
- **reference**, tarama kaynağı screen_000: 2–6 km kümeler; 120°; n=3.0; 49 dBm; NF=9.0 dB; gölge σ=0.0 dB; DL EARFCN=1300; UDP=50 ms; sektör=three.

## Önceden belirlenen örnekte uzun doğrulama

Önerilen ayar: **2–6 km kümeler; 120°; n=3.0; 49 dBm; NF=9.0 dB; gölge σ=0.0 dB; DL EARFCN=1300; UDP=50 ms; sektör=three**. 64 sanal kullanıcı; 24 toplam saha. Üç tekrardan ilk örnek daha sonuçlara bakılmadan son doğrulama örneği olarak belirlendi. Aynı örnekte 8 s:

| Küme | RSRP MAE | SINR MAE | RSRQ MAE | Geçerli saha |
|---|---:|---:|---:|---:|
| Eğitim | 2.93 | 3.45 | 2.52 | 5/5 |
| Kontrol | 2.14 | 5.20 | 3.80 | 3/3 |

8 s / 24 saha koşusunda 64/64 bağlı ve 64/64 veri alan kullanıcı. Sekiz değerlendirme sahasında en büyük mutlak RSRP / SINR / RSRQ hataları **7.58 / 10.06 / 4.39 dB**. Ortalama yakınlık her sahanın yakın olduğunu söylemez.

4 → 8 s kontrolü: **geçti**; %95 kullanıcı RSRP değişimi 0.000, SINR 0.409 dB; hizmet sektörü aynı 100.0%. 4 s ve 8 s sonuçları ayrı raporlanır.

| Toplam saha | RSRP %95 mutlak değişim | SINR %95 mutlak değişim | RSRQ %95 değişim (tanısal) | Aynı hizmet sektörü | Sonuç |
|---|---:|---:|---:|---:|---|
| 24 → 32 | 0.000 | 0.192 | 0.163 | 100.0% | geçti |
| 32 → 48 | 0.000 | 0.145 | 0.141 | 100.0% | geçti |

Önceden yazılan sınırlar: RSRP ve SINR %95 değişim ≤1 dB; aynı hizmet sektörü ≥%95. RSRQ burada ek tanısal sonuçtur. İki genişletmenin ortak sonucu: **geçti**. Bu koşullar geçmezse 24 sahayı yeterli ilan etmeyiz.

## Sabit kalanlar ve açık varsayımlar

- Ham ölçümler, verideki saha koordinatları/kimlikleri, özgün hücre–saha eşlemesi, hedefler ve eğitim/kontrol ayrımı korunur. 24→32→48 genişlemesi aynı envanter kaynaklarından gelir. 553/554/555'in ek konumlarının özgün kaynağı hâlâ sorulacak.
- Kullanıcı yerleri gerçek müşteri konumları değildir. Sektörler sentetik radyo temsilleridir; iki-sektör alternatifi yalnız 482/554'te sınandı. Hiçbir denemede verideki sahayı sonuç güzelleşsin diye taşımadık.
- 64 kullanıcı toplamı saha başına eşit temsil sağlamaz. Seçilen ayarın üç tekrarından birinde 296'yı yalnız bir, birinde 443'ü iki kullanıcı temsil eder. Saha ortalamaları kullanıcı/anten örneklerine duyarlıdır. [Saha başına kullanıcı kapsamı ve üç tekrar özeti](selected_site_coverage.csv). Daha yoğun kullanıcı örneklemi ve sabit toplam sunulan yükle duyarlılık, bir sonraki araştırma konusudur; bu kampanyada yapılmış sayılmaz.
- Gölge modeli: koordinat çiftine bağlı, karşılıklı aynı ve zamanda sabit, sıfır ortalamalı Gaussian dB kaybı. Aynı konumlu sektörlerde ortak; farklı kullanıcı konumlarında uzaysal korelasyon yok. Gerçek arazi/bina modeli veya hızlı fading değildir. σ=0 özgün log-distance yoluna aynen döner.
- Her taşıyıcı denemesi tek ortak, eşlenmiş DL/UL taşıyıcı kullanır; yayılım referans frekansı ve UE arama kanalı birlikte değiştirilir. Bant birleştirme, gerçek çok katmanlı ağ ve frekanslar arası handover modellenmedi. Bantlar varsayımdır.
- Mixed SINR ve ns-3'ün native RSRQ hesabı korunur; hedefe uysun diye sabit RSRQ düzeltmesi eklenmedi. Mixed tanımındaki güncel veri girişimi bulunmadığında gürültüye dönüş davranışı nedeniyle sonuçların ölçüm tanımıyla uyumu hocayla netleştirilmeli. [Önceki tanım incelemesi](../placement_propagation_2026-11-10/RSRQ_TANIM_NOTU.md).
- Üç kontrol sahası önceki çalışmalarda görüldü; yeni kör doğrulama değildir. Bütün koşullar kısa süreli, düşük sentetik yükte çalışır. Yakınlık gerçek operatör ayarlarının bulunduğunu göstermez; kapasite doğrulaması yapılmadı.

## Yazılım ve yeniden üretme

Özgün C++ SHA-256 değişmedi: `0b8451817d0857dc682e7b13b40eb40076147b007bdbef3594794f74932f0254`. Gölgesiz 4 s referansın eski sonuçlarla UE başına tüm radyo metrikleri, hizmet sektörü ve byte sayıları aynı. Gölge için karşılıklılık, zamana göre sabitlik, aynı koordinatlar, σ=0 eşdeğerliği ve dağılım kontrolü geçti; pozitif σ ile 6/6 kullanıcı bağlantı/veri testi geçti. Her native koşuda mixed SINR bağımsız bileşenlerden yeniden hesaplandı; sayısal eşleşme `checks.json` içinde.

Windows proje kökünde rapor: `.venv\Scripts\python.exe experiments/extended_radio_2026-11-10/report.py`

Ubuntu-22.04 WSL'de kampanya: `python3 /mnt/c/Users/bi025305/Downloads/paylasim/paylasim/experiments/extended_radio_2026-11-10/run_campaign.py`

`experiment_plan.json` bütün girdilerin/deney kaynaklarının özetlerini, seçimi ve tohumları saklar. `prepare.py` girdileri üretir; mevcut tamamlanmış koşuları değiştirmeden yeniden raporlamak için doğrudan `report.py` çalıştırılır. Kampanya aynı kod/girdiyle geçerli sonuçları önbellekten kullanır.

## Dosyalar

- [Analizdeki tarama/tekrar/doğrulama sonuçları](all_native_runs.csv), [tam geçerli tarama sırası](screening_rank.csv), [tekrar sıralaması](robust_model_rank.csv)
- [Her koşulun kendi başlangıcına göre etkisi](paired_factor_effects.csv); negatif değişim daha düşük hata demektir, kısa taramadır
- [Saha bazında bütün karşılaştırmalar](site_comparison.csv), [UE bazında bütün çıktılar](ue_comparison.csv)
- [Deney planı](experiment_plan.json), [tam sonuç](study_result.json), [sayısal kontroller](checks.json)
- [Önerilen senaryo](selected_scenario/configuration.json); sahalar ve kullanıcılar aynı klasörde
- [Tarama grafiği](screening_top20.png), [tekrar grafiği](robustness_comparison.png), [saha karşılaştırması](final_site_comparison.png)
