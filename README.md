# Sındırgı LTE baseline — ns-3 simülasyonu

Turkcell ölçüm verilerinden (saha koordinatları, Experia radyo ölçümleri, LTE KPI)
yararlanarak Sındırgı bölgesi için ns-3.44 üzerinde bir LTE/EPC başlangıç
senaryosu kurmak ve simülasyon çıktılarını gerçek ölçümlerle karşılaştırmak.
Sonraki aşamalar: KPI'dan yük modeli, stres testi, öncelikli bölge ve rota/UAV.

## Güncel durum — 15 Kasım 2026

**İlk aşama tamamlandı.** Baştan okumak için: [İlk aşama özeti](toplantilar/2026-11-15_ilk_asama_ozeti/ILK_ASAMA_OZETI.md)
(hocanın istekleri ve karşılıkları, güncel başlangıç senaryosunun tam tanımı, ana sonuçlar, açık sorular).
Hocaya gönderilecek mesaj taslağı: [HOCAYA_MESAJ_TASLAGI.md](toplantilar/2026-11-15_ilk_asama_ozeti/HOCAYA_MESAJ_TASLAGI.md).

- **Başlangıç senaryosu (S0):** 24 saha, 3 sektör, tek taşıyıcı (Band 3), 256 ölçüm kullanıcısı, KPI
  günlük ortalama yükü, rastgele başlayan trafik, 3 örnek.
- **Experia'ya göre kontrol sahaları hatası:** RSRP 1,72 / SINR 2,15 / RSRQ 4,30 dB. Saha RSRP sıralaması
  Spearman 0,79–0,95. RSRQ karşılaştırması ns-3 tanımı nedeniyle anlamlı değil.
- **KPI CQI'sıyla eşzamanlı karşılaştırma:** simülasyon 1,1 birim düşük (girişim biraz fazla).
- **Kapsama:** değerlendirme alanının %99,8'inde RSRP ≥ −120 dBm.
- **Açık sorular:** hücre bant/EARFCN ve güç bilgisi, Experia SINR/RSRQ tanımı, KPI birimleri.
- **Sıradaki adım:** hocayla değerlendirme, ardından S0 ve S2 ile stres pilotu.

## Gelişim kaydı

Kronolojik kayıt. Her maddedeki sayılar o günün senaryosuna aittir; güncel değerler yukarıda ve ilk
aşama özetindedir.

- Koordinat envanteri güncellendi: **563 saha / 6.475 hücre**.
  **SITE_000553, 000554 ve 000555 güncel ana dosyada doğrulandı**; seçilen 96
  hücrenin 96'sı doğru sahayla eşleşiyor. Eski belgelerdeki "eksik koordinat"
  ifadeleri 10 Kasım sürümüne aittir.
  → [Koordinat doğrulama raporu](toplantilar/2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/KOORDINAT_GUNCELLEME_SONUCU.md)
- 12 Kasım senaryosu: hocanın 8 ana + 8 komşu sahası korunarak 24 saha, saha başına 3 sektör,
  64 sanal kullanıcı. Kontrol sahalarında hata (MAE): RSRP 2,96 / SINR 3,63 /
  RSRQ 4,07 dB *(64 kullanıcı, yüksüz; sonradan yetersiz bulundu)*. → [Güncel envanter kontrolü](deneyler/07_guncel_envanter_kontrolu_2026-11-12/SONUCLAR.md)
- Açık konular: Experia SINR/RSRQ tanımları, TAAVG ve KPI birimleri, yük aşamasına
  geçiş ölçütü.
- Kullanıcı örneklemi duyarlılığı (64→128→256) tamamlandı: önceden yazılan ölçüt
  **geçmedi**. Saha ortalamaları 64 kullanıcıda örneklemeye bağlıymış. 256 kullanıcıda
  kontrol MAE RSRP 1,72 / SINR 4,74 / RSRQ 4,30 dB. Simülasyon SINR'si çoğu sahada
  Experia'dan sistematik olarak yüksek. → [Deney 08](deneyler/08_kullanici_orneklemi_2026-11-12/SONUCLAR.md)
- KPI yük profili ve gerçekçi yük tamamlandı: önceki simülasyon ağı gerçeğe göre 7–10 kat
  boş çalıştırıyordu (PRB %3 vs KPI %23–36). KPI'daki PRB yükü verilince kontrol SINR hatası
  4,74 → 1,44–1,72 dB; RSRP değişmedi. *(15 Kasım notu: bu yakınlık kısmen ns-3'ün SINR ortalama
  biçimine ve eşzamanlı yük trafiğine bağlıydı; rastgele başlayan trafikle 2,15 dB.)* Deprem anında bağlı kullanıcı ≈2× artıyor, veri
  hacmi ilk yarım saatte düşüyor. → [Deney 09](deneyler/09_kpi_yuk_profili_2026-11-12/SONUCLAR.md)
- Izgara kapsama haritaları hazır (15 Kasım): değerlendirme alanının %99,8'inde RSRP ≥ −120 dBm;
  tek taşıyıcı varsayımıyla ağ girişim sınırlı (tam girişimde alanın %60'ında SINR < 0 dB).
  Haritalar ns-3 ile birebir aynı çıkan büyüklüklerle çizildi. Doğrulamada ns-3 mixed SINR'sinin
  çoğunlukla girişimsiz örneklerden oluştuğu bulundu; yük çalışmasındaki SINR yakınlığı bu nedenle
  ölçüm tanımına duyarlı. → [Kapsama haritaları](deneyler/10_kapsama_haritalari_2026-11-15/SONUCLAR.md)
- CQI karşılaştırması (15 Kasım, KPI ile eşzamanlı): simülasyon CQI'sı KPI'dan 0,9–2,1 birim düşük ve
  yüke iki kat duyarlı. Yalnız girişimli örneklerde fark 6–7 birim. Tek taşıyıcı varsayımı girişimi
  abartıyor. → [CQI karşılaştırması](deneyler/11_cqi_karsilastirmasi_2026-11-15/SONUCLAR.md)
- Dağılım ve sıralama karşılaştırması (15 Kasım): RSRP'de sahaların sıralaması iyi (Spearman 0,79–0,95),
  ama hücre dağılımı dar ve 7,5 dB düşük; gerçek ağda güçlü hücreler ve saha içi büyük farklar var.
  RSRQ sıralaması tutmuyor (ns-3 tanımı farklı). → [Dağılım karşılaştırması](deneyler/12_dagilim_karsilastirmasi_2026-11-15/SONUCLAR.md)
- Saha içi hücre imzası analizi (15 Kasım): 130, 296, 440, 441, 443 sahalarının hücrelerinde düzenli
  frekanslar arası handover var → çok frekanslı. 444 ve 554'te yok → tek frekans olası; 554 için
  2 sektör destekleniyor. → [Hücre imzası analizi](deneyler/13_hucre_imzasi_2026-11-15/SONUCLAR.md)
- Çok taşıyıcılı senaryo S2 (15 Kasım): 17 sahaya 800 MHz katmanı eklendi. Hücre RSRP medyanı ve
  CQI düzeyi gerçeğe yaklaştı, ama saha hataları ve sıralama S0'dan kötü (kontrol RSRP 1,7 → 3,0;
  SINR 2,2 → 4,5 dB). Fark doğrulanmamış iki varsayıma (800 MHz gücü, kullanıcı atama eşiği) bağlı.
  S0 başlangıç olarak korunuyor; yük deneylerinde S0 ve S2 iki uç olarak birlikte kullanılabilir.
  Yük trafiği artık rastgele başlatılıyor. → [S2](deneyler/14_cok_tasiyici_s2_2026-11-15/SONUCLAR.md)
- Sıradaki adım: hocayla ilk aşama sonuçlarının değerlendirilmesi. Hocaya/Turkcell'e sorulacak:
  hücrelerin bant/EARFCN ve taşıyıcı gücü, hangi hücrelerin aynı sektörde olduğu, Experia SINR/RSRQ
  tanımı, KPI CQI tablosu ve throughput birimleri.
- Ekip için özet: [Kullanıcı örneklemi ve gerçekçi ağ yükü — bulgular](toplantilar/2026-11-12_orneklem_ve_yuk_bulgulari/BULGULAR_OZETI.md)
- 12 Kasım'da hocaya gönderilen mesaj: [HOCAYA_MESAJ.md](toplantilar/2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/HOCAYA_MESAJ.md)

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
| 8 | [08_kullanici_orneklemi](deneyler/08_kullanici_orneklemi_2026-11-12/SONUCLAR.md) | 64→128→256 kullanıcı, toplam yük sabit; örneklem duyarlılığı |
| 9 | [09_kpi_yuk_profili](deneyler/09_kpi_yuk_profili_2026-11-12/SONUCLAR.md) | KPI'dan yük profili, deprem anı yükü; KPI PRB yüküyle radyo karşılaştırması |
| 10 | [10_kapsama_haritalari](deneyler/10_kapsama_haritalari_2026-11-15/SONUCLAR.md) | Izgara RSRP/SINR/hizmet alanı haritaları; analitik modelin ns-3 ile doğrulanması |
| 11 | [11_cqi_karsilastirmasi](deneyler/11_cqi_karsilastirmasi_2026-11-15/SONUCLAR.md) | Simülasyon CQI'sının eşzamanlı KPI CQI'sıyla karşılaştırılması |
| 12 | [12_dagilim_karsilastirmasi](deneyler/12_dagilim_karsilastirmasi_2026-11-15/SONUCLAR.md) | Hücre düzeyi dağılımlar ve saha sıralaması (Experia) |
| 13 | [13_hucre_imzasi](deneyler/13_hucre_imzasi_2026-11-15/SONUCLAR.md) | Saha içi hücre imzaları: sektör/taşıyıcı ipuçları, S2 önerisi |
| 14 | [14_cok_tasiyici_s2](deneyler/14_cok_tasiyici_s2_2026-11-15/SONUCLAR.md) | Çok taşıyıcılı senaryo (S2) ve tek taşıyıcı (S0) karşılaştırması |

## Notlar

- Eski deney kayıtlarındaki (`*.json`, `*.log`) mutlak yollar eski klasör
  adlarını (`paylasim/paylasim`, `turkcell_tam_paket_2026-11-10`, `experiments/…`)
  gösterir; bunlar tarihsel kayıttır ve değiştirilmedi.
- `build/` klasörleri silindi; ns-3 programı ilk küçük test koşusunda yeniden derlenir.
