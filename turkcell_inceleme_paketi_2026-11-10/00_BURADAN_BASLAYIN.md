# Buradan başlayın — İNCELEME PAKETİ

Paketleme tarihi: 10 Kasım 2026. Bu paket kodları, özet CSV'leri, haritaları, deney girdilerini ve hazır sonuçları içerir. Büyük boyutlu 12 ana kaynak Excel dosyası bu sürümde yoktur; seçim XLSX'i dahildir. Ana Excel'lerden yeniden veri üretmek için tam paket gerekir.

ZIP'i önce bir klasöre çıkarın. Markdown dosyaları VS Code veya bir Markdown okuyucuyla; HTML haritaları tarayıcıyla; CSV'ler Excel veya Python ile açılabilir. ZIP içinden doğrudan çalıştırmayın.

## Hangi belgeyi okuyayım?

Belgeler birleştirilmedi. Hepsi bu klasörde, konularına göre ayrı dosyalardır.

| Belge | Ne için okunur? |
|---|---|
| [01 — Veri ve proje özeti](01_VERI_VE_PROJE_OZETI.md) | Kaynak veriler, bulgular, tamamlanan işler ve hocaya sorulacak sorular. İlk okunacak belge. |
| [02 — Sındırgı saha seçimi](02_SINDIRGI_SAHA_SECIMI.md) | İlk 8 ana ve 8 komşu sahanın seçimi; koordinat dönüşümü ve tarihsel başlangıç. |
| [03 — Konum ve harita kontrolü](03_KONUM_VE_HARITA_KONTROLU.md) | Ana koordinat envanteriyle seçim dosyasının karşılaştırması ve harita renkleri. |
| [04 — ns-3 ve çalıştırma](04_NS3_VE_CALISTIRMA.md) | Simülatör, varsayımlar, ilk testler ve yeniden çalıştırma adımları. |
| [05 — Radyo deneyleri ve sonuçlar](05_RADYO_DENEYLERI_VE_SONUCLAR.md) | Güncel deneylerin yöntemi, ortalama hesabı, grafikler ve başarı sınırları. |
| [06 — Eksik koordinat araştırması](06_EKSIK_KOORDINAT_ARASTIRMASI.md) | 553/554/555 numaralı sahaların ana envanterde bulunmaması ve kaynak kanıtları. |
| [07 — Harita kütüphaneleri](07_HARITA_KUTUPHANELERI.md) | Haritaların kullandığı yerel dosyalar, lisanslar ve çevrimiçi zemin. |
| [08 — Dosya rehberi](08_DOSYA_REHBERI.md) | Kodların, veri tablolarının, grafiklerin ve sonuç klasörlerinin görevleri. |

## Önce açılabilecek çıktılar

- [Sahaların coğrafi haritası](analysis/sindirgi/konum_kontrolu/harita.html).
- [İnternetsiz Kartezyen konum grafiği](analysis/sindirgi/konum_kontrolu/kartezyen.html).
- [Güncel saha bazlı ölçüm–simülasyon karşılaştırması](analysis/sindirgi/radio_study/final_site_comparison.png).
- [Sabitlenen son senaryo](analysis/sindirgi/radio_study/frozen/configuration.json).

Haritadaki noktalar saha konumudur; kapsama veya deprem hasarı sınırı değildir. Coğrafi haritanın zemin görüntüsü internet kullanır; erişim olmazsa yerel çizgiler gösterilir. Kartezyen grafik internet gerektirmez.

## Şu an neredeyiz?

Radyo karşılaştırma deneyleri tamamlandı. Son senaryoda 8 ana ve 16 komşu saha, saha başına 3 varsayımsal sektör ve 64 sanal kullanıcı cihazı var. Ayrılmış üç kontrol sahasında RSRP ortalama mutlak hatası 3,86 dB; SINR ve RSRQ hataları 9,97 ve 5,42 dB. Sinyal gücünde belirlenen başlangıç hedefi sağlandı; sinyal kalitesinin gerçek ölçümlerle uyumu henüz doğrulanmadı. Gerçek operatör ağının eksiksiz kopyası kurulmuş değildir.

Eski 16 saha/100 cihaz sonuçları da tarihsel karşılaştırma için tutuldu. Güncel sonuçlar `radio_study/` ve `simulation/results/stage3/` içindedir. Yük/stres çalışmaları henüz tamamlanmadı.

## Paketin düzeni

Kodların ve verilerin göreli klasör yapısı korundu; açıklama belgeleri bu kök klasöre taşındı ve belge bağlantıları düzeltildi. Asıl çalışma projesindeki dosyalar taşınmadı. Kodlar yeniden rapor üretirse kendi özgün klasörlerinde yeniden `README.md` oluşturabilir; kökteki belgeler paylaşım anının kopyasıdır.

`PAKET_ICERIGI.json`, dosya boyutlarını ve SHA-256 özetlerini içerir. `PAKET_DOGRULAMA.json`, bağlantı ve içerik kontrollerini kaydeder. Tarihsel sonuçlardaki mutlak bilgisayar yolları ve kaynak özetleri değiştirilmedi. Derleme ürünleri, Python önbellekleri ve tarayıcı profilleri paketlenmedi.

Hazır sonuçları okumak için Python veya ns-3 gerekmez. Yeniden üretim için [çalıştırma belgesine](04_NS3_VE_CALISTIRMA.md) bakın. Python analiz bağımlılıkları `requirements-analysis.txt` dosyasında bu bilgisayardaki sürümleriyle listelendi; başka bir bilgisayarda kurulum testi yapılmadı. ns-3, Ubuntu/WSL ve tarayıcı bu dosyayla kurulmaz.

`EE550_Project.pdf` çalışma klasöründe bulunmadığından pakette yoktur. Danışman notları ve LaTeX taslağı dahildir.
