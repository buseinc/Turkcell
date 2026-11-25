# Deney 38: Mantık denetimi (23 Kasım)

**Soru:** Kesinti ve yol sonuçlarında mantıksal olarak hatalı bir şey var mı?

## Ana bulgu: mesafe düzeltmesi çöken sahaya bağlı kalıyor

Modelde her kullanıcıya, kendi sahasına uzaklığına göre tek bir düzeltme veriliyor ve bu düzeltme kullanıcının **bütün** bağlantılarına ekleniyor (`building-vertical-model.h`, "same on every link of that UE"). Örneğin 482'ye 300 m uzaktaki kullanıcıya yaklaşık 41 dB kayıp ekleniyor.

Saha çökünce kullanıcı komşuya bağlanıyor, ama çöken sahaya yakınlıktan gelen bu kayıp komşu bağlantısında da kalıyor. Yani kullanıcı sahaya çok yakın olduğu için cezalandırılıyor.

ns-3'te (deney 33) 482 çökünce servis kaybedenlerin %93'ü çöken sahaya 1 km'den yakın. 300 m içindeki 8 kullanıcının 8'i servis kaybediyor.

## Etkisi (hızlı model)

A: bugüne kadarki hâli. B: etkilenen kullanıcıların düzeltmesi, açık kalan en yakın sahaya göre yeniden hesaplanıyor.

| Çöken sahanın çevresinde servis yok | A | B |
|---|---|---|
| Sındırgı, 482 | %28,4 | %1,2 |
| Sındırgı, 130 | %22,5 | %5,0 |
| Sındırgı, ikisi | %25,6 | %2,5 |
| Edremit, 529 (3 çekiliş) | %2,6 | %4,2 |
| Edremit, 105 (3 çekiliş) | %6,8 | %11,1 |

| Yolda servissiz kısım | A | B |
|---|---|---|
| İl yolu, 130 çökünce | 6,81 km | 0,16 km |
| D240, 482 çökünce | 0,34 km | 0,20 km |

## Ne anlama geliyor

- **"Sındırgı %15–19, Edremit %0–5" ve "130 çökünce yolun 6,6 km'si kopuyor" sonuçları bu varsayıma bağlı.** B ile fark kayboluyor, sıralama tersine bile dönebiliyor.
- **Hangisinin doğru olduğu henüz bilinmiyor.** Düzeltme kullanıcının yerinden geliyorsa (örneğin bina içi) A'ya, kuleye uzaklıktan geliyorsa B'ye yakın. B de kesin doğru değil: tek bir değeri bütün bağlantılara uyguluyor.
- ns-3 sayıları doğru hesaplanmış; sorun kurduğumuz varsayımda.
- Deprem yükünün ağı tıkamadığı sonucu bundan doğrudan etkilenmiyor; o kesintisiz ağda ölçüldü.

## Diğer sınırlar

1. **Sındırgı ve Edremit ns-3 koşuları aynı ayarda değil.** Edremit'te yumuşak gölgeleme, konuma bağlı görüş hattı ve %3 katsayısı açık; deney 33'te kapalı.
2. **Yalnız indirme yönü var.** Trafik yalnız kullanıcıya doğru. Ses iki yönlüdür ve hücre kenarında telefonun gönderme gücü sınır olabilir.
3. **Saha run başından kapalı.** Çökme anı, kopan telefonların aynı anda yeniden bağlanması ve sinyalleşme yükü modelde yok. "Ağ tıkanmıyor" yalnız indirme yönündeki veri kapasitesi için geçerli.
4. **Her bölgede iki saha kapatıldı.** "Sık bölge / seyrek bölge" genellemesi için az.

## Önerilen düzeltme (henüz yapılmadı)

Düzeltmeyi kullanıcıya değil **her kullanıcı–saha bağlantısına kendi mesafesiyle** uygulamak. Önce hızlı modelde gerçek ölçümlere uyumu yeniden sınanmalı; geçerse ns-3 kesinti ve yol koşuları tekrarlanmalı.

## Sınama sonucu: üç uygulama (hızlı model, 23 Kasım)

Kurallar `KURALLAR.md`, kod `duzeltme_sinama.py`, sayılar `duzeltme_sinama.json`. %3 katsayısı üç hâlde de açık; iki bölgede ayar aynı.

**A:** bugünkü (düzeltme ev sahasına bağlı). **S:** düzeltme bağlı olunan hücreye uzaklıktan. **C:** her bağlantıya kendi mesafesiyle.

### Gerçek ölçümlerle uyum (saha başına ortalama fark, dB)

| | A | S | C |
|---|---|---|---|
| Edremit test, SINR | 0,71 | **0,55** | 0,90 |
| Edremit test, RSRP | 3,29 | **2,63** | 3,64 |
| Sındırgı test, SINR | 1,95 | **1,18** | 1,92 |
| Sındırgı test, RSRP | 4,17 | **2,27** | 6,55 |
| Kural | geçti | **geçti, seçildi** | kaldı (Sındırgı RSRP) |

### Kesinti ve yol

| Çevrede servis yok (saha açıkken → çökünce) | A | S | C |
|---|---|---|---|
| Sındırgı, 482 | %0 → %28,4 | %0 → %0 | %1,2 → %2,5 |
| Sındırgı, 130 | %10 → %22,5 | %5 → %2,5 | %0 → %0 |
| Edremit, 529 (3 çekiliş) | %1,6 → %2,6 | %3,1 → %3,1 | %3,1 → %3,1 |
| Edremit, 105 (3 çekiliş) | %6,0 → %6,8 | %5,1 → %6,8 | %5,1 → %6,0 |
| İl yolu servissiz, 130 çökünce | 6,81 km | 0,10 km | 0,19 km |
| D240 servissiz, 482 çökünce | 0,34 km | 0,13 km | 0,10 km |

### Karar

- **Sındırgı'daki %15–19, il yolundaki 6,6 km ve "seyrek bölge dolduramıyor, sık bölge dolduruyor" sonuçları geçerli değil.** Büyük kısmı düzeltmenin çöken sahaya bağlı kalmasından geliyordu.
- S hem ölçüme daha iyi uyuyor hem de kesinti etkisini neredeyse sıfırlıyor. Kurala göre yeni model S.
- **S iyimser olabilir.** Düzeltme eğrisi normal günde o hücreye bağlı olan kullanıcılardan çıktı. Saha çökünce uzak hücreye mecburen geçen kullanıcı bu kitleye benzemeyebilir. Bu yüzden "kesinti hiç etki etmiyor" da denemez; doğru cümle: "tek saha kesintisinin kapsama etkisi, modelin bu varsayımına bağlı ve düzeltilmiş modelde küçük".
- "Deprem yükü ağı tıkamıyor" sonucu bundan etkilenmiyor; yine yalnız indirme yönü için geçerli.
- Bu sayılar hızlı modelden. Kurala göre ns-3'te tekrar gerekiyor.

## Modelsiz kontrol: gerçek kesintilerde kullanıcılar komşulara geçti mi? (KPI, 23 Kasım)

Kod ve kural `gercek_kesinti_kayma.py`, sayılar `gercek_kesinti_kayma.json`. Simülasyon yok. Bir sahanın bütün hücreleri en az 30 dakika kapalıyken, o sahadan eksilen bağlı kullanıcıların ne kadarının en yakın 6 sahada göründüğüne bakıldı. Genel zaman değişimi diğer sahalarla düzeltildi. Gürültü, aynı saha ve saatin kesintisiz günlerinden hesaplandı.

| Saha | Ne zaman | En yakın saha | Eksilen kullanıcı | Komşuda görünen | Not |
|---|---|---|---|---|---|
| 011 (Edremit) | 11 Ağu, 30 dk | 0,9 km | 158 | %102 ± 22 | kısmi kesinti, depremden sonraki gün |
| **200 (Sındırgı komşusu)** | **27 Eki, 5 saat** | **1,0 km** | **320** | **%67 ± 12** | **en temiz olay; depremden önce** |
| 494 | 20 Eki, 1 saat | 5,9 km | 24 | −%12 ± 40 | çok az kullanıcı |
| 494 | 27 Eki, 30 dk | 5,9 km | 16 | −%22 ± 48 | çok az kullanıcı |

**Kullanılmayan olaylar:** 438 (%58 ± 8) ve 389 (%442) 28 Ekim'deki toplu kesintiye denk geliyor, komşuları da aynı gün etkilenmiş olabilir. 494'ün 11 Ağustos olayı gürültü içinde. 130 ve 482'nin bütün hücreleri kapanmadığı için bu listeye girmiyor.

**Ne söylüyor:**
- Gerçek kesintide kullanıcıların önemli kısmı komşulara geçiyor, ama hepsi değil. En temiz olayda (200) yaklaşık **üçte ikisi** görünüyor, **üçte biri** en yakın 6 sahada görünmüyor.
- Bu, "kesinti neredeyse kimseyi etkilemiyor" diyen S hâlinin fazla iyimser olabileceğini gösteriyor.
- Sahalar uzaklaştıkça komşuya geçen pay azalıyor gibi, ama olay sayısı çok az ve 494'te belirsizlik büyük. Kanıt değil, işaret.

**Sınır:** "Komşuda görünmüyor", "servis alamadı" demek değil. Kullanıcı daha uzak bir sahaya geçmiş, telefonu boşta kalmış ya da bölgeden ayrılmış olabilir. Bu yüzden üçte bir, servis kaybı için **üst sınır**.

## Gerçek 200 kesintisiyle model karşılaştırması (hızlı model, 23 Kasım)

Kural `KURALLAR.md`, kod `kesinti_200.py`, sayılar `kesinti_200.json`. 200'ün modeldeki 144 kullanıcısı, 3 anten çekilişi. KPI: eksilen kullanıcıların %67'si (± 12) en yakın 6 sahada.

| Düzeltmenin uygulanışı | En yakın 6 sahada | Başka sahada servis alan | Servis yok | KPI ile uyumlu (%55–79) |
|---|---|---|---|---|
| A (tamamı kullanıcıda) | %87,5 | %10,0 | %2,5 | hayır |
| %75 kullanıcıda | %88,2 | %10,0 | %1,9 | hayır |
| %50 kullanıcıda | %88,4 | %10,0 | %1,6 | hayır |
| %25 kullanıcıda | %89,1 | %10,0 | %0,9 | hayır |
| S (tamamı yeni hücreye göre) | %88,9 | %9,7 | %1,4 | hayır |
| C (bağlantı başına) | %65,3 | %33,8 | %0,9 | evet |

**Sonuç: bu olay A ile S'yi ayıramıyor.**

- 200'ün 1 km yakınında bir komşusu var (206). Bu yüzden düzeltme nasıl uygulanırsa uygulansın servis kaybı %1–3 çıkıyor. A ile S'nin farkı yalnız yakın komşusu olmayan sahalarda (482, 130) ortaya çıkıyor.
- A, S ve ara paylar komşulara geçişi KPI'dan fazla gösteriyor (%88'e karşı %67).
- C bu ölçüde uyuyor, ama C seçilemez: normal gün ölçüm testinden kaldı (Sındırgı RSRP farkı 6,6 dB). Tek olaya bakarak seçmemek de kuraldı.
- **Karşılaştırma zayıf:** en yakın 6 sahadan biri (461, 10,9 km) modelde yok.
- **Tek güvenli bilgi:** Yakın komşusu olan bir sahada model, düzeltmenin biçiminden bağımsız olarak küçük servis kaybı veriyor.

**Hâlâ çözülmeyen:** Yakın komşusu olmayan sahalarda kesinti etkisi (Sındırgı'da %0–28). Bu sahaların elimizde temiz bir tam saha kesintisi yok: 130'un 7 hücresinden 6'sı yarım saat, 482'nin 2 hücresinden 1'i kapandı ve ikisi de deprem sonrasına denk geliyor.
