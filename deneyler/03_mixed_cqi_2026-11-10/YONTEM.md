# Kontrol ve mixed CQI karşılaştırması

Amaç: aynı düşük yüklü varsayımsal LTE senaryosunda ölçüm/CQI yönteminin
raporlanan SINR'ye etkisini görmek. Experia'ya daha yakın bir sayıyı otomatik
olarak doğru yöntem kabul etmiyoruz.

## Sabit tutulanlar

- 24 saha, 72 sektör; bütün sektörler aynı taşıyıcıda.
- Aynı 64 sabit kullanıcı, saha konumları, anten yönleri ve güçleri.
- Aynı log-distance modeli, seed=42, run=1, 4 s süre ve 1 s ısınma sınırı.
- Her kullanıcıya 512 baytlık UDP paketleri, 50 ms aralıkla sunuluyor.
  Bu trafik düzeni gerçek KPI talebinden kalibre edilmiş değildir.

## Değişen tek yapılandırma

`LteHelper::UsePdschForCqiGeneration`:

| Durum | Değer | İstenen sinyal | Girişim |
|---|---|---|---|
| Kontrol | false | Referans/kontrol sinyali | Kontrol kanalı girişimi |
| Mixed | true | Referans sinyali, P_A ölçeğiyle | Mevcut veri kanalı girişim+gürültü güncellemesi; yoksa yalnız gürültü |

**Bu ayar CQI geri bildirimini de değiştirir.** Zamanlayıcı farklı CQI ile
farklı veri iletimi kararları alabilir. Dolayısıyla iki koşu arasında yalnız
bir çıktı sütununun adı değişmez. Alınan baytlar ayrı raporlanır; bu kısa
koşudan kapasite veya gerçek hizmet başarısı sonucu çıkarılmaz.

Birincil kaynak: kurulu ns-3.44 `LteUePhy::GenerateMixedCqiReport`,
`LteHelper` ve [resmî model belgesi](https://www2.nsnam.org/docs/release/3.44/models/singlehtml/index.html).
Önceki tanıda hash'lenmiş [yerel kaynak kopyası](../02_sinr_tanisi_2026-11-10/sources/src/lte/model/lte-ue-phy.cc)
hesabın ayrıntısını içerir.

## Eklediğimiz pasif kontroller

İki koşuda da istenen sinyal PSD'si ve kontrol girişim+gürültü PSD'si
kaydedilir. Bunlardan bağımsız kontrol SINR'si hesaplanır. Ayrıca son veri
girişim güncellemesi izlenir; yerel mixed hesabının aynı güncellemeyi tüketme
anında ne hesapladığı yeniden üretilir.

- Yerel kontrol çıktısı → kontrol S/(I+N) ile karşılaştırılır.
- Yerel mixed çıktısı → veri güncellemesi varsa S/(I_data+N), yoksa S/N ile karşılaştırılır.
- Bu başlangıçta P_A=0 dB ve 100 RB kullanılır. RBG modulo sıfır olduğu için
  kaynak koddaki artık RB düzeltmesi sonucu değiştirmez.
- Eklenen gözlemciler hiçbir yayını susturmaz, güç/frekans değiştirmez.

Önce yeni kontrol kodu eski 64 kullanıcı sonucunu yeniden üretmek zorundadır.
Bu kontrol geçmeden mixed koşusu başlamaz. Son analizde kullanıcıların
hizmet saha/sektörlerinin, RSRP/RSRQ'nun ve bağımsız kontrol SINR'sinin
aynı kalıp kalmadığı sınanır.

## Sonucu okurken

Düşük yükte veri girişim güncellemesi olmayan örneklerde mixed yöntemin
yalnız gürültüyü kullanması mümkündür. Bu durum sinyal oranını yükseltebilir;
gerçek şebekedeki girişimin azaldığını kanıtlamaz. Daha yüksek/daha farklı
yükte aynı sayılar beklenmemelidir. Deneyde yük artırılmadı.

Üç eski kontrol sahası daha önce görüldü. Buradaki hata karşılaştırması
yeni bir kör doğrulama veya yeni kalibrasyon değildir. Experia'nın kanal,
örneklem ve ortalama tanımları hâlâ netleştirilmelidir.

## Tekrar üretim

Proje kökünde PowerShell:

```powershell
.\.venv\Scripts\python.exe deneyler/03_mixed_cqi_2026-11-10/prepare.py
wsl --distribution Ubuntu-22.04 --exec python3 deneyler/03_mixed_cqi_2026-11-10/run_experiment.py
.\.venv\Scripts\python.exe deneyler/03_mixed_cqi_2026-11-10/report.py
```

Deney planı/hash'ler `experiment_plan.json`, ham koşular `simulation/results/`,
karşılaştırmalar CSV dosyaları ve `checks.json` içinde saklanır. Ana projenin
başlangıç senaryosu ve C++ kaynağı değiştirilmez.
