"""WSL: load-only pilot calibration, frozen rate, two independent validations, one report."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import csv
import hashlib
import importlib.util
import json
import math
import shutil
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D17 = HERE.parent/'17_saha440_gruplama_2026-11-16'
SIM = HERE/'simulation'
FILES = ['sectors.csv','ues.csv','radio_samples.csv','sinr_components.csv','measurements.csv','prb_usage.csv','result.json']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def save(path,value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    tmp.replace(path)


def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


helpers = module('load18_helpers',D17/'study.py').previous


def report_status(status,body=None):
    path = HERE/'SONUCLAR.md'
    text = path.read_text(encoding='utf-8')
    text = '\n'.join(f'**Durum: {status}**' if line.startswith('**Durum:') else line for line in text.splitlines())
    if body is not None:
        marker = '## ns-3 sonuçları'
        text = text.split(marker)[0].rstrip()+'\n\n'+marker+'\n\n'+body
    path.write_text(text.rstrip()+'\n',encoding='utf-8')


def make_input(seed,interval_ms,name):
    original = read(HERE/f'inputs/ues_G17_{seed}.csv')
    rows = deepcopy(original)
    changed = []
    for row in rows:
        if row['kind']=='load' and row['dl_earfcn']=='6400':
            row['udp_interval_ms']=f'{interval_ms:.6f}'
            changed.append(int(row['ue_id']))
    assert len(changed)==14 and len(rows)==355
    for before,after in zip(original,rows):
        delta = {k for k in before if before[k]!=after[k]}
        assert delta<=({'udp_interval_ms'} if int(before['ue_id']) in changed else set())
    path = HERE/'inputs'/name
    if path.exists():
        assert read(path)==rows, 'Existing frozen input differs: '+name
    else:
        with path.open('w',encoding='utf-8',newline='') as stream:
            writer = csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
            writer.writeheader();writer.writerows(rows)
    return path


def band_load(folder):
    cells = {r['synthetic_cell_id']:r for r in read(folder/'sectors.csv')}
    usage = read(folder/'prb_usage.csv')
    by_band = {band:statistics.mean(float(r['dl_prb_utilization']) for r in usage if cells[r['synthetic_cell_id']]['carrier']==band)
               for band in ['B3','B20','B1']}
    assert len(cells)==99
    return {'prb_by_carrier':by_band,'prb_mean_achieved':statistics.mean(float(r['dl_prb_utilization']) for r in usage)}


def next_interval(points,target,bounds):
    below = [p for p in points if p['prb_by_carrier']['B20']<target]
    above = [p for p in points if p['prb_by_carrier']['B20']>target]
    last = points[-1]
    interval = last['interval_ms']*last['prb_by_carrier']['B20']/target
    if below and above:
        lo = min(below,key=lambda p:target-p['prb_by_carrier']['B20'])
        hi = min(above,key=lambda p:p['prb_by_carrier']['B20']-target)
        y0,y1 = lo['prb_by_carrier']['B20'],hi['prb_by_carrier']['B20']
        rate0,rate1 = 1/lo['interval_ms'],1/hi['interval_ms']
        rate = rate0+(target-y0)/(y1-y0)*(rate1-rate0)
        interval = 1/rate
        interval = min(max(interval,min(lo['interval_ms'],hi['interval_ms'])),max(lo['interval_ms'],hi['interval_ms']))
    interval = min(max(interval,last['interval_ms']*0.5),last['interval_ms']*2)
    return round(min(max(interval,bounds[0]),bounds[1]),6)


def evaluate(folder,seed,az,input_path):
    # Called only AFTER rate selection has been persisted, never during calibration.
    assert json.loads((HERE/'calibration.json').read_text())['selected']
    full = helpers.radio.metrics(folder,1)
    measured = helpers.measurement_metrics(full,256)
    targets = helpers.radio.read(HERE/'inputs/targets.csv')
    users = measured['ues']
    old_folder = D17/f'simulation/results/G17_draw{seed}'
    old = json.loads((old_folder/'metrics.json').read_text())
    previous_users = {u['ue_id']:u for u in old['ues'] if u['ue_id']<256}
    diffs = [abs(u['rsrp']-previous_users[u['ue_id']]['rsrp']) for u in users
             if u['rsrp'] is not None and previous_users[u['ue_id']]['rsrp'] is not None]
    inputs = read(input_path)
    cells = {r['synthetic_cell_id']:r for r in read(folder/'sectors.csv')}
    output = read(folder/'ues.csv')
    same_camping = all(not int(u['synthetic_cell_id']) or int(cells[u['synthetic_cell_id']]['dl_earfcn'])==int(inputs[int(u['ue_id'])]['dl_earfcn']) for u in output)
    out = {'case':{'seed':seed,'az':az,'folder':str(folder.relative_to(HERE)),
                   'frozen_input':str(input_path.relative_to(HERE)),'input_sha256':sha(input_path)},
           **band_load(folder),'sites':measured['sites'],
           'training':helpers.ev.evaluate(measured,targets,'train'),'control':helpers.ev.evaluate(measured,targets,'holdout'),
           'measurement_connected':sum(bool(u['connected']) for u in users),
           'measurement_with_dl':sum(u['dl_bytes']>0 for u in users),
           'rsrp_max_change_from_G17_db':max(diffs) if diffs else None,
           'same_layout_as_G17':(folder/'sectors.csv').read_bytes()==(old_folder/'sectors.csv').read_bytes(),
           'same_camping_frequencies':same_camping}
    return out


def summarize():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    cal = json.loads((HERE/'calibration.json').read_text(encoding='utf-8'))
    result = json.loads((HERE/'result.json').read_text(encoding='utf-8'))
    assert result['completed'] and len(result['results'])==3
    rows = result['results']
    assert {r['case']['seed'] for r in rows}=={701,702,703}
    g17 = json.loads((D17/'result.json').read_text(encoding='utf-8'))['results']
    s0 = [r for r in json.loads((ROOT/'deneyler/14_cok_tasiyici_s2_2026-11-15/result.json').read_text(encoding='utf-8'))['results'] if r['case']['scenario']=='S0']
    target,tol = plan['target_prb'],plan['validation_relative_tolerance']
    per_draw_checks = []
    for r in rows:
        seed = r['case']['seed']
        base = next(x for x in s0 if x['case']['ue_seed']==seed)
        per_draw_checks.append({'seed':seed,
            'B20_matches':abs(r['prb_by_carrier']['B20']-target)<=target*tol,
            'B1_still_matches':abs(r['prb_by_carrier']['B1']-target)<=target*tol,
            'network_PRB_close_to_S0':abs(r['prb_mean_achieved']-base['prb_mean_achieved'])<=0.03,
            'layout_unchanged':r['same_layout_as_G17'],'camping_unchanged':r['same_camping_frequencies'],
            'rsrp_unchanged':r['rsrp_max_change_from_G17_db'] is not None and r['rsrp_max_change_from_G17_db']<0.01,
            'all_measurement_connected':r['measurement_connected']==256})
    load_pass = all(c['B20_matches'] and c['B1_still_matches'] and c['network_PRB_close_to_S0'] for c in per_draw_checks)
    invariants_pass = all(c['layout_unchanged'] and c['camping_unchanged'] and c['rsrp_unchanged'] for c in per_draw_checks)
    def avg(runs,split,m):
        values=[r[split]['mae_db'][m] for r in runs]
        return statistics.mean(values) if all(v is not None for v in values) else None
    metrics = {label:{'mae_db':{sp:{m:avg(rs,sp,m) for m in ['rsrp','sinr']} for sp in ['training','control']},
                     'mean_prb':statistics.mean(r['prb_mean_achieved'] for r in rs)} for label,rs in [('S0',s0),('G17',g17),('L18',rows)]}
    comparison = {'load_matching_passed':load_pass,'load_only_invariants_passed':invariants_pass,
                  'checks_by_draw':per_draw_checks,'metrics':metrics,'selected_interval_ms':cal['selected']['interval_ms'],
                  'mean_prb_by_carrier':{b:statistics.mean(r['prb_by_carrier'][b] for r in rows) for b in ['B3','B20','B1']},
                  'RF_configuration_verified':False,'automatic_model_replacement':False}
    save(HERE/'comparison.json',comparison)
    body = ['## Yük ayarı','',
            f"701 örneğiyle seçilen B20 paket aralığı: **{cal['selected']['interval_ms']:.6f} ms**. Hedef PRB 0,233. Aynı aralık 702 ve 703’e değiştirilmeden uygulandı. 701’in başarılı kalibrasyon koşusu tekrar çalıştırılmadan nihai sonuç olarak kullanıldı.",'',
            '| Örnek | B3 PRB | B20 PRB | B1 PRB | Ağ ortalaması | B20 hedef aralığında |',
            '|---|---:|---:|---:|---:|---|']
    for r,c in zip(sorted(rows,key=lambda r:r['case']['seed']),sorted(per_draw_checks,key=lambda c:c['seed'])):
        b = r['prb_by_carrier']
        body.append(f"| {r['case']['seed']} | {b['B3']:.3f} | {b['B20']:.3f} | {b['B1']:.3f} | {r['prb_mean_achieved']:.3f} | {'Evet' if c['B20_matches'] else 'Hayır'} |")
    body += ['', '**Yük eşleme: '+('Geçti.' if load_pass else 'Üç örneğin tamamında geçmedi; kalan farklar açıkça kayıtlı.')+'**', '',
             '**Yalnız yük değişikliği kontrolleri: '+('Geçti; hücre yapısı, taşıyıcı atamaları ve RSRP korundu.' if invariants_pass else 'Geçmedi; ayrıntılı kontrol gerekli.')+'**','',
             '## Ölçümlerle karşılaştırma','',
             '| Senaryo | Kontrolde RSRP farkı | Kontrolde SINR farkı | Ağ PRB ortalaması |',
             '|---|---:|---:|---:|']
    for name in ['S0','G17','L18']:
        m = metrics[name]
        def fmt(v): return f'{v:.2f}' if v is not None else 'Eksik'
        body.append(f"| {name} | {fmt(m['mae_db']['control']['rsrp'])} | {fmt(m['mae_db']['control']['sinr'])} | {m['mean_prb']:.3f} |")
    body += ['', 'Farklar dB, küçük değer daha iyi. S0 eski tek taşıyıcılı referans; G17 yük eşlemesi öncesi gruplamalı model; L18 aynı modelin yalnız B20 trafiği düzeltilmiş sürümü.','',
             'Yük eşlemesi sinyal gücü ayarı değildir. Sinyal gücü farkının değişmemesi beklenir; SINR karşılaştırması benzer dolulukta yeniden yapılmıştır. Bantlar, güçler, kullanıcıların taşıyıcı payları ve gerçek anten yönleri hâlâ varsayım; bu işlem bunları doğrulamaz.','',
             'Benzer doluluk, aynı toplam trafik veya aynı toplam güç demek değildir. B20’ye daha fazla trafik verilmesi planlıdır; yeni sunulan trafik miktarı input CSV’lerinden yeniden hesaplanabilir. Her hücredeki doluluk da birebir aynı değildir; kabul ölçütü taşıyıcı ortalamasıdır.','',
             '| Örnek | Bağlanan / 256 | Veri alan / 256 | RSRP en büyük değişim (dB) |',
             '|---|---:|---:|---:|']
    for r in rows:
        body.append(f"| {r['case']['seed']} | {r['measurement_connected']} | {r['measurement_with_dl']} | {r['rsrp_max_change_from_G17_db']:.8f} |")
    body += ['', 'Hiçbir paket aralığı Experia RSRP/SINR hatasına göre seçilmedi. 702/703 sonuçları görüldükten sonra seçilen aralık değiştirilmedi. Eski deneyler korunur; S0 otomatik değiştirilmez.']
    status = 'Yük ayarı ve üç örnek tamamlandı. '+('Yük eşleme ölçütleri geçti.' if load_pass else 'Yük eşleme ölçütlerinin tamamı geçmedi.')
    report_status(status,'\n'.join(body))
    print(json.dumps(comparison,indent=2,ensure_ascii=False),flush=True)


def main():
    if '--summarize' in sys.argv:
        summarize();return
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for name,h in plan['source_hashes'].items(): assert sha(SIM/name)==h,name
    for name,h in plan['initial_input_hashes'].items(): assert sha(HERE/'inputs'/name)==h,name
    assert sha(D17/'plan.json')==plan['parent_plan_sha256']
    assert sha(D17/'result.json')==plan['parent_result_sha256']
    assert sha(D17/'regression.json')==plan['parent_regression_sha256']
    assert sha(SIM/'build/sindirgi_baseline')==plan['reused_build']['binary_sha256']
    tested = subprocess.run([str(SIM/'build/sindirgi_baseline'),'--verifyCarrierLayout=1'],capture_output=True,text=True,check=True)
    model_checks = json.loads(tested.stdout)
    assert model_checks['passed']
    save(HERE/'verification.json',{'source_identical_to_G17':True,'binary_identical_to_G17':True,
                                'reused_regression_passed':True,'model_checks':model_checks})
    (HERE/'logs').mkdir(exist_ok=True)
    source_id = hashlib.sha256((SIM/'sindirgi_baseline.cc').read_bytes()+(SIM/'static-shadow-model.h').read_bytes()).hexdigest()
    def run(name,az,input_path):
        folder = SIM/'results'/name
        sp = HERE/f'inputs/sites_G17_{az}.csv'
        key = {'source':source_id,'sites_sha256':sha(sp),'ues_sha256':sha(input_path),'duration':4,
               'fixed_radio':{'power':49,'beamwidth':120,'exponent':3,'nf':9,'mixed_cqi':1,'udp_jitter':1}}
        cache = folder/'run_cache.json'
        cached = False
        if cache.exists():
            old = json.loads(cache.read_text())
            cached = old.get('key')==key and bool(old.get('outputs')) and all((folder/n).exists() and sha(folder/n)==h for n,h in old['outputs'].items())
        if not cached:
            cmd = [sys.executable,str(SIM/'run_baseline.py'),'--skip-build','--name',name,'--sites','0','--ues','355',
                   '--duration','4','--sites-file',str(sp),'--ue-file',str(input_path),'--mixed-cqi','1','--udp-jitter','1',
                   '--beamwidth','120','--exponent','3','--enb-power','49','--receiver-nf','9','--shadow-std','0',
                   '--dl-earfcn','1300','--ul-earfcn','19300']
            print('START',name,flush=True)
            with (HERE/'logs'/f'{name}.log').open('w') as log:
                subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            save(cache,{'key':key,'outputs':{n:sha(folder/n) for n in FILES}})
        return folder
    cal_path = HERE/'calibration.json'
    if cal_path.exists():
        cal = json.loads(cal_path.read_text(encoding='utf-8'))
    else:
        point = {'round':0,'seed':701,'interval_ms':plan['baseline_point']['interval_ms'],
                 'prb_by_carrier':plan['baseline_point']['prb_by_carrier'],'source':'existing G17 draw701'}
        cal = {'selection_uses':'B20 mean PRB only; no signal targets','points':[point],'selected':None}
        save(cal_path,cal)
    while cal['selected'] is None:
        round_number = len(cal['points'])
        if round_number>plan['max_new_calibration_runs']:
            raise RuntimeError('Predeclared calibration limit reached without matching the pilot; do not inspect validation to choose a rate.')
        interval = next_interval(cal['points'],plan['target_prb'],plan['interval_bounds_ms'])
        name = f'cal_r{round_number}_draw701'
        input_path = make_input(701,interval,f'ues_cal_r{round_number}_701.csv')
        report_status(f'Yalnız PRB ile yük ayarı: kalibrasyon {round_number} çalışıyor.')
        folder = run(name,42,input_path)
        point = {'round':round_number,'seed':701,'interval_ms':interval,**band_load(folder),
                 'folder':str(folder.relative_to(HERE)),'input':str(input_path.relative_to(HERE)),
                 'input_sha256':sha(input_path)}
        cal['points'].append(point)
        if abs(point['prb_by_carrier']['B20']-plan['target_prb'])<=plan['target_prb']*plan['pilot_relative_tolerance']:
            cal['selected']=dict(point)
        save(cal_path,cal)
        print('PILOT',round_number,'B20_PRB',point['prb_by_carrier']['B20'],'interval',interval,'selected',cal['selected'] is not None,flush=True)
    selected = cal['selected']
    # Persisted selection precedes all radio error analysis and both independent runs.
    frozen = {}
    for az,seed in plan['draws']:
        frozen[str(seed)] = make_input(seed,selected['interval_ms'],f'ues_L18_{seed}.csv')
    assert sha(frozen['701'])==selected['input_sha256']
    if 'frozen_final_inputs' not in cal:
        cal['frozen_final_inputs']={seed:{'path':str(p.relative_to(HERE)),'sha256':sha(p)} for seed,p in frozen.items()}
        save(cal_path,cal)
    else:
        assert all(sha(frozen[seed])==entry['sha256'] for seed,entry in cal['frozen_final_inputs'].items())
    results = [evaluate(HERE/selected['folder'],701,42,frozen['701'])]
    save(HERE/'checkpoint.json',{'completed':1,'planned':3,'results':results})
    report_status('Yük aralığı sabitlendi; 701 tamamlandı, bağımsız 702/703 koşuları çalışıyor.')
    def one(az,seed):
        folder = run(f'L18_draw{seed}',az,frozen[str(seed)])
        return evaluate(folder,seed,az,frozen[str(seed)])
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(one,az,seed) for az,seed in plan['draws'] if seed!=701]):
            result = future.result();results.append(result)
            save(HERE/'checkpoint.json',{'completed':len(results),'planned':3,'results':results})
            report_status(f'Yük aralığı sabit; {len(results)}/3 örnek tamamlandı.')
            print('DONE',result['case']['seed'],flush=True)
    save(HERE/'result.json',{'completed':True,'results':sorted(results,key=lambda r:r['case']['seed'])})
    summarize()


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        report_status('Çalışma durdu; hata kaydı kontrol edilmeli.',str(exc))
        raise
