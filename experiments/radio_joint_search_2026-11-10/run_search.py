"""WSL campaign: fixed six cases, training-only ranking, resumable checkpoints."""
from pathlib import Path
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
spec=importlib.util.spec_from_file_location('radio',PROJECT/'simulation/run_radio_study.py')
radio=importlib.util.module_from_spec(spec)
spec.loader.exec_module(radio)


def evaluate(metrics,targets,split):
    rows=[t for t in targets if t['split']==split]
    missing=[t['site'] for t in rows if any(metrics['sites'].get(t['site'],{}).get(m) is None
                                          for m in ['rsrp','sinr','rsrq'])]
    errors={m:statistics.mean([abs(metrics['sites'][t['site']][m]-float(t[m+'_target']))
              for t in rows if t['site'] not in missing]) if len(missing)<len(rows) else None
              for m in ['rsrp','sinr','rsrq']}
    return {'mae_db':errors,'valid_sites':len(rows)-len(missing),'missing_sites':missing,
            'score':statistics.mean([v if v is not None else 1000 for v in errors.values()])+10*len(missing)}


def main():
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    targets=radio.read(HERE/'inputs/targets.csv')
    reference={int(r['ue_id']):r for r in radio.read(ROOT/'experiments/mixed_cqi_2026-11-10/ue_comparison.csv') if r['case']=='mixed'}
    report={'completed':False,'cases':[]}
    for index,case in enumerate(plan['cases']):
        name=case['name']
        folder=HERE/'simulation/results'/name
        command=[sys.executable,str(HERE/'simulation/run_baseline.py'),'--sites','0','--ues','64',
            '--duration','4','--sites-file',str(HERE/'inputs/sites.csv'),'--ue-file',str(HERE/'inputs/ues.csv'),
            '--mixed-cqi','1','--beamwidth',str(case['beamwidth_deg']),
            '--udp-interval-ms',str(case['udp_interval_ms']),'--name',name]
        if index:command.append('--skip-build')
        cached=False
        if (folder/'result.json').exists():
            old=json.loads((folder/'result.json').read_text())
            cached=(old['source_sha256']==plan['source_cpp_sha256'] and
                    old['sites_sha256']==plan['input_hashes']['sites.csv'] and
                    old['ue_positions_sha256']==plan['input_hashes']['ues.csv'] and
                    old['duration_s']==4 and old['model_assumptions']['mixed_cqi_enabled'] and
                    old['model_assumptions']['horizontal_beamwidth_deg']==case['beamwidth_deg'] and
                    f"every {case['udp_interval_ms']:g} ms" in old['model_assumptions']['dl_application'])
        print('START',name,'cached',cached,flush=True)
        if not cached:
            with (HERE/(name+'.log')).open('w') as stream:
                subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True)
        result=json.loads((folder/'result.json').read_text())
        assert result['source_sha256']==plan['source_cpp_sha256']
        assert result['sites_sha256']==plan['input_hashes']['sites.csv']
        assert result['ue_positions_sha256']==plan['input_hashes']['ues.csv']
        metrics=radio.metrics(folder,1.0)
        if index==0:
            maximum=0.0
            for row in metrics['ues']:
                ref=reference[row['ue_id']]
                assert row['site']==ref['site']
                for key in ['sector','connected','dl_bytes','rsrp','sinr','rsrq','x_m','y_m']:
                    a,b=float(row[key]),float(ref[key])
                    assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8),(row['ue_id'],key,a,b)
                    maximum=max(maximum,abs(a-b))
            report['regression']={'passed':True,'max_numeric_difference':maximum}
            print('BASELINE REGRESSION PASSED',flush=True)
        training=evaluate(metrics,targets,'train')
        report['cases'].append({'case':case,'result':result,'metrics':metrics,'training':training})
        radio.save(HERE/'checkpoint.json',report)
        print('DONE',name,'train',training,'connected',result['connected_ues'],
              'DL',result['ues_receiving_dl'],'wall',round(result['wall_seconds'],1),flush=True)
    winner=min(report['cases'],key=lambda r:r['training']['score'])
    report['selected_name']=winner['case']['name']
    # Freeze the training-only choice before adding control-site comparisons.
    radio.save(HERE/'training_selection.json',{'selected_name':report['selected_name'],
                                              'rule':plan['selection_rule'],'training':winner['training']})
    for case in report['cases']:
        case['control']=evaluate(case['metrics'],targets,'holdout')
    report['completed']=True
    radio.save(HERE/'study_result.json',report)
    print('SEARCH COMPLETE',report['selected_name'],flush=True)


if __name__=='__main__':main()
