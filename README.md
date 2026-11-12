# Sındırgı LTE baseline — ns-3 simülasyonu

Turkcell ölçüm verilerinden (saha koordinatları, Experia radyo ölçümleri, LTE KPI)
yararlanarak Sındırgı bölgesi için ns-3.44 üzerinde bir LTE/EPC başlangıç
senaryosu kurmak ve simülasyon çıktılarını gerçek ölçümlerle karşılaştırmak.
Sonraki aşamalar: KPI'dan yük modeli, stres testi, öncelikli bölge ve rota/UAV.

## Güncel durum — 12 Kasım 2026

- Koordinat envanteri güncellendi: **563 saha / 6.475 hücre**.
  **SITE_000553, 000554 ve 000555 güncel ana dosyada doğrulandı**; seçilen 96
  hücrenin 96'sı doğru sahayla eşleşiyor. Eski belgelerdeki "eksik koordinat"
  ifadeleri 10 Kasım sürümüne aittir.
  → [Koordinat doğrulama raporu](toplantilar/2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/KOORDINAT_GUNCELLEME_SONUCU.md)
- Senaryo: hocanın 8 ana + 8 komşu sahası korunarak 24 saha, saha başına 3 sektör,
  64 sanal kullanıcı. Kontrol sahalarında hata (MAE): **RSRP 2,96 / SINR 3,63 /
  RSRQ 4,07 dB**. → [Güncel envanter kontrolü](deneyler/07_guncel_envanter_kontrolu_2026-11-12/SONUCLAR.md)
- Açık konular: Experia SINR/RSRQ tanımları, TAAVG ve KPI birimleri, yük aşamasına
  geçiş ölçütü. Sıradaki adım: kullanıcı örneklemi duyarlılığı (64→128→256) ve
  KPI'dan yük profili.
- Hocaya gönderilen son mesaj: [HOCAYA_MESAJ.md](toplantilar/2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/HOCAYA_MESAJ.md)

## Klasör haritası

| Yol | İçerik |
|---|---|
| [ana_proje/](ana_proje/) | Ana proje: ham veriler, analiz ve simülasyon kodu, temel belgeler (`00_`…`08_`). Başlangıç: [00_BURADAN_BASLAYIN.md](ana_proje/00_BURADAN_BASLAYIN.md) |
| `ana_proje/cell_site_coordinates/` | Güncel saha–hücre koordinat dosyası |
| `ana_proje/experia/`, `ana_proje/LTE Main KPI_*/` | Ham Experia ve KPI Excel'leri (büyük; git'te yok) |
| `ana_proje/analysis/` | Veri denetimi, saha seçimi, harita ve radyo analizi kodları ve çıktıları |
| `ana_proje/simulation/` | ns-3 C++ senaryosu (`sindirgi_baseline.cc`), çalıştırıcılar, ilk sonuçlar |
| [deneyler/](deneyler/) | Radyo ayar deneyleri, kronolojik sırayla (aşağıda) |
| [toplantilar/](toplantilar/) | Toplantı notları, hocaya özetler, durum/plan belgeleri |
| `pc_validation/` | Bu bilgisayarda yeniden üretim kontrolünün kaydı (10 Kasım) |
| [CALISTIRMA_REHBERI.md](CALISTIRMA_REHBERI.md) | Ortam kurulumu ve komutlar |
| `calistir.cmd`, `run_project.py` | Proje script'lerini `.venv` veya WSL ile çalıştırır |
| `pc_kontrol.cmd`, `verify_pc.py` | Analiz + simülasyon yeniden üretim kontrolü |

## Deneyler (sırasıyla)

Her deney bir öncekinin sonucunu kullanır. Sonuç belgesi genellikle `SONUCLAR.md`.

| # | Klasör | Ne yapıldı |
|---|---|---|
| 1 | [01_sektor_sayisi](deneyler/01_sektor_sayisi_2026-11-10/SONUCLAR.md) | İki sahada sektör sayısı (1/2/3) etkisi |
| 2 | [02_sinr_tanisi](deneyler/02_sinr_tanisi_2026-11-10/TANI_SONUCLARI.md) | SINR farkının kaynağı; ölçüm hesabı tanısı |
| 3 | [03_mixed_cqi](deneyler/03_mixed_cqi_2026-11-10/SONUCLAR.md) | Kontrol ve mixed CQI yöntemlerinin karşılaştırması |
| 4 | [04_ortak_radyo_taramasi](deneyler/04_ortak_radyo_taramasi_2026-11-10/SONUCLAR.md) | RSRP/SINR/RSRQ için ortak keşif taraması |
| 5 | [05_kullanici_yayilim_guc](deneyler/05_kullanici_yayilim_guc_2026-11-10/SONUCLAR.md) | Kullanıcı yerleşimi, yayılım modeli ve güç araştırması |
| 6 | [06_genis_tarama_secilen_ayar](deneyler/06_genis_tarama_secilen_ayar_2026-11-10/SONUCLAR.md) | 49 koşullu geniş tarama, ortak tekrarlar; **seçilen ayar** |
| 7 | [07_guncel_envanter_kontrolu](deneyler/07_guncel_envanter_kontrolu_2026-11-12/SONUCLAR.md) | Seçilen ayarın güncel envanterle (563 saha) yeniden kontrolü |

## Notlar

- Eski deney kayıtlarındaki (`*.json`, `*.log`) mutlak yollar eski klasör
  adlarını (`paylasim/paylasim`, `turkcell_tam_paket_2026-11-10`, `experiments/…`)
  gösterir; bunlar tarihsel kayıttır ve değiştirilmedi.
- `build/` klasörleri silindi; ns-3 programı ilk küçük test koşusunda yeniden derlenir.
