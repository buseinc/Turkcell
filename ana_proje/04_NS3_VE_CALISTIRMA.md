# İlk LTE/EPC denemesi

Bu belgedeki komutlar, ZIP açıldıktan sonra paket kökündeki PowerShell terminalinden çalıştırılacak şekilde düzenlendi. WSL/Ubuntu ve ns-3.44 ayrıca kurulmalıdır; bunlar ZIP'e dahil değildir. `run_baseline.py`, `run_stock_smoke.py`, `probe_environment.py` ve `inspect_radio_models.py` içindeki ns-3 yolu kendi kurulumunuza göre değiştirilmelidir. Aşağıdaki `/home/umut/...` yolu, sonuçların üretildiği bilgisayara aittir. Hazır harita ve sonuçları incelemek için kurulum gerekmez.

**3. aşama tamamlandı:** [Radyo karşılaştırması ve duyarlılık raporu](05_RADYO_DENEYLERI_VE_SONUCLAR.md). Aşağıdaki ilk denemeler ayrıca saklandı. Yeni kampanya 64 sabit UE ile 17 farklı koşulda yerleşim, yayılım, azimut, buffer ve ayrılmış saha kontrollerini içerir; RSRP tanı hedefi sağlandı, SINR/RSRQ uyumu doğrulanmadı.

Mevcut Ubuntu/WSL ortamında ns-3 **3.44**, klasik LTE/EPC kullanılıyor. Kurulum yolu `/home/umut/ns-allinone-3.44/ns-3.44`; araç sürümleri [environment.json](simulation/environment.json) içinde. Kaynak ve ns-3 yapılandırması değiştirilmedi; mevcut yapılandırmanın LTE örnek hedefi derlendi.

## Çalıştırma

Proje kökünde PowerShell'den:

```powershell
wsl --distribution Ubuntu --exec python3 simulation/run_stock_smoke.py
wsl --distribution Ubuntu --exec python3 simulation/run_baseline.py
wsl --distribution Ubuntu --exec python3 simulation/run_baseline.py --sites 16 --ues 100 --duration 2 --placement uniform --name sindirgi_s0_uniform
python analysis/summarize_baseline.py
```

`run_stock_smoke.py` mevcut kurulumda `lena-simple-epc` hedefini 2 derleme işiyle oluşturur. Yerel örnek, stok örneğin kayıtlı derleyici ayarlarını kullanarak proje içinde derlenir. Başka bir bilgisayarda WSL/proje/ns-3 yolları uyarlanmalıdır; bu aşama genel bir kurulum paketi değildir.

## İlk kontroller

- Stok LTE+EPC: 2 eNB / 2 UE; 1,1 saniyede DL ve UL PDCP yönlerinin her birinde 25.296 bayt alındı. Sonuç: [stock_smoke/result.json](simulation/results/stock_smoke/result.json).
- Coğrafi küçük test: 2 saha / 6 sentetik sektör / 6 UE; 6 UE de otomatik bağlandı ve veri aldı. Sonuç: [geographical_smoke/result.json](simulation/results/geographical_smoke/result.json).
- 16 saha / 48 sentetik sektör / 100 UE: 2 simülasyon saniyesi yaklaşık 44,8 saniyede çalıştı; 100 UE bağlandı, 75 UE DL verisi aldı, 1.768 radyo örneği üretildi. Güncel sayımlar [sonuç dosyasında](simulation/results/sindirgi_s0_uniform/result.json); analiz [baseline_summary.json](analysis/sindirgi/baseline_summary.json) içinde.

İlk [radyo dağılımı karşılaştırması](analysis/sindirgi/radio_distribution_comparison.png), değerlendirme sahalarının hizmet verdiği 73 sentetik UE'yi, değerlendirme grubundaki 55 ölçülmüş hücrenin zaman ortalamalarıyla karşılaştırır. RSRP medyanları yaklaşık −117,43 / −104,19 dBm; SINR medyanları −1,67 / 11,75 dB. Örneklem/ağırlıklar, dönem ve SINR tanımları farklıdır; bu grafik keşif amaçlıdır ve kalibrasyon başarısı göstermez. UE noktaları ve anten yönleri [örnek haritasında](analysis/sindirgi/ue_radio_samples.png) gösterilir; sürekli kapsama sınırı çizilmedi.

## Açık varsayımlar

S0 tüm sahalarda üç sentetik, eş frekanslı sektör kullanır; Turkcell hücrelerine birebir eşleme yapmaz. Band 3, DL/UL EARFCN 1300/19300, 100 RB, eNB 46 dBm ve anten tepe kazancı 15 dBi ayrı parametrelerdir (boresight yönünde varsayımsal 61 dBm EIRP). Anten `CosineAntennaModel`, yatay 65°, düşey 360°; düşey desen/tilt çalışması yapılmadı. Azimutlar doğudan saat yönünün tersine ölçülür. eNB/UE yüksekliği 30/1,5 m; zemin düzdür.

Başlangıç yayılımı `LogDistancePropagationLossModel`, üs 3 ve 1815 MHz'de 1 m serbest uzay referans kaybıdır. Shadowing/fading kapalı, scheduler PF. Bunlar çalışma kontrolü içindir; radyo kalibrasyonu yapılmış değildir. UE'ler küçük testte sahaların 250–750 m çevresinde, büyük testte 16 sahanın sınırlayıcı dikdörtgeninde rastgele yerleştirilir. Gerçek UE dağılımı bilinmiyor.

Otomatik ilk seçim `Attach(ueDevices)` ile yapılır; UE arama EARFCN'i de 1300 olarak açıkça tanımlanır. Kanal/frekans, güç, anten ve yerleşim yine yapılandırılır; yalnızca konum vermek yeterli değildir. Statik başlangıç için handover çalışması henüz yapılmadı.

`ReportCurrentCellRsrpSinr` ham RSRP'yi watt, SINR'yi doğrusal verir; CSV'ye dBm/dB dönüşümü yapılıyor. CQI/radyo tanısı `UsePdschForCqiGeneration=false` ile PDCCH sinyali ve PDCCH girişimini kullanır; böylece boş veri kaynaklarındaki düşük yük ölçümüyle karıştırılmaz. Ölçüm aralığı 97 alt çerçevedir. Bu SINR'nin Experia alanıyla tanımı henüz eşleştirilmedi.

Kısa UDP uygulaması yalnızca uçtan uca veri akışını kontrol eder. Eksik paket veya sıfır DL baytı, kısa koşudan gerçek arıza veya doğrulanmış hizmet sınırı olarak yorumlanamaz. Buffer yakınsaması, UE yerleşimi/azimut/yayılım duyarlılığı ve ayrılmış saha kontrolü 3. aşamada yapıldı; gerçek KPI yük kalibrasyonu sonraki iştir.

## 3. aşamayı tekrar üretme

Proje kökünde:

```powershell
python analysis/prepare_radio_study.py
wsl --distribution Ubuntu --exec python3 simulation/run_baseline.py --name stage3/smoke
wsl --distribution Ubuntu --exec python3 simulation/run_radio_study.py
python analysis/report_radio_study.py
```

Deney planı koşulardan önce yazılır; eğitim sahalarında yalnız RSRP ile seçilen parametreler ayrılmış üç sahaya göre yeniden ayarlanmaz. Süre ile UDP etkisini ayıran ek kontrol planda ayrıca kaydedildi. Geçerli simülasyon sonuçları hash ve parametre kontrolüyle tekrar kullanılır. Parametreli C++ programı sabit saha dönüşlerini ve UE CSV'lerini alır, farklı buffer koşullarında aynı iç geometriyi korur; tarama koşuları veri yükü olmadan radyo kontrolüdür. RSRQ ve en güçlü ölçülen hücreyle hizmet hücresi farkı da kaydedilir.

Son koşul 8 ana + 16 komşu saha, 72 sentetik sektör ve 64 UE kullanır; 4 saniyede 64 UE bağlandı, 60 UE veri aldı. Eski 16 saha / 100 UE başlangıç sonuçları korunur; eski ve yeni C++ kaynakları hash adlarıyla `archive/` altında saklanır. Tam yapılandırma ve girdiler [frozen/](analysis/sindirgi/radio_study/frozen/configuration.json) altında.

Resmî kurulum başvurusu: [ns-3.44 Installation Guide](https://www.nsnam.org/docs/release/3.44/installation/html/quick-start.html). API ve trace ayarları, kurulu sürümün `src/lte/` ve `src/antenna/` kaynaklarından kontrol edildi.
