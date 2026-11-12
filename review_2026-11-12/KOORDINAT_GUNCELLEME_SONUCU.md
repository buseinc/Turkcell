# Güncel hücre/koordinat dosyası kontrolü — 12 Kasım 2026

> **Aynı gün tamamlanan takip:** Güncel envanterle yedi native koşu tamamlandı; hocanın 8+8 seçimi korundu. 24→32→48 komşu kontrolleri ve üç kullanıcı örneğinde eski–yeni eşli kontroller geçti. [Güncel deney sonuçları](../experiments/inventory_refresh_2026-11-12/SONUCLAR.md). Aşağıdaki “henüz simüle edilmedi” ifadeleri ilk dosya denetiminin tarihsel durumudur.

**553, 554 ve 555 artık güncel ana koordinat dosyasında bulunuyor.** Üçünün konumu ve seçimdeki hücre–saha bağlantıları yeni dosyayla uyuşuyor. “Ana envanterde yok” sorusu bu sürüm için kapandı. Bu, sağlanan dosyalar arasında doğrulamadır; bağımsız saha ölçümü yapıldığı anlamına gelmez.

Karşılaştırılan kaynaklar:

- Güncel: [cell_site_coordinates.xlsx](../turkcell_tam_paket_2026-11-10/cell_site_coordinates/cell_site_coordinates.xlsx), `Sheet1`, A1:D6476.
- Önceki: [10 Kasım PC denetimindeki kopya](../pc_validation/20261110_pc/analysis_workspace/cell_site_coordinates/cell_site_coordinates.xlsx), `Sheet1`, A1:D5722.
- Seçim: [saha listesi](../turkcell_tam_paket_2026-11-10/sindirgi_lte_sites.csv) ve [96 hücre bağlantısı](../turkcell_tam_paket_2026-11-10/sindirgi_lte_cells.csv).

| Saha | Seçimdeki rol | Güncel envanter hücre sayısı | Güncel Excel satırları | Seçim koordinatından fark |
|---|---|---:|---|---:|
| SITE_000553 | Komşu | 6 | 6016–6021 | 0,024 m |
| SITE_000554 | Ana/değerlendirme | 2 | 6040–6041 | 0,057 m |
| SITE_000555 | Komşu | 3 | 6042–6044 | 0,035 m |

Santimetre düzeyindeki farklar, seçim CSV'sindeki altı ondalık basamaklı koordinatlarla uyumludur. İlk seçimin 16 sahasının tamamı bulundu; seçili 96 hücrenin 96'sı aynı saha ile eşleşti. Üç sahadaki hücre sayısı toplamı 11'dir; önceki rapordaki 15 eksik hücre bağlantısı tüm 16 saha içindi, yalnız bu üç sahanın toplamı değildi.

## Envanterde ne değişti?

| Ölçü | Önceki dosya | Güncel dosya |
|---|---:|---:|
| Benzersiz hücre | 5.721 | 6.475 |
| Benzersiz saha | 516 | 563 |
| Experia hücrelerinden koordinatı bulunan | 5.144 | 5.867 |
| Experia hücrelerinden koordinatı bulunmayan | 723 | 0 |

754 hücre ve 47 saha eklenmiş. Önceki 5.721 hücrenin hiçbirinin saha/koordinat kaydı değişmemiş ve hiçbiri çıkarılmamış. Güncel dosyada yinelenen hücre kimliği veya aynı saha için farklı koordinat bulunmadı. Experia eşleşmesi, önceki denetimde çıkarılmış 5.867 kimlik içeren hücre özetinden yeniden yapıldı; tüm ham Experia dosyası bu kontrolde yeniden taranmadı.

## Simülasyona etkisi

Güncel envanter ve mevcut Experia kimlikleriyle ana sekiz saha ve ilk sekiz komşu seçimi aynı kalıyor. Önceki 24/32/48 sahalık deneylerde kullanılan bütün sahalar yeni dosyada da var; kullanılan coğrafi konumlarla fark en fazla 0,057 m.

Ancak envanter genişlediği için **yakın komşu sıralaması genişletilmiş listelerde değişiyor**. Aynı ana sekize en yakın sahalar kuralıyla:

| Toplam saha | Güncel listede eklenecek | Sabit sayı nedeniyle listeden çıkacak |
|---|---|---|
| 24 | 549 | 162 |
| 32 | 549 | 490 |
| 48 | 549, 552 | 276, 436 |

549, verilen referansın yaklaşık 18,15 km çevresinde ve Experia bağlantısı var. Eski 24 sahalık senaryoda bulunmuyordu. Bu nedenle geçmiş komşu yakınsaması kontrolleri **eski dondurulmuş topoloji** için geçerlidir. Sonraki teknik adım güncel envanterle komşu listesini yeniden üretmek ve seçili ayarı bu listede karşılaştırmaktır. Yeni komşu etkisi henüz simüle edilmedi; önceki sonuçlar güncellenmiş ağın sonucu gibi sunulmamalı.

Eski deney girdileri ve ölçüm hedefleri bu kontrolde değiştirilmedi. Önceki `analysis/` özetleri ve eski haritalar da otomatik yeniden üretilmedi; 516 saha veya eksik koordinat ifadeleri bu nedenle tarihsel sürüme aittir. Aktif giriş notlarına bu güncellemeye bağlantı eklendi.

Kontrolün sayısal kaydı ve kaynak SHA-256 değerleri: [coordinate_check.json](coordinate_check.json). Tekrar üretim: proje kökünde `.venv\Scripts\python.exe review_2026-11-12/check_updated_inventory.py`.

Hocaya sorulacak güncel konular: Experia SINR/RSRQ tanımları, TAAVG ve KPI birimleri; mevcut başlangıcın yük pilotuna geçiş için yeterliliği. Üç sahanın ana dosyada bulunamaması artık açık soru olarak gönderilmemeli.
