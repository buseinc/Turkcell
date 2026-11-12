"""Run the predeclared stage-3 campaign under WSL, resumably and sequentially.

Only standard-library Python is needed in WSL. The preparation/report scripts
run in the project's Windows Python environment. No measured targets are fit
outside the training split, and SINR/RSRQ are never tuning objectives.
"""
from collections import defaultdict
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
STUDY=ROOT/'analysis/sindirgi/radio_study'
INPUTS=STUDY/'inputs'
RESULTS=HERE/'results/stage3'


def read(path):
    with path.open() as f:return list(csv.DictReader(f))


def avg(values):
    values=[v for v in values if v is not None and math.isfinite(v)]
    return statistics.mean(values) if values else None


def quantile(values,q):
    values=sorted(v for v in values if v is not None and math.isfinite(v))
    if not values:return None
    x=(len(values)-1)*q;i=int(x)
    return values[i]+(values[min(i+1,len(values)-1)]-values[i])*(x-i)


def save(path,data):
    path.write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')


def metrics(folder,warmup):
    ues=read(folder/'ues.csv');sectors=read(folder/'sectors.csv')
    cell={int(s['synthetic_cell_id']):s for s in sectors}
    power=defaultdict(list);quality=defaultdict(list);gaps=defaultdict(list)
    sinr=defaultdict(list);physical_power=defaultdict(list)
    final={int(u['ue_id']):int(u['synthetic_cell_id']) for u in ues}
    connected={int(u['ue_id']):float(u['connected_at_s']) for u in ues}
    for r in read(folder/'measurements.csv'):
        u=int(r['ue_id']);cid=int(r['synthetic_cell_id'])
        if float(r['time_s'])<max(warmup,connected[u]) or cid!=final[u] or not cid:continue
        power[u].append(float(r['rsrp_dbm']));quality[u].append(float(r['rsrq_db']))
        gaps[u].append(float(r['serving_gap_db']))
    for r in read(folder/'radio_samples.csv'):
        u=int(r['ue_id'])
        if float(r['time_s'])<max(warmup,connected[u]) or int(r['synthetic_cell_id'])!=final[u]:continue
        sinr[u].append(float(r['sinr_db']));physical_power[u].append(float(r['rsrp_dbm']))
    per_ue=[];by_sector=defaultdict(list)
    for u in ues:
        ident=int(u['ue_id']);s=cell.get(final[ident])
        row={'ue_id':ident,'site':s['site'] if s else None,'sector':int(s['sector']) if s else None,
             'role':s['role'] if s else None,'x_m':float(u['x_m']),'y_m':float(u['y_m']),
             'rsrp':avg(power[ident]),'rsrq':avg(quality[ident]),'sinr':avg(sinr[ident]),
             'best_serving_gap_db':avg(gaps[ident]),'connected':int(u['rrc_connected']),
             'connected_at_s':float(u['connected_at_s']),'dl_bytes':int(u['dl_bytes']),
             'power_trace_difference_db':None}
        p=avg(physical_power[ident])
        if p is not None and row['rsrp'] is not None:row['power_trace_difference_db']=abs(p-row['rsrp'])
        if s:
            dx=row['x_m']-float(s['x_m']);dy=row['y_m']-float(s['y_m'])
            row['serving_distance_m']=math.sqrt(dx*dx+dy*dy+28.5**2)
            by_sector[(row['site'],row['sector'])].append(row)
        per_ue.append(row)
    by_site=defaultdict(list)
    for (site,_),rows in by_sector.items():
        by_site[site].append({m:avg([r[m] for r in rows]) for m in ['rsrp','sinr','rsrq']})
    sites={site:{m:avg([r[m] for r in rows]) for m in ['rsrp','sinr','rsrq']}
           |{'active_sectors':len(rows)} for site,rows in by_site.items()}
    diffs=[r['power_trace_difference_db'] for r in per_ue]
    out={'sites':sites,'ues':per_ue,'warmup_s':warmup,
         'rsrp_trace_agreement_q95_db':quantile(diffs,.95),
         'serving_gap_q95_db':quantile([r['best_serving_gap_db'] for r in per_ue],.95)}
    # Both native traces implement the same RSRP reference-power conversion.
    assert out['rsrp_trace_agreement_q95_db'] is not None and out['rsrp_trace_agreement_q95_db']<1.0,out
    save(folder/'metrics.json',out)
    return out


def errors(m,targets,split):
    rows=[];missing=[]
    for t in targets:
        if t['split']!=split:continue
        s=m['sites'].get(t['site'],{})
        if s.get('rsrp') is None:missing.append(t['site']);continue
        rows.append({'site':t['site'],'rsrp_error_db':s['rsrp']-float(t['rsrp_target']),
                     'sinr_error_db':None if s.get('sinr') is None else s['sinr']-float(t['sinr_target']),
                     'rsrq_error_db':None if s.get('rsrq') is None else s['rsrq']-float(t['rsrq_target'])})
    mae=avg([abs(r['rsrp_error_db']) for r in rows])
    return {'rsrp_mae_db':mae,'missing_sites':missing,'site_errors':rows,
            'selection_score':(mae if mae is not None else 1000)+10*len(missing)}


def pair_check(a,b,tolerances):
    left={r['ue_id']:r for r in a['ues']};right={r['ue_id']:r for r in b['ues']}
    assert set(left)==set(right)
    for u in left:
        assert abs(left[u]['x_m']-right[u]['x_m'])<1e-6
        assert abs(left[u]['y_m']-right[u]['y_m'])<1e-6
    pairs=[(left[u],right[u]) for u in left if left[u]['rsrp'] is not None and right[u]['rsrp'] is not None]
    same=sum(x['site']==y['site'] and x['sector']==y['sector'] for x,y in pairs)/len(left)
    dp=quantile([abs(x['rsrp']-y['rsrp']) for x,y in pairs],.95)
    ds=quantile([abs(x['sinr']-y['sinr']) for x,y in pairs if x['sinr'] is not None and y['sinr'] is not None],.95)
    passed=(dp is not None and ds is not None and dp<=tolerances['rsrp_q95_absolute_change_db']
            and ds<=tolerances['sinr_q95_absolute_change_db'] and same>=tolerances['same_serving_sector_fraction_min'])
    return {'paired_ues':len(pairs),'rsrp_q95_abs_change_db':dp,'sinr_q95_abs_change_db':ds,
            'same_serving_sector_fraction':same,'passed':passed}


def main():
    plan=json.loads((STUDY/'experiment_plan.json').read_text())
    targets=read(STUDY/'measured_site_targets.csv')
    RESULTS.mkdir(parents=True,exist_ok=True)
    source_hash=hashlib.sha256((HERE/'sindirgi_baseline.cc').read_bytes()).hexdigest()
    def run_case(name,placement,model,buffer=8,az=42,duration=2.0,traffic=False,without=False):
        folder=RESULTS/name
        sites=INPUTS/('sites_without_selection_only.csv' if without else f'sites_b{buffer}_az{az}.csv')
        ues=INPUTS/f'ues_{placement}.csv'
        cached=False
        if (folder/'result.json').exists():
            old=json.loads((folder/'result.json').read_text())
            cached=(old['source_sha256']==source_hash and old['duration_s']==duration
                and old['sites_sha256']==hashlib.sha256(sites.read_bytes()).hexdigest()
                and old['ue_positions_sha256']==hashlib.sha256(ues.read_bytes()).hexdigest()
                and old['model_assumptions']['propagation']==model['pathloss']
                and old['model_assumptions']['log_distance_exponent']==model['exponent']
                and old['diagnostic_udp_enabled']==traffic)
        if not cached:
            args=[sys.executable,str(HERE/'run_baseline.py'),'--skip-build','--name','stage3/'+name,
                  '--sites','0','--sites-file',str(sites),'--ue-file',str(ues),'--ues','64',
                  '--duration',str(duration),'--pathloss',model['pathloss'],'--exponent',str(model['exponent']),
                  '--traffic','1' if traffic else '0']
            print('START',name,flush=True)
            p=subprocess.run(args,capture_output=True,text=True)
            if p.returncode:
                print(p.stdout,p.stderr,flush=True)
                raise RuntimeError(f'Failed case {name}: inspect {folder}')
        m=metrics(folder,plan['warmup_s'])
        r=json.loads((folder/'result.json').read_text())
        print('DONE',name,'RRC',r['connected_ues'],'/64','wall',round(r['wall_seconds'],1),flush=True)
        return {'name':name,'placement':placement,'model':model,'buffer':buffer,'azimuth_seed':az,
                'duration_s':duration,'traffic':traffic,'result':r,'metrics':m}

    screening=[]
    for placement in plan['placements']:
        for model in plan['models']:
            name=f'screen_{placement}_{model["name"]}'
            c=run_case(name,placement,model)
            c['training']=errors(c['metrics'],targets,'train')
            screening.append(c)
            save(STUDY/'screening_checkpoint.json',screening)
    winner=min(screening,key=lambda c:c['training']['selection_score'])
    frozen={k:winner[k] for k in ['name','placement','model','buffer','azimuth_seed','training']}
    frozen['holdout_not_used_for_selection']=True
    save(STUDY/'selected_configuration.json',frozen)
    print('FROZEN WINNER',winner['name'],winner['training']['rsrp_mae_db'],flush=True)

    azimuths=[winner]
    for az in [7,99]:
        azimuths.append(run_case(f'azimuth_{az}',winner['placement'],winner['model'],az=az))
    save(STUDY/'azimuth_cases.json',azimuths)
    buffers=[winner];comparisons=[];stable_buffer=None
    previous=winner
    for n in [16,24,40,64]:
        current=run_case(f'buffer_{n}',winner['placement'],winner['model'],buffer=n)
        # Match common antennas by site/sector, not changing numeric cell IDs.
        a={(s['site'],s['sector']):float(s['orientation_ccw_from_east_deg']) for s in read(RESULTS/previous['name']/'sectors.csv')}
        b={(s['site'],s['sector']):float(s['orientation_ccw_from_east_deg']) for s in read(RESULTS/current['name']/'sectors.csv')}
        assert all(abs(v-b[k])<1e-6 for k,v in a.items())
        check=pair_check(previous['metrics'],current['metrics'],plan['buffer_tolerances'])
        check.update({'from_buffer':previous['buffer'],'to_buffer':n})
        comparisons.append(check);buffers.append(current)
        save(STUDY/'buffer_checks.json',{'checks':comparisons,'cases':buffers})
        if len(comparisons)>=2 and comparisons[-1]['passed'] and comparisons[-2]['passed']:
            stable_buffer=comparisons[-2]['from_buffer'];break
        previous=current
    selected_buffer=stable_buffer if stable_buffer is not None else buffers[-1]['buffer']
    final=run_case('final_confirmation',winner['placement'],winner['model'],buffer=selected_buffer,
                   duration=plan['confirmation_duration_s'],traffic=True)
    final['training']=errors(final['metrics'],targets,'train')
    final['holdout']=errors(final['metrics'],targets,'holdout')
    reference=next(c for c in buffers if c['buffer']==selected_buffer)
    duration_check=pair_check(reference['metrics'],final['metrics'],plan['buffer_tolerances'])
    long_radio=run_case('long_radio_confirmation',winner['placement'],winner['model'],
                        buffer=selected_buffer,duration=plan['confirmation_duration_s'],traffic=False)
    duration_only=pair_check(reference['metrics'],long_radio['metrics'],plan['buffer_tolerances'])
    probe_only=pair_check(long_radio['metrics'],final['metrics'],plan['buffer_tolerances'])
    uncertainty=run_case('without_unverified_sites',winner['placement'],winner['model'],without=True)
    uncertainty_effect=pair_check(winner['metrics'],uncertainty['metrics'],plan['buffer_tolerances'])
    final['rsrp_holdout_diagnostic_passed']=(not final['holdout']['missing_sites'] and
          final['holdout']['rsrp_mae_db'] is not None and final['holdout']['rsrp_mae_db']<=plan['diagnostic_rsrp_mae_target_db'])
    report={'selected':frozen,'buffer_converged':stable_buffer is not None,
        'selected_buffer_count':selected_buffer,'buffer_checks':comparisons,
        'duration_and_probe_traffic_check':duration_check,'final':final,
        'duration_only_check':duration_only,'probe_traffic_only_check':probe_only,
        'long_radio_confirmation':long_radio,
        'unverified_coordinate_sensitivity':uncertainty_effect,'unverified_case':uncertainty,
        'screening_case_count':len(screening),'azimuth_case_count':len(azimuths),
        'experiment_plan':'experiment_plan.json','stage3_campaign_completed':True,
        'interpretation':'Completion means the predeclared checks were executed; operator-equivalent validation is not implied.'}
    save(STUDY/'study_result.json',report)
    print('STUDY COMPLETE',json.dumps({'selected':winner['name'],'buffer':selected_buffer,
        'buffer_converged':stable_buffer is not None,'holdout_mae_db':final['holdout']['rsrp_mae_db'],
        'holdout_diagnostic_passed':final['rsrp_holdout_diagnostic_passed']}),flush=True)


if __name__=='__main__':main()
