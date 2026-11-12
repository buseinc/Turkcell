"""Report all six cases, training-only selection, controls and tradeoffs."""
from pathlib import Path
import hashlib
import json
import os

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]/'turkcell_tam_paket_2026-11-10'
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'matplotlib_cache'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    result=json.loads((HERE/'study_result.json').read_text())
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    assert result['completed'] and result['regression']['passed']
    assert hashlib.sha256((PROJECT/'simulation/sindirgi_baseline.cc').read_bytes()).hexdigest()==plan['original_cpp_sha256']
    targets=pd.read_csv(HERE/'inputs/targets.csv').set_index('site')
    rows=[];site_frames=[];ue_frames=[]
    for case in result['cases']:
        params=case['case'];name=params['name']
        metrics=case['metrics']
        sites=targets.join(pd.DataFrame.from_dict(metrics['sites'],orient='index'))
        sites['case']=name
        for metric in ['rsrp','sinr','rsrq']:
            sites[metric+'_error_db']=sites[metric]-sites[metric+'_target']
        site_frames.append(sites.reset_index())
        ues=pd.DataFrame(metrics['ues'])
        assert len(ues)==64
        original=pd.read_csv(HERE/'inputs/ues.csv')
        # C++ exports metres with 12 significant digits; allow sub-micrometre rounding.
        assert np.allclose(ues[['x_m','y_m']].to_numpy(),original[['x_m','y_m']].to_numpy(),atol=1e-7,rtol=0)
        ues['case']=name
        ue_frames.append(ues)
        samples=pd.read_csv(HERE/'simulation/results'/name/'sinr_components.csv')
        final=pd.read_csv(HERE/'simulation/results'/name/'ues.csv').set_index('ue_id').synthetic_cell_id
        samples=samples[samples.time_s.ge(1)&samples.synthetic_cell_id.eq(samples.ue_id.map(final))]
        reconstruction_error=float((samples.native_sinr_db-samples.reconstructed_mixed_sinr_db).abs().max())
        assert reconstruction_error<1e-6,(name,reconstruction_error)
        row={**params,'training_score':case['training']['score'],
             'train_valid_sites':case['training']['valid_sites'],
             'control_valid_sites':case['control']['valid_sites'],
             'train_missing_sites':','.join(case['training']['missing_sites']),
             'control_missing_sites':','.join(case['control']['missing_sites']),
             'connected':case['result']['connected_ues'],'receiving_dl':case['result']['ues_receiving_dl'],
             'total_dl_bytes':case['result']['total_dl_bytes'],
             'wall_seconds':case['result']['wall_seconds'],
             'sampled_ues':int(samples.ue_id.nunique()),
             'fresh_data_sample_pct':float(100*samples.data_interference_fresh.mean()),
             'median_passive_control_sinr_db':float(samples.groupby('ue_id').control_sinr_db.mean().median()),
             'native_mixed_reconstruction_max_error_db':reconstruction_error}
        for split,key in [('train','training'),('control','control')]:
            for metric,value in case[key]['mae_db'].items():row[split+'_'+metric+'_mae_db']=value
        rows.append(row)
    summary=pd.DataFrame(rows)
    names=['train_'+m+'_mae_db' for m in ['rsrp','sinr','rsrq']]
    summary['training_pareto']=True
    for i,row in summary.iterrows():
        values=row[names].to_numpy(dtype=float)
        for j,other in summary.iterrows():
            if i==j:continue
            candidate=other[names].to_numpy(dtype=float)
            if (candidate<=values).all() and (candidate<values).any():
                summary.loc[i,'training_pareto']=False
                break
    summary=summary.sort_values(['training_score','name'])
    assert summary.iloc[0]['name']==result['selected_name']
    summary.to_csv(HERE/'summary.csv',index=False)
    sites=pd.concat(site_frames,ignore_index=True)
    sites.to_csv(HERE/'site_comparison.csv',index=False)
    pd.concat(ue_frames,ignore_index=True).to_csv(HERE/'ue_comparison.csv',index=False)
    winner=summary.iloc[0]
    baseline=summary[summary.name.eq('b65_t50')].iloc[0]
    selected_case=next(c for c in result['cases'] if c['case']['name']==winner['name'])
    selected={'status':'Exploratory candidate; original frozen baseline unchanged',
        'name':winner['name'],'case':selected_case['case'],'training':selected_case['training'],
        'control':selected_case['control'],'model_assumptions':selected_case['result']['model_assumptions'],
        'source_sha256':plan['source_cpp_sha256'],'input_hashes':plan['input_hashes'],
        'result_directory':'simulation/results/'+winner['name'],
        'caveats':['Previously observed control sites','Single UE/azimuth draw','Synthetic offered traffic',
                   'Real antenna/carrier/measurement definitions unknown','Buffer convergence not retested']}
    (HERE/'selected_candidate.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
    checks={'passed':True,'cases':len(summary),'regression':result['regression'],
        'original_baseline_unchanged':True,'all_ue_positions_preserved':True,
        'max_native_mixed_reconstruction_error_db':float(summary.native_mixed_reconstruction_max_error_db.max()),
        'selected_using_training_only':True,'selected_name':winner['name']}
    combined_ues=pd.concat(ue_frames,ignore_index=True)
    checks['load_pair_comparisons']=[]
    for width in [65,90,120]:
        low=combined_ues[combined_ues.case.eq(f'b{width}_t50')].set_index('ue_id')
        high=combined_ues[combined_ues.case.eq(f'b{width}_t5')].set_index('ue_id')
        checks['load_pair_comparisons'].append({'beamwidth_deg':width,
            'same_serving_sectors':bool((low.site.eq(high.site)&low.sector.eq(high.sector)).all()),
            'max_rsrp_change_db':float((low.rsrp-high.rsrp).abs().max()),
            'max_rsrq_change_db':float((low.rsrq-high.rsrq).abs().max()),
            'mean_native_sinr_change_db':float((high.sinr-low.sinr).mean())})
    (HERE/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,3,figsize=(16,5.2),constrained_layout=True)
    x=np.arange(len(targets))
    for ax,m,label in zip(axes,['rsrp','sinr','rsrq'],['RSRP (dBm)','SINR (dB)','RSRQ (dB)']):
        for index,split in enumerate(targets.split):
            if split=='holdout':ax.axvspan(index-.4,index+.4,color='#fff0df',zorder=0)
        ax.plot(x,targets[m+'_target'],'ko-',label='Experia')
        cases=[('b65_t50','Başlangıç mixed','#0072b2')]
        if winner['name']!='b65_t50':cases.append((winner['name'],'Eğitimden seçilen aday','#d55e00'))
        for name,legend,color in cases:
            frame=sites[sites.case.eq(name)].set_index('site').reindex(targets.index)
            ax.plot(x,frame[m],'o--',color=color,label=legend)
        ax.set_xticks(x,[s.replace('SITE_','') for s in targets.index],rotation=50)
        ax.set_ylabel(label)
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Altı varsayımsal koşul — seçim yalnız 5 eğitim sahasının üç metrik hatasıyla\n'
        f"Seçilen: {winner['beamwidth_deg']}° anten, {winner['udp_interval_ms']} ms paket aralığı; turuncu zemin: daha önce görülmüş 3 kontrol sahası",fontsize=11)
    fig.savefig(HERE/'selected_comparison.png',dpi=170)
    fig.savefig(HERE/'selected_comparison.svg')
    plt.close(fig)
    matrix=summary.pivot(index='beamwidth_deg',columns='udp_interval_ms',values='training_score').reindex(index=[65,90,120],columns=[50,5])
    fig,ax=plt.subplots(figsize=(7,5),constrained_layout=True)
    im=ax.imshow(matrix.to_numpy(),cmap='YlOrRd')
    for i in range(3):
        for j in range(2):ax.text(j,i,f'{matrix.iloc[i,j]:.2f}',ha='center',va='center')
    ax.set_xticks([0,1],['1× sunulan yük\n50 ms','10× sunulan yük\n5 ms'])
    ax.set_yticks([0,1,2],['65°','90°','120°'])
    ax.set(ylabel='Yatay anten genişliği',title='Üç metrik birlikte: eğitim puanı\nDüşük daha iyi; operatör kabul ölçütü değildir')
    fig.colorbar(im,ax=ax,label='Üç eğitim MAE ortalaması + eksik saha cezası')
    fig.savefig(HERE/'grid_scores.png',dpi=170)
    plt.close(fig)
    lines=['# RSRP, SINR ve RSRQ için altı koşulluk keşif taraması','',
        'Amaç eldeki ölçüm özetlerine daha yakın, açık varsayımlı bir başlangıç adayı bulmak. '
        'Gerçek anten/yük yapılandırmasını çıkarmak veya tam ağı yeniden kurmak değil.','',
        f"**Sonuç:** Eğitimden seçilen aday {winner['beamwidth_deg']}° / {winner['udp_interval_ms']} ms. "
        f"Ortak eğitim puanı {baseline['training_score']:.3f}'den {winner['training_score']:.3f}'e "
        f"(yaklaşık %{100*(baseline['training_score']-winner['training_score'])/baseline['training_score']:.1f} azalma) indi. "
        'Bu mütevazı bir toplam iyileşme; bütün metrikler aynı anda düzelmedi. '
        'Kontrol sahalarında RSRP/RSRQ hataları azaldı, SINR hatası büyüdü. '
        'Bu nedenle 65°, 90° ve 120° düşük yük adayları birer tradeoff olarak korunmalıdır.','',
        '## Ne değişti?','',
        '- Anten yatay genişliği: 65°, 90°, 120°. Tepe kazancı 15 dBi ve sektör başına güç 46 dBm korundu.',
        '- UDP paket aralığı: 50 ms ve 5 ms; kullanıcı başına sunulan yük 0,08192 ve 0,8192 Mbps. '
        '64 kullanıcı toplamı 5,24288 ve 52,4288 Mbps. Bunlar gerçek talep tahmini değildir.',
        '- Aynı 24 saha, 72 sektör, 64 kullanıcı konumu, yönler, yayılım ve mixed yöntemi kullanıldı. '
        'Genişlik değişince kullanıcıların bağlandığı saha/sektör değişebilir.',
        '- Her koşu 4 s; ilk 1 s dışarıda. Bu kısa pilot bir kapasite, gerçek hizmet veya deprem yükü doğrulaması değildir.','',
        '## Seçim kuralı','',
        'Önceden yazılan kural: beş eğitim sahasında RSRP, SINR, RSRQ MAE değerlerinin eşit '
        'ağırlıklı ortalaması + eksik eğitim sahası başına 10 dB ceza. Eşit ağırlık keşif amaçlıdır; '
        'operatör kabul kriteri değildir. Üç kontrol sahası sıralamaya alınmadı; daha önce '
        'görüldüklerinden kör doğrulama değildir. Bütün sonuçlar aşağıda korunur.','',
        '| Anten / aralık | Eğitim RSRP | Eğitim SINR | Eğitim RSRQ | Eğitim puanı | Geçerli eğitim/kontrol | Bağlanan / DL alan |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for _,row in summary.iterrows():
        mark=' **seçilen**' if row['name']==winner['name'] else ''
        lines.append(f"| {row['beamwidth_deg']}° / {row['udp_interval_ms']} ms{mark} | "
            f"{row['train_rsrp_mae_db']:.2f} | {row['train_sinr_mae_db']:.2f} | "
            f"{row['train_rsrq_mae_db']:.2f} | {row['training_score']:.2f} | "
            f"{row['train_valid_sites']}/5 — {row['control_valid_sites']}/3 | {row['connected']}/64 — {row['receiving_dl']}/64 |")
    lines+=['','## Başlangıç mixed ve seçilen aday: kontrol sahaları','',
            '| Metrik MAE (dB) | 65° / 50 ms başlangıç | Eğitimden seçilen aday |','|---|---:|---:|']
    for m in ['rsrp','sinr','rsrq']:
        lines.append(f"| {m.upper()} | {baseline['control_'+m+'_mae_db']:.2f} | {winner['control_'+m+'_mae_db']:.2f} |")
    lines+=['',f"Seçilen aday: **{winner['beamwidth_deg']}° ve {winner['udp_interval_ms']} ms**. "
        'Bu, yalnız denenmiş altı koşulun eğitim puanına göre seçimidir; bütün parametre uzayının optimumu değildir.',
        '', '## Yorumlama sınırları','',
        '- Her metriği ayrı okuyun. Eğitim puanındaki düşüşün kontrol sahalarına aynı biçimde taşınması garanti değildir.',
        '- Eksik sahalar ve hizmet alan kullanıcıların değişmesi ortalamaları etkileyebilir. '
        'Saha ve kullanıcı tabloları bu nedenle ayrıca saklandı.',
        '- Daha geniş anten, tepe kazancı sabitken farklı yönlere giden gücü artırır. '
        'Bu gerçek antenin bulunduğunu göstermez; bir senaryo hipotezidir.',
        '- Mixed SINR veri yüküne ve ölçüm güncellemesine duyarlıdır. Sunulan sentetik yükü '
        'gerçek KPI yükü gibi yorumlamayın. 2025 KPI ile 2026 radyo dönemi eşzamanlı değildir.',
        '- 553/554/555 konumlarının kaynağı ve Experia ölçüm tanımları hâlâ açık. '
        'Seçilen adayda komşu yakınsaması ve başka kullanıcı/azimut örnekleri yeniden sınanmadı.',
        '- Ana proje ve sabit başlangıç senaryosu değiştirilmedi. Bu ayrı bir aday taramasıdır.',
        '', '## Görseller','', '![Saha karşılaştırması](selected_comparison.png)','',
        '![Eğitim puanları](grid_scores.png)','', '## Dosyalar ve tekrar üretim','',
        '`experiment_plan.json` önceden yazılan planı, `training_selection.json` kontrol '
        'sonuçları eklenmeden sabitlenen seçimi, `study_result.json` tam koşuları içerir. '
        '`summary.csv`, `site_comparison.csv`, `ue_comparison.csv` sayısal sonuçlardır. '
        '`training_pareto` sütunu, diğer üç eğitim hatasında birden daha iyi/eşit başka '
        'aday bulunup bulunmadığını gösterir.','',
        'Proje kökünde PowerShell:','', '```powershell',
        '.\\.venv\\Scripts\\python.exe experiments/radio_joint_search_2026-11-10/prepare.py',
        'wsl --distribution Ubuntu-22.04 --exec python3 experiments/radio_joint_search_2026-11-10/run_search.py',
        '.\\.venv\\Scripts\\python.exe experiments/radio_joint_search_2026-11-10/report.py','```']
    (HERE/'SONUCLAR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(summary[['name','training_score']+names+['control_'+m+'_mae_db' for m in ['rsrp','sinr','rsrq']]].to_string(index=False))
    print('SELECTED',winner['name'])


if __name__=='__main__':main()
