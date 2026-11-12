"""Run the two predeclared CQI modes in WSL with an S0 regression gate."""
from pathlib import Path
import importlib.util
import json
import math
import subprocess
import sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]/'ana_proje'
spec=importlib.util.spec_from_file_location('radio',PROJECT/'simulation/run_radio_study.py')
radio=importlib.util.module_from_spec(spec)
spec.loader.exec_module(radio)


def main():
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    report={'completed':False,'cases':[]}
    old={int(r['ue_id']):r for r in radio.read(PROJECT/'analysis/sindirgi/radio_study/final_ue_metrics.csv')}
    for index,case in enumerate(plan['cases']):
        name=case['name']
        args=[sys.executable,str(HERE/'simulation/run_baseline.py'),'--sites','0','--ues','64',
              '--duration','4','--sites-file',str(HERE/'inputs/sites.csv'),
              '--ue-file',str(HERE/'inputs/ues.csv'),'--mixed-cqi',str(case['mixed_cqi']),'--name',name]
        if index:args.append('--skip-build')
        print('START',name,flush=True)
        with (HERE/(name+'.log')).open('w') as stream:
            subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT,check=True)
        folder=HERE/'simulation/results'/name
        metrics=radio.metrics(folder,1.0)
        result=json.loads((folder/'result.json').read_text())
        assert result['source_sha256']==plan['experiment_cpp_sha256']
        assert result['sites_sha256']==plan['input_hashes']['sites.csv']
        assert result['ue_positions_sha256']==plan['input_hashes']['ues.csv']
        if index==0:
            maximum=0.0
            for row in metrics['ues']:
                ref=old[row['ue_id']]
                assert row['site']==ref['site']
                for key in ['sector','connected','dl_bytes','rsrp','sinr','rsrq','x_m','y_m']:
                    a,b=float(row[key]),float(ref[key])
                    assert math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10),(row['ue_id'],key,a,b)
                    maximum=max(maximum,abs(a-b))
            report['control_regression']={'passed':True,'max_numeric_difference':maximum}
            print('CONTROL REGRESSION PASSED',flush=True)
        report['cases'].append({'name':name,'result':result,'metrics':metrics})
        radio.save(HERE/'study_result.json',report)
        print('DONE',name,'connected',result['connected_ues'],'DL',result['ues_receiving_dl'],flush=True)
    report['completed']=True
    radio.save(HERE/'study_result.json',report)
    print('COMPARISON COMPLETE',flush=True)


if __name__=='__main__':main()
