"""Summarize the initial S0 diagnostic, without claiming measurement validation.

Run: python analysis/summarize_baseline.py
"""
from pathlib import Path
import json
import hashlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'simulation/results/sindirgi_s0_uniform'
OUT=ROOT/'analysis/sindirgi'


def cdf(ax,values,label,color):
    values=np.sort(np.asarray(values.dropna()))
    if len(values):
        ax.step(values,np.arange(1,len(values)+1)/len(values),where='post',label=label,color=color)


def main():
    result=json.loads((RUN/'result.json').read_text())
    sources=[ROOT/'simulation/sindirgi_baseline.cc',ROOT/'simulation/archive'/(result['source_sha256']+'.cc')]
    assert any(p.exists() and result['source_sha256']==hashlib.sha256(p.read_bytes()).hexdigest() for p in sources)
    assert result['sites_sha256']==hashlib.sha256((OUT/'sites_local.csv').read_bytes()).hexdigest()
    ues=pd.read_csv(RUN/'ues.csv')
    radio=pd.read_csv(RUN/'radio_samples.csv')
    sectors=pd.read_csv(RUN/'sectors.csv')
    sites=pd.read_csv(OUT/'sites_local.csv')
    assert len(ues)==result['ues'] and len(sectors)==result['synthetic_sectors']
    assert int(ues.dl_bytes.sum())==result['total_dl_bytes']
    assert int(ues.rrc_connected.sum())==result['connected_ues']
    assert int((ues.dl_bytes>0).sum())==result['ues_receiving_dl']
    assert len(radio)==result['radio_samples']
    assert set(radio.ue_id)<=set(ues.ue_id)
    assert set(radio.synthetic_cell_id)<=set(sectors.synthetic_cell_id)
    assert np.isfinite(radio[['rsrp_dbm','sinr_db']]).all().all()
    assert radio.rsrp_dbm.between(-200,0).all()
    # Omit initial radio acquisition from the exploratory distribution comparison.
    steady=radio[radio.time_s>=.5]
    per_ue=steady.groupby('ue_id').agg(mean_rsrp_dbm=('rsrp_dbm','mean'),
        mean_sinr_db=('sinr_db','mean'),radio_samples=('time_s','size'),
        first_sample_s=('time_s','min'),last_sample_s=('time_s','max'))
    summary=ues.merge(per_ue,left_on='ue_id',right_index=True,how='left',validate='one_to_one')
    summary=summary.merge(sectors[['synthetic_cell_id','site','role']],on='synthetic_cell_id',
                           how='left',validate='many_to_one')
    summary.to_csv(OUT/'ue_radio_summary.csv',index=False)
    selected_cells=pd.read_csv(ROOT/'sindirgi_lte_cells.csv')
    measured=pd.read_csv(ROOT/'analysis/radio_cell_summary.csv')
    observed=selected_cells[selected_cells.role=='Evaluation'][['cell_id','site_id']].merge(
        measured,left_on='cell_id',right_on='FIRSTCELL',validate='one_to_one')
    assert len(observed)==55
    observed.to_csv(OUT/'experia_evaluation_cells.csv',index=False)
    evaluated=summary[summary.role=='Evaluation']
    fig,axes=plt.subplots(1,2,figsize=(12,5),constrained_layout=True)
    for ax,sim,obs,title in [(axes[0],'mean_rsrp_dbm','rsrp_mean','RSRP (dBm)'),
                              (axes[1],'mean_sinr_db','sinr_mean','SINR (dB)')]:
        cdf(ax,evaluated[sim],f'S0: {len(evaluated)} evaluation-serving UEs','#0072b2')
        cdf(ax,observed[obs],'Experia: 55 evaluation cell time means','#d55e00')
        ax.set(xlabel=title,ylabel='Empirical cumulative fraction',ylim=(0,1.02))
        ax.grid(alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle('Exploratory comparison: different periods and sampling populations\n'
                 'UE time means after 0.5 s vs. measured cell time means; not calibration or validation',fontsize=10)
    fig.savefig(OUT/'radio_distribution_comparison.png',dpi=170)
    fig.savefig(OUT/'radio_distribution_comparison.svg')
    plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(13,7),constrained_layout=True)
    for ax,metric,label in [(axes[0],'mean_rsrp_dbm','RSRP (dBm)'),
                             (axes[1],'mean_sinr_db','SINR (dB; control-channel interference)')]:
        d=summary[summary[metric].notna()]
        art=ax.scatter(d.x_m/1000,d.y_m/1000,c=d[metric],cmap='viridis',s=28)
        fig.colorbar(art,ax=ax,label=label,shrink=.8)
        for role,color in [('Evaluation','#0072b2'),('Interference buffer','#d55e00')]:
            s=sites[sites.role==role]
            ax.scatter(s.x_m/1000,s.y_m/1000,marker='^',s=80,c=color,edgecolors='black',label=role,zorder=4)
        # 0.8 km arrows show antenna directions only; their length is not coverage.
        angle=np.radians(sectors.orientation_ccw_from_east_deg)
        ax.quiver(sectors.x_m/1000,sectors.y_m/1000,.8*np.cos(angle),.8*np.sin(angle),
                  angles='xy',scale_units='xy',scale=1,color='#555555',width=.003,alpha=.7)
        no_data=summary[summary.dl_bytes==0]
        ax.scatter(no_data.x_m/1000,no_data.y_m/1000,marker='x',c='red',s=45,
                   label='No DL bytes in 2 s',zorder=5)
        ax.set(xlabel='East from reference (km)',ylabel='North from reference (km)',aspect='equal')
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=8,loc='upper left')
    fig.suptitle('S0: sampled synthetic UE radio values; not continuous coverage boundaries\n'
                 'Arrows show assumed sector directions. Flat ground; no shadowing/fading.',fontsize=11)
    fig.savefig(OUT/'ue_radio_samples.png',dpi=170)
    fig.savefig(OUT/'ue_radio_samples.svg')
    plt.close(fig)
    quantiles={}
    for name,d,col in [('s0_rsrp',evaluated,'mean_rsrp_dbm'),('experia_rsrp',observed,'rsrp_mean'),
                       ('s0_sinr',evaluated,'mean_sinr_db'),('experia_sinr',observed,'sinr_mean')]:
        quantiles[name]={'n':int(d[col].notna().sum()),'q05':float(d[col].quantile(.05)),
                         'median':float(d[col].median()),'q95':float(d[col].quantile(.95))}
    report={'sites':len(sites),'sectors':len(sectors),'ues':len(ues),
            'rrc_connected':int(ues.rrc_connected.sum()),'ues_with_dl_bytes':int((ues.dl_bytes>0).sum()),
            'zero_dl_ue_ids':ues.loc[ues.dl_bytes==0,'ue_id'].tolist(),
            'radio_samples':len(radio),'wall_seconds':result['wall_seconds'],
            'evaluation_serving_ues':len(evaluated),'quantiles':quantiles,
            'interpretation':['2-second diagnostic, not an availability or service-level estimate.',
              'Uniform UE placement is an assumption; observation population is unknown.',
              'Synthetic sector IDs do not map one-to-one to measured cell IDs.',
              'SINR uses PDCCH interference; Experia aggregation/channel semantics are not confirmed.',
              'Buffer convergence, alternative placements/seeds/models and holdout checks remain.']}
    (OUT/'baseline_summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
