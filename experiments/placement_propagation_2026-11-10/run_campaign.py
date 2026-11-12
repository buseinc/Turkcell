"""WSL: real shortlisted simulations, training-only selection, robustness checks."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PROJECT=ROOT/'turkcell_tam_paket_2026-11-10'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


radio=module('radio',PROJECT/'simulation/run_radio_study.py')
evaluation=module('evaluation',ROOT/'experiments/radio_joint_search_2026-11-10/run_search.py')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')
    temporary.replace(path)


def main():
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    targets=radio.read(HERE/'inputs/targets.csv')
    assert digest(PROJECT/'simulation/sindirgi_baseline.cc')==plan['original_cpp_sha256']
    for name,expected in plan['input_hashes'].items():assert digest(HERE/'inputs'/name)==expected,name
    def run_case(case,build=False):
        name=case['name'];folder=HERE/'simulation/results'/name
        sites=HERE/'inputs'/case['sites_file'];ues=HERE/'inputs'/case['ue_file']
        cached=False
        try:
            previous=json.loads((folder/'result.json').read_text())
            model=previous['model_assumptions']
            cached=(previous['source_sha256']==plan['source_cpp_sha256'] and
                previous['sites_sha256']==digest(sites) and previous['ue_positions_sha256']==digest(ues) and
                previous['duration_s']==case['duration_s'] and model['mixed_cqi_enabled'] and
                model['horizontal_beamwidth_deg']==case['beamwidth_deg'] and
                model['log_distance_exponent']==case['exponent'] and
                model['enb_conducted_tx_power_dbm']==case['power_dbm'] and
                'every 50 ms' in model['dl_application'])
        except (FileNotFoundError,KeyError,json.JSONDecodeError):pass
        if build and not (HERE/'simulation/build/sindirgi_baseline').exists():cached=False
        print('START',name,'cached',cached,flush=True)
        if not cached:
            command=[sys.executable,str(HERE/'simulation/run_baseline.py'),'--sites','0','--ues','64',
                '--duration',str(case['duration_s']),'--sites-file',str(sites),'--ue-file',str(ues),
                '--mixed-cqi','1','--beamwidth',str(case['beamwidth_deg']),'--exponent',str(case['exponent']),
                '--enb-power',str(case['power_dbm']),'--udp-interval-ms','50','--name',name]
            if not build:command.append('--skip-build')
            with (HERE/(name+'.log')).open('w') as stream:
                subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True)
        result=json.loads((folder/'result.json').read_text())
        assert result['source_sha256']==plan['source_cpp_sha256']
        assert result['sites_sha256']==digest(sites) and result['ue_positions_sha256']==digest(ues)
        metrics=radio.metrics(folder,1.0)
        answer={'case':case,'result':result,'metrics':metrics,
                'training':evaluation.evaluate(metrics,targets,'train')}
        print('DONE',name,'training',answer['training'],'wall',round(result['wall_seconds'],1),flush=True)
        return answer
    report={'completed':False,'cases':[],'followups':[]}
    baseline=run_case(plan['cases'][0],build=True)
    reference={int(r['ue_id']):r for r in radio.read(ROOT/'experiments/radio_joint_search_2026-11-10/ue_comparison.csv') if r['case']=='b120_t50'}
    maximum=0.0
    for row in baseline['metrics']['ues']:
        ref=reference[row['ue_id']]
        assert row['site']==ref['site']
        for key in ['sector','connected','dl_bytes','rsrp','sinr','rsrq','x_m','y_m']:
            a,b=float(row[key]),float(ref[key])
            assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8),(row['ue_id'],key,a,b)
            maximum=max(maximum,abs(a-b))
    report['regression']={'passed':True,'max_numeric_difference':maximum}
    report['cases'].append(baseline)
    save(HERE/'checkpoint.json',report)
    print('BASELINE REGRESSION PASSED',flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run_case,case) for case in plan['cases'][1:]]
        for future in as_completed(futures):
            report['cases'].append(future.result())
            report['cases'].sort(key=lambda c:c['case']['name'])
            save(HERE/'checkpoint.json',report)
    winner=min(report['cases'],key=lambda c:(c['training']['score'],c['case']['name']))
    report['selected_name']=winner['case']['name']
    save(HERE/'training_selection.json',{'selected_name':report['selected_name'],
        'case':winner['case'],'training':winner['training'],'rule':plan['selection_rule']})
    for case in report['cases']:
        case['control']=evaluation.evaluate(case['metrics'],targets,'holdout')
    print('FROZEN SELECTION',report['selected_name'],flush=True)
    followups=[]
    seed=copy.deepcopy(winner['case']);seed.update(name='check_new_ue_seed',
        ue_file='ues_'+winner['case']['family']+'_seed2.csv')
    followups.append(seed)
    for total in [32,48]:
        case=copy.deepcopy(winner['case']);case.update(name=f'check_buffer_{total}',sites_file=f'sites_{total}.csv')
        followups.append(case)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run_case,case) for case in followups]
        for future in as_completed(futures):
            answer=future.result();answer['control']=evaluation.evaluate(answer['metrics'],targets,'holdout')
            report['followups'].append(answer)
            report['followups'].sort(key=lambda c:c['case']['name'])
            save(HERE/'checkpoint.json',report)
    checks={c['case']['name']:c for c in report['followups']}
    tolerances={'rsrp_q95_absolute_change_db':1.0,'sinr_q95_absolute_change_db':1.0,'same_serving_sector_fraction_min':.95}
    report['buffer_checks']=[
        {'from_sites':24,'to_sites':32,**radio.pair_check(winner['metrics'],checks['check_buffer_32']['metrics'],tolerances)},
        {'from_sites':32,'to_sites':48,**radio.pair_check(checks['check_buffer_32']['metrics'],checks['check_buffer_48']['metrics'],tolerances)}]
    report['buffer_two_steps_passed']=all(c['passed'] for c in report['buffer_checks'])
    report['completed']=True
    save(HERE/'study_result.json',report)
    print('CAMPAIGN COMPLETE',report['selected_name'],'buffer_passed',report['buffer_two_steps_passed'],flush=True)


if __name__=='__main__':main()
