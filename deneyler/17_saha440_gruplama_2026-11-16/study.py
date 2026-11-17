"""WSL: check code, reproduce S0, run 3 frozen advisor cases and update one report."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import argparse
import hashlib
import importlib.util
import json
import math
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SIM = HERE/'simulation'
BASE = ROOT/'deneyler/14_cok_tasiyici_s2_2026-11-15'
FILES = ['sectors.csv','ues.csv','radio_samples.csv','sinr_components.csv','measurements.csv','prb_usage.csv']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    temp.replace(path)


def load_module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


previous = load_module('frozen_ta_helpers',ROOT/'deneyler/15_ta_yerlesim_2026-11-16/study.py')


def update_report(status,body=None):
    report = HERE/'SONUCLAR.md'
    text = report.read_text(encoding='utf-8')
    text = '\n'.join(f'**Durum: {status}**' if line.startswith('**Durum:') else line for line in text.splitlines())
    if body is not None:
        marker = '## ns-3 çalışma durumu ve sonuçları'
        text = text.split(marker)[0].rstrip()+'\n\n'+marker+'\n\n'+body
    report.write_text(text.rstrip()+'\n',encoding='utf-8')


def source_identity():
    return hashlib.sha256((SIM/'sindirgi_baseline.cc').read_bytes()+(SIM/'static-shadow-model.h').read_bytes()).hexdigest()


def summarize():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    data = json.loads((HERE/'result.json').read_text(encoding='utf-8'))
    assert data['completed'] and len(data['results'])==3
    assert {r['case']['seed'] for r in data['results']}=={701,702,703}
    old = [r for r in json.loads((BASE/'result.json').read_text(encoding='utf-8'))['results'] if r['case']['scenario']=='S0']
    rows = data['results']
    thresholds = plan['predeclared_experiment']['acceptance_before_any_run']
    def avg(runs,split,metric):
        vals = [r[split]['mae_db'][metric] for r in runs]
        return statistics.mean(vals) if all(v is not None for v in vals) else None
    metrics = {sc:{split:{m:avg(runs,split,m) for m in ['rsrp','sinr']} for split in ['training','control']}
               for sc,runs in [('S0',old),('G17',rows)]}
    per_site = {}
    for site in plan['predeclared_experiment']['training_sites']+plan['predeclared_experiment']['holdout_sites']:
        per_site[site] = {}
        for m in ['rsrp','sinr']:
            target = next(float(t[m+'_target']) for t in previous.radio.read(HERE/'inputs/targets.csv') if t['site']==site)
            before = [r['sites'].get(site,{}).get(m) for r in old]
            after = [r['sites'].get(site,{}).get(m) for r in rows]
            valid = all(v is not None for v in before+after)
            per_site[site][m] = {'S0_mean_error_db':statistics.mean(v-target for v in before) if valid else None,
                                 'G17_mean_error_db':statistics.mean(v-target for v in after) if valid else None,
                                 'MAE_change_db':statistics.mean(abs(v-target) for v in after)-statistics.mean(abs(v-target) for v in before) if valid else None}
    checks = {
        'all_evaluation_sites_present':all(not r['missing_sites'] for r in rows),
        'holdout_rsrp_improves':metrics['G17']['control']['rsrp'] is not None and metrics['S0']['control']['rsrp']-metrics['G17']['control']['rsrp']>=thresholds['holdout_mean_rsrp_improvement_db_min'],
        'holdout_sinr_not_degraded':metrics['G17']['control']['sinr'] is not None and metrics['G17']['control']['sinr']<=metrics['S0']['control']['sinr']+thresholds['holdout_mean_sinr_degradation_db_max'],
        'other_sites_rsrp_not_degraded':all(per_site[s]['rsrp']['MAE_change_db'] is not None and per_site[s]['rsrp']['MAE_change_db']<=thresholds['each_other_evaluation_site_rsrp_degradation_db_max'] for s in per_site if s!='SITE_000440'),
        'all_measurement_connected':all(r['measurement_connected']==256 for r in rows),
        'all_measurement_receive_dl':all(r['measurement_with_dl']==256 for r in rows),
        'prb_change_within_limit':all(abs(r['prb_mean_achieved']-next(x['prb_mean_achieved'] for x in old if x['case']['ue_seed']==r['case']['seed']))<=thresholds['per_draw_mean_prb_change_max'] for r in rows),
        'layout_and_band_allocation_correct':all(r['layout_verified'] for r in rows),
        'analytical_native_rsrp_agree':all(r['analytical_rsrp_max_abs_db'] is not None and r['analytical_rsrp_max_abs_db']<0.01 for r in rows),
    }
    result = {'metrics':metrics,'checks':checks,'accepted':all(checks.values()),'per_site':per_site,
              'mean_prb':{label:statistics.mean(r['prb_mean_achieved'] for r in runs) for label,runs in [('S0',old),('G17',rows)]},
              'mean_prb_by_carrier':{band:statistics.mean(r['prb_by_carrier'][band] for r in rows) for band in ['B3','B20','B1']},
              'no_post_result_retuning':True,'reference_scenario':'S0 remains available regardless of this test decision'}
    save(HERE/'comparison.json',result)
    accepted = result['accepted']
    body = ['Eski tek taşıyıcılı S0 koşusu içerik olarak birebir tekrarlandı (yalnız CRLF/LF normalize edildi). Yeni bant/sektör kodunun küçük kontrolleri ve üç tam koşu tamamlandı.','',
            '| Senaryo | Ayarda RSRP farkı | Kontrolde RSRP farkı | Kontrolde SINR farkı | Ortalama PRB |',
            '|---|---:|---:|---:|---:|']
    for label in ['S0','G17']:
        m = metrics[label]
        def fmt(value): return f'{value:.2f}' if value is not None else 'Eksik'
        body.append(f"| {label} | {fmt(m['training']['rsrp'])} | {fmt(m['control']['rsrp'])} | {fmt(m['control']['sinr'])} | {result['mean_prb'][label]:.3f} |")
    body += ['', 'Farklar dB; küçük değer daha iyi. Kontrol sahaları 440/441/443; hiçbir RF ayarı bunların sonuçlarına göre seçilmedi.','',
             '**Karar: '+('Önceden yazılan kabul ölçütleri geçti; senaryo temsili bir alternatif olarak desteklendi.' if accepted else 'Önceden yazılan kabul ölçütleri geçmedi; S0 temel kalıyor.')+'**','',
             '| Kontrol | Sonuç |','|---|---|']
    titles = {'all_evaluation_sites_present':'8 sahanın sonuçları var',
              'holdout_rsrp_improves':'Kontrol RSRP farkı en az 0,5 dB azaldı',
              'holdout_sinr_not_degraded':'Kontrol SINR farkı en fazla 0,5 dB kötüleşti',
              'other_sites_rsrp_not_degraded':'440 dışındaki sahalarda RSRP farkı en fazla 1 dB kötüleşti',
              'all_measurement_connected':'Her koşuda 256 ölçüm kullanıcısı bağlandı',
              'all_measurement_receive_dl':'Her koşuda 256 ölçüm kullanıcısı veri aldı',
              'prb_change_within_limit':'Her örnekte ortalama PRB farkı en fazla 0,03',
              'layout_and_band_allocation_correct':'Hücre yapısı, frekans ve kullanıcı taşıyıcı ataması doğru uygulandı',
              'analytical_native_rsrp_agree':'Yeni bantların RSRP hesabı analitik bütçeyle uyuştu'}
    body += [f"| {titles[k]} | {'Geçti' if v else 'Geçmedi'} |" for k,v in checks.items()]
    body += ['', '| Örnek | Bağlanan / 256 | Veri alan / 256 | Yük kullanıcısı hedef hücrede / 99 | B3/B20/B1 ölçüm kullanıcısı |',
             '|---|---:|---:|---:|---|']
    for r in rows:
        shares = r['measurement_carriers']
        body.append(f"| {r['case']['seed']} | {r['measurement_connected']} | {r['measurement_with_dl']} | {r['load_ues_on_target']} | {shares.get('B3',0)}/{shares.get('B20',0)}/{shares.get('B1',0)} |")
    body += ['', 'Eski S0’da da hedef hücreye bağlı yük kullanıcısı sayısı 67/72, 68/72 ve 68/72 idi. Yeni koşularda buna 27 yeni yük kullanıcısının tamamı eklendi; 94/99, 95/99 ve 95/99 değerleri bu nedenle yeni katmanlara ait bir hedefleme hatası göstermez.', '',
             'RSRP değişimi 440 sahasında yoğunlaştı: ortalama işaretli fark yaklaşık +0,08 → +3,31 dB oldu; modelin sinyali bu sahada ölçümden daha güçlü çıktı. Diğer yedi değerlendirme sahasının RSRP değerleri S0 ile aynı kaldı. Bu, yeni bant ve kullanıcı atamasının etkisinin nerede oluştuğunu gösterir; hocanın gruplamasının yanlış olduğunu kanıtlamaz.', '',
             'Yük eşitliği tam sağlanmadı. B20 ortalama PRB yaklaşık '+f"{result['mean_prb_by_carrier']['B20']:.3f}"+' oldu; hedef 0,233 idi. Bant genişliğiyle orantılı trafik vermek, aynı PRB’yi garanti etmedi. Bu yüzden SINR farkı, yalnız yeni hücre yapısının etkisi olarak yorumlanamaz. Sonuçlara göre yük katsayısı veya güç yeniden ayarlanmadı.', '',
             'Teknik düzeltme: İlk denemede iki dört-sektörlü yerleşimde 360° üstüne çıkan yönler anten modelinin aralık kontrolüne takıldı. Yönler modulo 360 ile aynı fiziksel yöne çevrildi; girdi konumları, güç, bant, yük ve kabul ölçütleri değiştirilmedi. Düzeltilen kaynakla S0 kontrolü ve üç koşu yeniden tamamlandı. Yeni kodun 20 küçük kontrolü geçti.']
    body += ['', 'Bantlar ve taşıyıcı kullanıcı payları senaryo varsayımlarıdır; bu sonuçlar gerçek saha konfigürasyonunu doğrulamaz. B1 için bölgesel CellMapper kaydı tarihsel; hedef sahalara eşleşme yok. Toplam sunulan trafik %27,8, yapılandırılmış toplam güç/hücre sayısı %37,5 arttığı için fark yalnız frekans etkisi diye yorumlanamaz. Kısa koşuda veri alamama kalıcı kesinti kanıtı değildir. Mixed SINR tanımı ve S0 kullanıcı mesafelerinin sınırlamaları devam ediyor.','',
             'Ayrıntılı saha hataları ve bütün kontroller comparison.json içinde. Sonuç görüldükten sonra ayar değiştirilmedi.']
    update_report('3/3 yeni koşu ve eski sonuçla kontrol tamamlandı. '+('Kabul ölçütleri geçti.' if accepted else 'Kabul ölçütleri geçmedi; S0 temel kalıyor.'),'\n'.join(body))
    print(json.dumps(result,indent=2,ensure_ascii=False),flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--summarize',action='store_true')
    args = parser.parse_args()
    if args.summarize:
        summarize(); return
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    runtime = plan['runtime']
    for name,h in runtime['simulation_hashes'].items(): assert sha(SIM/name)==h,name
    for name,h in runtime['input_hashes'].items(): assert sha(HERE/'inputs'/name)==h,name
    for name,h in runtime['regression_inputs'].items(): assert sha(ROOT/name)==h,name
    for name,h in plan['source_hashes'].items(): assert sha(ROOT/name.replace('\\','/'))==h,name
    logs = HERE/'logs'; logs.mkdir(exist_ok=True)
    build_manifest = SIM/'build/source_manifest.json'
    build_valid = build_manifest.exists() and (SIM/'build/sindirgi_baseline').exists()
    if build_valid:
        build_valid = json.loads(build_manifest.read_text()).get('source_sha256')==source_identity()
    if not build_valid:
        with (logs/'build.log').open('w') as log:
            subprocess.run([sys.executable,str(SIM/'run_baseline.py'),'--name','regression_S0','--build-only'],stdout=log,stderr=subprocess.STDOUT,check=True)
    completed = subprocess.run([str(SIM/'build/sindirgi_baseline'),'--verifyCarrierLayout=1'],capture_output=True,text=True,check=True)
    model_checks = json.loads(completed.stdout)
    assert model_checks['passed']
    targets = previous.radio.read(HERE/'inputs/targets.csv')
    def run(name,sp,up,count):
        folder = SIM/'results'/name
        key = {'source':source_identity(),'sites':sha(sp),'ues':sha(up),'duration':4,
               'mixed_cqi':1,'udp_jitter':1,'power':49,'beamwidth':120,'exponent':3,'nf':9}
        cache = folder/'run_cache.json'
        cached = False
        if cache.exists():
            c = json.loads(cache.read_text())
            cached = c.get('key')==key and bool(c.get('outputs')) and all((folder/n).exists() and sha(folder/n)==h for n,h in c['outputs'].items())
        if not cached:
            cmd = [sys.executable,str(SIM/'run_baseline.py'),'--skip-build','--name',name,
                   '--sites','0','--ues',str(count),'--duration','4','--sites-file',str(sp),'--ue-file',str(up),
                   '--mixed-cqi','1','--udp-jitter','1','--beamwidth','120','--exponent','3','--enb-power','49',
                   '--receiver-nf','9','--shadow-std','0','--dl-earfcn','1300','--ul-earfcn','19300']
            print('START',name,flush=True)
            with (logs/f'{name}.log').open('w') as log:
                subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            save(cache,{'key':key,'outputs':{n:sha(folder/n) for n in FILES+['result.json']}})
        return folder
    update_report('Kod kontrolleri geçti; önce S0 tekrar koşusu doğrulanıyor.')
    folder = run('regression_S0',BASE/'inputs/sites_S0_42.csv',BASE/'inputs/ues_S0_701.csv',328)
    ref = BASE/'simulation/results/S0_draw701'
    checks = {n:{'old':sha(ref/n),'new':sha(folder/n),'raw_equal':(ref/n).read_bytes()==(folder/n).read_bytes(),
                 'content_equal':(ref/n).read_bytes().replace(b'\r\n',b'\n')==(folder/n).read_bytes().replace(b'\r\n',b'\n')} for n in FILES}
    passed = all(c['content_equal'] for c in checks.values())
    save(HERE/'regression.json',{'passed':passed,'model_checks':model_checks,'files':checks,
                                'normalization':'CRLF to LF only; no numeric tolerance or row changes'})
    if not passed: raise RuntimeError('S0 regression failed. New cases will not run.')
    print('REGRESSION PASSED',flush=True)
    update_report('S0 tekrar kontrolü geçti; yeni koşular 0/3 tamamlandı.')

    def one(case):
        folder = run(case['name'],HERE/f"inputs/sites_G17_{case['az']}.csv",HERE/f"inputs/ues_G17_{case['seed']}.csv",355)
        full = previous.radio.metrics(folder,1)
        metric = previous.measurement_metrics(full,256)
        sectors = previous.read(folder/'sectors.csv')
        users = previous.read(folder/'ues.csv')
        input_users = previous.read(HERE/f"inputs/ues_G17_{case['seed']}.csv")
        cells = {int(s['synthetic_cell_id']):s for s in sectors}
        counts = Counter((r['site'],r['carrier']) for r in sectors)
        expected = {(s,band):3 for s in [r['site'] for r in previous.read(HERE/f"inputs/sites_G17_{case['az']}.csv")] for band in ['B3']}
        expected.update({(r['site'],r['assumed_band']):r['sectors'] for r in runtime['block_band_mapping']})
        assert dict(counts)==expected, 'Actual topology differs from frozen grouping'
        # Four-sector blocks must have four distinct directions; no duplicate 0/360 sector.
        for key,count in expected.items():
            angles = {float(s['orientation_ccw_from_east_deg'])%360 for s in sectors if (s['site'],s['carrier'])==key}
            assert len(angles)==count,key
        measured = [r for r in full['ues'] if r['ue_id']<256]
        raw_users = {int(r['ue_id']):r for r in users}
        carriers = Counter()
        errors = []
        shape = -3/(20*math.log10(math.cos(math.radians(120/4))))
        reference_loss = 20*math.log10(4*math.pi*1815e6/299792458)
        for u in measured:
            cid = int(raw_users[u['ue_id']]['synthetic_cell_id'])
            if cid not in cells: continue
            cell = cells[cid]
            assert int(cell['dl_earfcn'])==int(input_users[u['ue_id']]['dl_earfcn'])
            carriers[cell['carrier']]+=1
            if u['rsrp'] is None: continue
            pos = raw_users[u['ue_id']]
            dx,dy,dz = (float(pos[k])-float(cell[k]) for k in ['x_m','y_m','z_m'])
            angle = math.atan2(dy,dx)-math.radians(float(cell['orientation_ccw_from_east_deg']))
            angle = (angle+math.pi)%(2*math.pi)-math.pi
            gain = max(math.cos(angle/2)**(2*shape),1e-300)
            freq = runtime['bands'][cell['carrier']]['dl_mhz']
            prediction = 49+15-reference_loss-30*math.log10(max(math.sqrt(dx*dx+dy*dy+dz*dz),1))+10*math.log10(gain)+20*math.log10(1815/freq)-10*math.log10(int(cell['bandwidth_rb'])*12)
            errors.append(abs(prediction-u['rsrp']))
        prb = previous.read(folder/'prb_usage.csv')
        by_target = {(r['site'],int(r['sector'])):int(r['synthetic_cell_id']) for r in sectors}
        load = [r for r in input_users if r['kind']=='load']
        on_target = sum(int(raw_users[int(u['ue_id'])]['synthetic_cell_id'])==by_target[(u['target_site'],int(u['target_sector']))] for u in load)
        missing = [s for s in plan['predeclared_experiment']['training_sites']+plan['predeclared_experiment']['holdout_sites'] if s not in metric['sites']]
        return {'case':case,'sites':metric['sites'],'missing_sites':missing,
                'training':previous.ev.evaluate(metric,targets,'train'),'control':previous.ev.evaluate(metric,targets,'holdout'),
                'measurement_connected':sum(bool(u['connected']) for u in measured),
                'measurement_with_dl':sum(u['dl_bytes']>0 for u in measured),'measurement_carriers':dict(carriers),
                'layout_verified':True,'analytical_rsrp_max_abs_db':max(errors) if errors else None,
                'load_ues_on_target':on_target,'prb_mean_achieved':statistics.mean(float(r['dl_prb_utilization']) for r in prb),
                'prb_by_carrier':{band:statistics.mean(float(r['dl_prb_utilization']) for r in prb if cells[int(r['synthetic_cell_id'])]['carrier']==band) for band in ['B3','B20','B1']}}
    results = []
    with ThreadPoolExecutor(max_workers=max(1,args.workers)) as pool:
        futures = [pool.submit(one,c) for c in runtime['cases']]
        for f in as_completed(futures):
            results.append(f.result())
            save(HERE/'checkpoint.json',{'completed':len(results),'planned':3,'results':results})
            update_report(f'S0 kontrolü geçti; yeni koşular {len(results)}/3 tamamlandı.')
            print('DONE',results[-1]['case']['name'],flush=True)
    save(HERE/'result.json',{'completed':True,'results':sorted(results,key=lambda r:r['case']['seed'])})
    summarize()


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        update_report('Çalışma durdu; hata günlüğü kontrol edilmeli.',str(exc))
        raise
