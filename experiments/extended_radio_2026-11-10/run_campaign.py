"""WSL campaign: 49 native screens, common ensembles, and longer confirmation."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import copy
import csv
import hashlib
import importlib.util
import json
import math
import statistics
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PROJECT=ROOT/'turkcell_tam_paket_2026-11-10'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


radio=module('radio',PROJECT/'simulation/run_radio_study.py')
evaluation=module('evaluation',ROOT/'experiments/radio_joint_search_2026-11-10/run_search.py')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,data):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
    temporary.replace(path)


def identity(case):
    excluded={'name','category','profile','label','azimuth_seed','shadow_seed','spatial_seed','duration_s','model_id','draw_index','total_sites'}
    return json.dumps({k:v for k,v in case.items() if k not in excluded},sort_keys=True)


def main():
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    assert digest(PROJECT/'simulation/sindirgi_baseline.cc')==plan['original_cpp_sha256']
    for name,expected in plan['code_hashes'].items():assert digest(HERE/'simulation'/name)==expected,name
    for name,expected in plan['input_hashes'].items():assert digest(HERE/'inputs'/name)==expected,name
    targets=radio.read(HERE/'inputs/targets.csv')
    report={'completed':False,'screening':[],'ensemble':[],'finals':[],'phase':'regression'}
    def checkpoint():
        save(HERE/'checkpoint.json',report)
        save(HERE/'progress.json',{'phase':report['phase'],'screening_completed':len(report['screening']),
            'screening_planned':plan['screening_count'],'ensemble_completed':len(report['ensemble']),
            'ensemble_planned':report.get('ensemble_planned'), 'final_completed':len(report['finals']),
            'recommended_model':report.get('recommended_model')})
    def run(case,build=False):
        name=case['name'];duration=case['duration_s'];folder=HERE/'simulation/results'/name
        sites=HERE/'inputs'/f"sites_{case.get('total_sites',24)}_{case['azimuth_seed']}_{case['sector_policy']}.csv"
        ues=HERE/'inputs'/f"ues_{case['family']}_{case['spatial_seed']}.csv"
        if case.get('ue_file'):ues=HERE/'inputs'/case['ue_file']
        cached=False
        try:
            old=json.loads((folder/'result.json').read_text());m=old['model_assumptions'];s=m['shadowing']
            cached=(old['source_sha256']==plan['source_cpp_sha256'] and old['duration_s']==duration and
                old['sites_sha256']==digest(sites) and old['ue_positions_sha256']==digest(ues) and
                m['mixed_cqi_enabled'] and m['horizontal_beamwidth_deg']==case['beamwidth_deg'] and
                m['enb_conducted_tx_power_dbm']==case['power_dbm'] and m['log_distance_exponent']==case['exponent'] and
                m['receiver_noise_figure_db']==case['ue_nf_db'] and s['std_db']==case['shadow_std_db'] and
                s['seed']==case['shadow_seed'] and m['dl_earfcn']==case['dl_earfcn'] and m['ul_earfcn']==case['ul_earfcn'] and
                f"every {case['udp_interval_ms']:g} ms" in m['dl_application'] and
                all((folder/p).is_file() for p in ['ues.csv','sectors.csv','radio_samples.csv','measurements.csv','sinr_components.csv']))
        except (FileNotFoundError,KeyError,json.JSONDecodeError):pass
        if build and not (HERE/'simulation/build/sindirgi_baseline').exists():cached=False
        print('START',name,case.get('category',''), 'cached',cached,flush=True)
        if not cached:
            command=[sys.executable,str(HERE/'simulation/run_baseline.py'),
                '--sites',str(case.get('site_limit',0)),'--ues',str(case.get('ue_count',64)),
                '--duration',str(duration),'--sites-file',str(sites),'--ue-file',str(ues),
                '--mixed-cqi','1','--beamwidth',str(case['beamwidth_deg']),'--exponent',str(case['exponent']),
                '--enb-power',str(case['power_dbm']),'--receiver-nf',str(case['ue_nf_db']),
                '--shadow-std',str(case['shadow_std_db']),'--shadow-seed',str(case['shadow_seed']),
                '--dl-earfcn',str(case['dl_earfcn']),'--ul-earfcn',str(case['ul_earfcn']),
                '--udp-interval-ms',str(case['udp_interval_ms']),'--name',name]
            if not build:command.append('--skip-build')
            with (HERE/(name+'.log')).open('w') as stream:
                process=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
            if process.returncode:raise RuntimeError(f'{name}: exit {process.returncode}; inspect {name}.log')
        native=json.loads((folder/'result.json').read_text())
        assert native['source_sha256']==plan['source_cpp_sha256']
        assert native['sites_sha256']==digest(sites) and native['ue_positions_sha256']==digest(ues)
        metrics=radio.metrics(folder,1.0)
        answer={'case':case,'result':native,'metrics':metrics,'training':evaluation.evaluate(metrics,targets,'train')}
        save(folder/'case_manifest.json',{'case':case,'source_sha256':plan['source_cpp_sha256'],
            'sites_sha256':digest(sites),'ues_sha256':digest(ues),
            'outputs_sha256':{p:digest(folder/p) for p in ['ues.csv','sectors.csv','radio_samples.csv','measurements.csv','sinr_components.csv']}})
        print('DONE',name,'score',round(answer['training']['score'],3),
            'valid',answer['training']['valid_sites'],'connected',native['connected_ues'],
            'DL',native['ues_receiving_dl'],'wall',round(native['wall_seconds'],1),flush=True)
        return answer
    reference=copy.deepcopy(plan['reference']);reference.update(name='regression',duration_s=4.0)
    gate=run(reference,build=True)
    old=json.loads((ROOT/'experiments/placement_propagation_2026-11-10/study_result.json').read_text())
    old=next(c for c in old['cases'] if c['case']['name']==old['selected_name'])
    previous={r['ue_id']:r for r in old['metrics']['ues']}
    maximum=0.0
    for row in gate['metrics']['ues']:
        ref=previous[row['ue_id']]
        assert row['site']==ref['site']
        for key in ['sector','connected','dl_bytes','rsrp','sinr','rsrq','x_m','y_m']:
            a,b=float(row[key]),float(ref[key])
            assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8),(row['ue_id'],key,a,b)
            maximum=max(maximum,abs(a-b))
    report['regression']={'passed':True,'maximum_numeric_difference':maximum}
    result=subprocess.run([str(HERE/'simulation/build/sindirgi_baseline'),'--verifyShadow=1'],
        cwd=HERE,capture_output=True,text=True,check=True)
    report['shadow_unit_checks']=json.loads(result.stdout.strip().splitlines()[-1])
    assert report['shadow_unit_checks']['passed']
    # Tiny integration test of the positive-shadow branch, separate from scientific screens.
    site_rows=radio.read(HERE/'inputs/sites_24_42_three.csv')
    smoke_path=HERE/'inputs/ues_smoke6.csv'
    with smoke_path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['ue_id','x_m','y_m','z_m']);writer.writeheader()
        for u in range(6):
            centre=site_rows[u%2];angle=2*math.pi*u/6
            writer.writerow({'ue_id':u,'x_m':float(centre['x_m'])+500*math.cos(angle),
                             'y_m':float(centre['y_m'])+500*math.sin(angle),'z_m':1.5})
    smoke=copy.deepcopy(reference);smoke.update(name='shadow_integration',duration_s=1.2,shadow_std_db=4,
        ue_file='ues_smoke6.csv',ue_count=6,site_limit=2)
    smoke=run(smoke)
    assert smoke['result']['connected_ues']==smoke['result']['ues_receiving_dl']==6
    report['shadow_integration']={'passed':True,'connected':6,'receiving_dl':6,'input_sha256':digest(smoke_path)}
    checkpoint()
    def execute(cases,destination,phase):
        report['phase']=phase;checkpoint()
        with ThreadPoolExecutor(max_workers=plan['parallel_workers']) as pool:
            pending={pool.submit(run,case):case for case in cases}
            failures=[]
            for future in as_completed(pending):
                try:
                    destination.append(future.result());destination.sort(key=lambda c:c['case']['name'])
                except Exception as exc:
                    failures.append(str(exc));print('FAILED',str(exc),flush=True)
                checkpoint()
                print('PROGRESS',phase,len(destination),'/',len(cases),flush=True)
            if failures:
                report['failures']=failures;checkpoint()
                raise RuntimeError('; '.join(failures))
    execute(plan['screening_cases'],report['screening'],'screening')
    ranked=sorted(report['screening'],key=lambda c:(c['training']['score'],c['case']['name']))
    selected=[];seen=set()
    for candidate in ranked:
        key=identity(candidate['case'])
        if key in seen:continue
        seen.add(key);selected.append(candidate)
        if len(selected)==3:break
    reference_key=identity(plan['reference'])
    if reference_key not in seen:
        selected.append(next(c for c in report['screening'] if identity(c['case'])==reference_key))
    models=[];number=1
    for candidate in selected:
        is_reference=identity(candidate['case'])==reference_key
        ident='reference' if is_reference else f'model_{number:02d}'
        if not is_reference:number+=1
        models.append({'model_id':ident,'source_screen':candidate['case']['name'],
                       'case':candidate['case'],'screen_training':candidate['training']})
    report['shortlist']=models
    save(HERE/'shortlist.json',{'selection_uses':'screen training only','models':models})
    ensemble=[]
    for model in models:
        for index,draw in enumerate(plan['ensemble_draws']):
            cfg=copy.deepcopy(model['case']);cfg.update(draw)
            cfg.update(name=f"ensemble_{model['model_id']}_{index}",model_id=model['model_id'],draw_index=index,duration_s=4.0)
            ensemble.append(cfg)
    report['ensemble_planned']=len(ensemble)
    execute(ensemble,report['ensemble'],'ensemble')
    rankings=[]
    for model in models:
        observations=[r for r in report['ensemble'] if r['case']['model_id']==model['model_id']]
        values=[r['training']['score'] for r in observations]
        mean=statistics.mean(values);sd=statistics.pstdev(values)
        rankings.append({'model_id':model['model_id'],'mean_training_score':mean,
            'std_training_score':sd,'robust_score':mean+.5*sd,
            'mean_training_mae_db':{m:statistics.mean(r['training']['mae_db'][m] for r in observations)
                                    for m in ['rsrp','sinr','rsrq']}})
    rankings.sort(key=lambda r:(r['robust_score'],r['model_id']))
    nominal=rankings[0]
    ref=next(r for r in rankings if r['model_id']=='reference')
    recommended=ref if ref['robust_score']<=nominal['robust_score']+.10 else nominal
    report['ensemble_ranking']=rankings
    report['nominal_best_model']=nominal['model_id'];report['recommended_model']=recommended['model_id']
    report['reference_within_margin']=recommended['model_id']=='reference' and nominal['model_id']!='reference'
    save(HERE/'training_selection.json',{'rankings':rankings,'nominal_best_model':report['nominal_best_model'],
        'recommended_model':report['recommended_model'],'rule':plan['selection_rule']})
    print('FROZEN RECOMMENDATION',report['recommended_model'],rankings,flush=True)
    # Add control summaries only after robustness selection is frozen.
    for item in report['screening']+report['ensemble']:
        item['control']=evaluation.evaluate(item['metrics'],targets,'holdout')
    chosen=next(m for m in models if m['model_id']==report['recommended_model'])
    finals=[]
    for total in [24,32,48]:
        cfg=copy.deepcopy(chosen['case']);cfg.update(plan['ensemble_draws'][0])
        cfg.update(name=f'confirm_{total}',duration_s=8.0,total_sites=total,model_id=chosen['model_id'],draw_index=0)
        finals.append(cfg)
    execute(finals,report['finals'],'confirmation')
    for item in report['finals']:item['control']=evaluation.evaluate(item['metrics'],targets,'holdout')
    by_total={item['case']['total_sites']:item for item in report['finals']}
    tolerances={'rsrp_q95_absolute_change_db':1.0,'sinr_q95_absolute_change_db':1.0,'same_serving_sector_fraction_min':.95}
    report['buffer_checks']=[{'from_sites':a,'to_sites':b,**radio.pair_check(by_total[a]['metrics'],by_total[b]['metrics'],tolerances)}
        for a,b in [(24,32),(32,48)]]
    short=next(item for item in report['ensemble'] if item['case']['model_id']==chosen['model_id'] and item['case']['draw_index']==0)
    report['duration_check']=radio.pair_check(short['metrics'],by_total[24]['metrics'],tolerances)
    report['buffer_two_steps_passed']=all(c['passed'] for c in report['buffer_checks'])
    report['native_lte_run_count']=2+len(report['screening'])+len(report['ensemble'])+len(report['finals'])
    report['phase']='complete';report['completed']=True
    save(HERE/'study_result.json',report);checkpoint()
    print('CAMPAIGN COMPLETE',report['recommended_model'],'native LTE runs',report['native_lte_run_count'],
          'buffer',report['buffer_two_steps_passed'],flush=True)


if __name__=='__main__':main()
