# Deney 39: Gün içi trafik trendleri, kurallar

24 Kasım'da, gün içi eğrilerin hiçbiri görülmeden yazıldı. Daha önce görülen tek şey, depremin olduğu dilimdeki kullanıcı sıçraması (saatlerin yerel saat olduğunu kontrol etmek için).

**Soru (hocanın isteği):** Veriden gün içi trafik trendleri çıkıyor mu? Sabah işe ve okula gidiş, gündüz, akşam zirvesi. Önce sahaların sık olduğu şehir bölgeleri.

## Veri

- Turkcell'in verdiği 10 günlük KPI. Her gün 96 dilim, 15 dakika. Saatler Türkiye saati. Etiket dilimin başlangıcı: "22:45" = 22:45–23:00.
- Başka gün yok. Günleri Turkcell iki depremin etrafından seçmiş: 1 hafta önce, 1 gün önce, deprem günü, 1 gün sonra, 1 hafta sonra.
- **Trend için simülasyon gerekmiyor, bu yüzden modeldeki 24 sahayla sınırlı kalmıyoruz: bütün ilçe kullanılıyor.** Hücrenin ilçesi, Experia'da o hücrenin en çok ölçüldüğü ilçe. KPI'daki 6.129 hücrenin 5.538'inin ilçesi bu yolla bulunuyor, kalan 591 hücre dışarıda.
- Ham KPI dosyalarından yalnız seçilen ilçelerin hücreleri süzülür. Süzme yalnız yerelde kalır, GitHub'a gitmez.
- İlçe adları koordinattan tahmin (deney 35), resmî eşleşme değil.
- Seçim 20 Ekim pazartesi günündeki hücre ve kullanıcı sayılarına göre yapıldı (`ilce_secimi.md`). Bu sayılar gün içi eğriyi göstermiyor.

| Grup | İlçeler | KPI hücresi | Günlük ortalama bağlı kullanıcı | Neden |
|---|---|---|---|---|
| **Şehir** | Balıkesir merkez (0001 + 0014) | 1.152 | ~17.700 | İl merkezi, üniversite, iş yerleri. İşe ve okula gidiş için en uygun. |
| **Şehir** | Bandırma (0004) | 400 | ~6.800 | Liman, sanayi, üniversite. Hücre başına en kalabalık ilçe (17,3). İkinci şehir örneği. |
| **Sahil / turizm** | Edremit (0008) | 1.056 | ~9.700 | En sık ağ. Yazın turist etkisi. |
| **Sahil / turizm** | Ayvalık (0002) | 733 | ~5.400 | Edremit'i doğrulamak için ikinci sahil örneği. |
| **Kırsal** | Sındırgı (0019) | 96 | ~1.200 | Kendi bölgemiz. |
| **Kırsal, birlikte** | En yakın saha ortalaması 3 km'den uzak 10 ilçe (0003, 0005, 0007, 0011, 0012, 0013, 0015, 0018, 0019, 0020) | 1.131 | ~14.700 | Sındırgı tek başına az. Kırsal trendi daha sağlam görmek için. |

- Bölge sırası: önce şehir, sonra sahil, kırsal karşılaştırma için.

## Gün grupları

| Grup | Günler | Not |
|---|---|---|
| G1. Hafta içi, okul açık | 20 Eki, 3 Kas, 27 Eki 00:00–22:30 | Üçü de pazartesi. "Hafta içi" aslında pazartesi demek. |
| G2. Hafta sonu, okul açık | 26 Eki (pazar) | Tek gün. |
| G3. Hafta sonu, yaz | 3 Ağu (pazar), 9 Ağu (cumartesi), 10 Ağu 00:00–19:30 (pazar), 17 Ağu (pazar, aşağıdaki şarta bağlı) | Okullar kapalı. |
| G4. Deprem sonrası | 10 Ağu 19:45 sonrası, 11 Ağu, 27 Eki 22:45 sonrası, 28 Eki | Normal trende karışmaz, yalnız karşılaştırma. 28 Eki öğleden sonra bayram arifesi yarım gün tatili. |

- **Yaz hafta içi yok:** Ağustos'taki tek pazartesi deprem sonrası. Yaz ile okul dönemi yalnız hafta sonunda karşılaştırılır (G3 ile G2).
- **17 Ağustos şartı:** Depremden 1 hafta sonra. Saatlik biçimi (aşağıda) 3 ve 9 Ağustos ortalamasından hiçbir saatte 0,2'den fazla ayrılmıyorsa G3'e girer, ayrılıyorsa dışarıda kalır ve ayrıca gösterilir.
- **Üç pazartesi şartı:** G1'in üç gününün saatlik biçimi bir saatte birbirinden 0,2'den fazla ayrılıyorsa bu açıkça yazılır ve ortalama "tipik pazartesi" diye sunulmaz.

## Saat dilimleri

| Dilim | Saat |
|---|---|
| Gece | 03:00–05:00 |
| Sabah gidiş | 07:00–09:00 |
| Mesai / okul | 09:00–16:00 |
| Akşam dönüş | 16:00–19:00 |
| Akşam | 19:00–23:00 |

Zirve saatleri bu tablodan değil veriden bulunur.

## Hesap

**Temizlik:** Bir hücrenin erişilebilirliği %99'un altında olan dilimler o hücre için atılır (kesinti, trafik düşüşü gibi görünmesin).

**Ölçüler**, her bölge ve gün grubu için, her 15 dakikalık dilimde:
1. Hücre başına ortalama bağlı kullanıcı (ana ölçü).
2. Ortalama indirme kapasite kullanımı (DL PRB).
3. Hücre başına indirilen veri miktarı.

**Biçim:** Saatlik değer, o günün ortalamasına bölünür. Böylece bölgeler ve günler büyüklükten bağımsız karşılaştırılır. 0,2 sınırı bu biçim üzerinden.

**Raporlanacaklar:**
- Zirve saati: kullanıcı sayısının 1 saatlik kayan ortalamasının en yüksek olduğu saat. Kapasite kullanımı için de ayrı.
- Her dilimin ortalamasının gece ortalamasına oranı.
- Sabah gidişte artış: 07:00 ile 09:00 arasındaki artış, gün ortalamasının yüzdesi olarak.
- **Gündüz hücreleri / akşam hücreleri (G1):** Her hücre için mesai ortalaması ÷ akşam ortalaması.
  - 1,2'den büyükse **gündüz hücresi** (iş, okul, çarşı).
  - 0,8'den küçükse **akşam hücresi** (konut).
  - Arası **karışık**.
  - Her bölgede payları ve haritası verilir. Bu, kişileri takip etmek değil. İnsanların gün içinde nereye kaydığını hücre toplamlarından dolaylı gösterir.
- G3 ile G2 farkı (yaz ile okul dönemi, hafta sonu). Edremit'te turist etkisi beklenir.
- G4, G1/G3 eğrisinin üstüne ayrı çizgi olarak.

## Simülasyon saatleri

Simülasyon yükü için hafta içi (G1) grubundan 3 saat:

| Saat | Nasıl bulunuyor |
|---|---|
| Sabah gidiş | 07:00–09:00 arasında bağlı kişi sayısının en yüksek olduğu dilim |
| En kalabalık saat | bağlı kişi sayısının en yüksek olduğu 1 saat |
| Kapasite zirvesi | kapasite kullanımının (DL PRB) en yüksek olduğu 1 saat |

Her saat için hücre başına yük, üç pazartesinin o saatteki KPI ortalaması.

## Sınırlar (baştan biliniyor)

- Her grupta 1–3 gün var. Büyük örüntüyü (zirve saati, sabah artışı) görmek için yeterli; "tipik gün"ü kesin söylemek için az.
- Hafta içi yalnız pazartesi.
- Okul saatleri genel Türkiye düzenine göre tahmin. Bölgedeki gerçek okul saatleri bilinmiyor.
- KPI bağlı kullanıcıyı sayıyor. Boşta ama bağlı telefonlar da sayılıyor, yani bu "konuşan kişi" değil.
