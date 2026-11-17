# Bu bilgisayarda çalışma

Çalışma klasörü: `C:\Users\bi025305\Downloads\paylasim\Turkcell`
(eski adı `paylasim\paylasim`; eski deney kayıtlarındaki mutlak yollar bu adı gösterir).
Ana proje: `ana_proje` (eski adı `turkcell_tam_paket_2026-11-10`).
Klasör haritası için [README.md](README.md).

## Güncel devir bilgisi — 17 Kasım 2026

Bu bilgisayarda analiz `.venv/Scripts/python.exe -X utf8` (Python3.10.22), simülasyon
`wsl -d Ubuntu-22.04` / Python3.10.12 / `/home/buse/ns3/ns-3.44` ile çalıştı.
Deney16–19 tamamlandı; aktif koşu yok. S0 handover kodu Deney19'dadır ve `--handover 1`
ile açılır; varsayılan kapalı. Doğru tam S0 komutu ilgili sonuç JSON'unda kayıtlıdır;
çalıştırıcının küçük tanı varsayılanlarını tam S0 sanmayın.

Başka AI'a devir için önce [DEVAM_NOTU.md](DEVAM_NOTU.md), sonra Deney19/18 raporlarını okuyun.
Bitmiş `study.py` kampanyalarını veya dondurulmuş `prepare.py` adımlarını sırf ortamı kontrol etmek
için çalıştırmayın. Aşağıdaki 10–15 Kasım kayıtları tarihsel ortam/komut bilgilerini de içerir.

## İkinci bilgisayar (15 Kasım çalışmaları)

8–14 numaralı deneyler başka bir bilgisayarda koşuldu. Oradaki farklar:

- WSL dağıtımının adı `Ubuntu` (24.04); ns-3.44 `/home/<kullanıcı>/ns-allinone-3.44/ns-3.44` altında.
  `simulation/ns3_paths.py` bu yolu da otomatik bulur.
- `.venv` yok; analiz ve özet script'leri sistem Python'u (3.12, numpy 2.0.2, pandas, matplotlib, folium)
  ile çalıştırıldı.
- `calistir.cmd` için dağıtım adı ortam değişkeniyle verilebilir: `set TURKCELL_WSL_DISTRO=Ubuntu`.
- Yeni deneyler kendi klasöründen çalışır. Her klasörde sıra: `prepare.py` (Windows Python) →
  `study.py` (WSL: `wsl -d Ubuntu --cd <klasör> --exec python3 study.py`) → `summarize.py` (Windows Python).
  Simülasyon kodu her deneyin `simulation/` klasöründe; ilk koşu `--skip-build` olmadan derler.
- Ham KPI/Experia'dan süzülen ara dosyalar (`*.csv.gz`) git'te yok; ilgili `extract*.py` ile yeniden üretilir.
- Bu bilgisayarda 64 kullanıcılık koşular önceki sonuçları dosya düzeyinde birebir üretti
  (bkz. [kullanıcı örneklemi](deneyler/08_kullanici_orneklemi_2026-11-12/SONUCLAR.md)).

## Ortam

- Analizler: çalışma klasöründeki `.venv`, Python 3.10; ana analiz paketleri
  projenin `requirements-analysis.txt` dosyasındaki sürümlerdir.
- Simülasyon: WSL `Ubuntu-22.04`, `/home/buse/ns3/ns-3.44`, klasik LTE/EPC.
- Önceden kurulu `/home/buse/ns3/ns-3-dev` değiştirilmedi. Proje geliştirme
  sürümü yerine sonuçların üretildiği **3.44** sürümünü kullanır.
- `simulation/ns3_paths.py`, 3.44 kurulumunu otomatik bulur. Farklı kurulum
  için WSL içinde `NS3_ROOT` ortam değişkeni kullanılabilir.
- Paketle gelen `environment.json` ve deney sonuçlarındaki `/home/umut/...`
  yolları eski bilgisayarın kayıtlarıdır.

## Komutlar

Aşağıdaki komutlar çalışma klasöründe PowerShell veya CMD'den çalıştırılır.
Aktivasyon veya PowerShell yürütme ilkesi değişikliği gerekmez.

```powershell
# Bu bilgisayarın analiz + simülasyon kontrollerini yeniden çalıştırır.
.\pc_kontrol.cmd

# Yalnız analiz veya simülasyon kontrolü
.\pc_kontrol.cmd --phase analysis
.\pc_kontrol.cmd --phase simulation

# Küçük senaryo: 2 saha, 6 sektör, 6 kullanıcı
.\calistir.cmd simulation/run_baseline.py --name yeni_kucuk_test

# Deney girdileri, deney kampanyası ve rapor
.\calistir.cmd analysis/prepare_radio_study.py
.\calistir.cmd simulation/run_radio_study.py
.\calistir.cmd analysis/report_radio_study.py
```

`calistir.cmd`, analizleri `.venv` ile; `simulation/` kodlarını Ubuntu Python
ile çalıştırır. Çalışma dizinini otomatik ana proje klasörüne getirir.
Deney kampanyası geçerli eski sonuçları yeniden kullanır. Yeni C++ değişikliğinden
sonra önce küçük senaryoyu çalıştırın; bu adım programı yeniden derler.

`prepare_*.py`, `audit_dataset.py` ve `report_*.py` normal çalıştırıldığında
ana projenin üretilmiş dosyalarını günceller. `pc_kontrol.cmd` ise analiz ve
simülasyon doğrulaması için `pc_validation/<tarih_saat>/` altında ayrı
çalışma kopyaları oluşturur. Ham ölçümler ve tarihsel sonuçlar korunur.

## Doğrulama kanıtı

Her kontrol koşusunda `verification.json`, komut günlükleri, bu bilgisayarın
`environment.json` kaydı ve yeniden üretilen çıktılar saklanır.
`all_checks_passed: true` ancak hem analiz hem simülasyon kontrolleri geçince yazılır.
Bu oturumun raporu: [verification.json](pc_validation/20261110_pc/verification.json).

Analiz kontrolü 12 ana Excel'i yeniden tarar, beş temel CSV'yi mevcut sonuçlarla
karşılaştırır, harita/girdi/rapor kodlarını çalıştırır ve sabit deney girdilerinin
SHA-256 değerlerini karşılaştırır. Simülasyon kontrolü stok LTE/EPC örneğini,
2 saha/6 kullanıcı testini ve 24 saha/64 kullanıcı son senaryosunu çalıştırır;
kullanıcıların bağlantı, sektör, radyo ve alınan veri sonuçlarını eski koşuyla
karşılaştırır. Bu, yazılımın bu bilgisayarda tekrar üretimini sınar.
Harita tarayıcı kontrolü `--offline-only` ile bütün uzak sunucular engellenerek
yapılır; çevrimiçi harita servisinin erişilebilirliğini sınamaz.

ns-3.44 kurulum başvurusu:
[Resmî kurulum belgesi](https://www.nsnam.org/docs/release/3.44/installation/html/quick-start.html).

## İlk taşınabilirlik değişiklikleri (tarihsel paket)

Simülasyon modelinin C++ kaynağı değiştirilmedi. Çalıştırma kodlarına taşınabilir
ns-3 yolu seçimi, farklı çıktıya yazma seçenekleri ve derleme önbelleğinde kurulum
yolu kontrolü eklendi. Dolayısıyla paket içindeki eski manifest, değiştirilen bu
Python dosyalarının yeni hash'lerini içermez; paylaşım anının kaydı olarak tutuldu.
Harita kontrol koduna ayrıca tüm uzak sunucuları engelleyen çevrimdışı seçenek eklendi.

Bu paragraf ilk paket hakkındadır. Daha sonra Deney16/17/19'un kendi C++ kopyalarına deney
özellikleri eklendi; eski ana proje ve tarihsel deney kaynakları değiştirilmedi. Güncel farklar
ve doğrulama kanıtları ilgili deneyin plan/sonuç dosyalarında bulunur.
