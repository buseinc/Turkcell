# Deney 42: Şehir modeli ns-3'te, sonuçlar (25 Kasım)

Kurallar `KURALLAR.md`. Kod: `simulation/` (ns-3 senaryosu; yeni: `env-select-loss.h`, `spatial-field.h` ve `building-vertical-model.h` içindeki ekler), `hazirla42.py` (girdiler), `run42.py` (koşular), `k1.py` (sinyal gücü sınaması).

## Eski koşularla aynılık

Deney 34'ün `R5_ho_kapali` koşusu yeni programla tekrarlandı (`simulation/reg_R5.sh`). 9 çıktı dosyasının hepsi birebir aynı. Yeni ayarlar kapalıyken eski hesap değişmiyor.

## Sinyal gücü (K1): geçti

- 15:30, çekiliş 42, trafik yok. ns-3'ün 0,3. saniyedeki ilk RSRP kaydı kullanıldı. Trafik ve sönümlenme olmadığı için RSRP zamanla değişmiyor; koşu bu kayıttan sonra durduruldu.
- 2.624 kişiden 2.549'u kayıt yazmıştı; hepsi hızlı modeldeki hücreye bağlı.
- ns-3 − hızlı model: ortalama mutlak fark 0,001 dB, en çok 0,006 dB. Saha başına ortalama 0,001 dB (sınır 0,5 dB).
- Şehir ve kırsal kullanıcılarda fark aynı (0,0 dB).

Sayılar `k1.json`.

## Sinyal kalitesi

Ayrıca sınanmadı; nedeni `KURALLAR.md`'de. Kısaca: kalite hesabı ns-3'ün bu deneyde değişmeyen parçalarıyla yapılıyor ve onlar deney 31 ve 36'da sınandı. Kaliteye giren sinyal güçleri ise K1'de tutan formülden geçiyor. Başlatılan 1 saniyelik trafikli deneme koşusu bu karar üzerine durduruldu.

## Sonuç

Şehir modeli ns-3'te hızlı modelle aynı sinyali veriyor. Kesinti ve İHA senaryoları bu ns-3 modeliyle yapılabilir. Ölçümle karşılaştırma sonuçları deney 40'taki gibi.
