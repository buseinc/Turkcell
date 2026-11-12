"""Compare definitions, passive control references, and CQI feedback outcomes."""
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
    study=json.loads((HERE/'study_result.json').read_text())
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    assert study['completed'] and study['control_regression']['passed']
    assert hashlib.sha256((PROJECT/'simulation/sindirgi_baseline.cc').read_bytes()).hexdigest()==plan['original_cpp_sha256']
    targets=pd.read_csv(PROJECT/'analysis/sindirgi/radio_study/measured_site_targets.csv').set_index('site')
    summaries=[];site_frames=[];ue_frames=[];sample_frames=[]
    checks={'control_regression':study['control_regression'],'original_baseline_unchanged':True}
    for case in study['cases']:
        name=case['name']
        samples=pd.read_csv(HERE/'simulation/results'/name/'sinr_components.csv')
        final=pd.read_csv(HERE/'simulation/results'/name/'ues.csv').set_index('ue_id').synthetic_cell_id
        samples=samples[samples.time_s.ge(1)&samples.synthetic_cell_id.eq(samples.ue_id.map(final))].copy()
        assert samples.ue_id.nunique()==64
        reconstructed='control_sinr_db' if name=='control' else 'reconstructed_mixed_sinr_db'
        error=float((samples.native_sinr_db-samples[reconstructed]).abs().max())
        assert error<1e-6,(name,error)
        checks[name+'_native_reconstruction_max_error_db']=error
        samples['case']=name
        sample_frames.append(samples)
        ue=pd.DataFrame(case['metrics']['ues']).set_index('ue_id')
        ue=ue.join(samples.groupby('ue_id').agg(control_reference_db=('control_sinr_db','mean'),
            snr_db=('snr_db','mean'),fresh_data_fraction=('data_interference_fresh','mean')))
        ue['case']=name
        ue_frames.append(ue.reset_index())
        sites=targets.join(pd.DataFrame.from_dict(case['metrics']['sites'],orient='index'))
        sites['case']=name
        for metric in ['rsrp','sinr','rsrq']:
            sites[metric+'_error_db']=sites[metric]-sites[metric+'_target']
        site_frames.append(sites.reset_index())
        row={'case':name,'connected':case['result']['connected_ues'],
             'receiving_dl':case['result']['ues_receiving_dl'],'total_dl_bytes':case['result']['total_dl_bytes'],
             'median_native_ue_sinr_db':float(ue.sinr.median()),
             'median_passive_control_sinr_db':float(ue.control_reference_db.median()),
             'fresh_data_sample_pct':float(100*samples.data_interference_fresh.mean()),
             'no_fresh_data_sample_pct':float(100*(1-samples.data_interference_fresh.mean())),
             'native_equals_snr_sample_pct':float(100*np.isclose(samples.native_sinr_db,samples.snr_db,atol=1e-6,rtol=0).mean()),
             'valid_sites':int(sites.sinr.notna().sum())}
        for metric in ['rsrp','sinr','rsrq']:
            row['all_'+metric+'_mae_db']=float(sites[metric+'_error_db'].abs().mean())
            row['holdout_'+metric+'_mae_db']=float(sites.loc[sites.split.eq('holdout'),metric+'_error_db'].abs().mean())
        summaries.append(row)
    ue_table=pd.concat(ue_frames,ignore_index=True)
    sites_table=pd.concat(site_frames,ignore_index=True)
    sample_table=pd.concat(sample_frames,ignore_index=True)
    a=ue_table[ue_table.case.eq('control')].set_index('ue_id')
    b=ue_table[ue_table.case.eq('mixed')].set_index('ue_id')
    assert a.index.equals(b.index)
    assert a.site.eq(b.site).all() and a.sector.eq(b.sector).all()
    checks['same_serving_sectors']=True
    checks['max_passive_control_sinr_change_db']=float((a.control_reference_db-b.control_reference_db).abs().max())
    checks['max_rsrp_change_db']=float((a.rsrp-b.rsrp).abs().max())
    checks['max_rsrq_change_db']=float((a.rsrq-b.rsrq).abs().max())
    assert checks['max_passive_control_sinr_change_db']<1e-6
    assert checks['max_rsrp_change_db']<1e-6
    assert checks['max_rsrq_change_db']<1e-6
    checks['mean_paired_native_sinr_change_db']=float((b.sinr-a.sinr).mean())
    checks['passed']=True
    pd.DataFrame(summaries).to_csv(HERE/'summary.csv',index=False)
    ue_table.to_csv(HERE/'ue_comparison.csv',index=False)
    sites_table.to_csv(HERE/'site_comparison.csv',index=False)
    sample_table.to_csv(HERE/'sample_comparison.csv',index=False)
    (HERE/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
    ids=a.index
    axes[0].plot(ids,a.sinr,'o',ms=4,label='Kontrol: raporlanan SINR',color='#0072b2')
    axes[0].plot(ids,b.sinr,'o',ms=4,label='Mixed: raporlanan SINR',color='#d55e00')
    axes[0].plot(ids,b.control_reference_db,'x',ms=4,label='Mixed koşusunda pasif kontrol SINR',color='black')
    axes[0].set(xlabel='Aynı konumdaki kullanıcı kimliği',ylabel='SINR (dB)',title='Yöntem değişimi ve aynı fiziksel kontrol referansı')
    axes[0].legend(fontsize=7)
    x=np.arange(len(targets))
    axes[1].plot(x,targets.sinr_target,'ko-',label='Experia saha özeti')
    for name,color,label in [('control','#0072b2','Kontrol'),('mixed','#d55e00','Mixed')]:
        frame=sites_table[sites_table.case.eq(name)].set_index('site').reindex(targets.index)
        axes[1].plot(x,frame.sinr,'o--',color=color,label=label)
    axes[1].set_xticks(x,[s.replace('SITE_','') for s in targets.index],rotation=50)
    axes[1].set(ylabel='Saha SINR ortalaması (dB)',title='Tanımları eşdeğerliği doğrulanmamış karşılaştırma')
    axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(alpha=.25)
    fig.suptitle('Aynı 24 saha / 72 sektör / 64 UE — düşük UDP yükünde kontrol ve mixed CQI\n'
                 'CQI geri bildirimi de değişir; yakınlık gerçek ağ doğrulaması değildir.',fontsize=11)
    fig.savefig(HERE/'mixed_comparison.png',dpi=170)
    fig.savefig(HERE/'mixed_comparison.svg')
    plt.close(fig)
    print(pd.DataFrame(summaries).to_string(index=False))
    print(json.dumps(checks,indent=2))


if __name__=='__main__':main()
