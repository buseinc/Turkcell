"""Publish actual run counts, robust selection, uncertainty and raw evidence."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import statistics
import importlib.util

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PROJECT=ROOT/'turkcell_tam_paket_2026-11-10'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'experiments/radio_joint_search_2026-11-10/matplotlib_cache'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

METRICS=['rsrp','sinr','rsrq']
CATEGORY={'placement':'Kullanıcı dağılımı','shadow':'Sabit gölgeleme','receiver':'Alıcı gürültüsü',
          'propagation':'Yayılım kaybı','power':'Yayın gücü','carrier':'Taşıyıcı','load':'Sunulan yük',
          'sector':'Sektör düzeni','azimuth':'Anten yönü'}
FAMILY={'wide':'1–4 km kümeler','near':'0,5–2 km kümeler','far':'2–6 km kümeler',
        'uniform':'bölge içinde uniform','mixed':'yakın/uzak karışık kümeler'}
LABELS={'reference':'Önceki aday','model_01':'Gölgeleme 4 dB','model_02':'65° anten / NF 12','model_03':'1–4 km / NF 12'}


def triple(row,split):
    return ' / '.join(f"{row[split+'_'+m+'_mae_db']:.2f}" for m in METRICS)


def describe(case):
    return (f"{FAMILY[case['family']]}; {case['beamwidth_deg']}°; n={case['exponent']}; "
            f"{case['power_dbm']} dBm; NF={case['ue_nf_db']} dB; gölge σ={case['shadow_std_db']} dB; "
            f"DL EARFCN={case['dl_earfcn']}; UDP={case['udp_interval_ms']:g} ms; sektör={case['sector_policy']}")


def main():
    study=json.loads((HERE/'study_result.json').read_text())
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    assert study['completed'] and study['regression']['passed'] and study['shadow_unit_checks']['passed']
    assert digest(PROJECT/'simulation/sindirgi_baseline.cc')==plan['original_cpp_sha256']
    for name,expected in plan['code_hashes'].items():assert digest(HERE/'simulation'/name)==expected,name
    for name,expected in plan['input_hashes'].items():assert digest(HERE/'inputs'/name)==expected,name
    correction=json.loads((HERE/'band8_correction.json').read_text())
    assert len(correction['runs'])==2
    for name,expected in correction['code_hashes'].items():assert digest(HERE/'band8_10mhz_v2'/name)==expected,name
    assert all(r['observer_regression']['passed'] for r in correction['runs'])
    rejected=set(correction['rejected_names'])
    spec=importlib.util.spec_from_file_location('report_evaluation',ROOT/'experiments/radio_joint_search_2026-11-10/run_search.py')
    evaluation=importlib.util.module_from_spec(spec);spec.loader.exec_module(evaluation)
    raw_targets=pd.read_csv(HERE/'inputs/targets.csv').to_dict('records')
    for entry in correction['runs']:
        entry['control']=evaluation.evaluate(entry['metrics'],raw_targets,'holdout')
    study['screening']=study['screening']+correction['runs']
    admissible=sorted((r for r in study['screening'] if r['case']['name'] not in rejected),key=lambda r:(r['training']['score'],r['case']['name']))
    required=[];seen=set()
    for r in admissible:
        key=structural(r['case'])
        if key not in seen:required.append(key);seen.add(key)
        if len(required)==3:break
    validated={structural(m['case']) for m in study['shortlist']}
    assert all(key in validated for key in required),'Band 8 correction changes shortlist: add common-draw validation first'
    targets=pd.read_csv(HERE/'inputs/targets.csv').set_index('site')
    rows=[];sites_list=[];ues_list=[];items={}
    for phase,entries in [('screening',study['screening']),('ensemble',study['ensemble']),('confirmation',study['finals'])]:
        for entry in entries:
            case=entry['case'];name=case['name'];items[name]=entry
            sites=targets.join(pd.DataFrame.from_dict(entry['metrics']['sites'],orient='index'))
            sites['case']=name;sites['phase']=phase;sites['model_id']=case.get('model_id','')
            sites['admissible']=name not in rejected
            for m in METRICS:sites[m+'_error_db']=sites[m]-sites[m+'_target']
            sites_list.append(sites.reset_index())
            ues=pd.DataFrame(entry['metrics']['ues']);ues['case']=name;ues['phase']=phase;ues_list.append(ues)
            result_folder=HERE/entry.get('result_folder',str(Path('simulation/results')/name))
            samples=pd.read_csv(result_folder/'sinr_components.csv')
            final=pd.read_csv(result_folder/'ues.csv').set_index('ue_id').synthetic_cell_id
            samples=samples[samples.time_s.ge(1)&samples.synthetic_cell_id.eq(samples.ue_id.map(final))]
            error=float((samples.native_sinr_db-samples.reconstructed_mixed_sinr_db).abs().max())
            assert error<1e-6,(name,error)
            row={**case,'phase':phase,'admissible':name not in rejected,'training_score':entry['training']['score'],
                 'train_valid':entry['training']['valid_sites'],'control_valid':entry['control']['valid_sites'],
                 'connected':entry['result']['connected_ues'],'receiving_dl':entry['result']['ues_receiving_dl'],
                 'wall_seconds':entry['result']['wall_seconds'],
                 'mixed_reconstruction_max_error_db':error,
                 'sampled_ues':int(samples.ue_id.nunique()),'samples':len(samples),
                 'fresh_data_sample_pct':float(100*samples.data_interference_fresh.mean())}
            for split,key in [('train','training'),('control','control')]:
                for m in METRICS:
                    row[split+'_'+m+'_mae_db']=entry[key]['mae_db'][m]
            for m in METRICS:row['maximum_'+m+'_site_error_db']=float(sites[m+'_error_db'].abs().max())
            rows.append(row)
    table=pd.DataFrame(rows)
    table.to_csv(HERE/'all_native_runs.csv',index=False)
    site_table=pd.concat(sites_list,ignore_index=True);site_table.to_csv(HERE/'site_comparison.csv',index=False)
    pd.concat(ues_list,ignore_index=True).to_csv(HERE/'ue_comparison.csv',index=False)
    screen=table[table.phase.eq('screening')&table.admissible].sort_values(['training_score','name'])
    screen.to_csv(HERE/'screening_rank.csv',index=False)
    bases={}
    for _,r in screen.iterrows():
        if r.category=='placement' and ((r.profile=='B' and r.family=='wide') or (r.profile!='B' and r.family=='far')):
            bases[r.profile]=r
    effects=screen.copy()
    effects['profile_baseline']=[bases[r.profile]['name'] for _,r in effects.iterrows()]
    effects['training_score_change']=[r.training_score-bases[r.profile].training_score for _,r in effects.iterrows()]
    for m in METRICS:
        effects['train_'+m+'_mae_change_db']=[r['train_'+m+'_mae_db']-bases[r.profile]['train_'+m+'_mae_db'] for _,r in effects.iterrows()]
    effects.to_csv(HERE/'paired_factor_effects.csv',index=False)
    ensemble=table[table.phase.eq('ensemble')]
    rankings=[]
    for rank in study['ensemble_ranking']:
        frame=ensemble[ensemble.model_id.eq(rank['model_id'])]
        assert len(frame)==len(plan['ensemble_draws'])
        row={**rank,'train_site_observations':int(frame.train_valid.sum()),
             'control_site_observations':int(frame.control_valid.sum()),
             'minimum_connected':int(frame.connected.min()),'minimum_receiving_dl':int(frame.receiving_dl.min())}
        for split in ['train','control']:
            for m in METRICS:
                row[split+'_'+m+'_mae_db']=float(frame[split+'_'+m+'_mae_db'].mean())
                row[split+'_'+m+'_std_db']=float(frame[split+'_'+m+'_mae_db'].std(ddof=0))
        rankings.append(row)
    rank_table=pd.DataFrame(rankings).sort_values(['robust_score','model_id'])
    rank_table.drop(columns=['mean_training_mae_db']).to_csv(HERE/'robust_model_rank.csv',index=False)
    recommended=study['recommended_model']
    chosen=next(m for m in study['shortlist'] if m['model_id']==recommended)
    selected_rank=rank_table[rank_table.model_id.eq(recommended)].iloc[0]
    reference_rank=rank_table[rank_table.model_id.eq('reference')].iloc[0]
    final=table[table.name.eq('confirm_24')].iloc[0]
    site_summary=[]
    selected_entries=[r for r in study['ensemble'] if r['case']['model_id']==recommended]
    for site,target in targets.iterrows():
        record={'site':site,'split':target['split']}
        ue_counts=[sum(u['site']==site for u in r['metrics']['ues']) for r in selected_entries]
        record.update(minimum_ues=min(ue_counts),maximum_ues=max(ue_counts))
        for m in METRICS:
            values=[r['metrics']['sites'][site][m] for r in selected_entries if site in r['metrics']['sites']]
            record[m+'_target']=target[m+'_target'];record[m+'_mean']=statistics.mean(values)
            record[m+'_std']=statistics.pstdev(values)
            record[m+'_mae']=statistics.mean(abs(v-target[m+'_target']) for v in values)
        site_summary.append(record)
    pd.DataFrame(site_summary).to_csv(HERE/'selected_site_coverage.csv',index=False)
    # Extra RSRQ changes are descriptive; retain predeclared RSRP/SINR pass criterion.
    for check in study['buffer_checks']:
        left=items[f"confirm_{check['from_sites']}"]['metrics']['ues']
        right=items[f"confirm_{check['to_sites']}"]['metrics']['ues']
        a={r['ue_id']:r for r in left};b={r['ue_id']:r for r in right}
        differences=[abs(a[u]['rsrq']-b[u]['rsrq']) for u in a if a[u]['rsrq'] is not None and b[u]['rsrq'] is not None]
        check['descriptive_rsrq_q95_change_db']=float(np.quantile(differences,.95))
    final_entry=items['confirm_24'];config=final_entry['case']
    frozen=HERE/'selected_scenario';frozen.mkdir(exist_ok=True)
    input_sites=HERE/'inputs'/f"sites_24_{config['azimuth_seed']}_{config['sector_policy']}.csv"
    input_ues=HERE/'inputs'/f"ues_{config['family']}_{config['spatial_seed']}.csv"
    shutil.copy2(input_sites,frozen/'sites.csv');shutil.copy2(input_ues,frozen/'ues.csv')
    selected_config={'status':'Robustness-selected exploratory representative; not operator reconstruction',
        'recommended_model':recommended,'nominal_best_model':study['nominal_best_model'],
        'reference_within_margin':study['reference_within_margin'],'case':config,
        'model_assumptions':final_entry['result']['model_assumptions'],
        'ensemble_training':chosen['model_id'],
        'ensemble_summary':{k:(v.item() if isinstance(v,np.generic) else v) for k,v in selected_rank.items() if k!='mean_training_mae_db'},
        'representative_8s_training':final_entry['training'],'representative_8s_control':final_entry['control'],
        'source_cpp_sha256':plan['source_cpp_sha256'],'code_hashes':plan['code_hashes'],
        'files':{name:digest(frozen/name) for name in ['sites.csv','ues.csv']},
        'buffer_checks':study['buffer_checks'],'duration_check':study['duration_check'],
        'selection_rule':plan['selection_rule'],'original_baseline_unchanged':True}
    (frozen/'configuration.json').write_text(json.dumps(selected_config,indent=2),encoding='utf-8')
    counts={'screening_runs':len(study['screening']),'admissible_screening_runs':len(screen),'rejected_diagnostic_runs':len(rejected),
        'distinct_structural_screen_models':len({structural(c['case']) for c in study['screening'] if c['case']['name'] not in rejected}),
        'ensemble_runs':len(ensemble),'ensemble_models':len(rank_table),'confirmation_runs':len(study['finals']),
        'software_validation_lte_runs':2,'passive_observer_repeat_runs':correction['passive_observer_repeat_runs'],
        'native_lte_runs_total':study['native_lte_run_count']+len(correction['runs'])+correction['passive_observer_repeat_runs'],
        'previous_analytic_screens_included_in_native_count':False}
    checks={'computations_passed':True,'counts':counts,'regression':study['regression'],
        'shadow_unit_checks':study['shadow_unit_checks'],'shadow_integration':study['shadow_integration'],
        'maximum_mixed_reconstruction_error_db':float(table.mixed_reconstruction_max_error_db.max()),
        'all_data_defined_sites_and_targets_preserved':True,'original_cpp_unchanged':True,
        'buffer_two_steps_passed':study['buffer_two_steps_passed'],'duration_passed':study['duration_check']['passed'],
        'recommended_model':recommended,'nominal_best_model':study['nominal_best_model'],
        'rejected_unsupported_band8_names':sorted(rejected),'band8_correction_does_not_change_shortlist':True,
        'band8_passive_observer_regression_passed':True}
    (HERE/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    figures(screen,rank_table,site_table,targets,recommended,plan)
    documents(study,plan,screen,rank_table,selected_rank,reference_rank,final,counts,config)
    print(json.dumps(checks,indent=2))
    print(rank_table.drop(columns=['mean_training_mae_db']).to_string(index=False))


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def structural(case):
    excluded={'name','category','profile','label','azimuth_seed','shadow_seed','spatial_seed','duration_s','model_id','draw_index','total_sites'}
    return json.dumps({k:v for k,v in case.items() if k not in excluded},sort_keys=True)


def figures(screen,ranks,sites,targets,recommended,plan):
    colors=plt.get_cmap('tab10')
    categories=list(CATEGORY)
    top=screen.head(20).iloc[::-1]
    fig,ax=plt.subplots(figsize=(11,8),constrained_layout=True)
    ax.barh(range(len(top)),top.training_score,color=[colors(categories.index(c)) for c in top.category])
    ax.set_yticks(range(len(top)),[f"{r['name']} · {r['profile']} · {CATEGORY[r['category']]}" for _,r in top.iterrows()],fontsize=8)
    ax.set(xlabel='Eğitim puanı: düşük daha iyi',title=f"{len(screen)} gerçek tarama koşulundan en düşük puanlı 20\nKısa tarama sıralaması; son seçim tekrarlarla yapılır")
    ax.grid(axis='x',alpha=.2);fig.savefig(HERE/'screening_top20.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
    x=np.arange(len(ranks));axes[0].bar(x,ranks.mean_training_score,yerr=ranks.std_training_score,capsize=4,color='#0072b2')
    axes[0].scatter(x,ranks.robust_score,color='#d55e00',marker='D',label='Ortalama + 0,5 × std')
    axes[0].set_xticks(x,[LABELS.get(m,m) for m in ranks.model_id],rotation=25)
    axes[0].set(ylabel='Ortak eğitim puanı',title='Üç ortak kullanıcı/anten/gölgeleme örneklemi')
    axes[0].legend(fontsize=8)
    for index,(_,row) in enumerate(ranks.iterrows()):
        xs=np.arange(3)+(index-(len(ranks)-1)/2)*.18
        axes[1].bar(xs,[row['control_'+m+'_mae_db'] for m in METRICS],width=.17,
            yerr=[row['control_'+m+'_std_db'] for m in METRICS],capsize=3,label=LABELS.get(row.model_id,row.model_id))
    axes[1].set_xticks(range(3),['RSRP','SINR','RSRQ'])
    axes[1].set(ylabel='Kontrol MAE (dB)',title='Seçimde kullanılmayan kontrol sonuçları')
    axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(axis='y',alpha=.2)
    fig.suptitle('Hata çubukları yalnız denenen üç tekrarın standart sapmasıdır; güven aralığı değildir.',fontsize=10)
    fig.savefig(HERE/'robustness_comparison.png',dpi=170);plt.close(fig)
    ensemble=sites[sites.phase.eq('ensemble')]
    fig,axes=plt.subplots(1,3,figsize=(16,5.3),constrained_layout=True);x=np.arange(len(targets))
    for ax,m,label in zip(axes,METRICS,['RSRP (dBm)','SINR (dB)','RSRQ (dB)']):
        for idx,split in enumerate(targets.split):
            if split=='holdout':ax.axvspan(idx-.4,idx+.4,color='#fff0df',zorder=0)
        ax.plot(x,targets[m+'_target'],'ko-',label='Experia')
        lines=[(recommended,'#d55e00','Önerilen: 3 tekrar ortalaması')]
        if recommended!='reference':lines.insert(0,('reference','#0072b2','Önceki aday: 3 tekrar ortalaması'))
        for ident,color,legend in lines:
            values=ensemble[ensemble.model_id.eq(ident)].groupby('site')[m].mean().reindex(targets.index)
            ax.plot(x,values,'o--',color=color,label=legend)
        values=sites[sites.case.eq('confirm_24')].set_index('site')[m].reindex(targets.index)
        ax.plot(x,values,'s:',color='#009e73',label='Önerilen: önceden seçilmiş örnekte 8 s')
        ax.set_xticks(x,[s.replace('SITE_','') for s in targets.index],rotation=50)
        ax.set_ylabel(label);ax.grid(alpha=.2)
    axes[0].legend(fontsize=6.5)
    fig.suptitle('Genişletilmiş araştırma — verideki saha konumları ve hedefler korunur\nTuruncu zemin: daha önce görülmüş kontrol sahaları; gerçek ağ doğrulaması değildir.',fontsize=11)
    fig.savefig(HERE/'final_site_comparison.png',dpi=170);fig.savefig(HERE/'final_site_comparison.svg');plt.close(fig)


def documents(study,plan,screen,ranks,selected,reference,final,counts,config):
    chosen=study['recommended_model']
    status=lambda passed:'geçti' if passed else 'GEÇMEDİ; sınır kontrolü gerekiyor'
    improvement=100*(reference.robust_score-selected.robust_score)/reference.robust_score
    table=['| Aday | Eğitim puanı ort. ± std | Sağlamlık puanı | Eğitim MAE RSRP / SINR / RSRQ | Kontrol MAE RSRP / SINR / RSRQ |',
           '|---|---:|---:|---:|---:|']
    for _,r in ranks.iterrows():
        table.append(f"| {r.model_id}{' (önerilen)' if r.model_id==chosen else ''} | {r.mean_training_score:.3f} ± {r.std_training_score:.3f} | {r.robust_score:.3f} | {triple(r,'train')} | {triple(r,'control')} |")
    ranking='\n'.join(table)
    descriptions='\n'.join(f"- **{m['model_id']}**, tarama kaynağı {m['source_screen']}: {describe(m['case'])}." for m in study['shortlist'])
    categories=screen.category.value_counts()
    breadth='\n'.join(f"| {CATEGORY[c]} | {int(categories.get(c,0))} |" for c in CATEGORY)
    buffer='\n'.join(f"| {c['from_sites']} → {c['to_sites']} | {c['rsrp_q95_abs_change_db']:.3f} | {c['sinr_q95_abs_change_db']:.3f} | {c['descriptive_rsrq_q95_change_db']:.3f} | {100*c['same_serving_sector_fraction']:.1f}% | {status(c['passed'])} |" for c in study['buffer_checks'])
    duration=study['duration_check']
    maxima=' / '.join(f"{final['maximum_'+m+'_site_error_db']:.2f}" for m in METRICS)
    control_std=' / '.join(f"{selected['control_'+m+'_std_db']:.2f}" for m in METRICS)
    completeness=(f"Tekrarlarda eğitim {int(selected.train_site_observations)}/15, kontrol {int(selected.control_site_observations)}/9 saha-gözlemi; "
                  f"en az {int(selected.minimum_connected)}/64 kullanıcı bağlı, {int(selected.minimum_receiving_dl)}/64 kullanıcı veri aldı.")
    caveat=('Üç kontrol sahası önceki çalışmalarda görüldü; yeni kör doğrulama değildir. '
            'Bütün koşullar kısa süreli, düşük sentetik yükte çalışır. Yakınlık gerçek operatör ayarlarının bulunduğunu göstermez; kapasite doğrulaması yapılmadı.')
    choice=(f"Önceki adayın sağlamlık puanına göre azalma %{improvement:.1f}. " if chosen!='reference' else
            ('Önceki aday ortak tekrarların sağlamlık sıralamasında doğrudan ilk sırada kaldı. '
             if study['nominal_best_model']=='reference' else
             'Önceden yazılan 0,10 dB sadelik kuralıyla önceki aday korundu. '))
    gap=float(ranks.iloc[1].robust_score-ranks.iloc[0].robust_score)
    if gap<.10:choice+=f'İlk iki sağlamlık puanı arasındaki fark yalnız {gap:.3f} dB; güçlü bir üstünlük iddiası kurmuyoruz. '
    result=f'''# Genişletilmiş gerçek ns-3 denemeleri — 10 Kasım 2026

**Sonuç:** {counts['screening_runs']} gerçek tarama koşusu ({counts['admissible_screening_runs']} geçerli koşul; 2 reddedilmiş Band 8 tanı koşusu), {counts['ensemble_models']} adayda {counts['ensemble_runs']} ortak tekrar ve {counts['confirmation_runs']} uzun/komşu doğrulaması tamamlandı. Önerilen aday: **{chosen}**. {choice}

## Kaç ve ne çeşit deneme yaptık?

Tarama: önce **49**, ardından **2 düzeltme** ile **{counts['screening_runs']} gerçek koşu**; sıralamada **{counts['admissible_screening_runs']} geçerli koşul**. Rastgele anten örneklerini aynı yapısal model sayarsak **{counts['distinct_structural_screen_models']}** geçerli farklı yapısal ayar. Her tarama 2 s, ilk 1 s ısınma. Bunlar analitik kestirim değil, gerçek LTE/EPC ns-3 çalıştırmalarıdır.

**Kaydedilmiş düzeltme:** İlk iki Band 8 denemesinde 100 RB / 20 MHz kalmıştı. [ETSI TS 136 101 Tablo 5.6.1-1](https://www.etsi.org/deliver/etsi_ts/136100_136199/136101/18.05.00_60/ts_136101v180500p.pdf) Band 8 için bu genişliği desteklemez. `screen_015` ve `screen_031` aday sıralamasından çıkarıldı, kayıtları silinmedi; aynı girdilerle 50 RB / 10 MHz'de iki yeni koşu yapıldı. Düzeltme geçerli ilk üç yapısal adayı değiştirmedi; rapor bunu ayrıca doğrular. Diğer koşuların kaynakları değiştirilmedi. [Düzeltme kuralı](band8_amendment.json), [düzeltilen sonuçlar](band8_correction.json). Aşağıdaki aile sayıları yalnız geçerli taramaları içerir.

| Değişken ailesi | Atanan tarama sayısı |
|---|---:|
{breadth}

Kullanıcılar: 0,5–2 km / 1–4 km / 2–6 km kümeler, bölge içinde uniform ve yakın–uzak karışık; anten 65°/120°; yayılım üsleri yaklaşık 2,55–3,15; güç 40–49 dBm; alıcı NF 6/9/12 dB; gölge σ 0/4/8 dB; UDP 20/50 ms; anten yön örnekleri; 482/554 için iki veya üç sektör; ortak Band 3/8/1 taşıyıcı hipotezleri. Bu bir tam faktöriyel tarama değildir: üç başlangıç profili çevresinde tek-değişken denemeleri yapılmıştır. Tüm olası etkileşimleri tükettiğimiz iddia edilmez.

Toplam **{counts['native_lte_runs_total']} native LTE çalıştırması** = {counts['screening_runs']} tarama + {counts['ensemble_runs']} tekrar + {counts['confirmation_runs']} doğrulama + 2 yazılım testi + 2 pasif tanı tekrarı. Son ikisi yeni model alternatifi sayılmaz: 10 MHz'de native mixed SINR'nin kaynak-grubu kenar RB ortalamasını kontrol hesabına ekleyerek aynı iki modeli yeniden çalıştırdık. Native radyo, ölçüm, sektör ve UE CSV özetleri önceki 10 MHz koşularıyla birebir aynı; yalnız pasif tanı hesabı düzeldi. İlk kayıtlar `band8_10mhz/`, son doğrulanmış kayıtlar `band8_10mhz_v2/` altında. Önceki 135 analitik ön eleme bu sayıya dahil değildir. Ayrı küçük gölgeleme birim kontrolü LTE koşusu sayılmadı.

## Seçimi nasıl yaptık?

Basit örnek: saha yerini haritada sabit tutuyoruz. O sahanın 1 km çevresindeki kullanıcılarla 5 km çevresindeki kullanıcıların göreceği sinyal aynı olmayabilir. Kullanıcı dağılımı denemesi bunu değiştiriyor. Gölgeleme denemesinde ise aynı uzaklıktaki bağlantıların ek kaybının farklı olabileceğini varsayıyoruz; bunu gerçek bina haritasından çıkarmıyoruz. Alıcı gürültüsü denemesi de telefonun zayıf sinyali ne kadar temiz duyabildiğiyle ilgili. Bunlar ölçülmemiş koşullar için alternatiflerdir; saha konumları için alternatif üretmiyoruz.

Beş eğitim sahasında RSRP/SINR/RSRQ mutlak hatalarının eşit ağırlıklı ortalaması; eksik eğitim sahası başına 10 dB ceza. Taramanın ilk üç farklı yapısal modeli ve önceki referans, aynı üç kullanıcı/anten/gölgeleme örneğinde 4 s çalıştırıldı. Rastgele örnekler önceden yazıldı; en güzel sonuç veren örnek seçilmedi.

Son puan = üç tekrarın eğitim puanı ortalaması + 0,5 × standart sapması. Önceki referans minimuma 0,10 dB içinde kalırsa daha basit referans önerilir. Kontrol hataları bu seçim dondurulduktan sonra hesaplandı. Üç tekrarın standart sapması belirsizliğin sınırlı bir göstergesidir; güven aralığı değildir. Tarama ve tekrarlar aynı beş eğitim sahasını kullandığı için eğitim kazanımı genelleme kanıtı değildir.

{ranking}

Tablodaki MAE'ler dB; düşük daha yakın. Kontrol MAE standart sapmaları, önerilende RSRP / SINR / RSRQ: **{control_std} dB**. {completeness}

{descriptions}

## Önceden belirlenen örnekte uzun doğrulama

Önerilen ayar: **{describe(config)}**. 64 sanal kullanıcı; 24 toplam saha. Üç tekrardan ilk örnek daha sonuçlara bakılmadan son doğrulama örneği olarak belirlendi. Aynı örnekte 8 s:

| Küme | RSRP MAE | SINR MAE | RSRQ MAE | Geçerli saha |
|---|---:|---:|---:|---:|
| Eğitim | {final.train_rsrp_mae_db:.2f} | {final.train_sinr_mae_db:.2f} | {final.train_rsrq_mae_db:.2f} | {int(final.train_valid)}/5 |
| Kontrol | {final.control_rsrp_mae_db:.2f} | {final.control_sinr_mae_db:.2f} | {final.control_rsrq_mae_db:.2f} | {int(final.control_valid)}/3 |

8 s / 24 saha koşusunda {int(final.connected)}/64 bağlı ve {int(final.receiving_dl)}/64 veri alan kullanıcı. Sekiz değerlendirme sahasında en büyük mutlak RSRP / SINR / RSRQ hataları **{maxima} dB**. Ortalama yakınlık her sahanın yakın olduğunu söylemez.

4 → 8 s kontrolü: **{status(duration['passed'])}**; %95 kullanıcı RSRP değişimi {duration['rsrp_q95_abs_change_db']:.3f}, SINR {duration['sinr_q95_abs_change_db']:.3f} dB; hizmet sektörü aynı {100*duration['same_serving_sector_fraction']:.1f}%. 4 s ve 8 s sonuçları ayrı raporlanır.

| Toplam saha | RSRP %95 mutlak değişim | SINR %95 mutlak değişim | RSRQ %95 değişim (tanısal) | Aynı hizmet sektörü | Sonuç |
|---|---:|---:|---:|---:|---|
{buffer}

Önceden yazılan sınırlar: RSRP ve SINR %95 değişim ≤1 dB; aynı hizmet sektörü ≥%95. RSRQ burada ek tanısal sonuçtur. İki genişletmenin ortak sonucu: **{status(study['buffer_two_steps_passed'])}**. Bu koşullar geçmezse 24 sahayı yeterli ilan etmeyiz.

## Sabit kalanlar ve açık varsayımlar

- Ham ölçümler, verideki saha koordinatları/kimlikleri, özgün hücre–saha eşlemesi, hedefler ve eğitim/kontrol ayrımı korunur. 24→32→48 genişlemesi aynı envanter kaynaklarından gelir. 553/554/555'in ek konumlarının özgün kaynağı hâlâ sorulacak.
- Kullanıcı yerleri gerçek müşteri konumları değildir. Sektörler sentetik radyo temsilleridir; iki-sektör alternatifi yalnız 482/554'te sınandı. Hiçbir denemede verideki sahayı sonuç güzelleşsin diye taşımadık.
- 64 kullanıcı toplamı saha başına eşit temsil sağlamaz. Seçilen ayarın üç tekrarından birinde 296'yı yalnız bir, birinde 443'ü iki kullanıcı temsil eder. Saha ortalamaları kullanıcı/anten örneklerine duyarlıdır. [Saha başına kullanıcı kapsamı ve üç tekrar özeti](selected_site_coverage.csv). Daha yoğun kullanıcı örneklemi ve sabit toplam sunulan yükle duyarlılık, bir sonraki araştırma konusudur; bu kampanyada yapılmış sayılmaz.
- Gölge modeli: koordinat çiftine bağlı, karşılıklı aynı ve zamanda sabit, sıfır ortalamalı Gaussian dB kaybı. Aynı konumlu sektörlerde ortak; farklı kullanıcı konumlarında uzaysal korelasyon yok. Gerçek arazi/bina modeli veya hızlı fading değildir. σ=0 özgün log-distance yoluna aynen döner.
- Her taşıyıcı denemesi tek ortak, eşlenmiş DL/UL taşıyıcı kullanır; yayılım referans frekansı ve UE arama kanalı birlikte değiştirilir. Bant birleştirme, gerçek çok katmanlı ağ ve frekanslar arası handover modellenmedi. Bantlar varsayımdır.
- Mixed SINR ve ns-3'ün native RSRQ hesabı korunur; hedefe uysun diye sabit RSRQ düzeltmesi eklenmedi. Mixed tanımındaki güncel veri girişimi bulunmadığında gürültüye dönüş davranışı nedeniyle sonuçların ölçüm tanımıyla uyumu hocayla netleştirilmeli. [Önceki tanım incelemesi](../placement_propagation_2026-11-10/RSRQ_TANIM_NOTU.md).
- {caveat}

## Yazılım ve yeniden üretme

Özgün C++ SHA-256 değişmedi: `{plan['original_cpp_sha256']}`. Gölgesiz 4 s referansın eski sonuçlarla UE başına tüm radyo metrikleri, hizmet sektörü ve byte sayıları aynı. Gölge için karşılıklılık, zamana göre sabitlik, aynı koordinatlar, σ=0 eşdeğerliği ve dağılım kontrolü geçti; pozitif σ ile 6/6 kullanıcı bağlantı/veri testi geçti. Her native koşuda mixed SINR bağımsız bileşenlerden yeniden hesaplandı; sayısal eşleşme `checks.json` içinde.

Windows proje kökünde rapor: `.venv\\Scripts\\python.exe experiments/extended_radio_2026-11-10/report.py`

Ubuntu-22.04 WSL'de kampanya: `python3 /mnt/c/Users/bi025305/Downloads/paylasim/paylasim/experiments/extended_radio_2026-11-10/run_campaign.py`

`experiment_plan.json` bütün girdilerin/deney kaynaklarının özetlerini, seçimi ve tohumları saklar. `prepare.py` girdileri üretir; mevcut tamamlanmış koşuları değiştirmeden yeniden raporlamak için doğrudan `report.py` çalıştırılır. Kampanya aynı kod/girdiyle geçerli sonuçları önbellekten kullanır.

## Dosyalar

- [Analizdeki tarama/tekrar/doğrulama sonuçları](all_native_runs.csv), [tam geçerli tarama sırası](screening_rank.csv), [tekrar sıralaması](robust_model_rank.csv)
- [Her koşulun kendi başlangıcına göre etkisi](paired_factor_effects.csv); negatif değişim daha düşük hata demektir, kısa taramadır
- [Saha bazında bütün karşılaştırmalar](site_comparison.csv), [UE bazında bütün çıktılar](ue_comparison.csv)
- [Deney planı](experiment_plan.json), [tam sonuç](study_result.json), [sayısal kontroller](checks.json)
- [Önerilen senaryo](selected_scenario/configuration.json); sahalar ve kullanıcılar aynı klasörde
- [Tarama grafiği](screening_top20.png), [tekrar grafiği](robustness_comparison.png), [saha karşılaştırması](final_site_comparison.png)
'''
    (HERE/'SONUCLAR.md').write_text(result,encoding='utf-8')
    comparison=reference if chosen!='reference' else ranks[ranks.model_id.ne(chosen)].iloc[0]
    comparison_label='Önceki aday' if chosen!='reference' else f"En yakın eğitim alternatifi ({comparison.model_id})"
    selected_label='Önerilen' if chosen!='reference' else 'Korunan önceki aday'
    score_sentence=(f'Eğitim sağlamlık puanı {reference.robust_score:.3f} → {selected.robust_score:.3f}.' if chosen!='reference' else
                    f'Tekrarları dikkate alan eğitim puanı: seçilen {selected.robust_score:.3f}, en yakın alternatif {comparison.robust_score:.3f}.')
    brief=f'''# Hocaya kısa özet — 10 Kasım 2026

Amaç, verideki saha konumlarını koruyup bilinmeyen radyo ve kullanıcı koşullarını açık varsayımlarla deneyerek Experia'ya yakın, temsili bir LTE başlangıcı kurmak.

**Bu bilgisayarda çalışıyor.** Son genişletmede **{counts['screening_runs']} gerçek ns-3 tarama koşusu** ({counts['admissible_screening_runs']} geçerli; iki hatalı Band 8 koşusu çıkarılıp uygun genişlikle yeniden çalıştırıldı), **{counts['ensemble_models']} aday × 3 ortak tekrar** ve **3 uzun/komşu kontrolü** tamamlandı. Bunlara ek 2 yazılım testi ve 2 pasif tanı tekrarı yapıldı; bunlar yeni model alternatifi sayılmadı. Önceki analitik ön elemeler bu gerçek koşu sayısına dahil değil.

Dokuz başlık denendi: kullanıcı dağılımı, gölgeleme, alıcı gürültüsü, yayılım, güç, trafik, sektör sayısı, anten yönü ve taşıyıcı. Koordinatlar ve ölçüm hedefleri değiştirilmedi.

**Öneri: {chosen}.** {describe(config)}. {choice}

| Kontrol hatası: üç tekrar ort. ± std | {selected_label} | {comparison_label} |
|---|---:|---:|
| RSRP | {selected.control_rsrp_mae_db:.2f} ± {selected.control_rsrp_std_db:.2f} dB | {comparison.control_rsrp_mae_db:.2f} ± {comparison.control_rsrp_std_db:.2f} dB |
| SINR | {selected.control_sinr_mae_db:.2f} ± {selected.control_sinr_std_db:.2f} dB | {comparison.control_sinr_mae_db:.2f} ± {comparison.control_sinr_std_db:.2f} dB |
| RSRQ | {selected.control_rsrq_mae_db:.2f} ± {selected.control_rsrq_std_db:.2f} dB | {comparison.control_rsrq_mae_db:.2f} ± {comparison.control_rsrq_std_db:.2f} dB |

Düşük daha yakın. Seçim yalnız beş eğitim sahasında, ortalama hata ve tekrarlar arası oynaklıkla yapıldı. {score_sentence} ± değerleri üç tekrarın standart sapmasıdır, güven aralığı değildir. {completeness}

Kapsam sınırı: bazı tekrar/sahalarda yalnız 1–2 sanal kullanıcı vardır. Bir sonraki duyarlılık kontrolü, toplam sunulan yükü koruyarak kullanıcı örneklemini artırmak olmalı; bu kampanyada henüz yapılmadı.

Önceden seçilen ilk kullanıcı örneğinde 8 s kontrol hataları RSRP / SINR / RSRQ **{triple(final,'control')} dB**. Sekiz sahanın en büyük mutlak hataları **{maxima} dB**; bazı sahalarda fark devam ediyor. 24→32→48 saha kontrolü **{status(study['buffer_two_steps_passed'])}**; 4→8 s kontrolü **{status(duration['passed'])}**.

Hocaya söylenecek: “Yalnız birkaç ayar denemedik; farklı açıklamaları tarayıp iyi görünenleri farklı kullanıcı/anten örneklerinde tekrar sınadık. Seçtiğimiz ayar ölçümlere yakın bir başlangıç; gerçek ağın birebir konfigürasyonu olduğunu iddia etmiyoruz.”

{caveat}

Hocadan netleştirilecek üç konu:

1. 553/554/555 konumları ve hücre–saha bağlantılarının özgün kaynağı.
2. Experia SINR/RSRQ kanal ve ortalama tanımları; mixed çıktıyla karşılaştırma uygunluğu.
3. Temsili başlangıcın yeterlilik ölçütü ve KPI ile yük aşamasına geçiş.

[Son deneyin tam sonuçları](../experiments/extended_radio_2026-11-10/SONUCLAR.md) — [Seçilen senaryo](../experiments/extended_radio_2026-11-10/selected_scenario/configuration.json)
'''
    meeting=ROOT/'toplanti_2026-11-10'
    (meeting/'HOCAYA_KISA_OZET.md').write_text(brief,encoding='utf-8')
    for name,target in [('screening_top20.png','12_genis_tarama.png'),('robustness_comparison.png','13_ortak_tekrarlar.png'),
                        ('final_site_comparison.png','14_son_saha_karsilastirmasi.png')]:shutil.copy2(HERE/name,meeting/target)
    marker='## Genişletilmiş araştırma: gerçek tarama ve ortak tekrarlar'
    path=meeting/'TOPLANTI_NOTU.md';current=path.read_text(encoding='utf-8')
    if marker in current:current=current[:current.index(marker)].rstrip()+'\n'
    addition=f'''\n{marker}

{counts['screening_runs']} gerçek tarama koşusu ({counts['admissible_screening_runs']} geçerli; iki Band 8 koşusu genişlik uyumsuzluğu nedeniyle çıkarılıp yeniden çalıştırıldı), {counts['ensemble_runs']} ortak tekrar ve 3 uzun/komşu kontrolü tamamlandı. Yazılım doğrulaması ayrıca 2 LTE koşusu içerir. Dokuz değişken ailesi tarandı; analitik ön eleme sayıları gerçek koşulara eklenmedi. Önerilen **{chosen}**; ayar: {describe(config)}.

{ranking}

Kontrol sütunu seçimde kullanılmadı; bu üç saha geçmişte görüldüğünden kör test değildir. Üç tekrar ortalamaları 8 s tek örnek sonucundan ayrıdır. 8 s tek örnekte kontrol MAE RSRP / SINR / RSRQ: {triple(final,'control')} dB. En büyük saha hataları: {maxima} dB.

24→32→48 kontrolü: {status(study['buffer_two_steps_passed'])}; 4→8 s: {status(duration['passed'])}. Koordinatlar/ham veri/ölçüm hedefleri ve özgün başlangıç korunur.

[49 koşulun en iyi 20'si](12_genis_tarama.png) — [Ortak tekrarlar](13_ortak_tekrarlar.png) — [Saha karşılaştırması](14_son_saha_karsilastirmasi.png) — [Tam sonuçlar](../experiments/extended_radio_2026-11-10/SONUCLAR.md) — [Güncel kısa özet](HOCAYA_KISA_OZET.md).
'''
    path.write_text(current+addition,encoding='utf-8')


if __name__=='__main__':main()
