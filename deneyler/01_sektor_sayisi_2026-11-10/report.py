"""Report the fixed sector-removal pilot without selecting a new baseline."""
from pathlib import Path
import hashlib
import json
import os

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]/'ana_proje'
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

LABELS = {'s0_three':'S0: 3 sektör','s1_two':'S1: 2 sektör','s1_one':'S1: 1 sektör'}


def main():
    plan = json.loads((HERE/'experiment_plan.json').read_text())
    result = json.loads((HERE/'study_result.json').read_text())
    assert result['completed'] and result['regression']['passed']
    assert hashlib.sha256((PROJECT/'simulation/sindirgi_baseline.cc').read_bytes()).hexdigest() == plan['original_cpp_sha256']
    targets = pd.read_csv(HERE/'inputs/targets.csv').set_index('site')
    baseline = pd.DataFrame(result['cases'][0]['metrics']['ues']).set_index('ue_id')
    summaries, site_frames, pair_frames = [],[],[]
    for case in result['cases']:
        name = case['name']
        sites = pd.DataFrame.from_dict(case['metrics']['sites'],orient='index')
        comparison = targets.join(sites,how='left')
        comparison['case'] = name
        for metric in ['rsrp','sinr','rsrq']:
            comparison[metric+'_error_db'] = comparison[metric]-comparison[metric+'_target']
        site_frames.append(comparison.reset_index())
        current = pd.DataFrame(case['metrics']['ues']).set_index('ue_id')
        assert baseline.index.equals(current.index)
        assert np.allclose(baseline[['x_m','y_m']],current[['x_m','y_m']],rtol=0,atol=1e-8)
        pairs = pd.DataFrame(index=baseline.index)
        pairs['case'] = name
        pairs['baseline_site'] = baseline.site
        pairs['current_site'] = current.site
        pairs['baseline_sector'] = baseline.sector
        pairs['current_sector'] = current.sector
        pairs['baseline_served_by_affected_site'] = baseline.site.isin(plan['affected_sites'])
        pairs['same_serving_sector'] = baseline.site.eq(current.site)&baseline.sector.eq(current.sector)
        for metric in ['rsrp','sinr','rsrq']:
            pairs['baseline_'+metric] = baseline[metric]
            pairs['current_'+metric] = current[metric]
            pairs[metric+'_change_db'] = current[metric]-baseline[metric]
        pair_frames.append(pairs.reset_index())
        row = {'case':name,'label':LABELS[name],
               'sectors':case['result']['synthetic_sectors'],
               'connected':case['result']['connected_ues'],
               'receiving_dl':case['result']['ues_receiving_dl'],
               'wall_seconds':case['result']['wall_seconds'],
               'sites_with_rsrp':int(comparison.rsrp.notna().sum()),
               'same_serving_sector_pct':100*float(pairs.same_serving_sector.mean()),
               'paired_sinr_ues':int(pairs.sinr_change_db.notna().sum()),
               'mean_paired_sinr_change_db':float(pairs.sinr_change_db.mean()),
               'q95_absolute_sinr_change_db':float(pairs.sinr_change_db.abs().quantile(.95)),
               'q95_absolute_rsrp_change_db':float(pairs.rsrp_change_db.abs().quantile(.95)),
               'affected_baseline_ue_count':int(pairs.baseline_served_by_affected_site.sum()),
               'affected_baseline_ue_mean_sinr_change_db':float(pairs.loc[pairs.baseline_served_by_affected_site,'sinr_change_db'].mean()),
               'missing_rsrp_sites':','.join(comparison.index[comparison.rsrp.isna()])}
        for group,mask in [('all',np.ones(len(comparison),dtype=bool)),
                           ('holdout',comparison.split.eq('holdout')),
                           ('affected',comparison.index.isin(plan['affected_sites']))]:
            for metric in ['rsrp','sinr','rsrq']:
                row[group+'_'+metric+'_mae_db'] = float(comparison.loc[mask,metric+'_error_db'].abs().mean())
        summaries.append(row)
    summary = pd.DataFrame(summaries)
    summary.to_csv(HERE/'summary.csv',index=False)
    site_table = pd.concat(site_frames,ignore_index=True)
    site_table.to_csv(HERE/'site_comparison.csv',index=False)
    paired_table = pd.concat(pair_frames,ignore_index=True)
    paired_table.to_csv(HERE/'paired_ue_comparison.csv',index=False)
    fig,axes = plt.subplots(1,3,figsize=(16,5.5),constrained_layout=True)
    x = np.arange(len(targets))
    colors = ['#0072b2','#d55e00','#009e73']
    for ax,metric,label in zip(axes,['rsrp','sinr','rsrq'],['RSRP (dBm)','SINR (dB)','RSRQ (dB)']):
        ax.plot(x,targets[metric+'_target'],'ko-',label='Experia')
        for case,color in zip(result['cases'],colors):
            frame = site_table[site_table.case.eq(case['name'])].set_index('site').reindex(targets.index)
            ax.plot(x,frame[metric],'o--',color=color,label=LABELS[case['name']])
        ax.set_xticks(x,[s.replace('SITE_','')+('*' if s in plan['affected_sites'] else '') for s in targets.index],rotation=55)
        ax.set_ylabel(label)
        ax.grid(alpha=.25)
    axes[0].legend(fontsize=8)
    fig.suptitle('Sektör sayısı pilotu — yalnız 482 ve 554 sahalarında 3 → 2 → 1 etkin sektör\n'
                 '* değiştirilen sahalar; aynı 64 UE, kalan anten yönleri/güçleri sabit; tek azimut örneklemesi',fontsize=11)
    fig.savefig(HERE/'sector_comparison.png',dpi=170)
    fig.savefig(HERE/'sector_comparison.svg')
    plt.close(fig)
    fig,ax = plt.subplots(figsize=(12,4),constrained_layout=True)
    for name,color in zip(['s1_two','s1_one'],colors[1:]):
        frame = paired_table[paired_table.case.eq(name)]
        ax.plot(frame.ue_id,frame.sinr_change_db,'o',ms=4,color=color,label=LABELS[name])
    ax.axhline(0,color='black',lw=1)
    ax.set(xlabel='Aynı konumdaki sanal kullanıcı kimliği',ylabel='S0’a göre SINR değişimi (dB)',
           title='Aynı kullanıcı konumlarında sektör azaltmanın etkisi')
    ax.legend()
    ax.grid(alpha=.25)
    fig.savefig(HERE/'paired_sinr_change.png',dpi=170)
    plt.close(fig)
    lines = [
        '# İki sahada sektör sayısı deneyi',
        '',
        'Hocanın kırmızı notu: “cell sayısına bakmadan 3 sektöre böldüm ama bakılması lazım.” '
        'Üç sektör, hocanın ilk örnekte kullandığı ve incelenmesini istediği başlangıç varsayımıdır.',
        '',
        'İki hücre gözlenen ana sahalar **SITE_000482 ve SITE_000554** üzerinde üç, iki ve bir '
        'etkin sektör denendi. Diğer 22 saha üç sektörlü kaldı. 24 saha, aynı 64 kullanıcı, '
        'aynı yayılım modeli, seed, frekans, 4 saniyelik süre ve düşük UDP probu kullanıldı.',
        '',
        'Özgün üç sektörlü sonuç yeni kodla yeniden üretildi; alternatifler başlamadan önce '
        f"64 kullanıcının karşılaştırılan sonuçları doğrulandı (en büyük fark: {result['regression']['max_numeric_difference']:.10g}). "
        'Ana projenin C++ kaynağı ve sabit başlangıç senaryosu değiştirilmedi.',
        '',
        '## Sonuç tablosu',
        '',
        '| Durum | Toplam sektör | Bağlanan / DL alan UE | RSRP üreten ana saha | Ana saha RSRP MAE | Ana saha SINR MAE | Kontrol SINR MAE |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for row in summaries:
        lines.append(f"| {row['label']} | {row['sectors']} | {row['connected']}/64 — {row['receiving_dl']}/64 | "
                     f"{row['sites_with_rsrp']}/8 | {row['all_rsrp_mae_db']:.2f} dB | {row['all_sinr_mae_db']:.2f} dB | {row['holdout_sinr_mae_db']:.2f} dB |")
    lines += ['', '**Bu pilot sektör azaltmayı bir iyileştirme olarak benimsemek için destek vermedi.** '
              'İki alternatifte de aynı 64 kullanıcının ortalama SINR değişimi negatiftir; '
              'ayrılmış kontrol sahalarının SINR hatası başlangıca göre büyümüştür. '
              'Bir sektörlü koşuda 554 sahası hiç kullanıcıya hizmet vermediği için saha '
              'hata ortalaması yalnız yedi sahaya dayanır. Bu düşük ortalama sekiz sahalık '
              'başlangıçla başarı sıralaması yapmak için kullanılamaz.', '',
              'Eksik saha sayısı ve metrik ayrıntıları `summary.csv` içindedir. '
              'Ortalamalar geçerli sonucu olan sahaları kullanır; örneklem kaybı varsa ayrıca değerlendirilmelidir.',
              '', '## Aynı kullanıcıları karşılaştırınca', '']
    for row in summaries[1:]:
        lines.append(f"- **{row['label']}**: {row['paired_sinr_ues']}/64 kullanıcıda eşlenik SINR; "
            f"ortalama değişim {row['mean_paired_sinr_change_db']:+.2f} dB, "
            f"%95 mutlak değişim {row['q95_absolute_sinr_change_db']:.2f} dB; "
            f"aynı hizmet saha/sektörü oranı %{row['same_serving_sector_pct']:.1f}.")
        lines.append(f"  Başlangıçta değiştirilen iki sahadan hizmet alan aynı "
            f"{row['affected_baseline_ue_count']} kullanıcıda ortalama SINR değişimi "
            f"{row['affected_baseline_ue_mean_sinr_change_db']:+.2f} dB oldu.")
    lines += ['', '## Nasıl yorumlanmalı?', '',
        '- Bu bir duyarlılık pilotudur. Ölçümlerdeki iki hücrenin gerçekte bir veya iki sektör olduğunu kanıtlamaz.',
        '- Tek sektör durumu tek bir 65° yönlü antendir; her yöne hizmet veren antene dönüştürülmedi. '
        'Kalan yönler ilk sektörlerdir: 0; veya 0 ve 1. Diğer yön seçimi/azimutlar denenmedi.',
        '- Kalan antenlerin gücü değişmedi; sektör kaldırılınca toplam saha gücü ve bazı yönlerde kapsama azalır. '
        'Bu nedenle girişim azalması ve istenen sinyal kaybı birlikte gerçekleşebilir.',
        '- Kullanıcı başka sahaya geçerse saha ortalamasına giren kullanıcılar değişir. '
        'Bu yüzden saha hataları yanında aynı 64 konumdaki eşlenik farklar da verildi.',
        '- Bütün durumlar tek taşıyıcılı ve aynı frekansta. Gerçek çok taşıyıcılı S2 hipotezi uygulanmadı.',
        '- Sekiz saha daha önce görüldü; bu yeni bir kör doğrulama veya yeni başlangıç senaryosu seçimi değildir.',
        '- SITE_000554 konumunun ana envanterdeki kaynak belirsizliği devam ediyor. '
        'Bu koşullarda komşu saha yakınsaması yeniden sınanmadı; sonuçlar mevcut 24 saha içindir.',
        '- Bu kısa UDP probu bir yük veya kapasite deneyi değildir.',
        '', '## Görseller', '',
        '![Saha bazında karşılaştırma](sector_comparison.png)', '',
        '![Aynı kullanıcıların SINR değişimi](paired_sinr_change.png)', '',
        '## Tekrar üretim', '',
        'Proje kökünde Windows Python ile `deneyler/01_sektor_sayisi_2026-11-10/prepare.py`; '
        'ardından Ubuntu-22.04 Python ile `run_experiment.py`; son olarak Windows proje Python ile `report.py` çalıştırılır. '
        'Girdiler ve C++ kaynak hash’leri `experiment_plan.json` içinde, ham çıktılar `simulation/results/` altındadır.']
    (HERE/'SONUCLAR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(summary[['case','all_rsrp_mae_db','all_sinr_mae_db','holdout_sinr_mae_db',
                   'connected','receiving_dl','same_serving_sector_pct']].to_string(index=False))


if __name__ == '__main__':
    main()
