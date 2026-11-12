# Önce saha konumlarını karşılaştırma

Danışmanın “yakındaki bütün sahaları ve ChatGPT seçimini aynı haritada gösterin” isteği için ana envanter ve seçim dosyası ayrı ayrı okundu. Ana envantere seçimden konum eklenmedi; radyo verisi bulunması şartı uygulanmadı.

- [Coğrafi harita](analysis/sindirgi/konum_kontrolu/harita.html): yakınlaşma, katman açma/kapama ve noktalara tıklama. Esri topoğrafik zemini internet kullanır; erişim kesilirse yerel referans çizgilerine otomatik geçilir. Sağ üstten “Sade koordinat zemini (çevrimdışı)” elle de seçilebilir. Varsayılan yakın çevre 30 km; diğer 490 envanter sahası da katman olarak açılabilir.
- [Kartezyen görünüm](analysis/sindirgi/konum_kontrolu/kartezyen.html): internet gerektirmeyen, metre cinsinden etkileşimli grafik. “Tüm ana envanter” düğmesi 516 sahayı birlikte gösterir.
- [PNG](analysis/sindirgi/konum_kontrolu/konum_karsilastirma.png) / [SVG](analysis/sindirgi/konum_kontrolu/konum_karsilastirma.svg): dışa aktarılabilir karşılaştırma. Etiketlerde saha kimliğinin `SITE_` sonrası gösterilir.

## Harita nasıl okunur?

Gri dolu noktalar ana Excel'deki konumlar; mavi çemberler seçilmiş 8 ana saha, turuncu çemberler seçilmiş 8 komşu sahadır. Çemberin içindeki gri nokta iki kaynağın örtüştüğünü gösterir. Mor çarpı, kimliğin ana koordinat Excel'inde bulunmadığını belirtir. Kırmızı yıldız verilen deprem merkezidir. Çember işaretleri anten kapsaması değildir.

## Sonuç

Ana envanterde 516 saha var; merkezin 30 km çevresine 26'sı düşüyor. ChatGPT'nin 16 seçiminden 13'ü bu ham konumlarla örtüşüyor, ortak kimliklerde koordinat çelişkisi yok. En büyük fark 0,059 m; altı ondalığa yuvarlama düzeyiyle uyumlu. Karşılaştırma toleransı 1 m seçildi.

`SITE_000553`, `SITE_000554`, `SITE_000555` seçim dosyasında konumlu, ana envanterde yok. Haritada bu üç seçim ayrı gösteriliyor; bağımsız doğrulama yerine geçmiyor. Birlikte gösterildiğinde yakın çevrede 29 farklı konum görülmesinin nedeni bu ek üç noktadır. Bunların asıl kaynağı hocaya sorulacak.

## Referans ve dosyalar

Referans: 39,2461 N / 28,0697 E → `(x,y) = (0,0)`. WGS84 varsayımıyla ECEF üzerinden yerel ENU'ya dönüşüm yapıldı: `x_dogu_m` doğuya, `y_kuzey_m` kuzeye doğru artar. `enu_up_egirilik_m`, arazi yüksekliği değildir. Örneğin `SITE_000440` yaklaşık `(2344,68; −3713,19)` m: merkezin 2,34 km doğusunda, 3,71 km güneyinde.

| Dosya | Kapsam |
|---|---|
| [ana_envanter_kartezyen.csv](analysis/sindirgi/konum_kontrolu/ana_envanter_kartezyen.csv) | Ana Excel'den 516 sahanın konumu ve yerel koordinatları |
| [ana_envanter_yakin_30km.csv](analysis/sindirgi/konum_kontrolu/ana_envanter_yakin_30km.csv) | Yakın çevredeki 26 ana envanter sahası |
| [chatgpt_secimi_kartezyen.csv](analysis/sindirgi/konum_kontrolu/chatgpt_secimi_kartezyen.csv) | Seçim dosyasındaki 16 sahanın kendi konumları ve yerel koordinatları |
| [eslesme_kontrolu.csv](analysis/sindirgi/konum_kontrolu/eslesme_kontrolu.csv) | Her seçim için iki kaynağın koordinatları, farkı ve eşleşme durumu |
| [ozet.json](analysis/sindirgi/konum_kontrolu/ozet.json) | Sayımlar, yöntem, kaynak dosya özetleri |

Tekrar üretim: proje kökünde `python analysis/compare_site_locations.py`. Kaynak dosyalar ve mevcut simülasyon girdileri değiştirilmez. 30 km yalnızca gösterim tercihidir; deprem hasarı veya radyo kapsaması sınırı değildir. Referans koordinatı danışmandan alındı; harici deprem kataloğu doğrulaması yapılmadı.

## Arka plan erişim hatasının düzeltilmesi

OSM Standard katmanı yerel önizlemede 403 “Access blocked” görüntüleri verdi. Bu katman kaldırıldı. Harita çalışma dosyaları HTML'ye gömüldü; CDN olmadan da noktalar, açılır bilgiler ve katmanlar çalışır. İsteğe bağlı çevrimiçi zemin, [Esri'nin yayımladığı harita servisidir](https://developers.arcgis.com/web-map-specification/objects/mapServiceLayer/); atıflar haritada korunur. Ağ/zemin hatasında otomatik çevrimdışı görünüm kullanılır. Bu değişiklik koordinatları veya 13+3 eşleşme sonucunu etkilemez.
