# Üç sahanın koordinat envanterinde bulunmaması

> **12 Kasım güncel sonuç:** Hocanın 8 ana + 8 komşu sahası güncel envanterle doğrulandı ve korundu. Yeni yakın sahalarla yedi simülasyon koşusu tamamlandı; komşu genişletmeleri ve üç kullanıcı örneğinin eski–yeni kontrolleri geçti. Güncel 24 sahada kontrol MAE: RSRP 2,96 / SINR 3,63 / RSRQ 4,07 dB. [Sonuçlar ve grafik](../deneyler/07_guncel_envanter_kontrolu_2026-11-12/SONUCLAR.md) — [Hocaya güncel mesaj](../toplantilar/2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/HOCAYA_MESAJ.md). Aşağıdaki 516 saha/eksik koordinat ifadeleri ve eski tablolar tarihsel sürümdür; güncel envanter 563 saha / 6.475 hücredir.

İnceleme: 9 Kasım 2026. Konu: `SITE_000553`, `SITE_000554`, `SITE_000555`.

**Kapsamı netleştirme:** Bu üç sahanın koordinatları elimizdeki `sindirgi_lte_sites.csv` ve seçim XLSX'inde vardır; hücre bağlantıları da `sindirgi_lte_cells.csv` içindedir. Bulunmadıkları kaynak ana `cell_site_coordinates.xlsx` dosyasıdır. “Projedeki hiçbir dosyada yoklar” sonucu çıkarılmamalı. 13 kaynak XLSX'in tüm çalışma sayfası XML'leri ve ortak metin tabloları ayrıca tarandı; üç saha kimliği yalnızca seçim XLSX'inde bulundu. [Dosya bazında tarama](analysis/sindirgi/site_id_presence_check.json).

## Doğrudan kaynaklardan doğrulananlar

Ana koordinat XLSX'inin 5.721 farklı hücre kimliği, **3 Ağustos 2025 KPI dosyasının 5.721 hücresiyle birebir aynı**. İki küme arasında tek bir fazla/eksik kimlik yok. Bu, yalnızca satır sayısı benzerliği değildir; ham KPI XML'indeki kimlikler yeniden taranarak karşılaştırıldı.

| Seçim dosyasında belirtilen saha | Atanan hücre sayısı | 3 Ağustos 2025 KPI | 9 Ağustos ve sonraki verilen KPI günleri | Experia, Haziran 2026 |
|---|---:|---|---|---|
| `SITE_000553` | 3 | Hiçbiri yok | Üçü de var | Üçü de var |
| `SITE_000554` | 2 | Hiçbiri yok | İkisi de var | İkisi de var |
| `SITE_000555` | 3 | Hiçbiri yok | Üçü de var | Üçü de var |

Hücreler sırasıyla `CELL_006016/006018/006020`, `CELL_006039/006040`, `CELL_006041/006042/006043`. On KPI dosyasının tamamı yeniden tarandı. Bu 8 hücre için Experia'nın ham dosyasında toplam 1.245 saatlik kayıt bulundu; hepsi aynı anonim `DISTRICT_0019` etiketini taşıyor. Bu, hücrelerin ölçüm kaynaklarında var olduğunu doğrular; ilçe etiketi tam koordinatı veya saha kimliğini doğrulamaz.

Ana koordinat dosyasında tek görünür sayfa var; gizli sayfa/satır, filtre veya dış bağlantı bu eksikliği açıklamıyor. Saha kimlikleri `SITE_000001`–`SITE_000517` aralığında, 516 farklı saha içeriyor. Kimliklerin sayı sırası, fiziksel kurulum tarihi olarak yorumlanamaz.

Seçim dosyasındaki üç koordinat, başka bir kimlikle ana envanterde de yok. En yakın envanter koordinatı 553 için yaklaşık 5,71 km, 554 için 6,39 km, 555 için 3,49 km uzakta. Bu farklar koordinat yuvarlamasıyla açıklanamaz.

## En güçlü açıklama ve belirsiz kalan kısım

Koordinat tablosunun yalnızca ilk verilen KPI günündeki hücrelere göre hazırlanmış/filtrelenmiş olması güçlü bir olasılık. Sonraki dosyalarda bulunan hücrelerin koordinat eşlemesinin dışında kalması bu örüntüyle uyumlu. Ancak tabloyu üreten kod veya filtre tarifi verilmediği için bu neden **kesinleşmiş değil**. Koordinat dosyasında geçerlilik tarihi bulunmuyor; bu dosyaya doğrudan “3 Ağustos tarihli envanter” denemez.

Seçim dosyası daha geniş bir koordinat kaynağı kullanmış olabilir; üç ek konumun elle veya başka bir işlemle eklenmiş olması da mevcut dosyalardan ayırt edilemiyor. Seçim XLSX'i ve iki CSV birbirlerinin kopyası olduğundan bunlar üç bağımsız konum doğrulaması sayılmaz. Hücre–saha bağlantıları ve koordinatlar için bağımsız dayanak hâlâ yok.

8 hücrenin 3 Ağustos kaydında bulunmaması, o gün fiziksel olarak kurulu olmadıklarını kanıtlamaz. Sağlanan dosyalar içinde ilk görüldükleri gün 9 Ağustos'tur; aradaki günler elimizde yoktur. Bu nedenle yeni kurulum, devreye alma veya kesinti nedeni çıkarılamaz.

## Kaynağı netleştirecek soru

“Ana koordinat dosyasındaki hücre kümesi 3 Ağustos 2025 KPI kümesiyle aynı. `SITE_000553/554/555` için hücreler 9 Ağustos ve sonrasında mevcut, fakat koordinatları ana dosyada yok. Seçim ekindeki bu üç konumu ve hücre–saha bağlantısını hangi ana envanterden veya işlemden aldınız? Tam koordinat listesi ve seçim üretim kodu paylaşılabilir mi?”

## Tekrar üretim

Proje kökünde `python analysis/investigate_missing_sites.py`. Kaynak XLSX'ler değiştirilmez. [Ham kontrol sonuçları](analysis/sindirgi/missing_sites_investigation.json) ve [gün/hücre kayıt sayıları](analysis/sindirgi/missing_site_cell_timeline.csv) kaydedilir. Kaynaklardaki hücre varlığı doğrulandı; simülasyondaki üç ek konumun `selection_csv` kaynak etiketi korunuyor.
