"""Freeze stage-3 inputs and evaluation rules before simulation sweeps."""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
from scipy.spatial import Delaunay

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/sindirgi/radio_study'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    inputs=OUT/'inputs';inputs.mkdir(exist_ok=True)
    original=pd.read_csv(ROOT/'analysis/sindirgi/sites_local.csv')
    candidates=pd.read_csv(ROOT/'analysis/sindirgi/candidate_sites.csv')
    evaluation=original[original.role=='Evaluation'].copy()
    ids=sorted(evaluation.site)
    holdout=sorted(np.random.default_rng(20261109).choice(ids,3,replace=False).tolist())
    training=sorted(set(ids)-set(holdout))
    buffer=candidates[~candidates.site.isin(ids)].sort_values(['distance_to_core_km','site'])
    # Fixed per-site rotations: adding neighbours never changes interior antennas.
    for seed in [42,7,99]:
        rotations=dict(zip(sorted(candidates.site),np.random.default_rng(seed).uniform(0,120,len(candidates))))
        for n in [8,16,24,40,64]:
            selected=pd.concat([evaluation[['site','role','x_m','y_m']],
                buffer.head(n)[['site','role','x_m','y_m']].assign(role='Interference buffer')],ignore_index=True)
            selected['rotation_deg']=selected.site.map(rotations)
            selected.to_csv(inputs/f'sites_b{n}_az{seed}.csv',index=False,float_format='%.9f')
            if n==8 and seed==42:
                selected[~selected.site.isin(['SITE_000553','SITE_000554','SITE_000555'])].to_csv(
                    inputs/'sites_without_selection_only.csv',index=False,float_format='%.9f')
    assert set(pd.read_csv(inputs/'sites_b8_az42.csv').site)==set(original.site)
    xyz=evaluation[['x_m','y_m']].to_numpy()
    hull=Delaunay(xyz)
    for placement in ['uniform-hull','clustered','wide-clusters']:
        rng=np.random.default_rng(20261109)
        rows=[]
        for u in range(64):
            anchor=evaluation.iloc[u%len(evaluation)]
            if placement=='uniform-hull':
                for _ in range(10000):
                    p=rng.uniform(xyz.min(axis=0),xyz.max(axis=0))
                    if hull.find_simplex(p)>=0:break
                else:raise RuntimeError('Could not sample evaluation hull')
                centre=''
            else:
                lo,hi=(500,2000) if placement=='clustered' else (1000,4000)
                angle=rng.uniform(0,2*np.pi)
                radius=np.sqrt(rng.uniform(lo**2,hi**2))
                p=anchor[['x_m','y_m']].to_numpy(dtype=float)+radius*np.array([np.cos(angle),np.sin(angle)])
                centre=anchor.site
            rows.append({'ue_id':u,'x_m':p[0],'y_m':p[1],'z_m':1.5,'placement_anchor':centre})
        pd.DataFrame(rows).to_csv(inputs/f'ues_{placement}.csv',index=False,float_format='%.9f')
    measured=pd.read_csv(ROOT/'analysis/radio_cell_summary.csv')
    links=pd.read_csv(ROOT/'sindirgi_lte_cells.csv')
    target=links[links.role=='Evaluation'][['cell_id','site_id']].merge(measured,left_on='cell_id',right_on='FIRSTCELL')
    assert len(target)==55
    target=target.groupby('site_id').agg(measured_cells=('cell_id','size'),
        rsrp_target=('rsrp_mean','mean'),sinr_target=('sinr_mean','mean'),
        rsrq_target=('rsrq_mean','mean'),min_hours=('hours','min')).reset_index().rename(columns={'site_id':'site'})
    target['split']=np.where(target.site.isin(holdout),'holdout','train')
    target.to_csv(OUT/'measured_site_targets.csv',index=False)
    plan={'purpose':'Complete stage 3 as a reproducible radio plausibility/sensitivity study; no operator reconstruction claim.',
        'training_sites':training,'holdout_sites':holdout,'split_seed':20261109,
        'holdout_caveat':'Initial S0 explored all sites earlier. Holdout is prospective for this parameter search, not a blind external test.',
        'ue_count':64,'spatial_seed':20261109,'ns3_seed':42,'ns3_run':1,
        'warmup_s':1.0,'screening_duration_s':2.0,'confirmation_duration_s':4.0,
        'placements':{'uniform-hull':'Uniform within convex hull of eight evaluation sites; this hull is a scenario boundary.',
                      'clustered':'8 synthetic UEs per evaluation anchor; uniform annulus 0.5–2 km.',
                      'wide-clusters':'8 synthetic UEs per evaluation anchor; uniform annulus 1–4 km.'},
        'models':[{'name':'log3','pathloss':'log-distance','exponent':3.0},
                  {'name':'log27','pathloss':'log-distance','exponent':2.7},
                  {'name':'cost231','pathloss':'okumura','exponent':3.0}],
        'model_caveat':'OkumuraHata above 1.5 GHz uses COST231 with MediumCity. No rural/terrain correction is claimed; sub-km or long links extrapolate its usual macro domain.',
        'selection_rule':'Minimum training-site RSRP MAE + 10 dB per missing training site. No SINR, RSRQ or holdout values used for selection.',
        'diagnostic_rsrp_mae_target_db':5.0,
        'target_caveat':'5 dB is an explicit engineering diagnostic target, not an operator-certified validation threshold.',
        'azimuth_seeds':[42,7,99],'buffer_levels':[8,16,24,40,64],
        'buffer_rule':'Same UEs and per-site rotations. Stop after two consecutive expansions pass, or at 64 neighbours.',
        'buffer_tolerances':{'rsrp_q95_absolute_change_db':1.0,'sinr_q95_absolute_change_db':1.0,
                             'same_serving_sector_fraction_min':0.95},
        'confirmation_rule':'Freeze winner before holdout evaluation; extend duration from 2 to 4 s; reserve SINR/RSRQ as untuned checks.',
        'confirmation_controls':'Also run 4 seconds without UDP to isolate duration changes from probe-traffic effects.',
        'unverified_coordinate_sites':['SITE_000553','SITE_000554','SITE_000555'],
        'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [ROOT/'analysis/radio_cell_summary.csv',ROOT/'sindirgi_lte_cells.csv',ROOT/'analysis/sindirgi/candidate_sites.csv']}}
    (OUT/'experiment_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(json.dumps({'train':training,'holdout':holdout,'screening_cases':9,'ues':64},indent=2))


if __name__=='__main__':main()
