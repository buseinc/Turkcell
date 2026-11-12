"""Advisor's fixed 8+8 sites, refreshed inventory and paired radio checks."""
from pathlib import Path
import csv,json,hashlib,math,sys,subprocess,importlib.util
from concurrent.futures import ThreadPoolExecutor,as_completed
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=ROOT/'deneyler/06_genis_tarama_secilen_ayar_2026-11-10';PROJECT=ROOT/'ana_proje'
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8');t.replace(p)
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def prepare():
    import openpyxl,numpy as np
    inp=HERE/'inputs';inp.mkdir(exist_ok=True)
    book=PROJECT/'cell_site_coordinates/cell_site_coordinates.xlsx'
    w=openpyxl.load_workbook(book,read_only=True,data_only=True);it=w.active.values;head=next(it)
    cells=[dict(zip(head,r)) for r in it];w.close();sites={r['site']:r for r in cells}
    selected=read(PROJECT/'sindirgi_lte_sites.csv');core=[r['site_id'] for r in selected if r['role']=='Evaluation'];fixed={r['site_id'] for r in selected}
    assert len(core)==8 and len(fixed)==16 and fixed<=sites.keys()
    def dist(a,b):
        p,q=math.radians(a['lat']),math.radians(b['lat']);dl=math.radians(a['lon']-b['lon'])
        return 2*6371000*math.asin(math.sqrt(math.sin((p-q)/2)**2+math.cos(p)*math.cos(q)*math.sin(dl/2)**2))
    neighbours=sorted((s for s in sites if s not in core),key=lambda s:(min(dist(sites[s],sites[c]) for c in core),s))
    assert set(neighbours[:8])==fixed-set(core)
    def xyz(r):
        p,l=math.radians(r['lat']),math.radians(r['lon']);e=1/298.257223563;e=e*(2-e);n=6378137/math.sqrt(1-e*math.sin(p)**2)
        return np.array([n*math.cos(p)*math.cos(l),n*math.cos(p)*math.sin(l),n*(1-e)*math.sin(p)])
    origin=xyz({'lat':39.2461,'lon':28.0697});p,l=map(math.radians,[39.2461,28.0697])
    rotation=np.array([[-math.sin(l),math.cos(l),0],[-math.sin(p)*math.cos(l),-math.sin(p)*math.sin(l),math.cos(p)]])
    historical=read(PROJECT/'analysis/sindirgi/candidate_sites.csv');ids=sorted(r['site'] for r in historical)
    for seed in [42,7,99]:
        angles=dict(zip(ids,np.random.default_rng(seed).uniform(0,120,len(ids))))
        for s in sites:
            if s not in angles:angles[s]=int(hashlib.sha256(f'{seed}:{s}'.encode()).hexdigest()[:12],16)/16**12*120
        for count in [16,24,32,48]:
            chosen=core+neighbours[:count-8];assert fixed<=set(chosen)
            with (inp/f'sites_{count}_{seed}.csv').open('w',newline='') as f:
                wr=csv.DictWriter(f,fieldnames=['site','role','x_m','y_m','rotation_deg']);wr.writeheader()
                for s in chosen:
                    x,y=rotation@(xyz(sites[s])-origin)
                    wr.writerow(dict(site=s,role='Evaluation' if s in core else 'Interference buffer',x_m=f'{x:.9f}',y_m=f'{y:.9f}',rotation_deg=f'{angles[s]:.9f}'))
        # Exact old coordinates + only new 549 isolate its effect from coordinate precision.
        if seed==42:
            rr=read(OLD/'inputs/sites_24_42_three.csv');new=next(r for r in read(inp/'sites_24_42.csv') if r['site']=='SITE_000549');rr.append(new)
            with (inp/'sites_25_42.csv').open('w',newline='') as f:
                wr=csv.DictWriter(f,fieldnames=list(rr[0]));wr.writeheader();wr.writerows(rr)
    cases=[dict(name=f'updated_{n}',sites=n,az=42,ue=701,duration=4,old='ensemble_reference_0') for n in [16,24,32,48]]
    cases += [dict(name='addition_549',sites=25,az=42,ue=701,duration=4,old='ensemble_reference_0')]
    cases += [dict(name=f'updated_draw_{i}',sites=24,az=az,ue=ue,duration=4,old=f'ensemble_reference_{i}') for i,az,ue in [(1,7,702),(2,99,703)]]
    plan={'cases':cases,'core':core,'advisor_sites':sorted(fixed),'inventory_sha256':sha(book),
          'source_sha256':sha(OLD/'simulation/sindirgi_baseline.cc'),
          'input_hashes':{p.name:sha(p) for p in inp.glob('*.csv')},
          'ue_hashes':{str(seed):sha(OLD/f'inputs/ues_far_{seed}.csv') for seed in [701,702,703]},
          'rule':'Keep advisor 8+8. Rank extra inventory sites by distance to nearest evaluation site. Preserve old azimuths for common sites; deterministic keyed angles for new sites. Same 64 UE draws, reference radio settings, 4s duration,1s warmup. No retuning. Paired RSRP/SINR q95 <=1dB and same sector >=95%; inspect coverage and all three errors.'}
    save(HERE/'plan.json',plan);print('Prepared',len(cases),'native runs')
def run():
    plan=json.loads((HERE/'plan.json').read_text());assert sha(PROJECT/'cell_site_coordinates/cell_site_coordinates.xlsx')==plan['inventory_sha256']
    assert sha(OLD/'simulation/sindirgi_baseline.cc')==plan['source_sha256']
    for name,h in plan['input_hashes'].items():assert sha(HERE/'inputs'/name)==h
    for seed,h in plan['ue_hashes'].items():assert sha(OLD/f'inputs/ues_far_{seed}.csv')==h
    radio=module('refresh_radio',PROJECT/'simulation/run_radio_study.py');ev=module('refresh_eval',ROOT/'deneyler/04_ortak_radyo_taramasi_2026-11-10/run_search.py')
    targets=radio.read(OLD/'inputs/targets.csv');previous=json.loads((OLD/'study_result.json').read_text());previous={r['case']['name']:r for r in previous['ensemble']}
    tol={'rsrp_q95_absolute_change_db':1.,'sinr_q95_absolute_change_db':1.,'same_serving_sector_fraction_min':.95}
    results=[]
    def one(c):
        name='refresh_20261112_'+c['name'];folder=OLD/'simulation/results'/name
        sp=HERE/f"inputs/sites_{c['sites']}_{c['az']}.csv";up=OLD/f"inputs/ues_far_{c['ue']}.csv"
        cached=False
        if (folder/'result.json').exists():
            r=json.loads((folder/'result.json').read_text());cached=r['sites_sha256']==sha(sp) and r['ue_positions_sha256']==sha(up) and r['source_sha256']==plan['source_sha256'] and r['duration_s']==c['duration']
        if not cached:
            cmd=[sys.executable,str(OLD/'simulation/run_baseline.py'),'--sites','0','--ues','64','--duration',str(c['duration']),'--sites-file',str(sp),'--ue-file',str(up),'--mixed-cqi','1','--beamwidth','120','--exponent','3','--enb-power','49','--receiver-nf','9','--shadow-std','0','--udp-interval-ms','50','--name',name,'--skip-build']
            print('START',c['name'],flush=True)
            with (HERE/(c['name']+'.log')).open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
        r=json.loads((folder/'result.json').read_text());m=radio.metrics(folder,1.)
        out={'case':c,'result':r,'metrics':m,'training':ev.evaluate(m,targets,'train'),'control':ev.evaluate(m,targets,'holdout'),
             'paired_previous':radio.pair_check(previous[c['old']]['metrics'],m,tol)}
        print('DONE',c['name'],'score',out['training']['score'],flush=True);return out
    with ThreadPoolExecutor(max_workers=3) as pool:
        for f in as_completed([pool.submit(one,c) for c in plan['cases']]):
            results.append(f.result());save(HERE/'checkpoint.json',{'completed':len(results),'planned':len(plan['cases']),'results':results})
    by={r['case']['name']:r for r in results}
    checks=[dict(from_sites=a,to_sites=b,**radio.pair_check(by[f'updated_{a}']['metrics'],by[f'updated_{b}']['metrics'],tol)) for a,b in [(16,24),(24,32),(32,48)]]
    save(HERE/'result.json',{'completed':True,'results':results,'buffer_checks':checks,'inventory_sha256':plan['inventory_sha256']})
    lines=['# Güncel envanterle hocanın seçiminin yeniden kontrolü — 12 Kasım 2026','', 'Hocanın 8 ana + 8 komşu sahası bütün güncel topolojilerde korundu. 64 kullanıcı, önceki seçilmiş ayar, 4 s koşu ve 1 s ısınma kullanıldı. Ayar yeniden seçilmedi.','', '| Koşu | Eğitim MAE RSRP/SINR/RSRQ | Kontrol MAE RSRP/SINR/RSRQ | Eski 24 ile eşli kontrol |','|---|---|---|---|']
    for r in sorted(results,key=lambda r:r['case']['name']):
        t=lambda split:' / '.join(f'{r[split]["mae_db"][k]:.3f}' for k in ['rsrp','sinr','rsrq'])
        lines.append(f'| {r["case"]["name"]} | {t("training")} | {t("control")} | {r["paired_previous"]["passed"]} |')
    lines+=['','Komşu genişletme kontrolleri:', '', '```json',json.dumps(checks,indent=2),'```','','Eski eşli kontrol, aynı UE/anten örneğinin önceki 24 saha koşusuyla yapılır. 16 saha hocanın başlangıcıdır; 25 saha yalnız 549 ekleme tanısıdır. Sonuçlar düşük yük pilotudur; gerçek kapasite doğrulaması değildir. Yeni dosyada konumu teyit edilen üç saha zaten eski deneylerde yer alıyordu.','', '[Tam sayısal sonuç](result.json) — [Önceden kaydedilen plan](plan.json)']
    (HERE/'SONUCLAR.md').write_text('\n'.join(lines),encoding='utf-8');print('COMPLETE',checks,flush=True)
if __name__=='__main__':prepare() if '--prepare' in sys.argv else run()
