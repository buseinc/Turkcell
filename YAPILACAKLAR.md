# Yapılacaklar listesi (22 Kasım 2026)

✅ yapıldı · ⏳ şu an yapılıyor · ⬜ yapılmadı · ⏸️ bekletiliyor (şimdilik gerek yok)

Liste, hocanın istediği işlere göre gruplandı.

## 1. Gerçek ölçümlere dayanan bir LTE ağı kurmak (taslağın ana amacı)

- ✅ Sındırgı'da 24 sahalık ağ, ns-3'te kuruldu.
- ✅ Bütün değerler gerçek kaynaklardan alındı (3GPP, CellMapper, Turkcell ölçümleri).
- ✅ Model gerçek ölçümlere uyuyor: test sahalarında sinyal kalitesi 2,6 dB, sinyal gücü 4,8 dB farkla (deney 26).
- ✅ Hiç bakılmamış komşu sahalarda da tutuyor (deney 27).
- ✅ Hocanın istediği CellMapper kontrolü yapıldı (440, 206, 224).
- ✅ Çok frekanslı senaryo (S2) denendi. Tek frekanslı model tercih edildi (deney 14).
- ✅ Hızlı model yazıldı ve ns-3 ile aynı sonucu verdiği gösterildi (deney 31). Ana sonuçlar yine ns-3'ten geliyor; hızlı model yalnız ön eleme için.

## 2. Stres testi: deprem anında ağ ne olur?

- ✅ Bir hücrenin kaç görüşme kaldırdığı ölçüldü: en az 250–300 (deney 28, 29, 31).
- ✅ Deprem anındaki yük, KPI'dan ölçüldü: kullanıcı 1,6–1,85 kat artıyor, ağ kaynağı artmıyor (deney 32).
- ✅ **Sonuç:** Deprem yükü ağı tıkamıyor; ağ deprem anının ~3 katını kaldırıyor.

## 3. Saha kesintisi

- ✅ Depremde gerçekten çöken sahalar KPI'dan bulundu: 130 ve 482 (deney 30).
- ✅ ns-3'te bu sahalar kapatıldı. Hiçbir hücre dolmuyor, ama kapanan sahanın çevresindeki kullanıcıların %15–18'i servis alamıyor (deney 33).
- ✅ **Sonuç:** Sorun kapasite değil, kapsama.

## 4. Handover ve hareket (hocanın 16 ve 19 Kasım istekleri)

- ✅ Handover kuruldu ve iki saha arasında test edildi (deney 19).
- ✅ Araziye uygun hareket kuruldu: araçlar OpenStreetMap'teki gerçek yollarda gidiyor (deney 34).
- ✅ 130 çökünce il yolunun 6,6 km'si servissiz kalıyor; 482 çökünce D240 etkilenmiyor (deney 34).
- ⬜ Yükseklik (dağ, tepe) yok; model düz arazi varsayıyor. Büyük iş.

## 5. Başka bölgeler (hoca: "sahil bölgesi yoğun olabilir", "anayol üzerinde mobility")

- ✅ Elimizdeki verinin hangi ilçeleri kapsadığına bakıldı: ilin 20 ilçesi var (deney 35).
- ✅ Edremit kıyısı seçildi; veri çıkarıldı, kıyı çizgisi eklendi.
- ✅ Model kuruldu. Sinyal gücü tuttu, sinyal kalitesi ilk hâlde 3 dB fazla iyi çıktı.
- ✅ Balıkesir merkez denendi. Sinyal kalitesi 5 dB fazla iyi, sinyal gücü de fazla güçlü (bina içi kullanıcılar).
- ✅ Sebep arandı:
  - Çok frekans: tek başına sonucu değiştirmedi.
  - Komşuların hep yayında olan sinyalleri: tam sayılınca model ters yöne, fazla kötüye kaydı.
  - Tek bir katsayı (%3) eğitim sahalarında ayarlandı. Bakılmamış test sahalarında ve Sındırgı'da tuttu.
- ✅ **Katsayı ns-3'e eklendi** (deney 36).
  - ✅ Kapalıyken ns-3 eskisiyle birebir aynı.
  - ✅ Açıkken ns-3 ile hızlı model aynı sonucu veriyor (saha başına fark 0,14 dB).
- ✅ Katsayı Sındırgı'nın kesinti sonucunu değiştirmiyor; deney 33 geçerli (deney 36).
- ✅ Edremit'te kesinti (ns-3, deney 37). **Sonuç:** sık kıyı bölgesinde saha çökünce kapanan sahanın çevresinde servissiz kalan %0–5. Sındırgı'da bu oran %15–18'di. Komşular boşluğu dolduruyor. Hiçbir hücre dolmuyor.
- ⬜ Edremit'te yol koşusu (kıyı yolu). İsteğe bağlı; kesinti zaten az etki gösterdiği için önceliği düşük.
- ⏸️ Balıkesir merkez. Sinyal gücü kabulü geçmiyor; bina içi kayıp gerekir. Şimdilik bekletiliyor.

## 6. İHA ile hizmeti geri getirmek (taslakta "sonraki aşama")

- ✅ İlk somut hedef belli: 130 çökünce il yolundaki ~3 km'lik kopukluk ve kapanan sahanın çevresi.
- ⬜ İHA modeli henüz kurulmadı: 3GPP hava-yer kanal modeli, İHA'nın konumu ve yüksekliği.
- ⬜ Hızlı modelle İHA konum taraması, ardından ns-3'te doğrulama.
- ⬜ Öncelik ve rota planlaması (taslakta "RL ile, daha sonra").

## 7. Raporlama

- ✅ Durum özeti senin için yazıldı (`DURUM_OZETI.md`).
- ⬜ Taslak (`main.tex`) güncellenmedi. Eskimiş cümleler var: "stres testine başlamadık", "deprem yükü 2 kat".
- ⬜ Hocaya kompakt not yazılmadı.
- ⬜ Deney 35 ve 36 commit edilmedi.

## Açık kalan ama ana hedefi etkilemeyenler

- ⏸️ Normal günde simülasyonda %15–20 "konuşamıyor" çıkıyor; sebebi bilinmiyor. Kesinti ve yol sonuçlarını etkilemiyor, çünkü onlar sinyal ölçütleriyle değerlendirildi.
- ⏸️ Hücre geçişi gerçekte olduğundan sık çıkıyor (ns-3'ün varsayılan ayarları).
- ⏸️ %3'lük katsayının fiziksel açıklaması kapatılamıyor; verimizde yok.
- ⏸️ ns-3'ü hızlı ayarla (optimized) derlemek. Ancak çok uzun koşular gerekirse yapılır.

---

## Önerdiğim sıra

1. ✅ Deney 36 bitti: katsayı ns-3'te doğru çalışıyor.
2. ✅ Sındırgı kesinti sonucu katsayıyla değişmiyor.
3. ✅ Edremit'te kesinti: sık bölgede saha çökmesi az etkili (%0–5), seyrek Sındırgı'da çok etkili (%15–18).
4. **Taslağı güncellemek ve hoca notu.** 1–3 bitince. Notu sen gönderirsin.
5. **İHA aşaması.** Projenin bir sonraki büyük adımı; hedefi hazır.

**Şimdilik yapmamayı önerdiklerim:** Balıkesir merkez, yükseklik verisi, %15–20 konuşamama sorunu, hücre geçişi ayarları. Hocanın ana sorularına cevap vermiyorlar ya da çok büyük işler.
