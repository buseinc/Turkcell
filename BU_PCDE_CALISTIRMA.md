# Bu bilgisayarda çalışma

Çalışma klasörü: `C:\Users\bi025305\Downloads\paylasim\paylasim`.
Ana proje: `turkcell_tam_paket_2026-11-10`. İnceleme paketi tarihsel kopyadır.

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

## Değişiklikler

Simülasyon modelinin C++ kaynağı değiştirilmedi. Çalıştırma kodlarına taşınabilir
ns-3 yolu seçimi, farklı çıktıya yazma seçenekleri ve derleme önbelleğinde kurulum
yolu kontrolü eklendi. Dolayısıyla paket içindeki eski manifest, değiştirilen bu
Python dosyalarının yeni hash'lerini içermez; paylaşım anının kaydı olarak tutuldu.
Harita kontrol koduna ayrıca tüm uzak sunucuları engelleyen çevrimdışı seçenek eklendi.
