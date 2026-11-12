from pathlib import Path
import json,statistics,hashlib,os,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=HERE.parent/'extended_radio_2026-11-10'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'experiments/radio_joint_search_2026-11-10/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    study=json.loads((HERE/'result.json').read_text(encoding='utf-8'));assert study['completed']
    rows={r['case']['name']:r for r in study['results']}
    keys=['updated_24','updated_draw_1','updated_draw_2'];metrics=['rsrp','sinr','rsrq']
    old=json.loads((OLD/'study_result.json').read_text());oldrows=[r for r in old['ensemble'] if r['case']['model_id']=='reference']
    average=lambda rr,split:{m:statistics.mean(r[split]['mae_db'][m] for r in rr) for m in metrics}
    selected=[rows[k] for k in keys]
    summary={'current_24_three_draws':{split:average(selected,split) for split in ['training','control']},
        'previous_24_three_draws':{split:average(oldrows,split) for split in ['training','control']},
        'all_three_old_new_pairs_pass':all(r['paired_previous']['passed'] for r in selected),
        'two_expansions_pass':all(c['passed'] for c in study['buffer_checks'] if c['from_sites']>=24),
        'minimum_connected':min(r['result']['connected_ues'] for r in study['results']),
        'minimum_receiving_dl':min(r['result']['ues_receiving_dl'] for r in study['results']),
        'training_site_observations':sum(r['training']['valid_sites'] for r in selected),
        'control_site_observations':sum(r['control']['valid_sites'] for r in selected)}
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),constrained_layout=True)
    for i,m in enumerate(metrics):
        axes[0].bar(i-.18,summary['previous_24_three_draws']['control'][m],width=.35,color='#777777',label='Önceki envanter' if i==0 else None)
        axes[0].bar(i+.18,summary['current_24_three_draws']['control'][m],width=.35,color='#0072b2',label='Güncel envanter' if i==0 else None)
    axes[0].set_xticks(range(3),['RSRP','SINR','RSRQ']);axes[0].set(ylabel='Kontrol MAE (dB)',title='Aynı üç kullanıcı/anten örneğinin ortalaması');axes[0].legend()
    checks=study['buffer_checks'];axes[1].bar(range(3),[r['sinr_q95_abs_change_db'] for r in checks],color='#009e73')
    axes[1].axhline(1,color='red',ls='--',label='Önceden kullanılan 1 dB sınırı')
    axes[1].set_xticks(range(3),[f"{r['from_sites']} → {r['to_sites']}" for r in checks]);axes[1].set(ylabel='Kullanıcı SINR değişimi, %95 yüzdelik (dB)',title='Güncel envanterde komşu genişletmeleri');axes[1].legend(fontsize=8)
    fig.suptitle('Hocanın 8 ana + 8 komşu sahası korunarak güncel envanter kontrolü\n4 saniyelik düşük yük koşuları; 64 sanal kullanıcı',fontsize=12)
    for a in axes:a.grid(axis='y',alpha=.2)
    fig.savefig(HERE/'guncel_karsilastirma.png',dpi=160);plt.close(fig)
    text=['','## Güncel 24 saha: üç ortak tekrar özeti','','| Kontrol MAE (dB) | Önceki envanter | Güncel envanter |','|---|---:|---:|']
    for m in metrics:text.append(f"| {m.upper()} | {summary['previous_24_three_draws']['control'][m]:.3f} | {summary['current_24_three_draws']['control'][m]:.3f} |")
    text+=['',f"Eski–yeni eşli karşılaştırmaların üçü de geçti: {summary['all_three_old_new_pairs_pass']}. 24→32→48 iki genişletme geçti: {summary['two_expansions_pass']}. Tüm yedi koşuda en az {summary['minimum_connected']}/64 bağlı ve {summary['minimum_receiving_dl']}/64 veri alan kullanıcı. Üç tekrarda eğitim kapsamı {summary['training_site_observations']}/15, kontrol {summary['control_site_observations']}/9.", '', 'Bu çalışma eski seçilen ayarı yeniden sınar; bütün alternatiflerin yeni envanterde sıralamasını yeniden ölçmez. Önceki tam taramanın tekrarlanmasını gerektirecek büyük bir etki olup olmadığı eşli kontrollerle değerlendirilir. Yeni koşular 4 s olduğundan eski 8 s sonucu güncel envanterin sonucu olarak sunulmaz.', '', '[Karşılaştırma grafiği](guncel_karsilastirma.png) — [Sayısal özet](summary.json)']
    if summary['all_three_old_new_pairs_pass'] and summary['two_expansions_pass']:
        text+=['','**Karar:** Seçilen ayarla güncel 24 sahayı çalışma başlangıcı olarak korumak destekleniyor. Bu sınırlı güncelleme için bütün eski ayar taramasını tekrarlamak gerekmiyor. Sonraki adım kullanıcı örneklemi duyarlılığı; radyo tanımı ve yük modeli soruları devam ediyor.']
    p=HERE/'SONUCLAR.md';s=p.read_text(encoding='utf-8');s=s.split('\n## Güncel 24 saha:')[0];p.write_text(s+'\n'.join(text),encoding='utf-8')
    frozen=HERE/'selected_scenario';frozen.mkdir(exist_ok=True)
    shutil.copy2(HERE/'inputs/sites_24_42.csv',frozen/'sites.csv');shutil.copy2(OLD/'inputs/ues_far_701.csv',frozen/'ues.csv')
    (frozen/'configuration.json').write_text(json.dumps({'case':rows['updated_24']['case'],'model_assumptions':rows['updated_24']['result']['model_assumptions'],'inventory_sha256':study['inventory_sha256'],'summary':summary,'source_result':'../result.json','files':{n:hashlib.sha256((frozen/n).read_bytes()).hexdigest() for n in ['sites.csv','ues.csv']}},indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
