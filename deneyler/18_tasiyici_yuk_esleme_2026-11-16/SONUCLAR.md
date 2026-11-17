# Deney 18 — taşıyıcı yükünü eşleme

**Durum: Yük ayarı ve üç örnek tamamlandı. Yük eşleme ölçütleri geçti.**

Amaç, Deney 17’nin 800 MHz katmanındaki düşük doluluğu düzeltip aynı ağ yapısını benzer dolulukta karşılaştırmak. Hücre grupları, frekanslar, güçler, kullanıcı konumları ve taşıyıcı atamaları değişmeyecek.

Başlangıç: 701 örneğinde B20 PRB 0.09344, hedef 0,233. Eski yük paket aralığı 12.618026 ms; ilk aday 6.309013 ms (sınırsız oran tahmini 5,060208 ms; önceden yazılan 0,5× adım sınırı uygulandı). Aralık küçüldükçe daha çok trafik verilir.

Yalnız B20’deki 14 yapay yük kullanıcısının paket aralığı ayarlanır. B1 zaten hedefin ±%10 aralığında olduğu için değiştirilmez; B3 ve ölçüm kullanıcılarının trafiği de aynen korunur.

Ayarlama yalnız 701 örneğinin benzetim PRB’sine göre yapılır. 440 dahil bütün B20 hücrelerinin yük sayaçları kullanılır; hiçbir sahanın Experia sinyal hatası ayarı seçmekte kullanılmaz. Bu bir güç/frekans kalibrasyonu değildir.

Kural: En fazla dört yeni kalibrasyon koşusu; 701’de hedefin ±%5’ine ulaşan ilk aday sabitlenir. Sonra aynı aralık, ayarlamada kullanılmayan 702 ve 703 örneklerinde ±%10 sınırıyla kontrol edilir. Bu iki sonuç görüldükten sonra aralık değiştirilmez.

Simülasyon kodu ve çalıştırıcı Deney 17 ile dosya düzeyinde aynı. Önceden geçen 20 kod kontrolü ve S0 karşılaştırması kaynak/binary hash’leriyle taşındı. Yeni kod eklenmediği için S0’ın pahalı tam koşusu tekrar edilmeyecek; aynı binary’nin küçük kontrolleri yeniden çalıştırılacak.

Birinci başarılı pilot, 701’in nihai sonucu olarak kullanılacak; aynı koşu ikinci kez yapılmayacak. Önceki deneyler değiştirilmeyecek. Kalibrasyon planı plan.json, seçilen aralık calibration.json, nihai kıyas comparison.json içinde; kullanıcıya yönelik tek rapor bu dosyadır.

## ns-3 sonuçları

## Yük ayarı

701 örneğiyle seçilen B20 paket aralığı: **5.021216 ms**. Hedef PRB 0,233. Aynı aralık 702 ve 703’e değiştirilmeden uygulandı. 701’in başarılı kalibrasyon koşusu tekrar çalıştırılmadan nihai sonuç olarak kullanıldı.

| Örnek | B3 PRB | B20 PRB | B1 PRB | Ağ ortalaması | B20 hedef aralığında |
|---|---:|---:|---:|---:|---|
| 701 | 0.250 | 0.227 | 0.223 | 0.243 | Evet |
| 702 | 0.255 | 0.226 | 0.223 | 0.247 | Evet |
| 703 | 0.245 | 0.225 | 0.222 | 0.239 | Evet |

**Yük eşleme: Geçti.**

**Yalnız yük değişikliği kontrolleri: Geçti; hücre yapısı, taşıyıcı atamaları ve RSRP korundu.**

## Ölçümlerle karşılaştırma

| Senaryo | Kontrolde RSRP farkı | Kontrolde SINR farkı | Ağ PRB ortalaması |
|---|---:|---:|---:|
| S0 | 1.72 | 2.15 | 0.254 |
| G17 | 2.64 | 3.61 | 0.224 |
| L18 | 2.64 | 3.44 | 0.243 |

Farklar dB, küçük değer daha iyi. S0 eski tek taşıyıcılı referans; G17 yük eşlemesi öncesi gruplamalı model; L18 aynı modelin yalnız B20 trafiği düzeltilmiş sürümü.

Yük eşlemesi sinyal gücü ayarı değildir. Sinyal gücü farkının değişmemesi beklenir; SINR karşılaştırması benzer dolulukta yeniden yapılmıştır. Bantlar, güçler, kullanıcıların taşıyıcı payları ve gerçek anten yönleri hâlâ varsayım; bu işlem bunları doğrulamaz.

Benzer doluluk, aynı toplam trafik veya aynı toplam güç demek değildir. B20’ye daha fazla trafik verilmesi planlıdır; yeni sunulan trafik miktarı input CSV’lerinden yeniden hesaplanabilir. Her hücredeki doluluk da birebir aynı değildir; kabul ölçütü taşıyıcı ortalamasıdır.

| Örnek | Bağlanan / 256 | Veri alan / 256 | RSRP en büyük değişim (dB) |
|---|---:|---:|---:|
| 701 | 256 | 255 | 0.00000000 |
| 702 | 256 | 256 | 0.00000000 |
| 703 | 256 | 256 | 0.00000000 |

Hiçbir paket aralığı Experia RSRP/SINR hatasına göre seçilmedi. 702/703 sonuçları görüldükten sonra seçilen aralık değiştirilmedi. Eski deneyler korunur; S0 otomatik değiştirilmez.
