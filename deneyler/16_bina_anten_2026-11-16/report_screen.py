"""Report analytical results after freezing selection; native results remain separate."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from screen import received_power_w, site_values, vertical_loss

HERE = Path(__file__).resolve().parent
D15 = HERE.parent/'15_ta_yerlesim_2026-11-16'


def main():
    if (HERE/'comparison.json').exists():
        raise RuntimeError('Native results already exist; preserve the unified SONUCLAR.md report.')
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    screening = json.loads((HERE/'screening.json').read_text(encoding='utf-8'))
    targets = pd.read_csv(HERE/'inputs/targets.csv').set_index('site').rsrp_target
    summaries = {}
    candidates = [dict(label='TA_unchanged',indoor_loss_db=0,downtilt_deg=0,vertical_pattern=0)]+screening['native_candidates']
    for candidate in candidates:
        maes = {'training':[],'holdout':[]}
        site_draws = []
        for az,seed in plan['draws']:
            sectors = pd.read_csv(D15/'simulation/results'/f'S0TA_draw{seed}'/'sectors.csv')
            points = pd.read_csv(HERE/'inputs'/f'ues_S0TA_{seed}.csv').iloc[:256][['x_m','y_m','z_m']].to_numpy()
            power = received_power_w(points,sectors)
            loss = candidate['indoor_loss_db']
            if candidate['vertical_pattern']:
                loss = loss+vertical_loss(points,sectors,candidate['downtilt_deg'])
            values = site_values(power*10**(-loss/10),sectors)
            site_draws.append(values.reindex(targets.index))
            for split,sites in [('training',plan['train_sites']),('holdout',plan['holdout_sites'])]:
                assert values.reindex(sites).notna().all()
                maes[split].append(float((values.reindex(sites)-targets.reindex(sites)).abs().mean()))
        summaries[candidate['label']] = {
            'mae_db':{split:float(np.mean(values)) for split,values in maes.items()},
            'by_draw_db':maes,
            'site_signed_error_db':(pd.concat(site_draws,axis=1).mean(axis=1)-targets).to_dict()}
    result = {'kind':'analytical_only_not_ns3_validation','selection_unchanged':screening['winner'],'summaries':summaries}
    (HERE/'analytical_comparison.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    grid = pd.DataFrame(screening['grid']).pivot(index='indoor_loss_db',columns='downtilt_deg',values='training_rsrp_mae_db')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig,ax = plt.subplots(figsize=(7,4.6))
    im = ax.imshow(grid.to_numpy(),cmap='YlOrRd',aspect='auto')
    ax.set_xticks(range(len(grid.columns)),grid.columns)
    ax.set_yticks(range(len(grid.index)),grid.index)
    ax.set_xlabel('Aşağı eğim (derece)')
    ax.set_ylabel('Ölçüm kullanıcılarına ek kayıp (dB)')
    ax.set_title('Ön tarama: 5 sahada ortalama sinyal gücü farkı\n3 örnek; dikey desen 10°; küçük değer daha iyi')
    for i,row in enumerate(grid.to_numpy()):
        for j,value in enumerate(row):
            ax.text(j,i,f'{value:.2f}',ha='center',va='center',color='black' if value<10 else 'white')
    fig.colorbar(im,ax=ax,label='RSRP farkı (dB)')
    fig.tight_layout()
    fig.savefig(HERE/'on_tarama.png',dpi=160)
    plt.close(fig)
    lines = ['# Deney 16 — bina kaybı ve dikey anten deseni','',
             '**Durum: analitik ön tarama tamamlandı; ns-3 doğrulaması henüz yapılmadı.**', '',
             'Önceki deneylerin girdileri aynen kopyalandı. TA yerleşimi, güç, yük ve diğer radyo ayarları korundu. Karar kuralları koşudan önce plan.json dosyasına yazıldı.', '',
             '## Hızlı hesabın kontrolü', '',
             'Ek etkiler kapalıyken 3 eski TA koşusunun toplam 768 ölçüm kullanıcısında bağlantı hücreleri birebir aynı çıktı. En büyük RSRP farkı 0,000000006 dB altındaydı. Bu kontrol yalnız eski durumun analitik RSRP hesabını doğrular; yeni C++ kodunun çalıştığını doğrulamaz.', '',
             '## Seçim ve sonuç', '',
             '0/6/12/18 dB bina kaybı ile 0/3/6/9 derece eğim, 3 örneğin tamamında tarandı. Dikey desen genişliği 10 derece, en fazla zayıflatma 20 dB olarak sabitlendi. Bunlar operatör ayarları değil, bu deneyin varsayımlarıdır.', '',
             'Yalnız ayarda kullanılan 5 saha ile seçilen aday: **6 dB ek kayıp, 0 derece eğim, dikey desen açık.** Kontrol sahaları aday seçiminde kullanılmadı. Aday dondurulduktan sonra aşağıdaki kontrol hesabı yapıldı.', '',
             '| Analitik senaryo | Ayarda kullanılan 5 sahada RSRP farkı | Diğer 3 sahada RSRP farkı |',
             '|---|---:|---:|']
    labels = {'TA_unchanged':'TA yerleşimi, ek etki yok','combined':'6 dB + dikey desen, 0°',
              'indoor_only':'Yalnız 6 dB','vertical_only':'Yalnız dikey desen, 0°'}
    for name,summary in summaries.items():
        lines.append(f"| {labels[name]} | {summary['mae_db']['training']:.2f} dB | {summary['mae_db']['holdout']:.2f} dB |")
    base,winner = summaries['TA_unchanged']['mae_db'],summaries['combined']['mae_db']
    if winner['holdout']>base['holdout']:
        lines += ['', '**İlk bulgu:** Seçilen aday ayarda kullanılan sahaları iyileştirse de diğer 3 sahada uyumu bozuyor. Bu nedenle bina kaybı ve basit dikey desenin sorunu çözdüğü söylenemez. Sonuç görüldükten sonra ayar değiştirilmedi.']
    lines += ['', '0 derece seçilmesi, gerçek antenlerin eğimsiz olduğunu göstermez. Bu basit model ve tarama aralığında aşağı eğim eklemek ayar sahalarının RSRP hatasını azaltmadı.', '',
              'TA saatlik bir ortalamadır; kullanıcı yönleri bilinmiyor. Kullanıcıların komşu sahalara bağlanması, tek frekans varsayımı ve saha yapısı hâlâ sınırlardır. Bina kaybı bütün ölçüm kullanıcılarına uygulanan etkili bir kayıp varsayımıdır; kullanıcıların gerçekten bina içinde olduğunu kanıtlamaz.', '',
              '## ns-3 aşaması', '',
              'Yeni C++ kodunda iki etki ayrı ayrı açılabilir. Bina kaybı yalnız ilk 256 ölçüm kullanıcısına, bütün eNB bağlantılarında uygulanır; yapay yük kullanıcılarına uygulanmaz. Dikey desen tüm eNB–UE bağlantılarını etkiler. Her iki etki hem aşağı hem yukarı yönlü bağlantıda uygulanır.', '',
              'Önce etkiler kapalı bir tam koşu eski TA koşusuyla 6 CSV dosyasında bayt düzeyinde karşılaştırılacak. Geçmeden aday koşuları başlamaz. Sonra seçilen aday ve iki ayrı etki, 3 örnekle çalıştırılır. SINR, bağlantı, veri alma ve gerçekleşen yük ayrıca sınanır.', '',
              'İlk denemede WSL yanıt vermedi. Yönetici yetkisiyle WSL hizmeti yeniden başlatılınca Ubuntu-22.04, Python ve ns-3.44 erişimi doğrulandı. Yeni C++ kodu derlendi; yalıtılmış bağlantı testlerinin 12 kontrolü geçti. Tam eski koşu karşılaştırması başlatıldı; bu rapor yazılırken henüz tamamlanmadı. Aday koşuları bu karşılaştırma geçerse otomatik başlar. Güncel kayıtlar: environment_status.json, regression.json ve checkpoint.json. Tamamlanan sonuçlar yine bu raporda yer alacak.', '',
              'WSL çalıştığında proje kökünde:', '',
              '```powershell',
              '.venv/Scripts/python.exe -X utf8 deneyler/16_bina_anten_2026-11-16/run_windows.py',
              '# Gerekirse dağıtımı açıkça seç: --distro Ubuntu-22.04 veya --distro Ubuntu',
              '```', '',
              'Girdiler zaten donduruldu; prepare.py tekrar çalıştırılmaz. screen.py tekrar üretilebilir; report_screen.py tamamlanmış nihai raporun üzerine yazmayı reddeder. Native sonuçlar tamamlandığında bu SONUCLAR.md raporu güncellenir ve comparison.json yazılır. Mevcut S0 temel senaryosu korunur.', '',
              'Model başvurusu: [ns-3.44 Model Library](https://www.nsnam.org/docs/release/3.44/models/ns-3-model-library.pdf). Yeni dikey kayıp, mevcut yatay antenin üstüne eklenen açık formüllü deney varsayımıdır; ns-3 stok anteninin tam 3 boyutlu operatör modeli olduğu iddia edilmez.']
    (HERE/'SONUCLAR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
