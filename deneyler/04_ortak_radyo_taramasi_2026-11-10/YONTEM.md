# Neyi arıyoruz?

Amaç: eldeki ölçüm özetlerine birlikte yaklaşan, açık varsayımlı bir
başlangıç adayı bulmak. Hocanın taslağındaki ölçümlerden yararlanan temsili
senaryo yaklaşımı izleniyor. Gerçek konfigürasyonun bulunduğu iddia edilmiyor.

## Neden bu iki değişken?

**Anten genişliği** hangi yönlere ne kadar sinyal ulaştığını değiştirir.
Hem istenen sinyali hem çevredeki girişimi etkileyebilir. Bu nedenle RSRP
ve RSRQ üzerindeki etkisi araştırılıyor. 65°, 90°, 120° senaryo seçenekleri
seçildi. Tepe kazancı 15 dBi ve sektör başına güç 46 dBm sabit tutuldu.
Bu seçenekler gerçek anten tahmini değildir; genişlik/kazanç eşlemesi de
varsayımsaldır.

**Sunulan veri yükü** mixed yönteminin veri girişim ölçümlerini ve CQI üzerinden
iletim kararlarını etkiler. Önceki düşük yükte mixed SINR çoğu örnekte yalnız
gürültüye göre hesaplanıyordu. Daha sık paket göndererek bu duyarlılık
inceleniyor. Kullanıcı başına 512 bayt / 50 ms ve 512 bayt / 5 ms kullanıldı:
1× ve 10× sunulan sentetik yük. Bunlar gerçek talep veya deprem trafiği değildir.

Bu 3×2 tarama, iki değişkenin etkisini ve birlikte değiştiklerinde ortaya
çıkan farkı ayırmaya yardımcı olur. Frekans, güç, sektör sayısı, yayılım
modeli ve kullanıcı konumları bu taramada değiştirilmedi.

## Adil karşılaştırma

- Aynı 24 saha, 72 sektör, 64 sabit kullanıcı; aynı anten yönleri ve seed.
- Her koşu 4 s; analiz ilk 1 s sonrasını ve son hizmet hücresini kullanır.
- Başlangıç 65° / 50 ms koşulu yeni kodla eski mixed sonucunu yeniden
  üretmeden diğer koşullara geçilmez.
- Her koşuda native mixed SINR, pasif kaydedilen veri girişiminin güncelleme
  durumundan bağımsız yeniden hesaplanır.
- Anten genişliği değişince kullanıcı başka sektöre bağlanabilir. Saha
  ortalamasının bileşimi de değişir; kullanıcı ve saha tabloları saklanır.
- Eksik sahalar raporlanır; seçim puanına eksik eğitim sahası cezası eklenir.

## Sonucu nasıl seçeceğiz?

Kural koşulardan önce `experiment_plan.json` içine yazıldı:

```text
Eğitim puanı = (RSRP MAE + SINR MAE + RSRQ MAE) / 3
              + 10 × eksik eğitim sahası sayısı
```

Bu bir keşif sıralamasıdır. Üç metrik eşit ağırlıklıdır; fiziksel ortak bir
güç veya operatör kabul kriteri değildir. Her metrik ayrı gösterilir ve
eğitimde üç metrik açısından baskılanmayan adaylar da işaretlenir.

Puan yalnız orijinal **5 eğitim sahası** üzerinden hesaplanır. Seçim önce
`training_selection.json` dosyasına sabitlenir, sonra üç kontrol sahasının
karşılaştırmaları eklenir. Bu üç saha geçmiş çalışmalarda görüldüğünden
yeni bir kör doğrulama sayılmaz.

## Sınırlar

Yeni kullanıcı/azimut örnekleri, başka bölgeler veya farklı komşu sayıları
bu taramada denenmez. İyi çıkan aday için bunlar takip kontrolü gerektirir.
2025 KPI ile 2026 radyo verisi eşzamanlı gözlemler olarak kullanılmaz.
Experia SINR/RSRQ tanımları ve üç ek saha konumunun kaynağı soruları sürer.

Ana projenin kodu ve sabit başlangıç senaryosu korunur. Sonuçlar ayrı deney
klasöründe tutulur; iyi çıkan aday otomatik olarak gerçek ağ modeli veya
projenin yeni başlangıcı ilan edilmez.
