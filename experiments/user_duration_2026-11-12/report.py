"""Joint sampling, traffic timing and duration diagnosis; no candidate retuning."""
from pathlib import Path
import json,csv,statistics,collections,os,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=HERE.parent/'extended_radio_2026-11-10'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'experiments/radio_joint_search_2026-11-10/matplotlib_cache'))
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
M=['rsrp','sinr','rsrq']
def main():
    data=json.loads((HERE/'result.json').read_text(encoding='utf-8'));assert data['completed']
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    targets=pd.read_csv(OLD/'inputs/targets.csv').set_index('site')
    entries=[]
    for i,r in enumerate(data['baseline_results']):
        entries.append({**r,'case':{'name':f'baseline64_draw_{i}','users':64,'duration':4,'interval_ms':50,'seed':701+i}})
    entries+=data['results'];flat=[];sites=[]
    for r in entries:
        c=r['case'];ue=r['metrics']['ues'];counts=collections.Counter(u['site'] for u in ue)
        row={**c,'connected':r['result']['connected_ues'],'data_users':r['result']['ues_receiving_dl'],
             'min_core_users':min(counts[s] for s in targets.index),'dl_bytes':r['result']['total_dl_bytes']}
        for split in ['training','control']:
            row[split+'_valid']=r[split]['valid_sites']
            for m in M:row[split+'_'+m]=r[split]['mae_db'][m]
        for s,t in targets.iterrows():
            metric=r['metrics']['sites'].get(s,{})
            rec={'case':c['name'],'users':c['users'],'duration':c['duration'],'site':s,'split':t['split'],'ues':counts[s],
                 'active_sectors':metric.get('active_sectors')}
            for m in M:rec[m]=metric.get(m);rec[m+'_target']=t[m+'_target'];rec[m+'_error']=metric.get(m,float('nan'))-t[m+'_target']
            sites.append(rec)
        for m in M:row['max_'+m+'_site_error']=max(abs(s[m+'_error']) for s in sites if s['case']==c['name'])
        if not c['name'].startswith('baseline'):
            folder=OLD/'simulation/results'/('sampling_20261112_'+c['name'])
            samples=pd.read_csv(folder/'sinr_components.csv')
            error=float((samples.native_sinr_db-samples.reconstructed_mixed_sinr_db).abs().max());assert error<1e-6
            row['mixed_check_max_error']=error
            row['no_fresh_data_pct']=100*(1-samples.data_interference_fresh.mean())
            row.update({'original64_'+k:v for k,v in r['paired_original64'].items()})
        flat.append(row)
    frame=pd.DataFrame(flat);frame.to_csv(HERE/'run_summary.csv',index=False)
    site=pd.DataFrame(sites);site.to_csv(HERE/'site_summary.csv',index=False)
    agg=frame[frame.duration.eq(4)].groupby('users')
    means=agg[[s+'_'+m for s in ['training','control'] for m in M]].mean()
    means.to_csv(HERE/'three_draw_means.csv')
    density=site[site.duration.eq(4)]
    coverage=density.groupby(['users','site']).agg(min_users=('ues','min'),max_users=('ues','max'),mean_users=('ues','mean'))
    coverage.to_csv(HERE/'site_coverage.csv')
    fig,axes=plt.subplots(1,3,figsize=(14,4.5),constrained_layout=True)
    for ax,m in zip(axes,M):
        for split,color,label in [('training','#0072b2','Eğitim'),('control','#d55e00','Kontrol')]:
            col=split+'_'+m;std=agg[col].std(ddof=0)
            ax.errorbar(means.index,means[col],yerr=std,marker='o',capsize=4,color=color,label=label)
        ax.set(title=m.upper(),xlabel='Sanal kullanıcı',ylabel='MAE (dB)',xticks=[64,128,256]);ax.grid(alpha=.2)
    axes[0].legend();fig.suptitle('Aynı üç yerleşimin ortalama hataları; çubuklar üç tekrarın standart sapması\nToplam nominal sunulan hız sabit; paket zamanlaması ve kullanıcı başına yük değişir',fontsize=11)
    fig.savefig(HERE/'sampling_comparison.png',dpi=160);plt.close(fig)
    focus=site[site.duration.eq(4)].copy()
    fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
    for n,color in [(64,'#777777'),(128,'#0072b2'),(256,'#d55e00')]:
        subset=focus[focus.users.eq(n)].groupby('site')
        axes[0].plot(range(8),subset.ues.mean().reindex(targets.index),'o-',label=str(n),color=color)
        axes[1].plot(range(8),subset.sinr_error.apply(lambda x:x.abs().mean()).reindex(targets.index),'o-',label=str(n),color=color)
    for ax in axes:ax.set_xticks(range(8),[s.replace('SITE_','') for s in targets.index],rotation=45);ax.grid(alpha=.2);ax.legend(title='Kullanıcı')
    axes[0].set(ylabel='Saha başına kullanıcı (üç örnek ort.)',title='Kullanıcı kapsamı');axes[1].set(ylabel='Saha SINR mutlak hatası (dB)',title='Örneklem arttığında kalan fark')
    fig.savefig(HERE/'site_diagnosis.png',dpi=160);plt.close(fig)
    lines=['# Kullanıcı örneklemi ve süre kontrolü — 12 Kasım 2026','',
        'Güncel 24 saha ve radyo ayarı korundu. 64/128/256 kullanıcı, aynı üç yerleşimde iç içe örneklemlerdir: ilk 64 nokta korunur. Altı yeni 4 s örneklem koşusu ve 64 kullanıcıyla 10/20 s iki süre koşusu yapıldı. Önceki üç 64 kullanıcı koşusu yeniden çalıştırılmadan referans olarak kullanıldı. İlk 1 s ısınma dışlanır.',
        '', '**Trafik kontrolü:** 512 byte UDP, kişi başına 50/100/200 ms aralık; nominal toplam 5,24288 Mbit/s sabit. Toplam hızın sabit olması saha başına yükü, scheduler kararlarını veya paket zamanlamasını aynı tutmaz. Sonlu sürede paket sayıları da biraz değişebilir. Bu nedenle özellikle mixed SINR farkını yalnız daha iyi kullanıcı örneklemesine bağlamıyoruz. Kapasite/stres testi değildir.',
        '', '| Kullanıcı | Eğitim RSRP / SINR / RSRQ MAE | Kontrol RSRP / SINR / RSRQ MAE | Saha başına en az kullanıcı (üç örnekte) |', '|---|---|---|---:|']
    for n,r in means.iterrows():
        t=lambda s:' / '.join(f'{r[s+"_"+m]:.3f}' for m in M)
        lines.append(f'| {n} | {t("training")} | {t("control")} | {int(coverage.loc[n].min_users.min())} |')
    change={m:float(means.loc[256,'control_'+m]-means.loc[128,'control_'+m]) for m in M}
    lines+=['',f'128→256 arasında üç örneğin kontrol MAE değişimi RSRP/SINR/RSRQ: '+ ' / '.join(f'{change[m]:+.3f}' for m in M)+' dB. Negatif, hedefe daha yakın demektir. Bu fark tek tek her sahanın sabit olduğunu göstermez.', '', '## Süre kontrolü', '', '| Süre | Kontrol MAE RSRP / SINR / RSRQ | Son yarıdaki kontrol MAE | 4 s ile aynı64 kullanıcı kontrolü | Tüm pencere / son yarı kontrolü |','|---|---|---|---|---|']
    for r in data['results']:
        if r['case']['duration']<=4:continue
        t=lambda key:' / '.join(f'{r[key]["mae_db"][m]:.3f}' for m in M)
        lines.append(f'| {r["case"]["duration"]} s | {t("control")} | {t("late_control")} | {r["paired_original64"]["passed"]} | {r["whole_vs_late"]["passed"]} |')
    lines+=['', 'Eşli kontroller: kullanıcı RSRP/SINR %95 mutlak değişim≤1 dB ve aynı hizmet sektörü≥%95. Son yarı10 s koşuda5 s,20 s koşuda10 s sonrasıdır. Bunlar yalnız bir yerleşimde süre kontrolleridir; üç bağımsız uzun tekrar değildir. RSRQ değişimi ve saha hata değerleri ayrıca incelenir.', '', '## Hangi sahalarda fark kalıyor?', '']
    diag=density[density.users.eq(256)].copy()
    for m in M:
        worst=diag.groupby('site')[m+'_error'].apply(lambda x:x.abs().mean()).sort_values(ascending=False)
        lines.append(f'- {m.upper()}: 256 kullanıcıda üç örneğin en büyük ortalama mutlak saha hataları '+', '.join(f'{s.replace("SITE_","")}: {v:.2f} dB' for s,v in worst.head(3).items())+'.')
    lines+=['', 'Bu özet en kötü üç sahayı açıklar; kaynak ölçüm tanımlarının eşdeğerliği veya gerçek kullanıcı dağılımı teyit edilmiş değildir. Eksik/kapsanmayan sahalar sıfır hata sayılmaz; kapsam değerleri tabloda ve ham sonuçta tutulur.', '', '[Örneklem grafiği](sampling_comparison.png) — [Saha tanısı](site_diagnosis.png) — [Her koşunun özeti](run_summary.csv) — [Saha bazında tüm değerler](site_summary.csv) — [Saha kapsamı](site_coverage.csv) — [Tam sonuçlar](result.json) — [Önceden kaydedilen plan](plan.json)']
    (HERE/'SONUCLAR.md').write_text('\n'.join(lines),encoding='utf-8')
    print(means.to_string());print('128->256 control delta',change)
    print(frame[['name','users','duration','connected','data_users','min_core_users']].to_string(index=False))
if __name__=='__main__':main()
