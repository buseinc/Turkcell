# Deney 16 — bina kaybı ve dikey anten deseni

**Durum: 9/9 yeni koşu ve önceki sonuçla doğrulama tamamlandı. Seçilen aday kabul edilmedi; S0 temel kalıyor.**

Önceki deneylerin girdileri aynen kopyalandı. TA yerleşimi, güç, yük ve diğer radyo ayarları korundu. Karar kuralları koşudan önce plan.json dosyasına yazıldı.

## Hızlı hesabın kontrolü

Ek etkiler kapalıyken 3 eski TA koşusunun toplam 768 ölçüm kullanıcısında bağlantı hücreleri birebir aynı çıktı. En büyük RSRP farkı 0,000000006 dB altındaydı. Bu kontrol yalnız eski durumun analitik RSRP hesabını doğrular; yeni C++ kodunun çalıştığını doğrulamaz.

## Seçim ve sonuç

0/6/12/18 dB bina kaybı ile 0/3/6/9 derece eğim, 3 örneğin tamamında tarandı. Dikey desen genişliği 10 derece, en fazla zayıflatma 20 dB olarak sabitlendi. Bunlar operatör ayarları değil, bu deneyin varsayımlarıdır.

Yalnız ayarda kullanılan 5 saha ile seçilen aday: **6 dB ek kayıp, 0 derece eğim, dikey desen açık.** Kontrol sahaları aday seçiminde kullanılmadı. Aday dondurulduktan sonra aşağıdaki kontrol hesabı yapıldı.

| Analitik senaryo | Ayarda kullanılan 5 sahada RSRP farkı | Diğer 3 sahada RSRP farkı |
|---|---:|---:|
| TA yerleşimi, ek etki yok | 8.25 dB | 3.28 dB |
| 6 dB + dikey desen, 0° | 4.68 dB | 5.01 dB |
| Yalnız 6 dB | 5.00 dB | 4.96 dB |
| Yalnız dikey desen, 0° | 7.32 dB | 3.13 dB |

**İlk bulgu:** Seçilen aday ayarda kullanılan sahaları iyileştirse de diğer 3 sahada uyumu bozuyor. Bu nedenle bina kaybı ve basit dikey desenin sorunu çözdüğü söylenemez. Sonuç görüldükten sonra ayar değiştirilmedi.

0 derece seçilmesi, gerçek antenlerin eğimsiz olduğunu göstermez. Bu basit model ve tarama aralığında aşağı eğim eklemek ayar sahalarının RSRP hatasını azaltmadı.

TA saatlik bir ortalamadır; kullanıcı yönleri bilinmiyor. Kullanıcıların komşu sahalara bağlanması, tek frekans varsayımı ve saha yapısı hâlâ sınırlardır. Bina kaybı bütün ölçüm kullanıcılarına uygulanan etkili bir kayıp varsayımıdır; kullanıcıların gerçekten bina içinde olduğunu kanıtlamaz.


## ns-3 sonuçları

**9/9 koşu tamamlandı.** Ayarlama hızlı RSRP hesabıyla 5 sahada yapıldı; seçilen aday değiştirilmeden 3 ayrı örnekte sınandı.

| Senaryo | Ayarda RSRP farkı | Kontrolde RSRP farkı | Kontrolde SINR farkı | Tüm ölçütler |
|---|---:|---:|---:|---|
| Eski temel S0 (2–6 km) | 3.59 | 1.72 | 2.15 | Karşılaştırma |
| TA yerleşimi, ek etki yok | 8.25 | 3.28 | 3.44 | Karşılaştırma |
| 6 dB + dikey desen, 0° | 4.68 | 5.01 | 3.10 | Geçmedi |
| Yalnız 6 dB | 5.00 | 4.96 | 3.19 | Geçmedi |
| Yalnız dikey desen, 0° | 7.32 | 3.13 | 3.24 | Geçmedi |

Bütün farklar dB. Ayrıntılı kabul kontrolleri comparison.json içinde.

**Karar: Seçilen yeni aday kabul edilmedi; temel S0 korunuyor.** 6 dB kayıp ve dikey desen birlikte ayar sahalarını iyileştirirken diğer üç sahada RSRP farkını 3,28 → 5,01 dB artırdı. Etkileri ayrı uygulamak da önceden belirlenen kabul ölçütlerini karşılamadı. Sonuç görüldükten sonra yeniden ayar yapılmadı.

Bütün yeni koşularda 256 ölçüm kullanıcısı da şebekeye bağlandı. 4 saniyelik koşuda veri alan kullanıcı sayısı, 6 dB kayıp içeren iki senaryoda 242–246; yalnız dikey desende 255–256 oldu. Ek etkisiz eski TA koşularında da 255–256 idi. Bu kısa koşudaki veri alamama, tek başına kalıcı kapsama kesintisi kanıtı değildir. PRB yükü bütün senaryolarda belirlenen sınır içinde kaldı.

Öğrendiğimiz: Her kullanıcıya aynı kaybı eklemek genel çözüm olmadı. Bu sonuç gerçek ağda bina kaybı veya anten eğimi olmadığı anlamına gelmez. Kullanıcı yönleri, saatlik ortalama TA ve komşu sahalara bağlanma sınırlamaları devam ediyor.

Bu deney gerçek bina kaybını veya anten eğimini belirlemez; varsayımların ölçümleri açıklama gücünü sınar. Temel S0 senaryosu korunur.
