# RSRQ farkı için ek araştırma notu

Bu not bir düzeltme veya yeni simülasyon sonucu değildir. Kalan farkın
yalnız konum/güç ayarlarından kaynaklandığını varsaymamak için ölçüm tanımını inceler.

## Standartta tanım

RSRQ, aynı kaynak blokları üzerinden alınan RSRP ile toplam RSSI'nin
oranına dayanır. RSSI, seçilmiş OFDM sembollerindeki bütün alınan gücü
ve gürültüyü içerir; ölçüm sembollerinin seçimi yapılandırmaya bağlıdır.
[ETSI TS 136 214 V18.1.0, §5.1.3, sayfa 10](https://www.etsi.org/deliver/etsi_TS/136200_136299/136214/18.01.00_60/ts_136214v180100p.pdf).

## Kullandığımız ns-3.44 modelinde ne gördük?

Yerel kaynakta `GenerateCqiRsrpRsrq`, RSRQ hesabını PSS gücü ile kontrol
kanalından gelen istenen sinyal ve girişim+gürültüye dayandırıyor. Aynı
fonksiyon mixed CQI durumunda da çağrılıyor; veri girişimiyle değişen
mixed SINR, RSRQ paydasını doğrudan değiştirmiyor.
[İncelenen kaynak](../02_sinr_tanisi_2026-11-10/sources/src/lte/model/lte-ue-phy.cc).

Önceki altı koşulluk antenden/yükten taramada, her sabit anten genişliğinde
UDP yükü 10 kat artırıldığında RSRQ farkı bütün 64 kullanıcıda sıfırdı.
Bu, bizim sabit radyo koşullarımız için gözlenen bir model davranışıdır.
[Sayısal kontroller](../04_ortak_radyo_taramasi_2026-11-10/checks.json).

## Çıkarım ve açık soru

Bu bulgular, Experia ile kalan RSRQ farkının bir bölümünde ölçüm
tanımı/örnekleminin etkili olabileceğini düşündürüyor. Experia'nın nasıl
hesaplandığı bilinmediğinden neden kesinleşmiş değildir; standart ihlali
veya ns-3 hatası tespiti olarak sunulmaz.

RSRQ'ya sabit bir düzeltme eklenmedi ve Experia verisi değiştirilmedi.
Hocaya/veri sağlayıcıya sorulacak hedefli soru:

“`AVG(MED_SERVINGRSRQMEDIAN)` hangi kullanıcı örnekleri, RSSI bant/sembol
tanımı ve zaman/medyan ağırlıklarıyla üretiliyor? ns-3'ün kontrol/PSS
temelli UE RSRQ çıktısıyla eşdeğer kabul edilebilir mi?”
