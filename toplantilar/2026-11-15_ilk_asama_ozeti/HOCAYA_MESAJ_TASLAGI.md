Hocam merhaba,

Sındırgı başlangıç senaryosunda notlarınızdaki ilk aşamayı tamamladık; özetini paylaşmak istedik.

**Yaptıklarımız**
- Seçtiğiniz 8 ana ve 8 komşu sahayı güncel envanterle doğruladık; ns-3.44 LTE/EPC üzerinde 24 sahalık ağ çalışıyor.
- Bölge geneli kapsama haritalarını çıkardık (RSRP, hizmet alanları, SINR sınırları).
- Experia ile karşılaştırmada kontrol sahalarında hata RSRP için 1,7 dB, SINR için 2,2 dB. Sahaların güçlü/zayıf sıralamasını simülasyon iyi yakalıyor (Spearman 0,79–0,95).
- KPI'dan yük profili çıkardık ve simülasyona gerçekçi yük verdik. İlk senaryo ağı gerçeğe göre 7–10 kat boş çalıştırıyordu.
- Sektör/taşıyıcı kombinasyonlarını denedik. KPI'daki frekanslar arası handover kayıtlarına göre ana sahaların beşi çok frekanslı görünüyor.

**Dikkat çeken bulgular**
- İki Sındırgı depremi KPI'da açıkça görülüyor: Aynı anda bağlı kullanıcı ilk yarım saatte yaklaşık iki katına çıkıyor, veri hacmi ise düşüyor. Stres testini buna göre kurmayı öneriyoruz.
- Tek frekans varsayımı girişimi biraz abartıyor. Çok taşıyıcılı senaryo bazı göstergeleri iyileştirdi ama bant ve güç bilgisi olmadan kesinleşmiyor.

**Sorularımız**
1. Hücrelerin bant/EARFCN bilgisi ve taşıyıcı gücü, en azından hangi hücrelerin aynı sektörde olduğu paylaşılabilir mi?
2. Experia SINR/RSRQ hangi kanal ve ortalamayla hesaplanıyor? KPI'daki CQI, throughput ve TAAVG'nin birimleri nedir?
3. Bu başlangıç senaryosu, sınırlarıyla birlikte, stres testi aşamasına geçmek için yeterli mi?

Ayrıntılı özet ve haritaları ekte paylaşıyoruz. Uygun olduğunuzda görüşmek isteriz.
