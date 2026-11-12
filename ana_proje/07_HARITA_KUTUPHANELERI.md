# Yerel harita çalışma dosyaları

Leaflet 1.9.3 (BSD-2-Clause) ve jQuery 3.7.1 (MIT), kaynak ve lisanslarıyla bu dizine alındı. `sources.json` indirme URL'lerini ve SHA-256 özetlerini tutar. Oluşturulan harita HTML'lerine JS, CSS ve gerekli kontrol simgeleri gömülür; açılışta CDN erişimi gerekmez.

Harita zemini isteğe bağlı Esri World Topographic Map servisinden alınır; kaynak atıfları haritada görünür. Ağ/servis hatasında yerel koordinat çizgilerine otomatik geçilir. `tile.openstreetmap.org` kullanılmaz, harita karoları indirilip paketlenmez. Saha verileri ve dönüşümler bu değişiklikten etkilenmez.

Başvurular: [Esri'nin map service örneği](https://developers.arcgis.com/web-map-specification/objects/mapServiceLayer/), [OSM Standard tile kullanım politikası](https://operations.osmfoundation.org/policies/tiles/).
