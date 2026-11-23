# Nerede kaldık? (21 Kasım 2026)

Bu not senin okuman için; hocaya gidecek metin değil. Taslağın (`ana_proje/main.tex`) bittiği yerden bugüne kadar yapılanları sade bir dille anlatıyor.

## Taslak nerede bitiyordu

- **Model gerçek ağa uyuyor.** Bütün değerler gerçek kaynaklardan alındı. Test sahalarında sinyal kalitesindeki fark 2,6 dB, sinyal gücündeki fark 4,8 dB.
- **Stres testine başlanmamıştı.** Taslağın sonunda "stres testine henüz başlamadık" yazıyor.

Sonraki her şey tek bir soruyla ilgili: **deprem anında bu ağ ne olur?**

## Yapılanlar, sırayla

| # | Ne sorduk | Ne bulduk |
|---|---|---|
| 27 | Model, hiç bakmadığı komşu sahalarda da tutuyor mu? | Evet. Fark 3,1 dB ve 5,7 dB; ana sahalardakine yakın. |
| 28 | Bir hücre kaç görüşme kaldırır? (ilk deneme) | ns-3'ün varsayılan ayarı küçük bir ses paketine bile bütün kanalı veriyor. Sonuç yalnız "en kötü durum" olarak geçerli. |
| 29 | Kaynağı ihtiyaca göre veren gerçekçi ayarla? | Hücre başına 200 görüşmede bile tıkanma yok, gecikme 14 ms. |
| 30 | Depremde gerçekten saha çöktü mü? | Evet. 10 Ağustos'ta 130, 28 Ekim'de 482 (KPI kayıtlarından). |
| 31 | Binlerce durumu hızlıca tarayabilir miyiz? | ns-3'ün formülleriyle çalışan, saniyeler süren bir hızlı model yazıldı ve ns-3 ile aynı sonucu verdiği gösterildi. Kapasite: hücre başına en az 250–300 eşzamanlı görüşme. |
| 32 | Deprem yükü gerçekte ne kadar? | Bağlı kişi sayısı 1,6–1,85 kat artıyor; ağın kullanılan kaynağı artmıyor. En yoğun anda hücre başına ~100 kişi. |
| 33 | Saha çökünce ne olur? (ns-3) | Hiçbir hücre dolmuyor. Ama kapanan sahanın çevresindeki kullanıcıların %15–18'i servis alamıyor; saha açıkken bu oran %0. |
| 34 | Yoldaki araçlar ne yaşar? (ns-3, gerçek yollar) | 130 çökünce il yolunun 6,6 km'si servissiz kalıyor; en uzun kopukluk 2,8 km. 482 çökünce D240 etkilenmiyor. |

## Üç cümlelik sonuç

1. **Deprem yükü ağı tıkamıyor.** Ağ, deprem anının ~3 katını kaldırıyor.
2. **Asıl sorun, çöken sahanın çevresine sinyalin ulaşmaması.** Bu en çok seyrek bölgelerde oluyor: 130'un çevresi kötü, 482'nin çevresi iyi.
3. **İHA'nın işi kapasite eklemek değil, sinyal ulaşmayan yere sinyal götürmek.** İlk somut hedef: 130 çökünce il yolundaki ~3 km'lik kopukluk.

## Güvendiğimiz ve güvenmediğimiz şeyler

**Güvendiklerimiz:**
- Model gerçek ölçümlere uyuyor. Taslakta ve deney 27'de gösterildi; deney 34'teki değişikliklerden sonra tekrar kontrol edildi.
- Hızlı model ns-3 ile aynı sonucu veriyor. Örneğin yolda servissiz kısım ns-3'te 6,6 km, hızlı modelde 6,8 km.
- Kapasite ve kesinti sonuçları, koşudan önce yazılmış kurallarla değerlendirildi.

**Dikkatli söylememiz gerekenler:**
- **Anten yönleri bilinmiyor.** Rastgele seçildi ve kesinti koşularında tek bir seçim kullanıldı.
- **Arazi düz kabul ediliyor.** Gerçekte Sındırgı dağlık; tepeler kapsamayı değiştirebilir.
- **Tek frekans var sayılıyor.** Gerçek sahaların çoğu birden çok frekans kullanıyor; hücre başına bant bilgisi verimizde yok.
- **Yolda gerçek ölçüm yok.** Yol sonuçları gerçekle karşılaştırılamıyor.
- **Hücre geçişi gerçekte olduğundan sık çıkıyor.** Sebebi ns-3'ün varsayılan ayarları.

**Açık kalan tek soru:** Normal günde simülasyonda kullanıcıların %15–20'si "düzgün konuşamıyor" çıkıyor. "Kodlama düzeltme döngüsü yok" açıklamasını sınadık, tutmadı; sebep bilinmiyor. Kesinti ve yol sonuçlarını etkilemiyor, çünkü onları paket teslimine göre değil sinyal ölçütlerine göre değerlendirdik.

## Taslakta düzeltilmesi gerekenler (hocaya gönderirsen)

- "Stres testine henüz başlamadık" → yapıldı (deney 28–34).
- "Deprem anında bağlı kişi yaklaşık iki katı" → ölçüm 1,6–1,85 kat.
- "Yük deneylerinde tek ve çok frekanslı senaryoyu birlikte koştururuz" → yalnız tek frekansla koşturuldu. Hücre başına bant bilgisi verimizde yok; bu kalıcı bir sınır olarak yazılmalı.
- "Kullanıcılar sabit, handover kurulmadı" → yollarda hareketli araçlar ve hücre geçişi artık var.
- Taslağın sonundaki "Turkcell'e sorabilme ihtimalimiz var mı" bölümü artık geçerli değil. Turkcell'den ek veri gelmeyecek; eksikler kalıcı sınır olarak yazılmalı.

## Kalıcı sınırlar (verimizde yok, gelmeyecek)

- Hücrelerin frekans bandı ve aynı sektördeki hücreler.
- Anten yönleri (azimut). Kapsama sonuçlarını en çok bu değiştiriyor; üç rastgele çekilişle ele alınıyor.
- Yolda gerçek ölçüm (drive test). Yol sonuçları gerçekle karşılaştırılamıyor.
- Experia'daki sinyal kalitesinin (SINR) tanımı. Sık bölgelerde bu yüzden ayarlanmış bir katsayı (f = 0,03) kullanılıyor (deney 35).

## Sırada

- **Başka bölge (sahil / şehir merkezi):** Önce elimizdeki dosyalarda hangi ilçelerin verisi olduğuna bakıyoruz (deney 35).
- **İHA aşaması:** Şimdilik bekliyor; hedefi belli.
