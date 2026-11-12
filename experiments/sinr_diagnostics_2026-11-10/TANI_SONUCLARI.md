# Sinyal, girişim ve gürültü: ne bulduk?

**Mevcut varsayımsal şebekede düşük SINR'nin baskın bileşeni girişim.**
Kayıt birimlerini ve hesapları kontrol ettik; incelediğimiz dönüşümlerde hata
bulmadık. Gerçek Turkcell ağındaki farkın nedenini henüz doğrulamış değiliz.

## Ne yaptık?

Sabitlenen 24 saha / 72 sektör / 64 kullanıcı senaryosuna yalnız gözlemci
ekledik. Her kullanıcıda istenen sinyal (S), diğer sinyallerin toplamı (I)
ve alıcı gürültüsünü (N) ayrı çıkardık. Isınma sonrasında 1.984 örnek topladık.

Gözlemci eklenmesi hizmet saha/sektörlerini, bağlantıları ve alınan baytları
değiştirmedi. RSRP/SINR/RSRQ önceki sonuçla sayısal hassasiyet düzeyinde uyuştu.
S, I ve N'den yeniden hesaplanan SINR ile yerel SINR izi arasındaki en büyük
fark yaklaşık 2,38×10⁻¹⁴ dB. Ayrıntı: [checks.json](checks.json).

## Ana bulgular

| Kontrol | Sonuç | Basit anlamı |
|---|---:|---|
| Girişimi gürültüsünden büyük kullanıcı | **64/64** | SINR paydasında baskın terim girişim. |
| İstenen sinyali gürültüsünden küçük kullanıcı | **0/64** | Bu senaryoda her kullanıcının S/N oranı sıfır dB'nin üzerinde. |
| SINR'si sıfır dB'nin altında kullanıcı | **30/64** | Bu kullanıcıların sinyali toplam girişim+gürültüden küçük. |
| Girişimin çoğu başka sahalardan gelen kullanıcı | **61/64** | Baskın etki çoğunlukla kendi istasyonunun diğer sektörleri değil. |
| Kullanıcılar arası medyan S/N | **10,99 dB** | Aynı istenen sinyalin yalnız gürültüye oranı. |
| Kullanıcılar arası medyan SINR | **0,63 dB** | Girişim de hesaba katılınca elde edilen kalite. |
| Medyan girişim payı | **%90,57** | SINR'nin I+N paydasında girişimin payı. |

Sıfır dB burada bir hizmet kabul eşiği olarak seçilmedi; iki gücün eşit
olduğu matematiksel sınırdır. Bütün kullanıcıların gerçek hizmeti alabileceği
veya gürültünün hiçbir etkisi olmadığı sonucu çıkarılmamalıdır.

## Tek kullanıcı üzerinden örnek

Sanal kullanıcı **7**, `SITE_000444` üzerinden hizmet alıyor:

- Yalnız gürültüye göre sinyal oranı (S/N): **11,37 dB**.
- Girişim dahil SINR: **0,71 dB**.
- I+N paydasının **%91,42'si girişim**.
- En güçlü girişim kaynağı: `SITE_000480`.

Bir kişinin sesi ortamın doğal uğultusundan yüksek olabilir. Ama çevredeki
başka konuşmalar eklenince o kişiyi anlamak zorlaşır. Buradaki fark buna benziyor.
S/N, girişimi kapatarak yapılan yeni bir şebeke koşusu değildir; aynı kullanıcı
ve aynı hizmet sinyalinden hesaplanan bir referanstır.

## Başka sahalardan gelen girişimi nasıl ayırdık?

Her sektörün bu kullanıcıya ne kadar güç ulaştıracağını, aynı konumlar,
anten yönleri/deseni ve yayılım formülüyle ayrıca hesapladık. Hesaplanan
istenen sinyal ve bütün diğer sektörlerin güç toplamı, doğrudan gözlenen
değerlerle yaklaşık 10⁻⁹ dB düzeyinde uyuştu. Bu kontrol geçtikten sonra
girişimi aynı sahanın diğer sektörleri ve diğer sahalar olarak ayırdık.

Kullanıcıların 61'inde girişimin yarıdan fazlası başka sahalardan geliyor.
Bu, önceki iki sahada sektör azaltma pilotunun bütün kalite sorununu
çözmesini beklemememiz için ek bir açıklama sağlıyor. O pilotta bazı
kullanıcıların hizmet aldığı yönler de kaldırıldığı için sinyal kaybı yaşanmıştı.

## Ölçüm tanımıyla ilgili önemli bulgu

Bizim SINR izimiz **kontrol kanalı** yöntemiyle çalışıyor. Bu ns-3 yöntemi,
komşu istasyonların veri trafiği olmasa da kontrol sinyallerini girişim olarak
hesaba katıyor. Resmî belgede veri kanalı girişimini kullanan ayrı bir mixed
yöntem de tanımlanmış. Bu tanıda ayar değiştirilmedi.
[ns-3.44 model belgesi](https://www2.nsnam.org/docs/release/3.44/models/singlehtml/index.html).

Bu nedenle mevcut SINR'yi doğrudan “veri trafiği altındaki gerçek kullanıcı
SINR'si” olarak adlandıramayız. Experia alanının hangi kanal, örneklem ve
ortalama tanımına dayandığı sorusu artık daha hedefli sorulabilir.

RSRQ hesabını da bileşenlerden yeniden ürettik; yerel ölçüm iziyle uyuşuyor.
Bu, kendi modelimizin iç tutarlılığını gösteriyor. Experia ile eşdeğerlik
ve gerçek radyo yapılandırması hâlâ doğrulanmış değil.

## Toplantıda söylenecek

“SINR farkını araştırmak için sinyal, girişim ve gürültüyü ayırdık. Birim
dönüşümlerini ve hesap zincirini kontrol ettik. Kurduğumuz aynı frekanslı,
kontrol kanalı senaryosunda girişim baskın; çoğu kullanıcıda ana kaynak
başka sahalar. Experia'nın SINR tanımı bu kontrol kanalı ölçümüyle aynı mı?
Taşıyıcı/anten varsayımını ve ölçüm yöntemini hangi bilgiyle daraltabiliriz?”

## Dosyalar ve tekrar üretim

- [Görsel](sinr_diagnostics.png)
- [Kullanıcı bazında S/I/N ve kaynak ayrımı](ue_diagnostics.csv)
- [Her kullanıcıya her sektörün güç katkısı](sector_contributions.csv)
- [Teknik hesap ve kaynak incelemesi](OLCUM_HESABI.md)
- [Kontroller](checks.json), [deney planı](experiment_plan.json), [kaynak hash'leri](source_manifest.json)

Proje kökünden PowerShell komutları:

```powershell
.\.venv\Scripts\python.exe experiments/sinr_diagnostics_2026-11-10/prepare.py
wsl --distribution Ubuntu-22.04 --exec python3 experiments/sinr_diagnostics_2026-11-10/simulation/run_baseline.py --sites 0 --ues 64 --duration 4 --sites-file experiments/sinr_diagnostics_2026-11-10/inputs/sites.csv --ue-file experiments/sinr_diagnostics_2026-11-10/inputs/ues.csv --name diagnostic
.\.venv\Scripts\python.exe experiments/sinr_diagnostics_2026-11-10/analyze.py
```

Ana proje ve ns-3 kaynak kodu değiştirilmez. Ham tanı verisi
`simulation/results/diagnostic/` altında saklanır. Birim dönüşümleri ve
koşu parametreleri teknik notta açıklanır.

Sınır: Tek sabit yerleşim ve radyo varsayımı; tüm sektörler aynı taşıyıcıda.
Arazi, gerçek kullanıcı dağılımı ve gerçek taşıyıcı planı bilinmiyor. Bu sonuç
gerçek ağdaki girişim kaynaklarının veya kapsama sınırlarının tespiti değildir.
