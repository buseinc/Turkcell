"""Validate a static proxy, screen hypotheses, then freeze an ns-3 shortlist."""
from pathlib import Path
import hashlib
import itertools
import json
import shutil

import numpy as np
import pandas as pd
from scipy.spatial import Delaunay

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PROJECT=ROOT/'ana_proje'
JOINT=ROOT/'deneyler/04_ortak_radyo_taramasi_2026-11-10'
STUDY=PROJECT/'analysis/sindirgi/radio_study'
SEED=20261109
FAMILIES=['wide','near','uniform','mixed','far']


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)


def placement(family,seed,sites):
    anchors=sites[sites.role.eq('Evaluation')].reset_index(drop=True)
    rng=np.random.default_rng(seed)
    xyz=anchors[['x_m','y_m']].to_numpy()
    hull=Delaunay(xyz)
    rows=[]
    for u in range(64):
        anchor=anchors.iloc[u%8]
        if family=='uniform':
            for _ in range(10000):
                point=rng.uniform(xyz.min(axis=0),xyz.max(axis=0))
                if hull.find_simplex(point)>=0:break
            else:raise RuntimeError('Hull sampling failed')
            centre=''
        else:
            lo,hi={'wide':(1000,4000),'near':(500,2000),'far':(2000,6000),
                   'mixed':(500,2000) if (u//8)%2==0 else (2000,6000)}[family]
            angle=rng.uniform(0,2*np.pi)
            radius=np.sqrt(rng.uniform(lo*lo,hi*hi))
            point=anchor[['x_m','y_m']].to_numpy(dtype=float)+radius*np.array([np.cos(angle),np.sin(angle)])
            centre=anchor.site
        rows.append({'ue_id':u,'x_m':point[0],'y_m':point[1],'z_m':1.5,'placement_anchor':centre})
    return pd.DataFrame(rows)


def proxy(ues,sectors,beamwidth,exponent,power):
    delta=ues[['x_m','y_m','z_m']].to_numpy()[:,None,:]-sectors[['x_m','y_m','z_m']].to_numpy()[None,:,:]
    distances=np.linalg.norm(delta,axis=2)
    angles=np.arctan2(delta[:,:,1],delta[:,:,0])-np.deg2rad(sectors.orientation_ccw_from_east_deg.to_numpy())[None,:]
    angles=(angles+np.pi)%(2*np.pi)-np.pi
    shape=-3/(20*np.log10(np.cos(np.deg2rad(beamwidth/4))))
    gain=np.cos(angles/2)**(2*shape)
    reference=20*np.log10(4*np.pi*1815e6/299792458.0)
    loss=reference+10*exponent*np.log10(np.maximum(distances,1))
    powers=10**((power+15-loss-30)/10)*gain
    selected=powers.argmax(axis=1)
    signal=powers[np.arange(len(ues)),selected]
    noise=10**((-174+9-30)/10)*100*180000
    interference=powers.sum(axis=1)-signal
    rows=pd.DataFrame({'ue_id':ues.ue_id,'site':sectors.site.to_numpy()[selected],
        'sector':sectors.sector.to_numpy()[selected],
        'rsrp':10*np.log10(signal/(100*12))+30,
        'sinr':10*np.log10(signal/noise),
        'rsrq':10*np.log10(signal/(2*(signal+interference+noise)))})
    grouped=rows.groupby(['site','sector'])[['rsrp','sinr','rsrq']].mean().groupby('site').mean()
    return rows,grouped


def score(predicted,targets,split='train'):
    selected=targets[targets.split.eq(split)].join(predicted,rsuffix='_prediction')
    missing=selected[['rsrp','sinr','rsrq']].isna().any(axis=1)
    mae={m:float((selected.loc[~missing,m]-selected.loc[~missing,m+'_target']).abs().mean())
         if (~missing).any() else 1000.0 for m in ['rsrp','sinr','rsrq']}
    return {**{m+'_mae_db':value for m,value in mae.items()},
            'missing_sites':int(missing.sum()),'score':sum(mae.values())/3+10*int(missing.sum())}


def main():
    inputs=HERE/'inputs';inputs.mkdir(parents=True,exist_ok=True)
    sim=HERE/'simulation';sim.mkdir(exist_ok=True)
    for name in ['sites.csv','targets.csv']:
        shutil.copy2(JOINT/'inputs'/name,inputs/name)
    sites=pd.read_csv(inputs/'sites.csv')
    targets=pd.read_csv(inputs/'targets.csv').set_index('site')
    canonical={'wide':'wide-clusters','near':'clustered','uniform':'uniform-hull'}
    for family in FAMILIES:
        dest=inputs/f'ues_{family}.csv'
        if family in canonical:
            shutil.copy2(STUDY/'inputs'/f'ues_{canonical[family]}.csv',dest)
        else:
            placement(family,SEED,sites).to_csv(dest,index=False,float_format='%.9f')
        placement(family,20261110,sites).to_csv(inputs/f'ues_{family}_seed2.csv',index=False,float_format='%.9f')
    for count,buffer in [(32,24),(48,40)]:
        shutil.copy2(STUDY/'inputs'/f'sites_b{buffer}_az42.csv',inputs/f'sites_{count}.csv')
    sectors=pd.read_csv(JOINT/'simulation/results/b120_t50/sectors.csv')
    base_ues=pd.read_csv(inputs/'ues_wide.csv')
    base_rows,_=proxy(base_ues,sectors,120,3.0,46)
    actual=pd.read_csv(JOINT/'ue_comparison.csv')
    actual=actual[actual.case.eq('b120_t50')].set_index('ue_id')
    check=base_rows.set_index('ue_id')
    assert check.site.eq(actual.site).all() and check.sector.eq(actual.sector).all()
    error=float(np.abs(check[['rsrp','rsrq']]-actual[['rsrp','rsrq']]).to_numpy().max())
    assert error<1e-6,error
    # SINR=S/N here is an optimistic proxy, NOT the native mixed SINR result.
    proxy_checks={'static_rsrp_rsrq_max_error_db':error,'same_serving_sectors':True,
                  'sinr_proxy':'S/N only, ignoring data-channel interference; screening only'}
    rows=[]
    for family,width,exponent,power in itertools.product(FAMILIES,[65,90,120],[2.7,3.0,3.3],[43,46,49]):
        _,predicted=proxy(pd.read_csv(inputs/f'ues_{family}.csv'),sectors,width,exponent,power)
        rows.append({'family':family,'beamwidth_deg':width,'exponent':exponent,
                     'power_dbm':power,**score(predicted,targets)})
    table=pd.DataFrame(rows).sort_values(['score','family','beamwidth_deg','exponent','power_dbm'])
    table.to_csv(HERE/'proxy_screen.csv',index=False)
    family_best=table.groupby('family',sort=False).head(1).sort_values(['score','family'])
    candidates=[]
    for _,row in family_best.iterrows():
        if row.family=='wide' and row.beamwidth_deg==120 and row.exponent==3 and row.power_dbm==46:continue
        candidates.append(row.to_dict())
    chosen=candidates[:3]
    wide=next((r for r in candidates if r['family']=='wide'),None)
    if wide and not any(r['family']=='wide' for r in chosen):chosen.append(wide)
    if not any(r['exponent']!=3 for r in chosen) and len(chosen)<4:
        # Include one propagation challenge because S/N-only screening can mis-rank mixed SINR.
        chosen.append(table[table.exponent.ne(3)].iloc[0].to_dict())
    cases=[{'name':'baseline','family':'wide','beamwidth_deg':120,'exponent':3.0,'power_dbm':46,
            'ue_file':'ues_wide.csv','sites_file':'sites.csv','duration_s':4.0}]
    for index,row in enumerate(chosen,1):
        cases.append({'name':f'candidate_{index:02d}',
            'family':row['family'],'beamwidth_deg':int(row['beamwidth_deg']),
            'exponent':float(row['exponent']),'power_dbm':int(row['power_dbm']),
            'proxy_training_score':float(row['score']),
            'ue_file':f"ues_{row['family']}.csv",'sites_file':'sites.csv','duration_s':4.0})
    source=(JOINT/'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    source=replace_once(source,'    double beamwidth = 65.0;',
        '    double beamwidth = 65.0;\n    double enbPower = 46.0;')
    source=replace_once(source,'    cmd.Parse(argc, argv);',
        '    cmd.AddValue("enbPower", "Per-sector conducted Tx power dBm", enbPower);\n    cmd.Parse(argc, argv);')
    source=replace_once(source,'"ns3::LteEnbPhy::TxPower", DoubleValue(46.0)',
        '"ns3::LteEnbPhy::TxPower", DoubleValue(enbPower)')
    (sim/'sindirgi_baseline.cc').write_text(source,encoding='utf-8')
    runner=(JOINT/'simulation/run_baseline.py').read_text(encoding='utf-8')
    runner=replace_once(runner,"    parser.add_argument('--skip-build',action='store_true')",
        "    parser.add_argument('--enb-power',type=float,default=46)\n"
        "    parser.add_argument('--skip-build',action='store_true')")
    runner=replace_once(runner,"    run.append('--mixedCqi='+str(args.mixed_cqi))",
        "    run.append('--mixedCqi='+str(args.mixed_cqi))\n    run.append('--enbPower='+str(args.enb_power))")
    runner=replace_once(runner,"'enb_conducted_tx_power_dbm':46", "'enb_conducted_tx_power_dbm':args.enb_power")
    (sim/'run_baseline.py').write_text(runner,encoding='utf-8')
    shutil.copy2(JOINT/'simulation/ns3_paths.py',sim/'ns3_paths.py')
    plan={'purpose':'Explore uncertain UE distribution, propagation loss and power while preserving all data-defined inputs.',
        'screen_count':len(table),'proxy_checks':proxy_checks,'cases':cases,
        'families':{'wide':'8 UEs per anchor, 1-4 km annulus','near':'8 per anchor, 0.5-2 km',
            'uniform':'uniform in evaluation-site hull','mixed':'4 near and 4 far per anchor, 0.5-2 / 2-6 km',
            'far':'8 per anchor, 2-6 km'},
        'grid':{'beamwidth_deg':[65,90,120],'exponent':[2.7,3.0,3.3],'power_dbm':[43,46,49]},
        'spatial_seed':SEED,'independent_spatial_seed':20261110,'mixed_cqi':True,'udp_interval_ms':50,
        'fixed':'Known site coordinates, site IDs/roles, azimuths, three sectors/site, one carrier, band, receiver NF, original Experia targets and five/three site split.',
        'shortlist_rule':'Best training proxy per family; take best three distinct non-baseline families, additionally best wide-family variation if absent. If all use exponent 3 and room remains, add best exponent-not-3 challenge because S/N is only a proxy. At most four new native candidates.',
        'proxy_caveat':'Static strongest-cell association, exact model RSRP/RSRQ and optimistic S/N proxy for mixed SINR. These are screening estimates, not native experiment results.',
        'selection_rule':'Select among native baseline and shortlisted native cases only, using equal-weight mean of three training-site MAEs plus 10 dB per missing training site. Control sites excluded from ranking; all previously seen.',
        'followup_rule':'Freeze selected native model before controls. Check a new UE seed without retuning; test same selected UEs with 32 and 48 total sites, preserving common azimuths. Report both adjacent buffer differences using <=1 dB q95 RSRP/SINR and >=95% same serving sector.',
        'uncertainty':'UE distributions, power, exponent and antennas are hypotheses, not operator estimates; no terrain or shadowing is introduced. Three supplemental site locations remain unverified. Low synthetic load is not real demand.',
        'source_cpp_sha256':digest(sim/'sindirgi_baseline.cc'),
        'original_cpp_sha256':digest(PROJECT/'simulation/sindirgi_baseline.cc'),
        'input_hashes':{p.name:digest(p) for p in inputs.glob('*.csv')}}
    (HERE/'experiment_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print('STATIC PROXY CHECK',proxy_checks)
    print('SCREENED',len(table),'analytical hypotheses; NOT native runs')
    print(json.dumps(cases,indent=2))


if __name__=='__main__':main()
