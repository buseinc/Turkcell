# Projeyi sıfırdan anlamak — basit anlatım

Bu belge, konuya yeni başlayan biri için yazıldı. Önce temel kavramları günlük hayattan örneklerle
anlatıyor, sonra ne yaptığımızı ve ne bulduğumuzu aynı dille açıklıyor. Teknik ayrıntılar
[ilk aşama özetinde](ILK_ASAMA_OZETI.md).

---

## Bölüm 1 — Mobil ağ nasıl çalışır?

### Baz istasyonu (saha, "site")

Tepelerde, binaların üstünde gördüğümüz telefon kuleleri. Telefonunuz internete ve aramalara bunlar
üzerinden bağlanır. Veride her kulenin bir kimliği var, örneğin `SITE_000443`.

### Sektör

Bir kule genellikle etrafını **üç dilime** böler. Her dilime bakan ayrı bir anten vardır: biri kuzeye, biri
güneydoğuya, biri güneybatıya. Kulenin tepesine konmuş, üç farklı yöne bakan üç el feneri gibi düşünün.
Her fener kendi önündeki bölgeyi aydınlatır.

### Frekans (taşıyıcı, bant)

Radyo kanallarına benzer. Aynı anten birden fazla "kanalda" yayın yapabilir.
- **Düşük frekans (ör. 800 MHz):** Uzağa gider, duvarları kolay geçer, ama daha az veri taşır. Bas ses gibi:
  uzaktan duyulur.
- **Yüksek frekans (ör. 1800 MHz):** Daha kısa menzil, ama daha çok veri. Tiz ses gibi: net ama yakında.

### Hücre ("cell")

Ağın en küçük birimi: **bir antenin bir frekansta oluşturduğu hizmet alanı.** Telefonunuz her an tek bir
hücreye bağlıdır. Bir kulede 3 yön × 2 frekans varsa 6 hücre olur. Veride bazı kulelerde 2, bazılarında
14 hücre var. Bunların kaç tanesinin "yön", kaç tanesinin "frekans" olduğunu bilmiyoruz. Hocanın
sorduğu soru da tam olarak bu.

### Girişim ve gürültü

Kalabalık bir odada bir arkadaşınızı dinlediğinizi düşünün:
- **Arkadaşınızın sesi** = sizin bağlı olduğunuz hücrenin sinyali.
- **Diğer masalardaki konuşmalar** = **girişim**. Aynı frekanstaki komşu kuleler de "konuşuyor" ve sizin
  sinyalinize karışıyor.
- **Klimanın uğultusu** = **gürültü**. Her alıcıda doğal olarak bulunan arka plan cızırtısı.

Farklı frekanstaki kuleler birbirine girişim yapmaz. Farklı odalarda konuşan insanlar gibi.

---

## Bölüm 2 — Ölçtüğümüz büyüklükler

### Desibel (dB) — önce birimi anlayalım

Sinyal gücü çok geniş bir aralıkta değiştiği için logaritmik bir ölçek kullanılır:
- **+3 dB ≈ 2 kat**, **+10 dB = 10 kat**, **+20 dB = 100 kat** güç.
- **dBm** mutlak güçtür. Telefonun aldığı sinyal çok zayıf olduğu için hep **negatif** sayılardır.
  −80 dBm, −110 dBm'den **daha güçlüdür** (sıfıra daha yakın).

Bu yüzden "simülasyon ile ölçüm arasında 2 dB fark var" demek, sinyal gücünde yaklaşık %60'lık bir fark
demek. Radyo dünyasında bu küçük bir farktır.

### RSRP — sinyal ne kadar güçlü?

**Telefonun, bağlı olduğu kuleden aldığı sinyalin gücü.** Arkadaşınızın sesinin yüksekliği.

| RSRP | Anlamı |
|---|---|
| −80 dBm ve üstü | Çok güçlü (kulenin dibindesiniz) |
| −90 … −100 dBm | İyi |
| −100 … −110 dBm | Orta |
| −110 … −120 dBm | Zayıf ama çalışır |
| −120 dBm altı | Çok zayıf, bağlantı kopabilir |

**"Telefon çekiyor mu?"** sorusunun cevabı büyük ölçüde RSRP'dir.

### SINR — sinyal ne kadar net?

**Sinyalin, girişim + gürültüye oranı.** Arkadaşınızın sesini kalabalığın içinde ne kadar net
ayırt edebildiğiniz.

| SINR | Anlamı |
|---|---|
| 20 dB ve üstü | Çok net, yüksek hız |
| 10 … 20 dB | İyi |
| 0 … 10 dB | Orta |
| 0 dB | Sinyal ile gürültü eşit güçte |
| 0 dB altı | Gürültü sinyalden güçlü, hız çok düşer |

Önemli: **Güçlü sinyal net sinyal demek değildir.** Yüksek sesle konuşan arkadaşınızı, herkes bağırıyorsa
yine anlayamazsınız. RSRP iyi olup SINR kötü olabilir. İnternet **hızını** asıl belirleyen SINR'dir.

### RSRQ — sinyal kalitesi

RSRP ile toplam alınan gücü karşılaştıran bir kalite ölçüsü. Kabaca SINR'nin kardeşi.
−10 dB iyi, −15 dB kötü sayılır. ns-3 bunu gerçek ağdan farklı hesapladığı için bizim projede
karşılaştırması güvenilir değil.

### CQI — telefonun karnesi

Telefon kuleye sürekli **"buradan seni ne kadar iyi duyuyorum"** diye 0–15 arası bir puan bildirir.
Kule bu puana bakarak o telefona ne kadar hızlı veri göndereceğine karar verir. Yüksek CQI = daha hızlı
gönderim.

### PRB — kulenin kapasitesi, ne kadar dolu?

Bir hücrenin veri taşıma kapasitesi küçük parçalara bölünmüştür. Bu parçalara **PRB (kaynak bloğu)** denir.
Bir restoranın masaları gibi düşünün:
- **PRB kullanımı %36** = masaların %36'sı dolu.
- Masalar dolarsa yeni gelenler bekler, yani internet yavaşlar.

Dolu bir hücre sadece kendi kullanıcılarını yavaşlatmaz; daha çok yayın yaptığı için **komşulara da daha
çok girişim** yapar. Kalabalık restoranın sesi yan restorana taşar gibi.

### TA — telefon kuleden ne kadar uzakta?

Sinyalin kuleye gidip gelme süresinden hesaplanan bir uzaklık göstergesi. Büyük TA = uzaktaki kullanıcılar.

### Handover — hücre değiştirme

Telefon hareket ederken veya sinyal zayıfladığında başka bir hücreye geçer. Buna handover denir.
**Frekanslar arası handover**, farklı bir frekansa geçiştir. Bir hücreden bu tür geçiş yapılıyorsa,
çevrede başka bir frekans **var** demektir. Bu bilgiyi hangi kulelerde birden fazla frekans olduğunu
anlamak için kullandık.

---

## Bölüm 3 — Elimizdeki veri

| Veri | Ne? | Benzetme |
|---|---|---|
| **Koordinatlar** | Kulelerin haritadaki yerleri | Şehir haritasındaki binalar |
| **Experia** | Gerçek telefonların ölçtüğü RSRP, SINR, RSRQ, TA. Saatlik, hücre bazında. Haziran 2026. | Müşterilerin doldurduğu memnuniyet anketi |
| **KPI** | Kulelerin kendi tuttuğu kayıtlar: kaç kişi bağlı, ne kadar veri geçti, PRB doluluğu, CQI. 15 dakikada bir, 2025'ten 10 gün. | Restoranın kendi kasa ve masa doluluk kayıtları |

**Elimizde olmayanlar:** Antenlerin hangi yöne baktığı, gücü, hangi frekansları kullandığı ve
kullanıcıların tam olarak nerede olduğu. Bunları tahmin etmemiz gerekti.

---

## Bölüm 4 — Ne yapıyoruz ve neden?

### Hedef

Sındırgı'da 2025'te depremler oldu. Deprem anında herkes telefona sarılır; ağ zorlanır. Amacımız:
**ağın bilgisayarda bir kopyasını kurup** "deprem anında ağ nerede yetersiz kalır, nasıl iyileştiririz"
sorusunu güvenle çalışabilmek. Gerçek ağda deney yapamayız; kuleyi kapatıp ne olacağına bakamayız.

### Simülatör: ns-3

Ağ için bir uçuş simülatörü. İçine kuleleri, antenleri ve sanal telefonları koyuyoruz. Simülatör sinyalin
nasıl yayıldığını, telefonların hangi kuleye bağlandığını ve ne kadar hızlı veri aldığını hesaplıyor.

### Ana zorluk: bilmediğimiz ayarları tahmin etmek

Bir fotoğrafı yalnız siyah-beyaz kopyasından renklendirmeye benziyor. Gerçek renkleri (anten ayarlarını)
bilmiyoruz, ama ipuçlarımız var: gerçek telefonların ölçümleri (Experia) ve kulelerin kayıtları (KPI).

Yöntemimiz:
1. Bir ayar dene (ör. anten gücü şu, yönü şu).
2. Simülasyonu çalıştır; sanal telefonların ölçtüğü RSRP/SINR'yi kaydet.
3. Gerçek ölçümlerle karşılaştır.
4. Gerçeğe en yakın sonucu veren ayarı seç.

### Kopya çekmemek için: eğitim ve kontrol sahaları

8 ana kuleden **5'ine bakarak** ayar seçtik (eğitim). **3'ünü** ayar seçerken hiç kullanmadık; sonra
"bunlarda da tutuyor mu?" diye kontrol ettik. Sınava sadece çalıştığınız sorulardan değil, yeni
sorulardan da girmek gibi.

### Hatayı nasıl ölçüyoruz: MAE

"Ortalama mutlak hata": her kulede simülasyonla gerçek arasındaki farkın ortalaması. **"RSRP hatası
1,7 dB"** demek, simülasyon her kulenin sinyal gücünü ortalamada 1,7 dB şaşırıyor demek. Bu iyi bir sonuç.

---

## Bölüm 5 — Adım adım ne yaptık

**1. Kuleleri doğruladık.** Hocanın seçtiği 16 kulenin yerlerini kontrol ettik ve haritaya koyduk.
Hepsi doğru.

**2. Ağı simülatörde kurduk.** 24 kule, her birinde 3 anten. Bilinmeyen ayarları (güç, anten genişliği,
sinyalin mesafeyle nasıl zayıfladığı) 49 farklı denemeyle taradık, en iyisini seçtik.

**3. Sanal telefon sayısını artırdık.** İlk başta 64 sanal telefon vardı; bazı kulelere sadece 1–2 telefon
düşüyordu. 64 kişilik bir anketin bazı mahallelerinden sadece 1 kişinin katılması gibi. 256'ya çıkınca
sonuçlar değişti. Yani 64 yetersizmiş.

**4. Ağı gerçek kalabalığa getirdik.** KPI'ya baktık: gerçek ağda masaların (PRB) normal günde %23'ü,
akşam yoğun saatinde %36'sı dolu. Bizim simülasyonda sadece %3'ü doluydu; boş bir restoranda gürültü
ölçmek gibi. Gerçek kalabalığı simülasyona verince sinyal kalitesi (SINR) gerçeğe çok yaklaştı.

**5. Depremleri veride gördük.** 10 Ağustos ve 27 Ekim 2025'teki depremlerde, KPI'da depremin olduğu
15 dakikada:
- aynı anda bağlı kişi sayısı **yaklaşık 2 katına** çıktı,
- ama indirilen veri miktarı **azaldı**.

Herkes aynı anda yakınını aramaya çalışıyor, ama video izleyen yok. Deprem yükü "daha çok veri" değil,
"aynı anda çok daha fazla kişi". Stres testini buna göre kurmalıyız.

**6. Kapsama haritalarını çizdik.** Bölgenin her 100 metresinde sinyal gücünü, hangi kulenin hizmet
verdiğini ve sinyal kalitesini gösteren haritalar. Sonuç: bölgede sinyalin hiç olmadığı bir yer yok.

**7. Telefonların karnesini (CQI) karşılaştırdık.** Simülasyondaki telefonlar gerçek telefonlardan biraz
daha düşük puan veriyor. Yani simülasyonda girişim biraz fazla.

**8. Kulelerin içindeki hücreleri inceledik.** Handover kayıtlarına bakarak 8 ana kulenin 5'inde birden
fazla frekans olduğunu bulduk. Bizim simülasyonda ise her kule tek frekanstaydı. Bu, girişimin neden
fazla çıktığını açıklıyor: herkes aynı odada konuşuyormuş gibi davrandık.

**9. Çok frekanslı versiyonu denedik.** Bu kulelere ikinci bir frekans (800 MHz) ekledik. Bazı şeyler
gerçeğe yaklaştı, bazıları uzaklaştı. Çünkü ikinci frekansın gücünü ve hangi telefonun hangi frekansa
bağlanacağını bilmiyoruz; tahmin ettik. Bu yüzden şimdilik tek frekanslı versiyonu ana senaryo olarak
tutuyoruz.

---

## Bölüm 6 — Sonuçlar ne anlama geliyor?

| Sonuç | Basitçe |
|---|---|
| RSRP hatası 1,7 dB | Simülasyon "telefon ne kadar güçlü çekiyor" sorusunu iyi tahmin ediyor. |
| Kulelerin sıralaması %79–95 doğru | Hangi kulenin güçlü, hangisinin zayıf olduğunu doğru biliyor. |
| SINR hatası 2,2 dB | "Sinyal ne kadar net" sorusunda da makul, ama gerçek ölçümün nasıl hesaplandığını bilmediğimiz için temkinliyiz. |
| CQI 1,1 puan düşük | Simülasyondaki ağ gerçeğinden biraz daha "gürültülü". |
| Kapsama boşluğu yok | Bölgenin %99,8'inde sinyal var. |
| Bazı kulelerde güçlü hücreler eksik | Gerçek ağ çok frekanslı; bizim modelimiz tek frekanslı olduğu için bu çeşitliliği tam yakalamıyor. |

**Tek cümleyle:** Kurduğumuz ağ "telefon çekiyor mu?" sorusu için güvenilir. "Ne kadar hızlı, ne kadar
kişiyi kaldırır?" sorusu için de makul bir başlangıç, ama frekans bilgisi gelirse daha iyi olur.

---

## Bölüm 7 — Hocaya ne soracağız (basitçe)

1. **Kulelerde hangi frekanslar var, antenler ne kadar güçlü?** Bu gelirse tahmin yapmayı bırakırız.
2. **Experia'daki sinyal kalitesi (SINR) nasıl hesaplanıyor?** Elma ile elmayı mı karşılaştırıyoruz, emin olmak için.
3. **KPI'daki bazı sayıların birimleri ne?** Örneğin veri hızı Mbit/s mi, MB mı?
4. **Bu başlangıç yeterli mi?** Stres testine (ağı zorlama deneylerine) geçebilir miyiz?

---

## Mini sözlük

| Terim | Kısaca |
|---|---|
| Saha / site | Kule |
| Sektör | Kulenin bir yöne bakan anteni |
| Hücre / cell | Bir antenin bir frekanstaki hizmet alanı |
| Taşıyıcı / bant | Frekans kanalı (800 MHz, 1800 MHz…) |
| RSRP | Sinyal gücü (dBm; sıfıra yakın = güçlü) |
| SINR | Sinyal netliği (dB; büyük = iyi) |
| RSRQ | Sinyal kalitesi |
| CQI | Telefonun kuleye bildirdiği 0–15 puan |
| PRB | Kulenin kapasite birimi; "masa" |
| KPI | Kulelerin performans kayıtları |
| Experia | Telefonlardan toplanan ölçümler |
| TA | Telefonun kuleye uzaklık göstergesi |
| Handover | Hücre değiştirme |
| Girişim | Komşu kulelerin aynı frekanstaki "gürültüsü" |
| ns-3 | Ağ simülatörü |
| UE | Kullanıcı cihazı, telefon (simülasyonda "sanal kullanıcı") |
| MAE | Ortalama hata |
| dB / dBm | Logaritmik güç birimi; +3 dB ≈ 2 kat, +10 dB = 10 kat |
| S0 / S1 / S2 | Tek frekans 3 sektör / az sektör / çok frekans senaryoları |
