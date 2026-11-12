# Güncel envanterle hocanın seçiminin yeniden kontrolü — 12 Kasım 2026

Hocanın 8 ana + 8 komşu sahası bütün güncel topolojilerde korundu. 64 kullanıcı, önceki seçilmiş ayar, 4 s koşu ve 1 s ısınma kullanıldı. Ayar yeniden seçilmedi.

| Koşu | Eğitim MAE RSRP/SINR/RSRQ | Kontrol MAE RSRP/SINR/RSRQ | Eski 24 ile eşli kontrol |
|---|---|---|---|
| addition_549 | 2.926 / 3.395 / 2.526 | 2.143 / 5.263 / 3.787 | True |
| updated_16 | 2.926 / 3.467 / 2.605 | 2.143 / 5.248 / 3.885 | True |
| updated_24 | 2.926 / 3.433 / 2.532 | 2.143 / 5.462 / 3.795 | True |
| updated_32 | 2.926 / 3.352 / 2.508 | 2.143 / 5.262 / 3.771 | True |
| updated_48 | 2.926 / 3.488 / 2.484 | 2.143 / 5.252 / 3.748 | True |
| updated_draw_1 | 3.540 / 3.383 / 2.737 | 4.105 / 3.293 / 4.307 | True |
| updated_draw_2 | 3.989 / 2.973 / 2.464 | 2.628 / 2.146 / 4.118 | True |

Komşu genişletme kontrolleri:

```json
[
  {
    "from_sites": 16,
    "to_sites": 24,
    "paired_ues": 64,
    "rsrp_q95_abs_change_db": 0.0,
    "sinr_q95_abs_change_db": 0.5494799152053723,
    "same_serving_sector_fraction": 1.0,
    "passed": true
  },
  {
    "from_sites": 24,
    "to_sites": 32,
    "paired_ues": 64,
    "rsrp_q95_abs_change_db": 0.0,
    "sinr_q95_abs_change_db": 0.5971388892393541,
    "same_serving_sector_fraction": 1.0,
    "passed": true
  },
  {
    "from_sites": 32,
    "to_sites": 48,
    "paired_ues": 64,
    "rsrp_q95_abs_change_db": 0.0,
    "sinr_q95_abs_change_db": 0.5770388275365242,
    "same_serving_sector_fraction": 1.0,
    "passed": true
  }
]
```

Eski eşli kontrol, aynı UE/anten örneğinin önceki 24 saha koşusuyla yapılır. 16 saha hocanın başlangıcıdır; 25 saha yalnız 549 ekleme tanısıdır. Sonuçlar düşük yük pilotudur; gerçek kapasite doğrulaması değildir. Yeni dosyada konumu teyit edilen üç saha zaten eski deneylerde yer alıyordu.

[Tam sayısal sonuç](result.json) — [Önceden kaydedilen plan](plan.json)
## Güncel 24 saha: üç ortak tekrar özeti

| Kontrol MAE (dB) | Önceki envanter | Güncel envanter |
|---|---:|---:|
| RSRP | 2.959 | 2.959 |
| SINR | 3.636 | 3.633 |
| RSRQ | 4.081 | 4.073 |

Eski–yeni eşli karşılaştırmaların üçü de geçti: True. 24→32→48 iki genişletme geçti: True. Tüm yedi koşuda en az 64/64 bağlı ve 64/64 veri alan kullanıcı. Üç tekrarda eğitim kapsamı 15/15, kontrol 9/9.

Bu çalışma eski seçilen ayarı yeniden sınar; bütün alternatiflerin yeni envanterde sıralamasını yeniden ölçmez. Önceki tam taramanın tekrarlanmasını gerektirecek büyük bir etki olup olmadığı eşli kontrollerle değerlendirilir. Yeni koşular 4 s olduğundan eski 8 s sonucu güncel envanterin sonucu olarak sunulmaz.

[Karşılaştırma grafiği](guncel_karsilastirma.png) — [Sayısal özet](summary.json)

**Karar:** Seçilen ayarla güncel 24 sahayı çalışma başlangıcı olarak korumak destekleniyor. Bu sınırlı güncelleme için bütün eski ayar taramasını tekrarlamak gerekmiyor. Sonraki adım kullanıcı örneklemi duyarlılığı; radyo tanımı ve yük modeli soruları devam ediyor.