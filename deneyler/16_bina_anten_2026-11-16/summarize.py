"""Evaluate the preselected candidate without changing selection or thresholds."""
from pathlib import Path
import json
import statistics

HERE = Path(__file__).resolve().parent


def main():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    native = json.loads((HERE/'result.json').read_text(encoding='utf-8'))
    assert native['completed']
    old = json.loads((HERE.parent/'15_ta_yerlesim_2026-11-16/result.json').read_text(encoding='utf-8'))['results']
    s0 = json.loads((HERE.parent/'14_temel_s0_ve_cok_tasiyici_s2_2026-11-15/result.json').read_text(encoding='utf-8'))['results']
    s0 = [r for r in s0 if r['case']['scenario']=='S0']
    def avg(rows,split,metric):
        return statistics.mean(r[split]['mae_db'][metric] for r in rows)
    summaries = {}
    for label in sorted({r['case']['label'] for r in native['results']}):
        rows = [r for r in native['results'] if r['case']['label']==label]
        assert len(rows)==3
        checks = {
            'all_sites_present':all(not r['missing_sites'] for r in rows),
            'holdout_rsrp_improves_TA':avg(old,'control','rsrp')-avg(rows,'control','rsrp')>=0.5,
            'holdout_rsrp_close_to_S0':avg(rows,'control','rsrp')<=avg(s0,'control','rsrp')+0.5,
            'holdout_sinr_not_degraded':avg(rows,'control','sinr')<=avg(old,'control','sinr')+1,
            'all_ues_connected':all(r['measurement_connected']==256 for r in rows),
            'all_ues_with_dl':all(r['measurement_with_dl']==256 for r in rows),
            'prb_stable':all(abs(r['prb_mean_achieved']-next(o['prb_mean_achieved'] for o in old if o['case']['ue_seed']==r['case']['ue_seed']))<=0.03 for r in rows)}
        summaries[label] = {'mae_db':{split:{m:avg(rows,split,m) for m in ['rsrp','sinr']} for split in ['training','control']},
                            'checks':checks,'accepted':all(checks.values()),
                            'prb_mean':statistics.mean(r['prb_mean_achieved'] for r in rows)}
    comparison = {'summaries':summaries,'selected_label':'combined',
                  'selected_accepted':summaries['combined']['accepted'],
                  'decision':'S0 remains the reference; passing all checks supports further study, not automatic replacement.'}
    (HERE/'comparison.json').write_text(json.dumps(comparison,indent=2,ensure_ascii=False),encoding='utf-8')
    lines = ['## ns-3 sonuçları','',
             '**9/9 koşu tamamlandı.** Ayarlama hızlı RSRP hesabıyla 5 sahada yapıldı; seçilen aday değiştirilmeden 3 ayrı örnekte sınandı.',
             '', '| Senaryo | Ayarda RSRP farkı | Kontrolde RSRP farkı | Kontrolde SINR farkı | Tüm ölçütler |',
             '|---|---:|---:|---:|---|']
    for label,rows in [('Eski temel S0 (2–6 km)',s0),('TA yerleşimi, ek etki yok',old)]:
        lines.append(f"| {label} | {avg(rows,'training','rsrp'):.2f} | {avg(rows,'control','rsrp'):.2f} | {avg(rows,'control','sinr'):.2f} | Karşılaştırma |")
    labels = {'combined':'6 dB + dikey desen, 0°','indoor_only':'Yalnız 6 dB','vertical_only':'Yalnız dikey desen, 0°'}
    for label,r in summaries.items():
        lines.append(f"| {labels[label]} | {r['mae_db']['training']['rsrp']:.2f} | {r['mae_db']['control']['rsrp']:.2f} | {r['mae_db']['control']['sinr']:.2f} | {'Geçti' if r['accepted'] else 'Geçmedi'} |")
    lines += ['', 'Bütün farklar dB. Ayrıntılı kabul kontrolleri comparison.json içinde.', '',
              '**Karar: Seçilen yeni aday kabul edilmedi; temel S0 korunuyor.** 6 dB kayıp ve dikey desen birlikte ayar sahalarını iyileştirirken diğer üç sahada RSRP farkını 3,28 → 5,01 dB artırdı. Etkileri ayrı uygulamak da önceden belirlenen kabul ölçütlerini karşılamadı. Sonuç görüldükten sonra yeniden ayar yapılmadı.', '',
              'Bütün yeni koşularda 256 ölçüm kullanıcısı da şebekeye bağlandı. 4 saniyelik koşuda veri alan kullanıcı sayısı, 6 dB kayıp içeren iki senaryoda 242–246; yalnız dikey desende 255–256 oldu. Ek etkisiz eski TA koşularında da 255–256 idi. Bu kısa koşudaki veri alamama, tek başına kalıcı kapsama kesintisi kanıtı değildir. PRB yükü bütün senaryolarda belirlenen sınır içinde kaldı.', '',
              'Öğrendiğimiz: Her kullanıcıya aynı kaybı eklemek genel çözüm olmadı. Bu sonuç gerçek ağda bina kaybı veya anten eğimi olmadığı anlamına gelmez. Kullanıcı yönleri, saatlik ortalama TA ve komşu sahalara bağlanma sınırlamaları devam ediyor.', '',
              'Bu deney gerçek bina kaybını veya anten eğimini belirlemez; varsayımların ölçümleri açıklama gücünü sınar. Temel S0 senaryosu korunur.']
    report = HERE/'SONUCLAR.md'
    prefix = report.read_text(encoding='utf-8').split('## ns-3 aşaması')[0].split('## ns-3 sonuçları')[0]
    if '<!-- RUN_PROGRESS -->' in prefix:
        start = prefix.index('<!-- RUN_PROGRESS -->')
        end = prefix.index('<!-- END_RUN_PROGRESS -->')+len('<!-- END_RUN_PROGRESS -->')
        prefix = prefix[:start]+prefix[end:]
    prefix = '\n'.join('**Durum: 9/9 yeni koşu ve önceki sonuçla doğrulama tamamlandı. Seçilen aday kabul edilmedi; S0 temel kalıyor.**'
                       if line.startswith('**Durum:') else line for line in prefix.splitlines())
    while '\n\n\n' in prefix: prefix = prefix.replace('\n\n\n','\n\n')
    report.write_text(prefix+'\n'+'\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(comparison,indent=2))


if __name__=='__main__':
    main()
