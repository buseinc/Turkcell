# 30 — Depremlerden sonra hangi hücreler sustu? (KPI'daki hücre erişilebilirliği)

**Amaç:** Saha çökmesi senaryosunu uydurma değil, gerçekte olan kesintiye dayandırmak.

**Veri:** Deney 09'daki 15 dakikalık KPI. 47 saha var: 8'i değerlendirme sahası, gerisi komşu tampon sahalar.

**Yöntem:** Her deprem için, depremin olduğu andan 24 saat sonrasına kadarki pencereye bakıldı (`kesinti.py`).
- Bir önceki gün zaten kapalı olan hücreler sayılmadı. Bunlar depremden bağımsız, sürekli arızalı hücreler (örneğin 553).
- Kesinti süresi şöyle hesaplandı: her 15 dakikalık dilim için (1 − erişilebilirlik) × 0,25 saat, sonra dilimler toplandı.

## Sonuç

**10 Ağustos 2025, saat 19:53 depremi**

| Saha | Ne oldu |
|---|---|
| **130** (değerlendirme) | 7 hücreden 6'sı 21:30–22:00 arasında tamamen sustu: depremden yaklaşık 1,5 saat sonra, yarım saat boyunca. Öncesinde bu hücrelerde yaklaşık 93 bağlı kullanıcı vardı. |
| 484 (tampon) | 2 hücrede kısa, kısmi düşüşler oldu. |
| 494 (tampon, tek hücre) | Ertesi gün yaklaşık 10 saat kapalı kaldı. |

**27 Ekim 2025, saat 22:48 depremi**

| Saha | Ne oldu |
|---|---|
| **482** (değerlendirme) | Bir hücresi depremden yaklaşık 2,5 saat sonra (01:15'te) sustu ve yaklaşık **19 saat** kapalı kaldı. Öncesinde sahada yaklaşık 55 bağlı kullanıcı vardı. Kesinti sırasında 482'nin kullanıcı sayısı normalin %61'ine düştü. |
| 438, 199, 389, 208, 205, 283 (tampon) | 28 Ekim öğleden sonra, 11:45–22:00 arasında, aynı anda birden çok sahada saatlerce kesinti oldu. Bunun artçı sarsıntı, bölgesel elektrik kesintisi ya da bakım olup olmadığı veriden anlaşılmıyor. Bu sahalar simülasyondaki 24 sahanın içinde değil. |

**Ortak örüntü:** İki değerlendirme sahasında da kesinti depremle aynı anda değil, **1,5–2,5 saat sonra** başlıyor. Muhtemel sebep şu: şebeke elektriği deprem anında kesiliyor, saha bir süre yedek akülerle çalışıyor, aküler bitince saha susuyor. Bu bir tahmin; veri tek başına bunu kanıtlamıyor.

**Komşuya kayma:** 482 kapalıyken yakındaki 443 ve 441 sahalarında kullanıcı sayısı normalin yaklaşık 1,5 katına çıktı. Ama depremden sonra bölgenin her yerinde kullanıcı sayısı zaten yaklaşık 2 katına çıkıyor. Bu yüzden artışın ne kadarının 482'den kayan kullanıcılardan geldiği ayrılamıyor.

## Kesinti senaryosu için öneri

Senaryolar gerçekten yaşanmış kesintilere dayanıyor.

| Senaryo | Ne kapatılıyor | Yük |
|---|---|---|
| K1 | 482 sahasının tamamı | Deprem yükü (KPI ×2) |
| K2 | 130 sahasının tamamı | Deprem yükü |
| K3 | 482 ve 130 birlikte | Deprem yükü (daha kötü bir durum) |

Her senaryoda şunlara bakılacak:
- Kaç kullanıcı hiç bağlanamıyor (kapsama boşluğu)?
- Komşu hücreler kayan yükü taşıyabiliyor mu?
- Konuşabilenlerin oranı ne?

Bu sonuçlar sonraki adımda İHA'nın nereye konulacağına karar vermek için kullanılacak.
