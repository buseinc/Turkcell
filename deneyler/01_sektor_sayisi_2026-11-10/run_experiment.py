"""Run under WSL; gate alternatives on exact S0 regression and save evidence."""
from pathlib import Path
import importlib.util
import json
import math
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]/'ana_proje'
spec = importlib.util.spec_from_file_location('radio_metrics',PROJECT/'simulation/run_radio_study.py')
radio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radio)


def regression(metrics):
    old = {int(r['ue_id']):r for r in radio.read(
        PROJECT/'analysis/sindirgi/radio_study/final_ue_metrics.csv')}
    maximum = 0.0
    for row in metrics['ues']:
        ref = old[row['ue_id']]
        assert row['site'] == ref['site']
        for key in ['sector','connected','dl_bytes','rsrp','sinr','rsrq','x_m','y_m']:
            a, b = float(row[key]),float(ref[key])
            assert math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10), (row['ue_id'],key,a,b)
            maximum = max(maximum,abs(a-b))
    assert len(metrics['ues']) == len(old) == 64
    return {'passed':True,'ues':64,'max_numeric_difference':maximum}


def main():
    plan = json.loads((HERE/'experiment_plan.json').read_text())
    report = {'plan':'experiment_plan.json','cases':[],'completed':False}
    for index,case in enumerate(plan['cases']):
        name = case['name']
        args = [sys.executable,str(HERE/'simulation/run_baseline.py'),
                '--sites','0','--ues','64','--duration','4',
                '--sites-file',str(HERE/'inputs'/(name+'.csv')),
                '--ue-file',str(HERE/'inputs/ues.csv'),
                '--pathloss','log-distance','--exponent','3','--traffic','1','--name',name]
        if index:
            args.append('--skip-build')
        print('START',name,flush=True)
        with (HERE/(name+'.log')).open('w') as stream:
            subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT,check=True)
        folder = HERE/'simulation/results'/name
        metrics = radio.metrics(folder,plan['warmup_s'])
        result = json.loads((folder/'result.json').read_text())
        assert result['synthetic_sectors'] == case['total_sectors']
        assert result['source_sha256'] == plan['experiment_cpp_sha256']
        assert result['sites_sha256'] == case['sites_sha256']
        assert result['ue_positions_sha256'] == plan['ues_sha256']
        actual_sectors = radio.read(folder/'sectors.csv')
        baseline_sites = {r['site']:r for r in radio.read(HERE/'inputs/s0_three.csv')}
        for sector in actual_sectors:
            ref = baseline_sites[sector['site']]
            assert abs(float(sector['orientation_ccw_from_east_deg']) -
                       (float(ref['rotation_deg'])+120*int(sector['sector']))) < 1e-6
        if index == 0:
            report['regression'] = regression(metrics)
            print('S0 REGRESSION PASSED',report['regression'],flush=True)
        report['cases'].append({'name':name,'result':result,'metrics':metrics})
        radio.save(HERE/'study_result.json',report)
        print('DONE',name,'connected',result['connected_ues'],
              'DL',result['ues_receiving_dl'],'wall',round(result['wall_seconds'],1),flush=True)
    report['completed'] = True
    radio.save(HERE/'study_result.json',report)
    print('EXPERIMENT COMPLETE',flush=True)


if __name__ == '__main__':
    main()
