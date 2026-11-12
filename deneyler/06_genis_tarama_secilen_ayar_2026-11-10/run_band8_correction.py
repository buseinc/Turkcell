"""Keep unsupported 20 MHz Band 8 runs as rejected diagnostics; rerun at 10 MHz.

An explicit protocol correction, not an opportunity to tune against controls.
The original 49-run source and its hashes remain unchanged.
"""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import importlib.util

HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
    plan=json.loads((HERE/'experiment_plan.json').read_text())
    source=HERE/'simulation';fixed=HERE/'band8_10mhz_v2';fixed.mkdir(exist_ok=True)
    cpp=(source/'sindirgi_baseline.cc').read_text()
    assert cpp.count('UintegerValue(100));')==2
    cpp=cpp.replace('UintegerValue(100));','UintegerValue(50));')
    # Remove the last 50%3 unused RBs for this flat-PSD, no-fading experiment.
    # Native lte-ue-phy.cc:747-760 applies an edge-RB prefix average; the
    # simplified mean here is empirically checked against EVERY native sample.
    # It is not a generic reconstruction for arbitrary frequency-selective PSDs.
    assert cpp.count('for (uint32_t k=0;k<count;++k,++signalIt)')==1
    cpp=cpp.replace('for (uint32_t k=0;k<count;++k,++signalIt)',
        'const uint32_t mixedActive=count-(count==50 ? count%3 : 0);\n    for (uint32_t k=0;k<mixedActive;++k,++signalIt)')
    cpp=cpp.replace('mixed /= count;','mixed /= mixedActive;')
    (fixed/'sindirgi_baseline.cc').write_text(cpp)
    runner=(source/'run_baseline.py').read_text()
    assert runner.count("'bandwidth_rb':100")==1
    (fixed/'run_baseline.py').write_text(runner.replace("'bandwidth_rb':100","'bandwidth_rb':50"))
    for name in ['static-shadow-model.h','ns3_paths.py']:shutil.copy2(source/name,fixed/name)
    radio=module('correction_radio',HERE.parents[1]/'ana_proje/simulation/run_radio_study.py')
    evaluation=module('correction_evaluation',HERE.parent/'radio_joint_search_2026-11-10/run_search.py')
    targets=radio.read(HERE/'inputs/targets.csv')
    correction={'reason':'Band 8 supports at most 10 MHz here; original 100 RB (20 MHz) is unsupported.',
        'source':'https://www.etsi.org/deliver/etsi_ts/136100_136199/136101/18.05.00_60/ts_136101v180500p.pdf',
        'section':'Table 5.6.1-1',
        'rule':'Reject the two original Band 8 diagnostics; replace only their channel width (50 RB = 10 MHz), retain other inputs. Compare training only; if corrected result enters top three, expand common-draw validation before recommending.',
        'rejected_names':[],'runs':[],'source_cpp_sha256':digest(fixed/'sindirgi_baseline.cc'),
        'passive_observer_repeat_runs':2,
        'observer_correction':'For 50 RB, mirror native mixed-CQI averaging over the first 48 RB; native LTE model is unchanged. Preserve v1 outputs and verify all native trace CSV hashes identical.',
        'code_hashes':{n:digest(fixed/n) for n in ['sindirgi_baseline.cc','run_baseline.py','static-shadow-model.h']}}
    cases=[c for c in plan['screening_cases'] if c['dl_earfcn']==3600]
    amendment=HERE/'band8_amendment.json';backup=HERE/'band8_amendment_initial.json'
    if amendment.exists() and not backup.exists():shutil.copy2(amendment,backup)
    amendment.write_text(json.dumps({**correction,'runs':[],
        'rejected_names':[c['name'] for c in cases]},indent=2))
    for index,original in enumerate(cases):
        case=copy.deepcopy(original);case['name']=original['name']+'_10mhz';case['bandwidth_rb']=50
        name=case['name'];folder=fixed/'results'/name
        sites=HERE/'inputs'/f"sites_24_{case['azimuth_seed']}_{case['sector_policy']}.csv"
        ues=HERE/'inputs'/f"ues_{case['family']}_{case['spatial_seed']}.csv"
        command=[sys.executable,str(fixed/'run_baseline.py'),'--sites','0','--ues','64','--duration','2',
            '--sites-file',str(sites),'--ue-file',str(ues),'--mixed-cqi','1',
            '--beamwidth',str(case['beamwidth_deg']),'--exponent',str(case['exponent']),
            '--enb-power',str(case['power_dbm']),'--receiver-nf',str(case['ue_nf_db']),
            '--shadow-std',str(case['shadow_std_db']),'--shadow-seed',str(case['shadow_seed']),
            '--dl-earfcn',str(case['dl_earfcn']),'--ul-earfcn',str(case['ul_earfcn']),
            '--udp-interval-ms',str(case['udp_interval_ms']),'--name',name]
        if index:command.append('--skip-build')
        with (HERE/(name+'.log')).open('w') as stream:
            subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True)
        native=json.loads((folder/'result.json').read_text())
        assert native['source_sha256']==correction['source_cpp_sha256']
        assert native['sites_sha256']==digest(sites) and native['ue_positions_sha256']==digest(ues)
        assert native['model_assumptions']['bandwidth_rb']==50
        metrics=radio.metrics(folder,1.0)
        previous=HERE/'band8_10mhz/results'/name
        trace_hashes={n:digest(folder/n) for n in ['ues.csv','sectors.csv','radio_samples.csv','measurements.csv']}
        for n,h in trace_hashes.items():assert digest(previous/n)==h,(name,n,'observer changed native outputs')
        entry={'case':case,'result':native,'metrics':metrics,'training':evaluation.evaluate(metrics,targets,'train'),
               'replaces':original['name'],'result_folder':str(folder.relative_to(HERE)),
               'observer_regression':{'passed':True,'native_trace_hashes_identical':trace_hashes}}
        correction['rejected_names'].append(original['name']);correction['runs'].append(entry)
        (HERE/'band8_correction.json').write_text(json.dumps(correction,indent=2))
        print(name,'score',entry['training']['score'],flush=True)
    print('CORRECTION COMPLETE',flush=True)

if __name__=='__main__':main()
