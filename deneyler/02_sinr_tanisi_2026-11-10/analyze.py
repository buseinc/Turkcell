"""Validate passive observations and attribute synthetic control interference."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]/'ana_proje'
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'matplotlib_cache'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def db(value):
    return 10*np.log10(value)


def main():
    plan = json.loads((HERE/'experiment_plan.json').read_text())
    folder = HERE/'simulation/results/diagnostic'
    native_result = json.loads((folder/'result.json').read_text())
    assert native_result['source_sha256'] == plan['diagnostic_cpp_sha256']
    assert hashlib.sha256((PROJECT/'simulation/sindirgi_baseline.cc').read_bytes()).hexdigest() == plan['original_cpp_sha256']
    for name,expected in plan['input_hashes'].items():
        assert hashlib.sha256((HERE/'inputs'/name).read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location('radio',PROJECT/'simulation/run_radio_study.py')
    radio = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(radio)
    metrics = radio.metrics(folder,1.0)
    current = pd.DataFrame(metrics['ues']).set_index('ue_id')
    old = pd.read_csv(PROJECT/'analysis/sindirgi/radio_study/final_ue_metrics.csv').set_index('ue_id')
    assert len(current) == len(old) == 64
    pd.testing.assert_frame_equal(current[['site','sector','connected','dl_bytes']],
                                   old[['site','sector','connected','dl_bytes']],check_dtype=False)
    delta = np.abs(current[['rsrp','sinr','rsrq']]-old[['rsrp','sinr','rsrq']]).to_numpy()
    assert float(np.nanmax(delta)) < 1e-8
    samples = pd.read_csv(folder/'sinr_components.csv')
    final_cells = pd.read_csv(folder/'ues.csv').set_index('ue_id').synthetic_cell_id
    samples = samples[samples.synthetic_cell_id.eq(samples.ue_id.map(final_cells)) & samples.time_s.ge(1)].copy()
    assert samples.ue_id.nunique() == 64 and samples.rb_count.eq(100).all()
    rsrp_error = (samples.native_rsrp_dbm-samples.reconstructed_rsrp_dbm).abs()
    sinr_error = (samples.native_sinr_db-samples.reconstructed_sinr_db).abs()
    assert float(rsrp_error.max()) < 1e-6
    assert float(sinr_error.max()) < 1e-6
    assert samples.interference_fraction.between(0,1).all()
    assert float(samples.signal_rb_relative_spread.max()) < 1e-8
    ue = samples.groupby('ue_id').mean(numeric_only=True).join(current[['site','sector','rsrp','sinr','rsrq','dl_bytes']])
    ue['rsrq_reconstruction_error_db'] = ue.rsrq_from_components_db-ue.rsrq
    ue['snr_minus_sinr_db'] = ue.snr_db-ue.native_sinr_db
    ue['interference_dominated'] = ue.interference_psd_w_hz.gt(ue.noise_psd_w_hz)
    ue['signal_below_noise'] = ue.snr_db.lt(0)
    ue['sinr_below_zero'] = ue.native_sinr_db.lt(0)
    # A separate calculation, using the exact antenna/path-loss formulae read from the pinned sources.
    sectors = pd.read_csv(folder/'sectors.csv')
    locations = pd.read_csv(folder/'ues.csv').set_index('ue_id')
    exponent = -3/(20*np.log10(np.cos(np.deg2rad(65/4))))
    reference_loss = 20*np.log10(4*np.pi*1815e6/299792458.0)
    contributions = []
    for ident,row in ue.iterrows():
        loc = locations.loc[ident]
        dx,dy,dz = loc.x_m-sectors.x_m,loc.y_m-sectors.y_m,loc.z_m-sectors.z_m
        distance = np.sqrt(dx*dx+dy*dy+dz*dz)
        angle = np.arctan2(dy,dx)-np.deg2rad(sectors.orientation_ccw_from_east_deg)
        angle = (angle+np.pi)%(2*np.pi)-np.pi
        pattern = np.cos(angle/2)**(2*exponent)
        pathloss = reference_loss+30*np.log10(np.maximum(distance,1))
        powers = 10**((46+15-pathloss-30)/10)*pattern
        serving = sectors.synthetic_cell_id.eq(loc.synthetic_cell_id)
        same_site = sectors.site.eq(row.site)
        signal = float(powers[serving].sum())
        interference = float(powers[~serving].sum())
        ue.loc[ident,'analytic_signal_error_db'] = float(db(signal/row.signal_total_w))
        ue.loc[ident,'analytic_interference_error_db'] = float(db(interference/row.interference_total_w))
        ue.loc[ident,'same_site_interference_fraction'] = float(powers[same_site & ~serving].sum()/interference)
        ordered = powers[~serving].sort_values(ascending=False)
        top = sectors.loc[ordered.index[0]]
        ue.loc[ident,'strongest_interferer_site'] = top.site
        ue.loc[ident,'strongest_interferer_sector'] = int(top.sector)
        ue.loc[ident,'strongest_interferer_fraction'] = float(ordered.iloc[0]/interference)
        for index,sector in sectors.iterrows():
            contributions.append({'ue_id':ident,'site':sector.site,'sector':sector.sector,
                'is_serving':bool(serving[index]),'same_site_as_serving':bool(same_site[index]),
                'received_power_w':float(powers[index]),'distance_m':float(distance[index])})
    assert float(ue.analytic_signal_error_db.abs().max()) < 1e-5
    assert float(ue.analytic_interference_error_db.abs().max()) < 1e-5
    ue.to_csv(HERE/'ue_diagnostics.csv')
    pd.DataFrame(contributions).to_csv(HERE/'sector_contributions.csv',index=False)
    site_table = ue.groupby('site').agg(ues=('sinr','size'),mean_snr_db=('snr_db','mean'),
        mean_sinr_db=('sinr','mean'),mean_interference_fraction=('interference_fraction','mean'),
        mean_same_site_interference_fraction=('same_site_interference_fraction','mean'))
    site_table.to_csv(HERE/'site_diagnostics.csv')
    examples = ue.sort_values('sinr').head(5)
    examples.to_csv(HERE/'lowest_sinr_examples.csv')
    checks = {
        'passed':True,'ues':64,'post_warmup_samples':len(samples),
        'native_output_regression_max_db':float(np.nanmax(delta)),
        'rsrp_reconstruction_max_error_db':float(rsrp_error.max()),
        'sinr_reconstruction_max_error_db':float(sinr_error.max()),
        'rsrq_reconstruction_max_error_db':float(ue.rsrq_reconstruction_error_db.abs().max()),
        'analytic_signal_max_error_db':float(ue.analytic_signal_error_db.abs().max()),
        'analytic_interference_max_error_db':float(ue.analytic_interference_error_db.abs().max()),
        'noise_figure_db':sorted(samples.noise_figure_db.unique().tolist()),
        'noise_psd_dbm_hz':float(db(samples.noise_psd_w_hz.iloc[0])+30),
        'noise_per_re_dbm':float(db(samples.noise_psd_w_hz.iloc[0]*15000)+30),
        'noise_over_100_rb_dbm':float(db(samples.noise_total_w.iloc[0])+30),
        'interference_dominated_ues':int(ue.interference_dominated.sum()),
        'signal_below_noise_ues':int(ue.signal_below_noise.sum()),
        'sinr_below_zero_ues':int(ue.sinr_below_zero.sum()),
        'low_sinr_with_signal_above_noise_ues':int((ue.sinr_below_zero & ~ue.signal_below_noise).sum()),
        'median_snr_db':float(ue.snr_db.median()),'median_sinr_db':float(ue.sinr.median()),
        'median_snr_minus_sinr_db':float(ue.snr_minus_sinr_db.median()),
        'median_interference_fraction':float(ue.interference_fraction.median()),
        'median_same_site_interference_fraction':float(ue.same_site_interference_fraction.median()),
        'strongest_interferer_same_site_ues':int(ue.strongest_interferer_site.eq(ue.site).sum()),
        'same_site_majority_interference_ues':int(ue.same_site_interference_fraction.gt(.5).sum()),
        'other_sites_majority_interference_ues':int(ue.same_site_interference_fraction.lt(.5).sum()),
        'control_channel_only':True,'original_baseline_unchanged':True}
    (HERE/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    fig,axes = plt.subplots(1,3,figsize=(16,5),constrained_layout=True)
    axes[0].scatter(ue.snr_db,ue.sinr,color='#0072b2',s=25)
    lo,hi = min(ue.snr_db.min(),ue.sinr.min())-1,max(ue.snr_db.max(),ue.sinr.max())+1
    axes[0].plot([lo,hi],[lo,hi],'k--',lw=1,label='Girişim yokken S/N = SINR')
    axes[0].legend(fontsize=7)
    axes[0].set(xlabel='Yalnız S/N: gürültüye göre sinyal (dB)',ylabel='S/(I+N): mevcut SINR (dB)',
                title='Her nokta aynı konumdaki bir sanal kullanıcı')
    axes[1].bar(ue.index,100*ue.interference_fraction,color='#0072b2',label='Girişim')
    axes[1].bar(ue.index,100*(1-ue.interference_fraction),bottom=100*ue.interference_fraction,color='#e69f00',label='Gürültü')
    axes[1].set(xlabel='Sanal kullanıcı kimliği',ylabel='SINR paydasındaki pay (%)',ylim=(0,100),title='Girişim ve gürültünün payı')
    axes[1].legend(fontsize=8)
    axes[2].bar(ue.index,100*ue.same_site_interference_fraction,color='#009e73',label='Aynı sahanın diğer sektörleri')
    axes[2].bar(ue.index,100*(1-ue.same_site_interference_fraction),bottom=100*ue.same_site_interference_fraction,color='#cc79a7',label='Diğer sahalar')
    axes[2].set(xlabel='Sanal kullanıcı kimliği',ylabel='Toplam girişimdeki pay (%)',ylim=(0,100),title='Doğrulanmış analitik girişim ayrımı')
    axes[2].legend(fontsize=7)
    for ax in axes:
        ax.grid(alpha=.2)
    fig.suptitle('24 saha / 72 aynı frekanslı sektör / 64 sabit UE — kontrol kanalı tanısı\n'
                 'S/N yeni bir şebeke koşusu değildir; aynı sinyalin yalnız gürültüye oranıdır.',fontsize=11)
    fig.savefig(HERE/'sinr_diagnostics.png',dpi=170)
    fig.savefig(HERE/'sinr_diagnostics.svg')
    plt.close(fig)
    print(json.dumps(checks,indent=2))


if __name__ == '__main__':
    main()
