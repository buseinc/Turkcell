from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
note=('> **12 Kasım güncel sonuç:** Hocanın 8 ana + 8 komşu sahası güncel envanterle doğrulandı ve korundu. '
      'Yeni yakın sahalarla yedi simülasyon koşusu tamamlandı; komşu genişletmeleri ve üç kullanıcı örneğinin eski–yeni kontrolleri geçti. '
      'Güncel 24 sahada kontrol MAE: RSRP 2,96 / SINR 3,63 / RSRQ 4,07 dB. '
      '[Sonuçlar ve grafik](../experiments/inventory_refresh_2026-11-12/SONUCLAR.md) — '
      '[Hocaya güncel mesaj](../review_2026-11-12/HOCAYA_MESAJ.md). '
      'Aşağıdaki 516 saha/eksik koordinat ifadeleri ve eski tablolar tarihsel sürümdür; güncel envanter 563 saha / 6.475 hücredir.')
paths=[ROOT/'turkcell_tam_paket_2026-11-10'/n for n in ['00_BURADAN_BASLAYIN.md','01_VERI_VE_PROJE_OZETI.md','02_SINDIRGI_SAHA_SECIMI.md','06_EKSIK_KOORDINAT_ARASTIRMASI.md']]
paths += [ROOT/'toplanti_2026-11-11/PROJE_DURUMU_VE_PLAN.md',ROOT/'toplanti_2026-11-10/HOCAYA_KISA_OZET.md']
for p in paths:
    s=p.read_text(encoding='utf-8-sig');parts=s.split('\n\n')
    parts=[x for x in parts if not x.startswith('> **12 Kasım güncel envanter kontrolü:') and not x.startswith('> **12 Kasım güncel sonuç:')]
    parts.insert(1,note);p.write_text('\n\n'.join(parts),encoding='utf-8')
print('Updated',len(paths),'status pointers')
