# 28 — Stres testi: ses kapasitesi (ns-3'ün varsayılan zamanlayıcısıyla)

**Soru:** Deney 26'daki yeni modelde her hücre aynı anda kaç sesli görüşmeyi taşıyabilir?

**Kurulum:** Ayrıntılar `prepare.py` ve `plan.json`'da.
- Hücre başına N görüşme, N = 25 / 50 / 100.
- Arka planda normal günün veri yükü.
- Görüşme kalitesi ölçütleri 3GPP'ye göre:
  - Bir kullanıcı "konuşabiliyor" sayılır: paketlerinin %99'u 100 ms içinde ulaşıyorsa.
  - Bir hücre "taşıyor" sayılır: kullanıcılarının %98'i konuşabiliyorsa.

**200 ve 300'lük adımlar iptal edildi; hiç çalıştırılmadı.** Girdi dosyaları silindi. Aynı kullanıcı konumları deney 29'da `ues_V200_701.csv` ve `ues_V300_701.csv` olarak yeniden üretiliyor. Gerekçe aşağıda. Yarıda kalan süre ölçme denemesi de silindi.

## Sonuç

| Hücre başına görüşme | Ses kullanıcısı | Konuşabilen | Taşıyan hücre | Ortanca gecikme | Hücre doluluğu |
|---|---|---|---|---|---|
| 25 | 600 | %83,8 | 2/24 | 27 ms | %93 |
| 50 | 1200 | %85,6 | 1/24 | 38 ms | %99 |
| 100 | 2400 | %33,5 | 1/24 | 61 ms | %100 |

Bütün kullanıcılar bağlandı; "servis yok" durumunda kimse kalmadı.

## Neden güvenilmez: zamanlayıcı

**1. Hücreler gereğinden fazla dolu görünüyor.**
- ns-3'ün PF zamanlayıcısı, verisi olan her kullanıcıya bütün boş kaynak bloklarını veriyor. 72 baytlık tek bir ses paketi bile bütün bandı kaplayabiliyor. Bu, `pf-ff-mac-scheduler.cc` içindeki atama döngüsünde görülüyor.
- Bu yüzden hücreler 25 görüşmede bile %93 dolu görünüyor. Gerçek bir baz istasyonu bir ses paketine 1–2 kaynak bloğu verir; kaba hesapla bu kadar görüşme gerçekte yaklaşık %5 ek yük demek.

**2. Komşulara gereksiz girişim gidiyor.** `zayif_sinyal_kontrolu.py` bunu ölçüyor:

| | Ortanca SINR | 0 dB altındakiler |
|---|---|---|
| Experia, saatlik kayıtlar | 11,9 dB | ~%1 (alt sınır) |
| Model, normal yük (deney 26) | 17,2 dB | %3 |
| Model, hücre başına 25 görüşme | 6,0 dB | %21 |

**3. Konuşamayanlar bu zayıf sinyalli kullanıcılar.**
- 0 dB altındakilerin yalnızca %34'ü konuşabiliyor.
- 0 dB üstündekilerin %95–98'i konuşabiliyor.

**Ne yapıldı:** Zamanlayıcı düzeltilip test deney 29'da tekrarlanıyor. Bu deneydeki sayılar yalnızca "ns-3'ün varsayılan zamanlayıcısıyla en kötü durum" olarak kullanılmalı.
