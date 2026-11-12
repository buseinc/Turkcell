from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
note=('> **12 Kasım güncel envanter kontrolü:** 553/554/555 güncel ana dosyada bulundu; '
      'seçimin 96/96 hücre bağlantısı uyuşuyor. Envanter 563 saha / 6.475 hücre, '
      'Experia eşleşmesi 5.867/5.867. Yeni komşular nedeniyle genişletilmiş saha listesi '
      'yeniden kontrol edilmeli; yeni topolojide henüz simülasyon yapılmadı. '
      '[Kontrol raporu](../toplantilar/2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/KOORDINAT_GUNCELLEME_SONUCU.md) — '
      '[Hocaya güncel mesaj](../toplantilar/2026-11-12_koordinat_dogrulama_ve_hoca_mesaji/HOCAYA_MESAJ.md). '
      'Aşağıdaki eksik koordinat ifadeleri ve 516 saha sayısı tarihsel sürüme aittir; '
      'eski analiz tabloları ve haritalar yeniden üretilmedi.')
paths=[ROOT/'ana_proje'/name for name in
       ['00_BURADAN_BASLAYIN.md','01_VERI_VE_PROJE_OZETI.md','02_SINDIRGI_SAHA_SECIMI.md','06_EKSIK_KOORDINAT_ARASTIRMASI.md']]
paths += [ROOT/'toplantilar/2026-11-11_durum_ve_plan/PROJE_DURUMU_VE_PLAN.md',ROOT/'toplantilar/2026-11-10_toplanti_sunumu/HOCAYA_KISA_OZET.md']
for p in paths:
    t=p.read_text(encoding='utf-8-sig')
    if note not in t:
        head,rest=t.split('\n',1);p.write_text(head+'\n\n'+note+'\n'+rest,encoding='utf-8')
    print(p.name)
