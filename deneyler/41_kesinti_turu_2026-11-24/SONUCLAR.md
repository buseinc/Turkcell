# Deney 41: Kesintiler arıza mı, elle kapatma mı? Sonuçlar (24 Kasım)

Kurallar `KURALLAR.md`. Kod: `suz41.py` (KPI süzme), `olay41.py` (olaylar). Olay listesi `olaylar41.csv`, özet `olay41.json`. Ham süzme yalnız yerelde.

**Kontrol:** 48 sahanın 10 günlük verisinde "açık + otomatik kapalı + elle kapalı" her dilimde 1'e eşit (en büyük sapma 0,00001). Yani her kapalı dakikanın türü ayrılabiliyor.

## Modelde kapattığımız iki saha

**482 (27 Ekim depremi, 22:48): gerçek arıza, sonra elle kilitleme.**
- 01:15'ten 05:15'e kadar (depremden 2,5–6,5 saat sonra) iki hücre de defalarca kapanıp açılıyor; kapalı sürenin tamamı **otomatik**. Bağlı kullanıcı 46'dan 12–20'ye düşüyor.
- 05:30'dan itibaren bir hücre **elle** kapalı ve gün boyu (~19 saat) öyle kalıyor; diğer hücre açık.
- Yorum: önce sistemin kendi fark ettiği bir arıza var, sonra operatör sorunlu hücreyi kilitliyor. Depremden sonra gerçek bir sorun olduğu kesin; sebebi (elektrik, akü, bağlantı) KPI'dan anlaşılmıyor.

**130 (10 Ağustos depremi, 19:53): elle kapatma, kısa.**
- 21:30–22:15 arasında (depremden ~1,6 saat sonra) sahanın o gün açık olan 6 hücresinin 6'sı kapalı; kapalı sürenin tamamı **elle**. 21:45 diliminde bütün hücreler tamamen kapalı, bağlı kullanıcı ve trafik sıfır.
- Bir hücrenin kapalı kaldığı süre 30 dakikanın altında olduğu için kuraldaki olay listesine girmedi; dilim dilim ayrıca bakıldı.
- Yorum: sistemin kendisi bir arıza kaydetmemiş; operatör sahayı yarım saat kilitlemiş. Bunun bir arızaya tepki mi (örneğin yeniden başlatma), yoksa başka bir iş mi olduğu bilinmiyor. **Bu bir "çökme" olarak kesinleştirilemiyor.**

## Diğer kesintiler

| Saha | Ne zaman | Süre | Hücre | Tür | Not |
|---|---|---|---|---|---|
| 200 | 27 Eki 11:15, depremden 11,6 saat **önce** | 5,25 saat | 14/14 | elle | Bütün saha, kullanıcı ve trafik sıfır. Planlı iş olabilir. |
| 438 | 28 Eki 14:00 | 2,75 saat | 8/8 | elle | 28 Ekim toplu kesintisi |
| 199 | 28 Eki 16:30 | 1,5 saat | 10/10 | **arıza** (%96 otomatik) | 28 Ekim toplu kesintisi |
| 389 | 28 Eki 20:45 | 1,5 saat | 8/8 | elle | 28 Ekim toplu kesintisi |
| 494 | 10 Ağu 15:30, depremden 4,4 saat **önce** | 3,5 saat | 1/1 | arıza | Ayrıca 20 Eki'de 1 saat arıza; 11 Ağu'da 14 saat elle |
| 011 | 11 Ağu 19:30 | 1,25 saat | 13/28 | arıza | |

208, 205 ve 283'ün 28 Ekim kesintileri her hücrede 30 dakikanın altında kaldığı için olay listesine girmedi.

**Genel:** 48 sahada 10 günde 38 olay var: 33'ü elle kapatma, 5'i arıza. Elle kapatma deprem olmayan günlerde de sık (örneğin 389'da 20 Ekim'de 24 saat, 552'de 17 Ağustos'ta 24 saat).

## Ne anlama geliyor

- **482 kesintisi gerçek bir arıza.** Kırsal kesinti senaryomuzu (sahanın çökmesi) gerçek bir olaya dayandırmak için en sağlam örnek bu. Gerçekte sahanın tamamı değil, 2 hücreden biri uzun süre kapalı kaldı; modelde ise bütün sahayı kapattık (daha ağır durum).
- **130 kesintisi çökme olarak kesinleşmiyor.** Kısa ve elle yapılmış. Senaryoda kullanılabilir ama "gerçek çökme" değil "deprem sonrası kısa kapatma" diye anlatılmalı.
- **28 Ekim toplu kesintisinde yalnız 199 arıza**, diğerleri elle. Şehirde "komşu sahalar birlikte çökerse" senaryosu için bu olay tek başına güçlü bir dayanak değil.
- **200 kesintisi depremle ilgisiz ve elle**, muhtemelen planlı. Kullanıcıların komşulara kaymasını ölçmek için yine kullanılabilir (kayma, kapanmanın sebebinden bağımsız).

## Sınır

- "Elle" her zaman "planlı" demek değil; operatör arızalı bir sahayı da elle kilitleyebilir. "Otomatik" de sistemin kendi fark ettiği bir arıza; sebebi bilinmiyor.
- Yalnız Sındırgı çevresindeki 47 saha ile 200 ve 011 incelendi; veri 10 gün.
