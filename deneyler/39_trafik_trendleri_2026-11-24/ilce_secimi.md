# İlçe seçimi (24 Kasım)

Kod: `ilce_secimi.py`. Veri: 20 Ekim 2025 (pazartesi) KPI, yalnız sayılar. Hücrenin ilçesi Experia'da en çok ölçüldüğü ilçe. İlçe adları tahmin (deney 35).

| İlçe | Tahmini ad | KPI hücresi | KPI sahası | Hücre başına bağlı kullanıcı | Günlük ort. toplam | En yakın saha (km) |
|---|---|---|---|---|---|---|
| 0001 | Balıkesir merkez (Altıeylül) | 652 | 68 | 15,2 | 9.923 | 1,63 |
| 0008 | Edremit | 1.056 | 82 | 9,2 | 9.657 | 0,81 |
| 0014 | Balıkesir merkez (Karesi) | 500 | 46 | 15,5 | 7.746 | 1,68 |
| 0004 | Bandırma | 400 | 39 | 17,3 | 6.832 | 1,92 |
| 0002 | Ayvalık | 733 | 59 | 7,4 | 5.412 | 0,99 |
| 0006 | Burhaniye | 362 | 29 | 10,1 | 3.659 | 1,79 |
| 0011 | — | 222 | 22 | 14,5 | 3.215 | 3,27 |
| 0005 | — | 132 | 16 | 17,4 | 2.296 | 3,93 |
| 0009 | Erdek | 303 | 26 | 6,5 | 1.956 | 2,14 |
| 0020 | — | 142 | 16 | 13,2 | 1.876 | 3,51 |
| 0013 | — | 106 | 18 | 13,2 | 1.400 | 3,67 |
| 0017 | — | 193 | 18 | 7,1 | 1.358 | 1,51 |
| 0007 | — | 117 | 17 | 11,5 | 1.346 | 5,84 |
| 0019 | Sındırgı | 96 | 19 | 12,7 | 1.214 | 5,22 |
| 0010 | Gömeç | 151 | 10 | 7,5 | 1.138 | 1,56 |
| 0012 | — | 94 | 12 | 11,8 | 1.108 | 3,36 |
| 0015 | — | 81 | 11 | 12,3 | 984 | 5,08 |
| 0018 | — | 75 | 9 | 8,7 | 649 | 3,30 |
| 0016 | — | 57 | 6 | 11,6 | 617 | 4,37 |
| 0003 | — | 66 | 8 | 9,2 | 608 | 9,52 |

KPI'daki 6.129 hücreden 5.538'inin ilçesi bulundu.

**Ek bulgu (kesinti adımı için):** KPI'da `DownTime_Auto_PC_ERI` (otomatik, arıza) ve `DownTime_Man_PC_ERI` (elle, planlı kapatma) sütunları var. 130 ve 482'nin kapanmasının arıza mı planlı mı olduğu buradan ayrılabilir.
