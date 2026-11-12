"""Publish the native choice, every tradeoff, and untuned follow-up checks."""
from pathlib import Path
import hashlib
import json
import os
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PROJECT=ROOT/'ana_proje'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'deneyler/04_ortak_radyo_taramasi_2026-11-10/matplotlib_cache'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FAMILY={'wide':'1–4 km kümeler','near':'0,5–2 km kümeler','far':'2–6 km kümeler',
        'uniform':'bölge içinde uniform','mixed':'yakın/uzak karışık kümeler'}


def main():
    study=json.loads((HERE/'study_result.json').read_text())
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    assert study['completed'] and study['regression']['passed']
    assert hashlib.sha256((PROJECT/'simulation/sindirgi_baseline.cc').read_bytes()).hexdigest()==plan['original_cpp_sha256']
    for name,expected in plan['input_hashes'].items():
        assert hashlib.sha256((HERE/'inputs'/name).read_bytes()).hexdigest()==expected,name
    targets=pd.read_csv(HERE/'inputs/targets.csv').set_index('site')
    summaries=[];site_frames=[];ue_frames=[]
    for item in study['cases']+study['followups']:
        case=item['case'];name=case['name']
        sites=targets.join(pd.DataFrame.from_dict(item['metrics']['sites'],orient='index'))
        sites['case']=name
        for m in ['rsrp','sinr','rsrq']:sites[m+'_error_db']=sites[m]-sites[m+'_target']
        site_frames.append(sites.reset_index())
        ues=pd.DataFrame(item['metrics']['ues']);ues['case']=name;ue_frames.append(ues)
        samples=pd.read_csv(HERE/'simulation/results'/name/'sinr_components.csv')
        final=pd.read_csv(HERE/'simulation/results'/name/'ues.csv').set_index('ue_id').synthetic_cell_id
        samples=samples[samples.time_s.ge(1)&samples.synthetic_cell_id.eq(samples.ue_id.map(final))]
        error=float((samples.native_sinr_db-samples.reconstructed_mixed_sinr_db).abs().max())
        assert error<1e-6,(name,error)
        row={**case,'is_followup':item in study['followups'],
             'training_score':item['training']['score'],'train_valid':item['training']['valid_sites'],
             'control_valid':item['control']['valid_sites'],
             'connected':item['result']['connected_ues'],'receiving_dl':item['result']['ues_receiving_dl'],
             'native_mixed_reconstruction_error_db':error,
             'fresh_data_sample_pct':float(100*samples.data_interference_fresh.mean())}
        for split,key in [('train','training'),('control','control')]:
            for metric,value in item[key]['mae_db'].items():row[split+'_'+metric+'_mae_db']=value
        summaries.append(row)
    summary=pd.DataFrame(summaries)
    native=summary[~summary.is_followup].sort_values(['training_score','name'])
    winner=native.iloc[0]
    assert winner['name']==study['selected_name']
    baseline=summary[summary.name.eq('baseline')].iloc[0]
    seed=summary[summary.name.eq('check_new_ue_seed')].iloc[0]
    # RSRQ is descriptive here; the predeclared buffer pass criterion used RSRP/SINR.
    by_name={item['case']['name']:item for item in study['cases']+study['followups']}
    for check,left_name,right_name in zip(study['buffer_checks'],
            [study['selected_name'],'check_buffer_32'],['check_buffer_32','check_buffer_48']):
        left={r['ue_id']:r for r in by_name[left_name]['metrics']['ues']}
        right={r['ue_id']:r for r in by_name[right_name]['metrics']['ues']}
        diffs=[abs(left[u]['rsrq']-right[u]['rsrq']) for u in left
               if left[u]['rsrq'] is not None and right[u]['rsrq'] is not None]
        check['descriptive_rsrq_q95_absolute_change_db']=float(np.quantile(diffs,.95))
    summary.to_csv(HERE/'summary.csv',index=False)
    sites=pd.concat(site_frames,ignore_index=True);sites.to_csv(HERE/'site_comparison.csv',index=False)
    selected_site_rows=sites[sites.case.eq(winner['name'])]
    max_errors={m:float(selected_site_rows[m+'_error_db'].abs().max()) for m in ['rsrp','sinr','rsrq']}
    pd.concat(ue_frames,ignore_index=True).to_csv(HERE/'ue_comparison.csv',index=False)
    selected=next(c for c in study['cases'] if c['case']['name']==winner['name'])
    frozen=HERE/'selected_scenario';frozen.mkdir(exist_ok=True)
    shutil.copy2(HERE/'inputs'/selected['case']['sites_file'],frozen/'sites.csv')
    shutil.copy2(HERE/'inputs'/selected['case']['ue_file'],frozen/'ues.csv')
    config={'status':'Exploratory training-selected candidate; not operator reconstruction',
        'case':selected['case'],'training':selected['training'],'control':selected['control'],
        'model_assumptions':selected['result']['model_assumptions'],
        'source_cpp_sha256':plan['source_cpp_sha256'],
        'maximum_absolute_site_errors_db':max_errors,
        'files':{name:hashlib.sha256((frozen/name).read_bytes()).hexdigest() for name in ['sites.csv','ues.csv']},
        'buffer_checks':study['buffer_checks'],'buffer_two_steps_passed':study['buffer_two_steps_passed'],
        'independent_ue_seed_result':{'training_score':float(seed.training_score),
            'training':{m:float(seed['train_'+m+'_mae_db']) for m in ['rsrp','sinr','rsrq']},
            'control':{m:float(seed['control_'+m+'_mae_db']) for m in ['rsrp','sinr','rsrq']}},
        'original_baseline_unchanged':True}
    (frozen/'configuration.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    checks={'computations_passed':True,'original_site_and_target_inputs_preserved':True,
        'original_cpp_unchanged':True,'proxy_checks':plan['proxy_checks'],'native_regression':study['regression'],
        'native_search_cases':len(study['cases']),'native_followup_cases':len(study['followups']),
        'maximum_native_reconstruction_error_db':float(summary.native_mixed_reconstruction_error_db.max()),
        'buffer_two_steps_passed':study['buffer_two_steps_passed']}
    (HERE/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,3,figsize=(16,5.2),constrained_layout=True)
    x=np.arange(len(targets))
    for ax,m,label in zip(axes,['rsrp','sinr','rsrq'],['RSRP (dBm)','SINR (dB)','RSRQ (dB)']):
        for index,split in enumerate(targets.split):
            if split=='holdout':ax.axvspan(index-.4,index+.4,color='#fff0df',zorder=0)
        ax.plot(x,targets[m+'_target'],'ko-',label='Experia')
        cases=[('baseline','Önceki en iyi aday','#0072b2')]
        if winner['name']!='baseline':cases.append((winner['name'],'Yeni seçilen aday','#d55e00'))
        cases.append(('check_new_ue_seed','Aynı ayar, yeni UE örneklemi','#009e73'))
        for name,legend,color in cases:
            frame=sites[sites.case.eq(name)].set_index('site').reindex(targets.index)
            ax.plot(x,frame[m],'o--',color=color,label=legend)
        ax.set_xticks(x,[s.replace('SITE_','') for s in targets.index],rotation=50)
        ax.set_ylabel(label);ax.grid(alpha=.2)
    axes[0].legend(fontsize=7)
    fig.suptitle('Kullanıcı dağılımı / yayılım / güç araştırması — seçim yalnız 5 eğitim sahasında\n'
        'Turuncu zemin: daha önce görülmüş kontrol sahaları; yeşil: yeniden ayarlanmamış yeni kullanıcı örneklemi',fontsize=11)
    fig.savefig(HERE/'selected_comparison.png',dpi=170);fig.savefig(HERE/'selected_comparison.svg')
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,7),constrained_layout=True)
    all_sites=pd.read_csv(HERE/'inputs/sites.csv')
    old_ues=pd.read_csv(HERE/'inputs/ues_wide.csv')
    new_ues=pd.read_csv(frozen/'ues.csv')
    ax.scatter(old_ues.x_m/1000,old_ues.y_m/1000,s=18,c='#0072b2',alpha=.6,label='Önceki varsayımsal kullanıcılar')
    ax.scatter(new_ues.x_m/1000,new_ues.y_m/1000,s=25,c='#d55e00',marker='x',label='Seçilen varsayımsal kullanıcılar')
    ax.scatter(all_sites.x_m/1000,all_sites.y_m/1000,s=45,c='black',marker='^',label='Sabit saha konumları')
    ax.set(xlabel='Doğu (km)',ylabel='Kuzey (km)',aspect='equal',title='Verideki saha konumları korunur; kullanıcı konumları varsayımsaldır')
    ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.savefig(HERE/'ue_placements.png',dpi=150);plt.close(fig)
    def triple(row,split):return ' / '.join(f"{row[split+'_'+m+'_mae_db']:.2f}" for m in ['rsrp','sinr','rsrq'])
    lines=['# Kullanıcı, yayılım ve güç araştırması — sonuçlar','',
        f"**Seçilen aday: {winner['name']}** — {FAMILY[winner['family']]}, {winner['beamwidth_deg']}° anten, "
        f"yayılım üssü {winner['exponent']}, sektör gücü {winner['power_dbm']} dBm. Mixed ve düşük UDP yükü kullanıldı.",'',
        f"Önceki adayın ortak eğitim puanı {baseline.training_score:.3f}, yeni adayın {winner.training_score:.3f}. "
        'Puanlar birbirine çok yakındır; eğitim sıralaması güçlü bir üstünlük kanıtı değildir. '
        'Kontrol ve yeni kullanıcı örneklemi sonuçları ayrı değerlendirilmelidir.','',
        f"135 analitik ön eleme hesabından sonra **{len(study['cases'])} gerçek ns-3 seçim koşusu** ve "
        f"**{len(study['followups'])} takip koşusu** tamamlandı. Analitik SINR S/N yaklaşımıdır; "
        'native sonuç veya gerçek ağ doğrulaması olarak sunulmaz.','',
        '## Veriden gelenler korundu','',
        'Saha koordinatları ve kimlikleri, hücre eşlemeleri ve Experia hedefleri değiştirilmedi. '
        'Değişenler bilinmeyen kullanıcı dağılımı, anten genişliği, log-distance üssü ve yayın gücü hipotezleridir. '
        'Üç ek saha konumunun kaynak belirsizliği devam ediyor.','',
        '## Gerçek ns-3 adayları','',
        '| Aday | Yerleşim | Anten / üs / dBm | Eğitim RSRP / SINR / RSRQ MAE | Puan | Kontrol RSRP / SINR / RSRQ MAE | Geçerli eğitim/kontrol |',
        '|---|---|---|---|---:|---|---|']
    for _,row in native.iterrows():
        lines.append(f"| {row['name']} | {FAMILY[row.family]} | {row.beamwidth_deg}° / {row.exponent} / {row.power_dbm} | "
            f"{triple(row,'train')} | {row.training_score:.3f} | {triple(row,'control')} | {row.train_valid}/5 — {row.control_valid}/3 |")
    lines+=['','Seçim kuralı: üç eğitim MAE ortalaması + eksik eğitim sahası cezası. '
        'Kontrol değerleri seçime katılmadı. Bu sahalar daha önce görüldüğü için kör doğrulama değildir. '
        'Tek bir metriğin iyileşip diğerinin kötüleşmesi tabloda açıkça gösterilir.','',
        f"Seçilen adayda sekiz saha arasındaki en büyük mutlak hatalar: RSRP {max_errors['rsrp']:.2f}, "
        f"SINR {max_errors['sinr']:.2f}, RSRQ {max_errors['rsrq']:.2f} dB. "
        'Ortalamaların yakınlığı her sahanın yakın olduğu anlamına gelmez; saha tablosu ve grafikler birlikte sunulmalıdır.','',
        '## Takip kontrolleri','',
        f"Yeni kullanıcı örnekleminde eğitim hataları **{triple(seed,'train')} dB**, kontrol hataları "
        f"**{triple(seed,'control')} dB**; geçerli saha sayısı {seed.train_valid}/5 ve {seed.control_valid}/3. "
        'Yeni örnekleme göre yeniden ayar yapılmadı.','',
        '| Komşu çevresini genişletme | %95 mutlak RSRP farkı | %95 mutlak SINR farkı | RSRQ farkı (tanısal) | Aynı hizmet sektörü | Eşikler |',
        '|---|---:|---:|---:|---:|---|']
    for check in study['buffer_checks']:
        lines.append(f"| {check['from_sites']} → {check['to_sites']} toplam saha | {check['rsrp_q95_abs_change_db']:.3f} dB | "
            f"{check['sinr_q95_abs_change_db']:.3f} dB | {check['descriptive_rsrq_q95_absolute_change_db']:.3f} dB | "
            f"%{100*check['same_serving_sector_fraction']:.1f} | "
            f"{'geçti' if check['passed'] else 'geçmedi'} |")
    lines+=['',f"İki ardışık genişletme: **{'geçti' if study['buffer_two_steps_passed'] else 'geçmedi'}**. "
        'Eşikler RSRP/SINR %95 farkı ≤1 dB ve aynı hizmet sektörü ≥%95. '
        'RSRQ farkı ayrıca tanısal olarak verilir, önceden yazılan geçme kuralına sonradan eklenmez. '
        'Mixed örnekleme ve zamanlayıcı etkileri de bu farklara dahildir.','',
        '## Nasıl sunulmalı?','',
        'Bu sonuç, denenmiş hipotezler içinde eğitimden seçilen bir adaydır. '
        'Gerçek anten/yayılım/yük ayarlarının bulunduğunu göstermez. Yeni UE örneklemindeki '
        'değişim, örneklem belirsizliğini görünür kılar. RSRQ farkının sürüp sürmediği ayrıca okunmalıdır. '
        'Eksik saha veya geçmeyen takip kontrolü varsa sonuçla birlikte sunulmalıdır.','',
        'Seçilen senaryo `selected_scenario/` altında ayrı saklandı. Özgün başlangıç senaryosu değişmedi.','',
        '[Kalan RSRQ farkı için ölçüm tanımı araştırması](RSRQ_TANIM_NOTU.md). '
        'Bu not bir sayısal düzeltme uygulamaz; standart ve model tanımlarını ayırır.','',
        '![Saha karşılaştırması](selected_comparison.png)','', '![Kullanıcı yerleşimleri](ue_placements.png)','',
        '## Dosyalar ve tekrar üretim','',
        '`proxy_screen.csv` yalnız analitik ön elemeyi; `summary.csv`, `site_comparison.csv`, '
        '`ue_comparison.csv` native koşuları; `checks.json` doğrulamaları içerir. '
        '`training_selection.json` kontrol ve takip sonuçları eklenmeden sabitlenen seçimdir.','',
        'Proje kökünde PowerShell:','', '```powershell',
        r'.\.venv\Scripts\python.exe deneyler/05_kullanici_yayilim_guc_2026-11-10/prepare.py',
        'wsl --distribution Ubuntu-22.04 --exec python3 deneyler/05_kullanici_yayilim_guc_2026-11-10/run_campaign.py',
        r'.\.venv\Scripts\python.exe deneyler/05_kullanici_yayilim_guc_2026-11-10/report.py','```']
    (HERE/'SONUCLAR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    brief=['# Hocaya kısa özet — 10 Kasım 2026','',
        'Amaç, verinin belirlediği coğrafyayı koruyup bilinmeyen radyo ve kullanıcı koşullarını '
        'açık varsayımlarla temsil eden, ölçümlere yakın bir LTE başlangıcı oluşturmaktır.','',
        '## Bugünkü en somut ilerleme','',
        '- Mevcut LTE/EPC senaryosu bu bilgisayarda çalışıyor; kaynak veri ve koordinatlar korunuyor.',
        '- Kontrol/mixed tanımı SINR karşılaştırmasını belirgin değiştirdi. İlk mixed koşuda '
        'kontrol sahalarının SINR hatası 9,97 → 1,56 dB oldu; RSRQ aynı kaldı.',
        f"- Son araştırmada 135 ucuz analitik ön eleme, {len(study['cases'])} gerçek aday koşusu ve "
        f"{len(study['followups'])} takip koşusu yapıldı. Seçim yalnız beş eğitim sahasıyla yapıldı.",'',
        f"**Seçilen aday:** {FAMILY[winner.family]}, anten {winner.beamwidth_deg}°, üs {winner.exponent}, "
        f"güç {winner.power_dbm} dBm; aynı 24 saha, 72 sektör, 64 sanal kullanıcı, mixed ve düşük sentetik yük.",'',
        f"Eğitim puanları {baseline.training_score:.3f} ve {winner.training_score:.3f}; fark çok küçük. "
        'Yeni adayın önceki adaya kesin üstünlüğü iddia edilmiyor.','',
        '| Kontrol sahalarında MAE | Önceki 120° aday | Yeni seçilen aday | Yeni kullanıcı örneklemi |',
        '|---|---:|---:|---:|']
    for m in ['rsrp','sinr','rsrq']:
        brief.append(f"| {m.upper()} | {baseline['control_'+m+'_mae_db']:.2f} dB | {winner['control_'+m+'_mae_db']:.2f} dB | {seed['control_'+m+'_mae_db']:.2f} dB |")
    brief+=['',f"Geçerli kontrol sahaları: yeni aday {winner.control_valid}/3; yeni kullanıcı örneklemi "
        f"{seed.control_valid}/3. İki komşu genişletme kontrolü: **{'geçti' if study['buffer_two_steps_passed'] else 'geçmedi'}**.",'',
        f"Bunlar ortalama hatalardır. Sekiz saha arasındaki en büyük mutlak hatalar RSRP/SINR/RSRQ için "
        f"{max_errors['rsrp']:.2f} / {max_errors['sinr']:.2f} / {max_errors['rsrq']:.2f} dB; "
        'bazı sahalarda belirgin fark devam ediyor.','',
        '## Toplantıda dürüstçe söylenecek','',
        '“Tam ağın kopyasını kurmuyoruz. Bilinen saha konumlarını koruyup eksik ayarlar için '
        'senaryolar deniyoruz. Ölçümlere yakın adayları üç metriğe birlikte bakarak seçiyoruz; '
        'tek örnekleme bağımlılığı ve komşu etkisini de kontrol ediyoruz.”','',
        'Üç kontrol sahası geçmişte görüldü; yeni bir kör doğrulama değildir. Yakınlık, gerçek '
        'konfigürasyonun bulunduğunu kanıtlamaz. Kısa/düşük yük pilotu gerçek kapasite doğrulaması değildir.','',
        '## Hocadan netleştirmek istediğimiz üç konu','',
        '1. 553/554/555 konumları ve hücre–saha bağlantılarının asıl kaynağı.',
        '2. Experia SINR/RSRQ kanal, örneklem ve ortalama tanımları; mixed karşılaştırmasının uygunluğu.',
        '3. Mevcut yaklaşımın yeterli başlangıç sayılıp sayılmayacağı ve KPI tabanlı yük aşamasının kabul ölçütleri.','',
        '[Son deneyin tam sonuçları](../../deneyler/05_kullanici_yayilim_guc_2026-11-10/SONUCLAR.md) — '
        '[Seçilen senaryo](../../deneyler/05_kullanici_yayilim_guc_2026-11-10/selected_scenario/configuration.json)']
    meeting=ROOT/'toplantilar/2026-11-10_toplanti_sunumu'
    (meeting/'HOCAYA_KISA_OZET.md').write_text('\n'.join(brief)+'\n',encoding='utf-8')
    shutil.copy2(HERE/'selected_comparison.png',meeting/'10_kullanici_yayilim_arastirmasi.png')
    shutil.copy2(HERE/'ue_placements.png',meeting/'11_kullanici_yerlesimleri.png')
    print(native[['name','training_score']+['control_'+m+'_mae_db' for m in ['rsrp','sinr','rsrq']]].to_string(index=False))
    print('SELECTED',winner['name'],'BUFFER',study['buffer_two_steps_passed'])
    print('NEW UE SAMPLE',triple(seed,'train'),triple(seed,'control'))


if __name__=='__main__':main()
