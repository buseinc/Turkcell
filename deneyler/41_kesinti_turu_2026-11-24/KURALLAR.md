# Deney 41: Kesintiler arıza mı, elle kapatma mı? Kurallar

24 Kasım, sonuçlara bakmadan yazıldı. Hocanın isteği: modelde kapattığımız kesintilerin gerçekten çökme olup olmadığını kesinleştirmek.

## Veri

- KPI'da her hücre ve 15 dakika için üç pay var ve toplamları her zaman 1 (deney 39 verisinde 5.485 kesintili dilimin hepsinde kontrol edildi):
  - `EUtranCell_Availability_PC_ERI`: hücre açık.
  - `DownTime_Auto_PC_ERI`: hücre **otomatik** kapalı, yani sistem bir arıza nedeniyle kapattı (elektrik, donanım, bağlantı).
  - `DownTime_Man_PC_ERI`: hücre **elle** kapatılmış (operatör kilitlemiş).
- Ham KPI dosyalarından şu sahaların bütün hücreleri, 10 gün: deney 09'daki 47 Sındırgı çevresi sahası, ayrıca 200 ve 011. Süzme yalnız yerelde.

## İncelenen kesintiler

Deney 30 ve 38'de bulunanlar:
- **130**, 10 Ağustos akşamı (modelde kapattığımız saha).
- **482**, 27–28 Ekim gecesi ve 28 Ekim (modelde kapattığımız saha).
- **28 Ekim öğleden sonra** aynı anda kapanan 438, 199, 389, 208, 205, 283.
- **484**, **494** (10–11 Ağustos), **552** (Ekim).
- **200**, 27 Ekim, depremden önce 5 saat (gerçek veriyle karşılaştırdığımız saha).
- **011**, 11 Ağustos.

Ayrıca bu sahalarda 10 gün içindeki bütün kesintiler listelenir (en az 30 dakika, hücrenin erişilebilirliği %99'un altında).

## Sınıflandırma

Bir kesinti olayında (aynı sahada art arda kesintili dilimler) kapalı sürenin toplamı içinde:
- otomatik pay ≥ %90 ise **arıza**,
- elle pay ≥ %90 ise **elle kapatma**,
- arası **karışık**.

Ayrıca her olay için: kaç hücre etkilendi (sahanın tamamı mı), bağlı kullanıcı ve trafik sıfıra düştü mü, başlangıç saati ve depreme uzaklığı.

## Yorum sınırı

"Elle kapatma" her zaman planlı bakım demek değil: operatör arızalı ya da tehlikeli bir sahayı da elle kilitleyebilir. KPI bunun sebebini söylemiyor. "Otomatik" ise sistemin kendisinin fark ettiği bir arıza; sebebi (elektrik, hasar, bağlantı) yine bilinmiyor.
