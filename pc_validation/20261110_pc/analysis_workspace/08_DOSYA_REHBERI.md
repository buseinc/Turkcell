# Dosya rehberi

Bu belge, diğer raporları birleştirmez; hangi dosyanın ne işe yaradığını açıklar. Bağlantılar paket köküne göredir. `*` işareti aynı işi yapan dosya grubunu belirtir.

## Proje kökü ve ham kaynaklar

| Dosya veya klasör | Görevi |
|---|---|
| [advisors notes.txt](<advisors notes.txt>) | Danışmanın ilettiği çalışma notları ve öncelikler. |
| [main.tex](main.tex) | Projenin LaTeX taslağı; bütün güncel deney sonuçlarının işlendiği nihai metin değildir. |
| [sindirgi_lte_sites.csv](sindirgi_lte_sites.csv) | Danışmanın ilk 16 saha seçimi, konumları, rolleri ve özetleri. |
| [sindirgi_lte_cells.csv](sindirgi_lte_cells.csv) | Seçilen 96 hücrenin saha bağlantıları ve seçim özetleri. |
| [sindirgi_lte_site_selection.xlsx](sindirgi_lte_site_selection.xlsx) | Aynı seçimin Excel sayfaları ve senaryo açıklamaları; CSV'lerden bağımsız bir koordinat kaynağı değildir. |
| `cell_site_coordinates/cell_site_coordinates.xlsx` | 516 saha ve 5.721 hücrenin ana koordinat envanteri. Yalnız tam pakette. |
| `experia/experia.xlsx` | 22–28 Haziran 2026 saatlik hücre radyo ölçümleri. Yalnız tam pakette. |
| `LTE Main KPI_*/` | 2025'teki 10 gün için 15 dakikalık trafik ve hizmet göstergeleri. Klasör/dosya adları günü belirtir. Yalnız tam pakette. |
| `requirements-analysis.txt` | Analiz kodlarının Python paketleri ve paketleme sırasında kayıtlı sürümleri. |
| `PAKET_ICERIGI.json` | Dahil edilen dosyalar, boyutlar, SHA-256 özetleri ve taşınan belgelerin eski/yeni adları. |
| `PAKET_DOGRULAMA.json` | Paket içi bağlantı ve içerik kontrollerinin sonucu. |

## Temel veri tabloları — analysis/

| Dosya | Görevi |
|---|---|
| [site_inventory.csv](analysis/site_inventory.csv) | Ana envanterdeki her saha için hücre sayısı ve koordinatlar. |
| [radio_cell_summary.csv](analysis/radio_cell_summary.csv) | Her hücrenin mevcut saatlik kayıtlarından hesaplanan radyo özetleri. |
| [radio_site_summary.csv](analysis/radio_site_summary.csv) | Ana envanterdeki sahalar için hücre eşleşmeleri ve saha radyo özetleri. |
| [kpi_daily_summary.csv](analysis/kpi_daily_summary.csv) | KPI dosyalarının günlük sayımları. |
| [kpi_cell_site_pairs.csv](analysis/kpi_cell_site_pairs.csv) | KPI alanlarındaki hücre/saha etiketleri; KPI saha alanı fiziksel saha eşlemesi için güvenilir değildir. |
| `coordinates_audit.json`, `experia_audit.json`, `kpi_audit.json`, `LTE Main KPI_*_audit.json` | Kapsam, eksikler, tekrarlar, dağılımlar ve günlük kaynak denetimleri. |

## Analiz kodları — analysis/

Komutlar paket kökünden çalıştırılır. Ana kaynak denetimi büyük Excel dosyalarını tarar; inceleme paketinde bu kaynaklar yoktur.

| Kod | Görevi |
|---|---|
| [audit_dataset.py](analysis/audit_dataset.py) | Ana Excel kaynaklarını denetler; genel özet CSV ve JSON dosyalarını üretir. |
| [prepare_sindirgi.py](analysis/prepare_sindirgi.py) | İlk saha seçimini kontrol eder, yerel koordinatları ve ilk topoloji görsellerini üretir. |
| [explain_site_selection.py](analysis/explain_site_selection.py) | İlk 8 ana/8 komşu sahayı numaralı Türkçe görsel ve tabloyla anlatır. |
| [compare_site_locations.py](analysis/compare_site_locations.py) | Ana envanteri seçim dosyasıyla bağımsız karşılaştırır; konum haritalarını üretir. |
| [investigate_missing_sites.py](analysis/investigate_missing_sites.py) | Üç ek sahanın hücrelerini ham KPI/Experia kaynaklarında araştırır. |
| [map_background.py](analysis/map_background.py) | Haritalara yerel çalışma dosyalarını ve internet kesintisine dayanıklı zemin seçimini ekler. |
| [check_map_render.py](analysis/check_map_render.py) | Haritayı Chrome ile normal ve zemin erişimi engellenmiş koşullarda kontrol eder. Chrome yolu bilgisayara göre uyarlanır. |
| [summarize_baseline.py](analysis/summarize_baseline.py) | İlk 16 saha/100 cihaz koşusunu özetler; eski C++ kaynak özetini kontrol eder. |
| [prepare_radio_study.py](analysis/prepare_radio_study.py) | Güncel deney planını, sabit saha yönlerini, cihaz konumlarını ve gerçek ölçüm hedeflerini hazırlar. |
| [report_radio_study.py](analysis/report_radio_study.py) | Güncel deney sonuçlarından karşılaştırma tabloları, grafikler, rapor ve sabit senaryo kopyasını üretir. |

## Saha seçimi ve haritalar — analysis/sindirgi/

| Dosya veya alt klasör | Görevi |
|---|---|
| `01_saha_secimi.csv/.png/.svg` | İlk 16 sahanın numaralı listesi ve görsel anlatımı. |
| [candidate_sites.csv](analysis/sindirgi/candidate_sites.csv) | Ana envanter ve üç ek konumdan oluşan 519 bilinen aday. |
| [sites_local.csv](analysis/sindirgi/sites_local.csv) | İlk 16 sahanın simülasyona uygun yerel metre koordinatları. |
| [selected_cell_linkage.csv](analysis/sindirgi/selected_cell_linkage.csv) | Seçilen hücrelerin saha bağlantıları ve bağlantının hangi kaynaktan geldiği. |
| `site_map.html`, `topology_offline.html`, `site_positions.png/.svg` | İlk seçimin coğrafi haritası, internetsiz grafiği ve sabit görselleri. |
| `validation.json`, `coordinate_manifest.json` | Koordinat dönüşümü/seçim kontrolleri, yöntem ve kaynak özetleri. |
| `missing_sites_investigation.json`, `missing_site_cell_timeline.csv`, `site_id_presence_check.json` | Eksik üç saha araştırmasının sayısal kanıtları. Açıklaması kökteki 06 numaralı belgededir. |
| `baseline_summary.json`, `ue_radio_summary.csv`, `experia_evaluation_cells.csv` | İlk simülasyonun sayımları, cihaz özetleri ve 55 hücrenin ölçüm özetleri. |
| `ue_radio_samples.png/.svg`, `radio_distribution_comparison.png/.svg` | Tarihsel ilk simülasyonun cihaz haritası ve keşif amaçlı ölçüm karşılaştırması. Güncel başarı sonucu olarak okunmamalı. |
| [konum_kontrolu/harita.html](analysis/sindirgi/konum_kontrolu/harita.html) | Ham ana envanter ve ilk seçimin üst üste gösterildiği etkileşimli coğrafi harita. |
| [konum_kontrolu/kartezyen.html](analysis/sindirgi/konum_kontrolu/kartezyen.html) | Aynı kontrolün internetsiz, metre cinsinden etkileşimli görünümü. |
| `konum_kontrolu/ana_envanter_kartezyen.csv` | Ana envanterin 516 sahasının yerel koordinatları. |
| `konum_kontrolu/ana_envanter_yakin_30km.csv` | Referansın 30 km çevresindeki 26 ana envanter sahası. |
| `konum_kontrolu/chatgpt_secimi_kartezyen.csv` | İlk seçimin 16 konumu; ana envantere eklenmeden ayrı hesaplandı. |
| `konum_kontrolu/eslesme_kontrolu.csv`, `ozet.json` | Her seçimin konum farkı, eşleşme durumu ve genel sayımlar. |
| `konum_kontrolu/konum_karsilastirma.png/.svg` | Konum kontrolünün dışa aktarılabilir görselleri. |
| `konum_kontrolu/render_check/` | Haritanın tarayıcı kontrolleri, ekran görüntüleri, kayıtları ve test çıktıları. |
| `analysis/map_assets/` | Leaflet/jQuery dosyaları, kontrol simgeleri, lisanslar ve kaynak özetleri. |

## Güncel deneyler — analysis/sindirgi/radio_study/

| Dosya veya alt klasör | Görevi |
|---|---|
| [experiment_plan.json](analysis/sindirgi/radio_study/experiment_plan.json) | Deney seçenekleri, eğitim/kontrol ayrımı, başarı ve komşu saha kontrol eşikleri. |
| `inputs/sites_b*_az*.csv` | Komşu sayısı ve anten yönü düzenine göre saha girdileri. `az42/7/99` derece değil rastgele üretim numarasıdır. |
| `inputs/ues_*.csv` | Üç farklı varsayımsal yerleşimdeki 64 cihazın sabit konumları. |
| `inputs/sites_without_selection_only.csv` | Kaynağı doğrulanmayan üç konum çıkarılarak yapılan duyarlılık deneyinin girdisi. |
| [measured_site_targets.csv](analysis/sindirgi/radio_study/measured_site_targets.csv) | Gerçek radyo kayıtlarından hesaplanan sekiz sahanın hedef ortalamaları ve eğitim/kontrol ayrımı. |
| `screening_checkpoint.json`, `training_candidates.csv` | Dokuz yerleşim/yayılım adayının sonuçları ve eğitim hataları. |
| [selected_configuration.json](analysis/sindirgi/radio_study/selected_configuration.json) | Eğitim RSRP hatasına göre seçilen yerleşim ve model. |
| `azimuth_cases.json`, `azimuth_sensitivity.csv` | Üç anten yönü düzeninin sonuçları. |
| `buffer_checks.json`, `buffer_convergence.csv` | Komşu saha sayısı artınca aynı cihazlardaki değişim ve yakınsama kontrolleri. |
| [study_result.json](analysis/sindirgi/radio_study/study_result.json) | Son koşu, kontrol sahaları, süre/trafik ve belirsiz koordinat deneylerinin ayrıntılı toplu sonucu. |
| [final_site_comparison.csv](analysis/sindirgi/radio_study/final_site_comparison.csv) | Her ana saha için ölçüm, simülasyon ve hata değerleri. |
| [final_ue_metrics.csv](analysis/sindirgi/radio_study/final_ue_metrics.csv) | Son senaryodaki 64 cihazın bağlantı, sinyal ve veri alma sonuçları. |
| `training_comparison.png/.svg` | Dokuz adayın eğitim hatalarını gösteren grafik. |
| `final_site_comparison.png/.svg` | Sekiz saha için RSRP, SINR ve RSRQ karşılaştırması. |
| `buffer_convergence.png/.svg` | Komşu saha sayısının sonuçlara etkisi. |
| `azimuth_sensitivity.png/.svg` | Anten yönlerini değiştirmenin sonuçlara etkisi. |
| `final_ue_map.png/.svg` | Son senaryodaki cihaz noktalarının radyo değerleri; sürekli kapsama haritası değildir. |
| [frozen/configuration.json](analysis/sindirgi/radio_study/frozen/configuration.json) | Son senaryonun ayarları, varsayımları ve kaynak/girdi özetleri. |
| `frozen/sites.csv`, `frozen/ues.csv` | Son senaryonun 24 sahası ve 64 cihazının sabit girdileri. |

## Simülasyon kodları — simulation/

| Dosya | Görevi |
|---|---|
| [sindirgi_baseline.cc](simulation/sindirgi_baseline.cc) | Klasik LTE/EPC şebekesini kuran, cihazları bağlayan ve radyo/veri ölçümlerini yazan ns-3 C++ programı. |
| [run_baseline.py](simulation/run_baseline.py) | C++ programını yerel ns-3.44 ile derler ve tek bir senaryoyu çalıştırır. WSL/Linux içindir. |
| [run_radio_study.py](simulation/run_radio_study.py) | Güncel deneyleri sırayla yürütür, geçerli eski sonuçları yeniden kullanır, saha metriklerini ve karşılaştırmaları hesaplar. |
| [run_stock_smoke.py](simulation/run_stock_smoke.py) | ns-3'ün stok LTE/EPC örneğini derleyip çalıştırarak kurulumu kontrol eder. |
| [probe_environment.py](simulation/probe_environment.py) | ns-3 ve derleyici ortamının sürüm/yapılandırma bilgilerini kaydeder. |
| [inspect_radio_models.py](simulation/inspect_radio_models.py) | Kurulu ns-3 yayılım modeli kaynaklarını incelemeye yardımcı olur. |
| [environment.json](simulation/environment.json) | Sonuçların üretildiği bilgisayarın tarihsel ortam bilgisi; alıcının bilgisayarını tarif etmez. |
| `archive/<sha256>.cc` | Eski ve güncel sonuçların hangi C++ kaynakla üretildiğini doğrulamak için saklanan kaynak kopyaları. |

## Ham koşu çıktıları — simulation/results/

`stock_smoke/` stok örnektir. `geographical_smoke/` ilk küçük testtir. `sindirgi_s0_uniform/` tarihsel 16 saha/100 cihaz testidir. `stage3/` güncel deney kampanyasıdır. `stage3/smoke/` yeni kodun küçük çalışma kontrolüdür; aday taramasına dahil değildir.

`stage3/screen_*` dokuz adayı, `azimuth_*` yön değişimini, `buffer_*` komşu artışını gösterir. Diğer klasörler son doğrulamayı, yalnız süre etkisini ve üç belirsiz konumun çıkarılmasını içerir. Her koşunun ayarları kendi `result.json` dosyasında bulunur.

| Koşu içindeki dosya | Görevi |
|---|---|
| `result.json` | Parametreler, varsayımlar, bağlantı/veri sayımları, süre ve kaynak/girdi özetleri. |
| `ues.csv` | Cihaz konumları, bağlandıkları sektörler, bağlantı zamanı ve alınan veri. |
| `sectors.csv` | Saha/sektör bağlantısı, yönleri ve simülasyondaki hücre kimlikleri. |
| `radio_samples.csv` | Zaman içindeki RSRP ve SINR örnekleri. |
| `measurements.csv` | UE ölçüm izinden alınan RSRP/RSRQ, en güçlü hücre ve hizmet hücresi farkı. |
| `metrics.json` | Geçerli örneklerden hesaplanan cihaz ve saha ortalamaları; karşılaştırma kodunun çıktısı. |
| `run.log`, `compile.log`, `link.log`, `build.log` | Çalıştırma ve varsa derleme kayıtları. |
| Stok örnekteki `Dl*.txt` ve `Ul*.txt` | Aşağı/yukarı yön PHY, MAC, RLC, PDCP, SINR ve girişim izleri. |

Simülasyondaki hücre kimlikleri gerçek verideki `CELL_*` kimlikleri değildir. Gerçek hücrelerle bire bir eşleme yapılmadı.
