"""Export stage-3 comparisons and a candid, reproducible conclusion."""
from pathlib import Path
import hashlib
import json
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/sindirgi/radio_study'
RESULTS=ROOT/'simulation/results/stage3'


def figure_save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=170)
    fig.savefig(OUT/(name+'.svg'))
    plt.close(fig)


def main():
    result=json.loads((OUT/'study_result.json').read_text())
    plan=json.loads((OUT/'experiment_plan.json').read_text())
    screens=json.loads((OUT/'screening_checkpoint.json').read_text())
    azimuths=json.loads((OUT/'azimuth_cases.json').read_text())
    target=pd.read_csv(OUT/'measured_site_targets.csv').set_index('site')
    final=result['final']
    # Validate provenance and source-independent output counts before reporting.
    source=ROOT/'simulation/sindirgi_baseline.cc'
    assert final['result']['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
    assert len(screens)==9 and len(azimuths)==3
    metrics=final['metrics'];per_ue=pd.DataFrame(metrics['ues'])
    assert len(per_ue)==64
    assert int(per_ue.connected.sum())==final['result']['connected_ues']
    assert int(per_ue.dl_bytes.sum())==final['result']['total_dl_bytes']
    per_ue.to_csv(OUT/'final_ue_metrics.csv',index=False)
    simulated=pd.DataFrame.from_dict(metrics['sites'],orient='index')
    sites=target.join(simulated,how='left')
    for m in ['rsrp','sinr','rsrq']:sites[m+'_error_db']=sites[m]-sites[m+'_target']
    sites.reset_index().to_csv(OUT/'final_site_comparison.csv',index=False)
    candidates=pd.DataFrame([{'case':c['name'],'placement':c['placement'],'model':c['model']['name'],
        'training_rsrp_mae_db':c['training']['rsrp_mae_db'],
        'missing_training_sites':len(c['training']['missing_sites']),
        'selection_score':c['training']['selection_score'],
        'connected_ues':c['result']['connected_ues'],
        'rsrp_trace_agreement_q95_db':c['metrics']['rsrp_trace_agreement_q95_db'],
        'wall_seconds':c['result']['wall_seconds']} for c in screens])
    candidates.to_csv(OUT/'training_candidates.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,5),constrained_layout=True)
    matrix=candidates.pivot(index='placement',columns='model',values='selection_score')
    image=ax.imshow(matrix.to_numpy(),cmap='YlOrRd')
    for i in range(len(matrix)):
        for j in range(len(matrix.columns)):
            ax.text(j,i,f'{matrix.iloc[i,j]:.2f}',ha='center',va='center')
    ax.set_xticks(range(len(matrix.columns)),matrix.columns)
    ax.set_yticks(range(len(matrix)),matrix.index)
    ax.set_title('Ayar seçimi: yalnızca 5 eğitim sahasının RSRP sonuçları\n'
                 'Puan = saha MAE (dB) + eksik eğitim sahası başına 10; düşük daha iyi')
    fig.colorbar(image,ax=ax,label='Seçim puanı')
    figure_save(fig,'training_comparison')

    fig,axes=plt.subplots(1,3,figsize=(15,5),constrained_layout=True)
    x=np.arange(len(sites))
    for ax,m,label in zip(axes,['rsrp','sinr','rsrq'],['RSRP (dBm)','SINR (dB)','RSRQ (dB)']):
        for i,split in enumerate(sites.split):
            if split=='holdout':ax.axvspan(i-.45,i+.45,color='#fff0df',zorder=0)
        ax.plot(x,sites[m+'_target'],'o-',color='black',label='Experia saha özeti')
        ax.plot(x,sites[m],'s--',color='#0072b2',label='Son simülasyon')
        ax.set_xticks(x,[s.removeprefix('SITE_') for s in sites.index],rotation=60)
        ax.set_ylabel(label);ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Saha düzeyinde karşılaştırma — turuncu arka plan: ayrılmış son kontrol sahaları\n'
                 'SINR/RSRQ ayar seçiminde kullanılmadı; ölçüm örneklemi ve kanal tanımları farklı olabilir.',fontsize=11)
    figure_save(fig,'final_site_comparison')

    checks=pd.DataFrame(result['buffer_checks'])
    checks.to_csv(OUT/'buffer_convergence.csv',index=False)
    fig,axes=plt.subplots(3,1,figsize=(9,9),sharex=True,constrained_layout=True)
    for ax,col,label in [(axes[0],'rsrp_q95_abs_change_db','RSRP değişimi: %95 (dB)'),
                          (axes[1],'sinr_q95_abs_change_db','SINR değişimi: %95 (dB)')]:
        ax.plot(range(len(checks)),checks[col],'o-');ax.axhline(1,color='red',linestyle='--',label='1 dB sınırı')
        ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(fontsize=8)
    axes[2].plot(range(len(checks)),checks.same_serving_sector_fraction,'o-')
    axes[2].axhline(.95,color='red',linestyle='--');axes[2].set_ylabel('Aynı hizmet sektörü oranı')
    axes[2].set_xticks(range(len(checks)),[f'{int(r.from_buffer)} → {int(r.to_buffer)}' for r in checks.itertuples()])
    axes[2].set_xlabel('Komşu saha sayısının artırılması');axes[2].grid(alpha=.2)
    fig.suptitle('Buffer kontrolü: aynı UE konumları ve ortak sahalarda aynı anten yönleri')
    figure_save(fig,'buffer_convergence')

    azrows=[]
    for c in azimuths:
        core=[r for r in c['metrics']['ues'] if r['role']=='Evaluation']
        azrows.append({'azimuth_seed':c['azimuth_seed'],
            'median_rsrp_dbm':pd.Series([r['rsrp'] for r in core],dtype=float).median(),
            'median_sinr_db':pd.Series([r['sinr'] for r in core],dtype=float).median(),
            'connected_ues':c['result']['connected_ues'],
            'serving_gap_q95_db':c['metrics']['serving_gap_q95_db']})
    pd.DataFrame(azrows).to_csv(OUT/'azimuth_sensitivity.csv',index=False)
    azframe=pd.DataFrame(azrows)
    fig,axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for ax,col,label in [(axes[0],'median_rsrp_dbm','Ana sahaların hizmet verdiği UE medyan RSRP (dBm)'),
                          (axes[1],'median_sinr_db','Ana sahaların hizmet verdiği UE medyan SINR (dB)')]:
        ax.plot(range(3),azframe[col],'o-')
        ax.set_xticks(range(3),azframe.azimuth_seed.astype(str))
        ax.set_xlabel('Anten yönü örneklemesi');ax.set_ylabel(label);ax.grid(alpha=.2)
    fig.suptitle('Sabit UE konumlarında azimut duyarlılığı; 3 örneklem güven aralığı değildir',fontsize=10)
    figure_save(fig,'azimuth_sensitivity')
    fig,axes=plt.subplots(1,2,figsize=(12,6),constrained_layout=True)
    topology=pd.read_csv(OUT/'inputs'/f'sites_b{result["selected_buffer_count"]}_az42.csv')
    eval_sites=topology[topology.role=='Evaluation']
    for ax,m,label in [(axes[0],'rsrp','RSRP (dBm)'),(axes[1],'sinr','SINR (dB)')]:
        good=per_ue[per_ue[m].notna()]
        art=ax.scatter(good.x_m/1000,good.y_m/1000,c=good[m],cmap='viridis',s=32)
        fig.colorbar(art,ax=ax,label=label,shrink=.8)
        ax.scatter(eval_sites.x_m/1000,eval_sites.y_m/1000,marker='^',c='black',s=65,label='Ana sahalar')
        no_dl=per_ue[per_ue.dl_bytes==0]
        ax.scatter(no_dl.x_m/1000,no_dl.y_m/1000,marker='x',c='red',s=55,label='Kısa koşuda DL baytı yok')
        ax.set(xlabel='Doğu (km)',ylabel='Kuzey (km)',aspect='equal');ax.grid(alpha=.2)
    axes[0].legend(fontsize=7)
    fig.suptitle('Son koşu: 64 sabit sentetik UE noktasında radyo ölçümleri\n'
                 'Noktalar gerçek UE konumu veya sürekli kapsama sınırı değildir.',fontsize=11)
    figure_save(fig,'final_ue_map')

    archive=ROOT/'simulation/archive'/(final['result']['source_sha256']+'.cc')
    if not archive.exists():archive.write_bytes(source.read_bytes())
    frozen=OUT/'frozen';frozen.mkdir(exist_ok=True)
    for src,dest in [(OUT/'inputs'/f'sites_b{result["selected_buffer_count"]}_az42.csv',frozen/'sites.csv'),
                    (OUT/'inputs'/f'ues_{final["placement"]}.csv',frozen/'ues.csv')]:
        shutil.copyfile(src,dest)
    freeze={'ns3_version':'3.44','case':final['name'],'placement':final['placement'],'model':final['model'],
            'evaluation_sites':8,'buffer_sites':result['selected_buffer_count'],
            'ns3_seed':42,'ns3_run':1,'azimuth_seed':42,'ue_count':64,
            'source_archive':str(archive.relative_to(ROOT)),
            'source_sha256':final['result']['source_sha256'],
            'model_assumptions':final['result']['model_assumptions'],
            'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [frozen/'sites.csv',frozen/'ues.csv']},
            'status':'Checked scenario hypothesis; not certified reconstruction of operator deployment.'}
    (frozen/'configuration.json').write_text(json.dumps(freeze,indent=2),encoding='utf-8')
    train=final['training'];hold=final['holdout'];native=final['result']
    p='geçti' if final['rsrp_holdout_diagnostic_passed'] else 'geçmedi'
    bc='iki ardışık genişletmede eşikler sağlandı' if result['buffer_converged'] else '64 komşuya kadar eşikler iki kez ardışık sağlanmadı'
    duration=result['duration_only_check']
    probe=result['probe_traffic_only_check']
    uncertainty=result['unverified_coordinate_sensitivity']
    hold_sinr_mae=sites.loc[sites.split=='holdout','sinr_error_db'].abs().mean()
    hold_rsrq_mae=sites.loc[sites.split=='holdout','rsrq_error_db'].abs().mean()
    max_site_error=sites.rsrp_error_db.abs().max()
    text=f'''# 3. aşama: radyo karşılaştırması ve duyarlılık kontrolü

Bu aşamadaki deneyler tamamlandı. Bu, gerçek operatör ağının doğrulandığı anlamına gelmez; aşağıda ölçülen uyum ve sınırlar ayrı verilir.

## Ne yapıldı?

- Konumları sabit tutulan 64 kullanıcı cihazıyla (UE) deneyler yapıldı. Üç farklı cihaz yerleşiminin her biri, üç farklı sinyal yayılım modeliyle denendi. Böylece toplam dokuz senaryo karşılaştırıldı.
- 5 saha ayar seçimi, 3 saha son kontrol için ayrıldı. Seçim yalnız eğitim RSRP hatasını kullandı; SINR ve RSRQ ayarlanmadı. İlk S0 analizinde bütün sahalar görülmüştü; bu kontrol yeni arama için ayrılmıştır, kör dış doğrulama değildir.
- Anten yönleri için 42/7/99 örneklemeleri karşılaştırıldı. Komşu eklerken aynı UE konumları ve ortak sahaların anten yönleri korundu. 0,5–2 km ve 1–4 km kümeler ile ana sahaların dışbükey zarfında uniform yerleşim kullanıldı; bunlar gerçek UE dağılımı değildir.
- Komşu saha sayısı artırıldı; son koşu 2 yerine 4 saniye ve küçük UDP trafiğiyle tekrarlandı. Ana envanterde bulunmayan 553/554/555 konumlarını çıkarmanın etkisi ayrıca ölçüldü.
- İki yerel RSRP izi karşılaştırıldı; %95 fark {metrics['rsrp_trace_agreement_q95_db']:.6f} dB. RSRQ ve ölçülen en güçlü hücreye göre hizmet hücresi farkı da kaydedildi.

## Saha ortalamaları nasıl hesaplandı?

Simülasyonda önce her cihazın zaman içindeki geçerli RSRP, SINR ve RSRQ değerlerinin ortalaması alındı. Daha sonra aynı sektöre bağlanan cihazların ortalamaları, her cihaza eşit ağırlık verilerek birleştirildi. Buradaki sektör, simülasyonda sahanın belirli bir yöne hizmet vermesi için oluşturduğumuz anten bölümüdür; gerçek verideki bir hücreyle bire bir eşleştirilmiş değildir.

Sahanın sonucunu bulmak için o sahadaki sektör ortalamalarının ortalaması alındı. Yalnızca cihaz bağlanan ve ilgili metrik için geçerli sonuç üreten sektörler hesaba katıldı. Her sektör saha ortalamasına eşit katkı yaptı. Örneğin bir sektöre iki, diğerine on cihaz bağlansa bile bu iki sektörün ortalamaları saha hesabında eşit ağırlık taşıdı. Cihaz bağlanmayan sektörlere sıfır değeri verilmedi.

Experia verisinde ise önce her hücrenin mevcut saatlik kayıtlarının ortalaması alındı. Ardından aynı sahaya ait hücre ortalamaları, her hücreye eşit ağırlık verilerek birleştirildi. Daha fazla saatlik kaydı bulunan bir hücre, sırf bu nedenle saha ortalamasında daha fazla ağırlık almadı.

Karşılaştırmada bu iki yöntemle hesaplanan saha ortalamaları kullanıldı. Ancak simülasyondaki cihaz konumları varsayımsaldır; Experia kayıtlarının kaç kullanıcıyı ve hangi kullanıcı konumlarını temsil ettiğini bilmiyoruz. Bu nedenle ortalamaların yakın çıkması, gerçek kullanıcıların tamamının aynı sinyal koşullarını yaşadığını göstermez.

## Sonuç

| Gösterge | Sonuç |
|---|---|
| Eğitimden seçilen yerleşim / model | {final['placement']} / {final['model']['name']} |
| Son topoloji | 8 ana + {result['selected_buffer_count']} komşu saha; saha başına 3 sentetik sektör |
| Eğitim RSRP saha MAE | {train['rsrp_mae_db']:.2f} dB |
| Ayrılmış kontrol RSRP saha MAE | {hold['rsrp_mae_db']:.2f} dB |
| Ayrılmış kontrol SINR / RSRQ saha MAE | {hold_sinr_mae:.2f} / {hold_rsrq_mae:.2f} dB; bu metriklerde uyum doğrulanmadı |
| Bütün sahalarda en büyük mutlak RSRP hatası | {max_site_error:.2f} dB; 5 dB hedefi tek tek saha değil ortalama hata içindir |
| Kapsanan eğitim / kontrol sahası | {5-len(train['missing_sites'])}/5 ve {3-len(hold['missing_sites'])}/3 |
| Önceden yazılan 5 dB kontrol hedefi | {p} |
| Son koşuda bağlanan / DL alan UE | {native['connected_ues']}/64 ve {native['ues_receiving_dl']}/64 |
| 4 saniyelik koşunun gerçek çalışma süresi | {native['wall_seconds']:.1f} saniye |
| Buffer kontrolü | {bc} |
| Yalnız süre: 2 saniyeden 4 saniyeye uzatma | RSRP %95 değişim {duration['rsrp_q95_abs_change_db']:.3f} dB; SINR {duration['sinr_q95_abs_change_db']:.3f} dB |
| Yalnız UDP probu: aynı 4 s | RSRP %95 değişim {probe['rsrp_q95_abs_change_db']:.3f} dB; SINR {probe['sinr_q95_abs_change_db']:.3f} dB |
| Belirsiz 3 konum çıkarıldığında | RSRP %95 değişim {uncertainty['rsrp_q95_abs_change_db']:.3f} dB; aynı hizmet sektörü %{100*uncertainty['same_serving_sector_fraction']:.1f} |

5 dB hedefi bir mühendislik tanı eşiğidir; operatör onayı değildir. Buffer için %95 mutlak RSRP/SINR değişimi ≤1 dB ve aynı hizmet sektörü oranı ≥%95 şartları iki ardışık genişletmede arandı. Yakınsama yalnız seçilen model, UE yerleşimi ve azimut örneklemesi için kontrol edildi; yük/konfigürasyon değişirse yeniden sınanmalı. [Deney planı](experiment_plan.json) koşulardan önce yazıldı; süre ve UDP etkisini ayıran ek kontrol sonradan ayrıca belirtildi. [Tam sonuç](study_result.json) hesapları içerir.

## Görseller ve tablolar

- [Yerleşim / model taraması](training_comparison.png), [aday sonuçları](training_candidates.csv).
- [Saha bazında RSRP, SINR, RSRQ](final_site_comparison.png), [sayısal karşılaştırma](final_site_comparison.csv).
- [Buffer yakınsaması](buffer_convergence.png), [tablosu](buffer_convergence.csv), [azimut grafiği](azimuth_sensitivity.png), [azimut tablosu](azimuth_sensitivity.csv).
- [UE noktalarındaki radyo haritası](final_ue_map.png), [UE sonuçları](final_ue_metrics.csv).
- [Dondurulan yapılandırma](frozen/configuration.json), [sahalar](frozen/sites.csv), [UE konumları](frozen/ues.csv).

## Sınırlar ve kullanım

Üç sektör/tek taşıyıcı politikası, düz zemin, bilinmeyen UE örneklemi, anten gücü ve açıları varsayımdır. Shadowing/fading yoktur. COST231 seçeneği kurulu OkumuraHata modelinin 1,5 GHz üstü MediumCity dalıdır; kırsal arazi modeli sayılmaz, kısa/çok uzun bağlantılarda model aralığının dışına taşabilir. SINR kontrol kanalı girişiminden, RSRQ yerel UE ölçüm izinden alınır; Experia'nın kanal/örnekleme tanımlarıyla eşdeğerlik doğrulanmadı. TAAVG mesafeye çevrilmedi, 2025 trafik dönemiyle 2026 radyo dönemi birleştirilmedi.

Kaynakları belirsiz üç koordinatın etkisi raporlandı; bu konumların doğruluğu kanıtlanmış olmadı. Gerçek hücre sınırları veya arızalar çıkarılmadı. Başlangıç senaryosu ve belirsizlik aralığı sonraki kontrollü deneylere girdi sağlar; kalan tanım/envanter soruları hocaya sorulacak.

## Tekrar üretim

Windows Python: `python analysis/prepare_radio_study.py`. İlk derleme: `simulation/run_baseline.py --name stage3/smoke` WSL altında. Ardından WSL Python ile `simulation/run_radio_study.py`; mevcut geçerli sonuçları tekrar kullanır. Son olarak Windows Python: `python analysis/report_radio_study.py`. WSL yolları [simülasyon notunda](../../../simulation/README.md). Plan, girdiler, kaynak hash'leri ve arşivlenen C++ dosyası korunur. Eski S0 sonuçları ayrıca saklandı.
'''
    (OUT/'README.md').write_text(text,encoding='utf-8')
    print(json.dumps({'training_rsrp_mae':train['rsrp_mae_db'],'holdout_rsrp_mae':hold['rsrp_mae_db'],
        'holdout_passed':final['rsrp_holdout_diagnostic_passed'],'buffer':result['selected_buffer_count'],
        'buffer_converged':result['buffer_converged']},indent=2))


if __name__=='__main__':main()
