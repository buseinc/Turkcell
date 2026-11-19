# SINR tavanı: Experia eğrisi ve 3GPP verici kalitesi (EVM) — 19 Kasım 2026

**Soru:** 22–24. deneylerde SINR 8–9 dB yüksek çıktı ve ne anten ne de yük bunu değiştirdi. Experia'daki SINR
sinyal gücüyle nasıl değişiyor, simülasyondaki SINR nasıl değişiyor? Fark nereden geliyor?

**Tür:** Yalnızca analiz; yeni simülasyon koşusu yok ([analysis.py](analysis.py), [analysis.json](analysis.json)).
20–24. deneylerin sonuçları görüldükten sonra yapıldı. Ham Experia dosyası yalnızca yerelde okundu; burada
sadece gruplanmış medyanlar var.

## 1. Experia ile simülasyonun SINR–RSRP eğrisi

Kullanıcı medyan SINR'ı (dB), RSRP aralığına göre:

| RSRP aralığı (dBm) | −125…−115 | −115…−105 | −105…−95 | −95…−85 | −85…−75 |
|---|---:|---:|---:|---:|---:|
| **Experia** (bölgenin tamamı, 849.844 saat-hücre) | 3,3 | 8,4 | 15,1 | 18,1 | 19,6 |
| Simülasyon, veri kanalı SINR'ı (24. deney) | 5,3 | 12,8 | 22,3 | 32,7 | 41,6 |
| Simülasyon, yalnız gürültü (SNR) | 5,4 | 13,1 | 22,3 | 32,9 | 42,2 |
| Simülasyon, "komşular hep açık" | −1,8 | 1,6 | 4,6 | 11,8 | 18,9 |
| **Simülasyon, veri kanalı + 3GPP EVM** | 5,2 | 12,3 | 19,1 | 21,6 | 21,9 |

- Experia'da SINR −5 ile 25 dB arasında kalıyor; 490 değer tam 25'te, 25'in üstünde hiç değer yok.
  Raporlanan değer 25 dB'de kesiliyor.
- Zayıf sinyalde Experia ile simülasyon aynı: bu bölgede SINR'ı gürültü belirliyor ve modelin gürültü
  seviyesi (9 dB alıcı gürültüsü) doğru.
- Güçlü sinyalde Experia'da SINR yaklaşık **20 dB'de duruyor**. Simülasyonda ise 40 dB'ye kadar çıkıyor,
  yani simülasyondaki SINR aslında saf SNR. Fark yükten ya da antenden değil, bu tavandan geliyor.

## 2. Tavanın kaynağı: 3GPP verici kalitesi (EVM)

Gerçek bir baz istasyonu sinyali kusursuz göndermez. 3GPP TS 36.104 (Tablo 6.5.2-1), 64QAM için verici
hatasının (EVM) en fazla **%8** olmasını şart koşar. Bu, sinyalin içinde her zaman sinyalin %8'i kadar bir
bozulma olduğu anlamına gelir. Sinyal ne kadar güçlü olursa olsun SINR 1/0,08² = **21,9 dB**'yi geçemez.
Bunu her örneğe aynı formülle uyguladık:

    SINR_etkin = −10·log10(10^(−SINR/10) + 0,08²)

Bu sayı ayarlanmadı; standarttaki değer. Experia'nın 18–20 dB'de duran eğrisiyle aynı şekli veriyor.

## 3. EVM ile yeniden değerlendirme

| Senaryo | Ayarda kullanılmayan sahalarda SINR farkı, EVM'siz | **EVM ile** |
|---|---:|---:|
| Eski temel S0 (14. deney) | 1,5* | 1,0 |
| RMa + Turkcell mesafe düzeltmesi (22) | 8,4 | **2,3** |
| + 3GPP anten (23) | 9,6 | 3,0 |
| + yük KPI'ya göre (24) | 9,3 | **2,8** |

\* Bu hesap yöntemiyle; 14. deneyin resmi sonucu 2,2 dB. 22–24 için bu yöntem resmi sonuçları birebir verdi.

EVM ile saha bazında SINR hatası (dB):

| Saha | 130 | 440 | 441 | 443 | 296 | 444 | 482 | 554 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 22. deney | +1,9 | +2,0 | +3,7 | +1,0 | +4,6 | +6,6 | +2,0 | +2,3 |
| 24. deney | +1,6 | +4,2 | +2,9 | +1,3 | +3,4 | +7,4 | +2,0 | +3,1 |

## Bu ne demek

1. **SINR sorununun asıl nedeni bulundu:** Modelde gerçek vericinin kalite sınırı yoktu. Güçlü sinyal alan
   kullanıcılar gerçekte olamayacak kadar yüksek SINR görüyordu. Standarttaki %8 EVM eklenince kaynaklı
   senaryoların SINR farkı 8–9 dB'den **2,3–2,8 dB**'ye düşüyor; karar kuralının SINR sınırı (3 dB) içinde.
2. S0'yu bu değişiklik pek etkilemiyor, çünkü S0'da sinyal zaten zayıftı ve kullanıcılar tavana yaklaşmıyordu.
   Bu da S0'nun "zayıf sinyal + geniş anten" ile SINR'yi neden tutturduğunu açıklıyor.
3. **RSRP hâlâ sınırın üstünde:** 22. deneyde 3,5 dB, 24. deneyde 5,4 dB (sınır 3 dB). Yani kaynaklı senaryo
   SINR'de artık geçiyor, RSRP'de az farkla geçmiyor.

## Sınırlar

- Bu sadece sonradan yapılan bir hesap. Simülasyonun içinde CQI ve zamanlayıcı hâlâ EVM'siz SINR'yi
  kullanıyor; EVM simülatöre eklenip yeniden koşulmalı.
- EVM sınırı en kötü durum şartı; gerçek vericiler genelde daha iyidir. Telefonun kendi alıcı kusurları da
  benzer bir tavan ekler. İkisi birlikte Experia'daki ~20 dB'lik tavanla uyumlu.
- Seçim 20–24. deneylerin sonuçları görüldükten sonra yapıldı.

## Öneri

Bir sonraki deney (26), bütün parçaları önceden yazılmış kurallarla bir arada koşmalı:
- RMa + 3GPP anten + KPI'ya göre yük (24. deney)
- **EVM %8, simülatörün içinde** (gürültüye sinyalin %8²'si kadar ek bozulma olarak)
- Mesafe düzeltmesinin 22. deneydeki **aynı yöntemle**, bu kez 3GPP antenli simülasyondan yeniden
  hesaplanması (23–24'te RSRP'nin bozulmasının nedeni, düzeltmenin cosine antenle hesaplanmış olmasıydı)

[Analiz](analysis.py) — [Sayılar](analysis.json)
