# Kontrol ve mixed yöntemlerini karşılaştırınca ne oldu?

**Mixed yöntemde raporlanan SINR, Experia saha özetlerine belirgin biçimde
yaklaştı.** Bu, ölçüm tanımının karşılaştırma açısından önemli olduğunu
gösteriyor; gerçek ağ doğrulaması veya doğru yöntemin kesin seçimi değildir.

## Aynı koşullarda karşılaştırma

24 saha, 72 sektör, aynı 64 kullanıcı ve aynı düşük UDP trafik düzeni
kullanıldı. Frekanslar, antenler, güçler ve konumlar değiştirilmedi.
Önce kontrol yöntemi eski sonucu 64 kullanıcıda sıfır farkla yeniden üretti.

| Gösterge | Kontrol | Mixed |
|---|---:|---:|
| 3 kontrol sahasında SINR ortalama mutlak hatası | **9,97 dB** | **1,56 dB** |
| 8 ana sahada SINR ortalama mutlak hatası | 8,38 dB | 2,33 dB |
| 3 kontrol sahasında RSRP ortalama mutlak hatası | 3,86 dB | 3,86 dB |
| 3 kontrol sahasında RSRQ ortalama mutlak hatası | **5,42 dB** | **5,42 dB** |
| 64 kullanıcı arasındaki medyan raporlanan SINR | 0,63 dB | 9,74 dB |
| Aynı koşuda bağımsız ölçülen kontrol SINR medyanı | 0,63 dB | 0,63 dB |
| Bağlanan kullanıcı | 64/64 | 64/64 |
| Kısa koşuda DL veri alan kullanıcı | 60/64 | 64/64 |

Eski üç kontrol sahası daha önce görüldü; bu yeni bir kör doğrulama değildir.
RSRQ farkı devam ediyor. Daha yakın SINR sonucunu tek başına gerçek yapılandırma
veya ölçüm eşdeğerliği kanıtı olarak kullanamayız.

## Somut örnek

444 sahasına bağlı sanal kullanıcı 7:

- Kontrol yönteminde SINR: **0,71 dB**.
- Mixed yönteminde raporlanan SINR: **11,04 dB**.
- Mixed koşusuna ayrıca eklediğimiz kontrol SINR gözlemcisi: yine **0,71 dB**.
- Aynı kullanıcının yalnız gürültüye göre sinyal oranı (S/N): **11,37 dB**.

Yani fiziksel kontrol girişimi ortadan kalkmadı. İstenen sinyali veri
kanalındaki girişimle değerlendiren başka bir SINR hesabına geçtik.
Bu hesap düşük veri girişimi gözlendiğinde daha yüksek değer verebiliyor.

## Neden yükseldi?

Mixed örneklerinin **%88,46'sında** native hesap çağrısında yeni bir veri
girişim güncellemesi yoktu. ns-3 bu durumda paydada yalnız alıcı gürültüsünü
kullanıyor. Örneklerin toplam %88,81'inde raporlanan SINR, S/N ile aynı çıktı;
bu ikinci oran, yeni güncelleme olsa da yalnız gürültü bulunan örnekleri de içerir.

Bu sayılar kaydettiğimiz 1.984 örneğe aittir. “Şebeke zamanın %88'inde tamamen
boştu” anlamına gelmez. Bir UE'nin yeni veri girişim ölçümü bulunmaması,
diğer bütün istasyonların o sırada susmuş olduğunu kanıtlamaz.

Trafik yükseltilmedi ve gerçek KPI yüküne kalibrasyon yapılmadı. Daha yoğun
veya farklı bir yükte aynı yakınlık beklenmemelidir.

## CQI etkisini ayırmak neden önemli?

Bu seçenek, zamanlayıcıya verilen CQI'yi de değiştiriyor. Bu nedenle veri
alan kullanıcı sayısının 60'tan 64'e çıkması yalnız bir çıktı sütununu
yeniden adlandırmak değildir. Aynı fiziksel kontrol koşullarında veri
iletimi kararları da farklılaşabiliyor. 4 saniyelik düşük yük probu gerçek
hizmet kapasitesi veya kapsama doğrulaması olarak yorumlanmadı.

## Doğrulamalar

- İki koşuda 64 kullanıcının hizmet saha/sektörleri aynı.
- RSRP ve RSRQ farkı sıfır.
- Bağımsız kontrol SINR gözlemcisinin koşular arası farkı sıfır.
- Kontrol çıktısı S/(I_ctrl+N) ile yeniden üretildi; en büyük fark yaklaşık 2,38×10⁻¹⁴ dB.
- Mixed çıktısı veri girişiminin güncellenme/tüketilme durumu izlenerek yeniden üretildi;
  en büyük fark yaklaşık 3,55×10⁻¹⁴ dB.
- Ana projenin C++ kaynağı ve sabit başlangıç senaryosu korundu.

## Hocaya gösterilecek çıkarım

“Aynı şebekede SINR/CQI tanımını değiştirince kontrol sahalarındaki hata
9,97 dB'den 1,56 dB'ye indi. Fiziksel kontrol SINR'si, RSRP ve RSRQ aynı kaldı.
Bu düşük yükte mixed hesap çoğu örnekte yalnız gürültüye dayanıyor.
Experia SINR'si hangi kanal, yük/örneklem ve ortalama tanımından geliyor;
mixed yöntemle karşılaştırma uygun mu? RSRQ farkı için ayrıca neyi eşleştirmeliyiz?”

Takip araştırması için aday: farklı sunulan yüklerde kontrol/mixed farkını
ve ölçüm güncellemesi sıklığını incelemek. Bu deney henüz yapılmadı.

## Dosyalar

- [Görsel](mixed_comparison.png)
- [Yöntem, sınırlar ve tekrar üretim](YONTEM.md)
- [Özet sayılar](summary.csv)
- [Saha karşılaştırması](site_comparison.csv)
- [Kullanıcı karşılaştırması](ue_comparison.csv)
- [Örnek bazında karşılaştırma](sample_comparison.csv)
- [Kontroller](checks.json), [koşu sonuçları](study_result.json), [önceden yazılmış plan](experiment_plan.json)
