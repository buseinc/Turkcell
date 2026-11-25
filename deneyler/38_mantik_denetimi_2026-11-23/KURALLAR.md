# Deney 38: Mesafe düzeltmesi sınaması, kurallar

23 Kasım'da, aşağıdaki iki yeni hâlin hiçbir sonucu görülmeden yazıldı. Görülen tek şey `SONUCLAR.md`'deki ilk duyarlılık tablosu.

## Karşılaştırılan üç hâl

Düzeltme formülü (k0 + k1·log10 d) ve katsayıları **yeniden ayarlanmıyor**.

- **A (bugünkü):** d = kullanıcının ev sahasına uzaklığı. Aynı değer bütün bağlantılara ekleniyor. Saha çökse de değişmiyor.
- **S (hizmet veren hücre):** d = kullanıcının o senaryoda bağlandığı hücreye uzaklık. Tek değer, bütün bağlantılara ekleniyor. Saha çökünce yeni hücreye göre yeniden hesaplanıyor. Düzeltme, ölçümde de hizmet veren hücrenin RSRP'si ile TA uzaklığından çıkarıldığı için bu tanıma en yakın hâl.
- **C (bağlantı başına):** Her kullanıcı–hücre bağlantısına kendi mesafesiyle ayrı düzeltme.

## Ölçümle uyum testi (kesinti sonucuna bakmadan)

%3 katsayısı üç hâlde de açık.

Bir hâl **geçer**, eğer:
1. Edremit test sahalarında SINR farkı ≤ 3 dB ve RSRP farkı ≤ 5 dB (deney 35'teki sınırlar).
2. Sındırgı'nın ayrılmış sahalarında SINR ve RSRP farkı A'dan en fazla 1 dB kötü.

**Seçim:** S ve C ikisi de geçerse, eğitim sahalarındaki toplam fark (Edremit + Sındırgı, SINR + RSRP) küçük olan seçilir. Yalnız biri geçerse o seçilir. İkisi de geçmezse A'nın kesinti sonucu "varsayıma bağlı" olarak kalır ve yeni bir sayı ana sonuç yapılmaz.

## Kesinti ve yol

Üç hâl için aynı hesap (hızlı model, f = 0,03, yumuşak gölgeleme ve konuma bağlı görüş hattı, iki bölgede aynı ayar):
- Sındırgı: 482, 130, ikisi (tek anten çekilişi, deney 33'ün girdileri).
- Edremit: 529, 105 (3 anten çekilişi).
- Yol: il yolu (130), D240 (482).

Bu hızlı model sonucu **ön elemedir**. Seçilen hâl ana sonucu değiştiriyorsa ns-3'te tekrarlanması önerilir.

## Gerçek 200 kesintisiyle karşılaştırma (23 Kasım, model sonucu görülmeden yazıldı)

- **Gerçek değer:** KPI'da 200 kapanınca eksilen kullanıcıların %67'si (± 12) en yakın 6 sahada görünüyor.
- **Model ölçüsü:** 200'ün kullanıcılarından, 200 kapalıyken servis alan ve bu aynı 6 sahadan birine bağlanan pay. 6 sahadan modelde olmayanlar ayrıca raporlanır; eksikse karşılaştırma zayıf sayılır.
- **Karşılaştırılanlar:** A, S, C ve ara paylar (düzeltmenin %25, %50, %75'i kullanıcıda kalır, gerisi yeni hücreye göre hesaplanır). Hızlı model, f = 0,03, 3 anten çekilişi, deney 33 kullanıcıları.
- **Karar:** Çekiliş ortalaması 55–79 aralığında olan hâl "KPI ile uyumlu" sayılır. Tek olay olduğu için bu **ayar yapmak için kullanılmaz**, yalnız hangi hesabın gerçeğe yakın olduğunu gösterir.
