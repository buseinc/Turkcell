from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
note=('> **12 Kasım güncel envanter kontrolü:** 553/554/555 güncel ana dosyada bulundu; '
      'seçimin 96/96 hücre bağlantısı uyuşuyor. Envanter 563 saha / 6.475 hücre, '
      'Experia eşleşmesi 5.867/5.867. Yeni komşular nedeniyle genişletilmiş saha listesi '
      'yeniden kontrol edilmeli; yeni topolojide henüz simülasyon yapılmadı. '
      '[Kontrol raporu](../review_2026-11-12/KOORDINAT_GUNCELLEME_SONUCU.md) — '
      '[Hocaya güncel mesaj](../review_2026-11-12/HOCAYA_MESAJ.md). '
      'Aşağıdaki eksik koordinat ifadeleri ve 516 saha sayısı tarihsel sürüme aittir; '
      'eski analiz tabloları ve haritalar yeniden üretilmedi.')
paths=[ROOT/'turkcell_tam_paket_2026-11-10'/name for name in
       ['00_BURADAN_BASLAYIN.md','01_VERI_VE_PROJE_OZETI.md','02_SINDIRGI_SAHA_SECIMI.md','06_EKSIK_KOORDINAT_ARASTIRMASI.md']]
paths += [ROOT/'toplanti_2026-11-11/PROJE_DURUMU_VE_PLAN.md',ROOT/'toplanti_2026-11-10/HOCAYA_KISA_OZET.md']
for p in paths:
    t=p.read_text(encoding='utf-8-sig')
    if note not in t:
        head,rest=t.split('\n',1);p.write_text(head+'\n\n'+note+'\n'+rest,encoding='utf-8')
    print(p.name)
