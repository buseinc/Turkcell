"""Nested user sampling at constant aggregate offered rate and duration checks."""
from pathlib import Path
import csv,json,hashlib,math,sys,subprocess,importlib.util
from concurrent.futures import ThreadPoolExecutor,as_completed
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=HERE.parent/'extended_radio_2026-11-10';REF=HERE.parent/'inventory_refresh_2026-11-12'
PROJECT=ROOT/'turkcell_tam_paket_2026-11-10'
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8');t.replace(p)
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def prepare():
    import numpy as np
    inp=HERE/'inputs';inp.mkdir(exist_ok=True)
    anchors=[r for r in read(OLD/'inputs/sites_24_42_three.csv') if r['role']=='Evaluation']
    for seed in [701,702,703]:
        prefix=read(OLD/f'inputs/ues_far_{seed}.csv');rng=np.random.default_rng(seed);rows=[]
        for u in range(256):
            a=anchors[u%8];angle=rng.uniform(0,2*np.pi);radius=np.sqrt(rng.uniform(2000**2,6000**2))
            r={'ue_id':u,'x_m':float(a['x_m'])+radius*np.cos(angle),'y_m':float(a['y_m'])+radius*np.sin(angle),'z_m':1.5,'placement_anchor':a['site']}
            if u<64:
                assert abs(r['x_m']-float(prefix[u]['x_m']))<1e-6 and abs(r['y_m']-float(prefix[u]['y_m']))<1e-6
                r=prefix[u]
            rows.append(r)
        for n in [128,256]:
            with (inp/f'ues_{n}_{seed}.csv').open('w',newline='') as f:
                wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows[:n])
    draws=[(701,42,'updated_24'),(702,7,'updated_draw_1'),(703,99,'updated_draw_2')]
    cases=[dict(name=f'users_{n}_draw_{i}',users=n,seed=seed,az=az,baseline=b,duration=4,interval_ms=50*n/64) for n in [128,256] for i,(seed,az,b) in enumerate(draws)]
    cases += [dict(name=f'duration_{d}',users=64,seed=701,az=42,baseline='updated_24',duration=d,interval_ms=50) for d in [10,20]]
    save(HERE/'plan.json',{'cases':cases,'reference_results_sha256':sha(REF/'result.json'),
        'source_sha256':sha(OLD/'simulation/sindirgi_baseline.cc'),
        'input_hashes':{p.name:sha(p) for p in inp.glob('*.csv')},
        'site_hashes':{str(a):sha(REF/f'inputs/sites_24_{a}.csv') for a in [42,7,99]},
        'baseline_ue_hashes':{str(s):sha(OLD/f'inputs/ues_far_{s}.csv') for s in [701,702,703]},
        'packet_bytes':512,'nominal_total_offered_bps':64*512*8/.05,
        'protocol':'All current 24 sites and reference radio settings fixed. Three paired nested draws: 64 reused,128,256 users. Existing points remain exact prefixes; no seed selected. 50/100/200ms UDP intervals preserve nominal aggregate offered rate, not per-user rate or per-cell load/scheduler state. Finite packet count and delivery may differ. 4s sample runs,1s warmup; separate64-user10/20s duration checks. No radio retuning. Report equal-active-sector site averages, per-site coverage, all errors, duration windows and max outliers. Controls have been seen. Not a capacity experiment.'})
    print('Prepared',len(cases),'runs')
def run():
    plan=json.loads((HERE/'plan.json').read_text());assert sha(REF/'result.json')==plan['reference_results_sha256']
    assert sha(OLD/'simulation/sindirgi_baseline.cc')==plan['source_sha256']
    for n,h in plan['input_hashes'].items():assert sha(HERE/'inputs'/n)==h
    for a,h in plan['site_hashes'].items():assert sha(REF/f'inputs/sites_24_{a}.csv')==h
    for s,h in plan['baseline_ue_hashes'].items():assert sha(OLD/f'inputs/ues_far_{s}.csv')==h
    radio=module('density_radio',PROJECT/'simulation/run_radio_study.py');ev=module('density_eval',HERE.parent/'radio_joint_search_2026-11-10/run_search.py')
    targets=radio.read(OLD/'inputs/targets.csv');baseline=json.loads((REF/'result.json').read_text());baselines={r['case']['name']:r for r in baseline['results']}
    tol={'rsrp_q95_absolute_change_db':1.,'sinr_q95_absolute_change_db':1.,'same_serving_sector_fraction_min':.95}
    results=[]
    def one(c):
        name='sampling_20261112_'+c['name'];folder=OLD/'simulation/results'/name
        sp=REF/f"inputs/sites_24_{c['az']}.csv";up=OLD/f"inputs/ues_far_{c['seed']}.csv" if c['users']==64 else HERE/f"inputs/ues_{c['users']}_{c['seed']}.csv"
        cache=False
        if (folder/'result.json').exists():
            r=json.loads((folder/'result.json').read_text());cache=(r['source_sha256']==plan['source_sha256'] and r['sites_sha256']==sha(sp) and r['ue_positions_sha256']==sha(up) and r['duration_s']==c['duration'] and r['ues']==c['users'] and f"every {c['interval_ms']:g} ms" in r['model_assumptions']['dl_application'])
        if not cache:
            cmd=[sys.executable,str(OLD/'simulation/run_baseline.py'),'--sites','0','--ues',str(c['users']),'--duration',str(c['duration']),'--sites-file',str(sp),'--ue-file',str(up),'--mixed-cqi','1','--beamwidth','120','--exponent','3','--enb-power','49','--receiver-nf','9','--shadow-std','0','--udp-interval-ms',str(c['interval_ms']),'--name',name,'--skip-build']
            print('START',c['name'],flush=True)
            with (HERE/(c['name']+'.log')).open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
        r=json.loads((folder/'result.json').read_text());m=radio.metrics(folder,1.)
        out={'case':c,'result':r,'metrics':m,'training':ev.evaluate(m,targets,'train'),'control':ev.evaluate(m,targets,'holdout')}
        prefix={**m,'ues':[u for u in m['ues'] if u['ue_id']<64]}
        out['paired_original64']=radio.pair_check(baselines[c['baseline']]['metrics'],prefix,tol)
        if c['duration']>4:
            # Save late-window metrics distinctly, rather than claiming elapsed time is convergence.
            late=radio.metrics(folder,c['duration']/2)
            out['late_metrics']=late;out['late_training']=ev.evaluate(late,targets,'train');out['late_control']=ev.evaluate(late,targets,'holdout')
            out['whole_vs_late']=radio.pair_check(m,late,tol)
            radio.metrics(folder,1.)
        print('DONE',c['name'],'control',out['control']['mae_db'],'wall',round(r['wall_seconds']),flush=True);return out
    with ThreadPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(one,c) for c in plan['cases']]):
            results.append(f.result());save(HERE/'checkpoint.json',{'completed':len(results),'planned':len(plan['cases']),'results':results})
    save(HERE/'result.json',{'completed':True,'results':results,'baseline_results':[baselines[k] for k in ['updated_24','updated_draw_1','updated_draw_2']]})
    print('COMPLETE',flush=True)
if __name__=='__main__':prepare() if '--prepare' in sys.argv else run()
