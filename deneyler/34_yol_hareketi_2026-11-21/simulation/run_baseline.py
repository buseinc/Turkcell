"""Compile the local diagnostic against the existing ns-3.44 build and run it.

Run under WSL. Reuses compiler options from ns-3's stock EPC example;
does not copy or alter simulator source files.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys
import os
import shlex
import subprocess
import time
from ns3_paths import ns3_root

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
NS3=ns3_root()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sites',type=int,default=2)
    parser.add_argument('--ues',type=int,default=6)
    parser.add_argument('--duration',type=float,default=1.2)
    parser.add_argument('--placement',choices=['near-sites','uniform'],default='near-sites')
    parser.add_argument('--name',default='geographical_smoke')
    parser.add_argument('--sites-file',type=Path,default=ROOT/'analysis/sindirgi/sites_local.csv')
    parser.add_argument('--ue-file',type=Path)
    parser.add_argument('--pathloss',choices=['log-distance','okumura','rma'],default='log-distance')
    parser.add_argument('--exponent',type=float,default=3.0)
    parser.add_argument('--traffic',type=int,choices=[0,1],default=1)
    parser.add_argument('--mixed-cqi',type=int,choices=[0,1],default=0)
    parser.add_argument('--beamwidth',type=float,default=65)
    parser.add_argument('--udp-interval-ms',type=float,default=50)
    parser.add_argument('--udp-jitter',type=int,choices=[0,1],default=0)
    parser.add_argument('--enb-power',type=float,default=46)
    parser.add_argument('--shadow-std',type=float,default=0)
    parser.add_argument('--receiver-nf',type=float,default=9)
    parser.add_argument('--shadow-seed',type=int,default=42)
    parser.add_argument('--dl-earfcn',type=int,default=1300)
    parser.add_argument('--ul-earfcn',type=int,default=19300)
    parser.add_argument('--indoor-loss',type=float,default=0)
    parser.add_argument('--downtilt',type=float,default=0)
    parser.add_argument('--vertical-pattern',type=int,choices=[0,1],default=0)
    parser.add_argument('--vertical-beamwidth',type=float,default=10)
    parser.add_argument('--measurement-ues',type=int,default=256)
    parser.add_argument('--link-shadow-std',type=float,default=0)
    parser.add_argument('--antenna-3gpp',type=int,choices=[0,1],default=0)
    parser.add_argument('--max-attenuation',type=float,default=25)
    parser.add_argument('--evm',type=float,default=0)
    parser.add_argument('--pf-buffer-aware',type=int,default=0)
    parser.add_argument('--srs-periodicity',type=int,default=0)
    parser.add_argument('--dl-phy-traces',type=int,choices=[0,1],default=0)  # experiment 33
    # experiment 34 (DUZELTMELER.md)
    parser.add_argument('--spatial-shadow',type=int,choices=[0,1],default=0)
    parser.add_argument('--spatial-los',type=int,choices=[0,1],default=0)
    parser.add_argument('--handover',type=int,choices=[0,1],default=0)
    parser.add_argument('--waypoints',type=Path)
    parser.add_argument('--corr-sites',type=Path)
    parser.add_argument('--corr-k0',type=float,default=0)
    parser.add_argument('--corr-k1',type=float,default=0)
    parser.add_argument('--skip-build',action='store_true')
    args=parser.parse_args()
    if Path(args.name).is_absolute() or '..' in Path(args.name).parts:
        raise ValueError('Run name must stay under results')
    assert (NS3/'VERSION').read_text().strip()=='3.44'
    out=HERE/'results'/args.name
    out.mkdir(parents=True,exist_ok=True)
    build=HERE/'build'
    build.mkdir(exist_ok=True)
    source_hash=hashlib.sha256(b''.join(p.read_bytes() for p in [HERE/'sindirgi_baseline.cc', HERE/'building-vertical-model.h', HERE/'static-shadow-model.h', HERE/'build_private_lte.py', HERE/'spatial-field.h', HERE/'handover-support.h'])).hexdigest()
    binary=build/'sindirgi_baseline'
    build_manifest=build/'source_manifest.json'
    if args.skip_build:
        if (not binary.exists() or not build_manifest.exists()
                or json.loads(build_manifest.read_text())['source_sha256']!=source_hash
                or json.loads(build_manifest.read_text()).get('ns3_root')!=str(NS3)):
            raise RuntimeError('Build missing/stale; run once without --skip-build')
    commands=json.loads((NS3/'cmake-cache/compile_commands.json').read_text())
    entry=next((v for v in commands if v['file'].endswith('/src/lte/examples/lena-simple-epc.cc')),None)
    if entry is None:
        # This PC has LTE libraries but its current CMake configuration omits LTE examples.
        # A stock utility supplies the same executable compiler/profile/include flags.
        entry=next(v for v in commands if v['file'].endswith('/utils/perf/perf-io.cc'))
    command=entry.get('arguments') or shlex.split(entry['command'])
    command[command.index('-c')+1]=str(HERE/'sindirgi_baseline.cc')
    obj=build/'sindirgi_baseline.o'
    command[command.index('-o')+1]=str(obj)
    if not args.skip_build:
        print('Compiling local geographical diagnostic',flush=True)
        with (out/'compile.log').open('w') as log:
            subprocess.run(command,cwd=entry['directory'],stdout=log,stderr=subprocess.STDOUT,check=True)
    lib=NS3/'build/lib'
    binary=build/'sindirgi_baseline'
    modules=['spectrum','lte','applications','point-to-point','internet','mobility','antenna','propagation','network','core']
    private=build/'lte_private'  # experiment 26: patched libns3-lte (build_private_lte.py)
    if not (private/'libns3.44-lte-default.so').exists():
        subprocess.run([sys.executable,str(HERE/'build_private_lte.py')],check=True)
    link=[command[0],str(obj),'-o',str(binary),'-L'+str(private),'-L'+str(lib),'-Wl,-rpath,'+str(private)+':'+str(lib)]
    link+=['-l:libns3.44-'+m+'-default.so' for m in modules]
    if not args.skip_build:
        with (out/'link.log').open('w') as log:
            subprocess.run(link,cwd=HERE,stdout=log,stderr=subprocess.STDOUT,check=True)
        build_manifest.write_text(json.dumps({'source_sha256':source_hash,'ns3_version':'3.44','ns3_root':str(NS3)}))
    env=os.environ.copy()
    env['LD_LIBRARY_PATH']=str(private)+':'+str(lib)+':'+env.get('LD_LIBRARY_PATH','')
    run=[str(binary),'--sites='+str(args.sites_file.resolve()),
         '--output='+str(out),'--siteLimit='+str(args.sites),'--ues='+str(args.ues),
         '--duration='+str(args.duration),'--placement='+args.placement,
         '--pathloss='+args.pathloss,'--exponent='+str(args.exponent),'--traffic='+str(args.traffic)]
    run.append('--mixedCqi='+str(args.mixed_cqi))
    run += ['--shadowSigma='+str(args.shadow_std),'--receiverNf='+str(args.receiver_nf),
            '--shadowSeed='+str(args.shadow_seed),'--dlEarfcn='+str(args.dl_earfcn),'--ulEarfcn='+str(args.ul_earfcn)]
    run += ['--indoorLoss='+str(args.indoor_loss),'--downtilt='+str(args.downtilt),
            '--verticalPattern='+str(args.vertical_pattern),'--verticalBeamwidth='+str(args.vertical_beamwidth),
            '--measurementUes='+str(args.measurement_ues),'--linkShadowSigma='+str(args.link_shadow_std)]
    run.append('--enbPower='+str(args.enb_power))
    run += ['--beamwidth='+str(args.beamwidth),'--udpIntervalMs='+str(args.udp_interval_ms)]
    if args.udp_jitter:run.append('--udpJitter=1')
    if args.evm>0:run.append('--evm='+str(args.evm))
    if args.pf_buffer_aware:run.append('--pfBufferAware=1')
    if args.srs_periodicity:run.append('--srsPeriodicity='+str(args.srs_periodicity))
    if args.dl_phy_traces:run.append('--dlPhyTraces=1')
    if args.antenna_3gpp:run += ['--antenna3gpp=1','--maxAttenuation='+str(args.max_attenuation)]
    if args.ue_file:run.append('--uePositions='+str(args.ue_file.resolve()))
    if args.spatial_shadow:run.append('--spatialShadow=1')
    if args.spatial_los:run.append('--spatialLos=1')
    if args.handover:run.append('--handover=1')
    if args.waypoints:run.append('--waypoints='+str(args.waypoints.resolve()))
    if args.corr_sites:run += ['--corrSites='+str(args.corr_sites.resolve()),'--corrK0='+repr(args.corr_k0),'--corrK1='+repr(args.corr_k1)]
    print('Running',shlex.join(run),flush=True)
    started=time.perf_counter()
    with (out/'run.log').open('w') as log:
        subprocess.run(run,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    result=json.loads((out/'result.json').read_text())
    result['wall_seconds']=time.perf_counter()-started
    result['ns3_root']=str(NS3)
    result['command']=run
    result['compile_source']=str(HERE/'sindirgi_baseline.cc')
    result['source_sha256']=hashlib.sha256(b''.join(p.read_bytes() for p in [HERE/'sindirgi_baseline.cc', HERE/'building-vertical-model.h', HERE/'static-shadow-model.h'])).hexdigest()
    result['sites_sha256']=hashlib.sha256(args.sites_file.read_bytes()).hexdigest()
    result['ue_positions_file']=str(args.ue_file.resolve()) if args.ue_file else None
    result['ue_positions_sha256']=hashlib.sha256(args.ue_file.read_bytes()).hexdigest() if args.ue_file else None
    result['diagnostic_udp_enabled']=bool(args.traffic)
    if args.ue_file:result['placement']='fixed-csv'
    with args.sites_file.open() as stream:
        site_rows=list(csv.DictReader(stream))
    sector_counts={r['site']:int(r.get('sector_count') or 3) for r in site_rows}
    carriers={r['site']:(r.get('carriers') or 'B3') for r in site_rows}
    result['experiment16'] = {'indoor_loss_db':args.indoor_loss,'downtilt_deg':args.downtilt,
        'vertical_pattern':bool(args.vertical_pattern),'vertical_beamwidth_deg':args.vertical_beamwidth,
        'vertical_attenuation_cap_db':20,'measurement_ues':args.measurement_ues,
        'indoor_scope':'all measurement UEs, all links; excludes synthetic load UEs',
        'vertical_scope':'all eNB-UE links, DL and UL; horizontal cosine unchanged'}
    result['experiment20'] = {'link_shadow_std_db':args.link_shadow_std,'link_shadow_seed':args.shadow_seed,
        'link_shadow_scope':'static Gaussian per eNB-UE position pair, all links incl. load UEs, DL and UL; sectors of a site share it'}
    result['experiment29'] = {'pf_buffer_aware':bool(args.pf_buffer_aware)}
    result['experiment26'] = {'evm':args.evm,'evm_scope':'interf += EVM^2*wanted signal in every LteInterference chunk (DL and UL), 3GPP TS 36.104 64QAM 8%'}
    result['experiment23'] = {'antenna_3gpp':bool(args.antenna_3gpp),'max_attenuation_db':args.max_attenuation if args.antenna_3gpp else None,
        'pattern':'TR 36.814 A=min(A_H+A_V,Am), A_H cap Am, A_V cap 20; isotropic 15 dBi element' if args.antenna_3gpp else None}
    result['model_assumptions']={
        'stack':'classic LTE/EPC','sectors_per_site':sector_counts,'carriers':1 if set(carriers.values())=={'B3'} else carriers,
        'udp_start_jitter':bool(args.udp_jitter),
        'dl_earfcn':args.dl_earfcn,'ul_earfcn':args.ul_earfcn,'bandwidth_rb':100,
        'enb_conducted_tx_power_dbm':args.enb_power,'ue_configured_tx_power_dbm':23,
        'antenna':'CosineAntennaModel plus optional separable vertical loss','horizontal_beamwidth_deg':args.beamwidth,
        'vertical_beamwidth_deg':args.vertical_beamwidth if args.vertical_pattern else 360,'antenna_max_gain_dbi':15,
        'orientation':'counterclockwise degrees from east (+x)',
        'enb_height_m':30,'ue_height_m':1.5,'ground':'flat; actual altitude unknown',
        'propagation':args.pathloss,'log_distance_exponent':args.exponent,
        'propagation_note':'1 m free-space reference at selected DL carrier; optional static shadow, no terrain' ,
        'shadowing':{'type':'static reciprocal coordinate-keyed per-link Gaussian dB','std_db':args.shadow_std,'seed':args.shadow_seed},
        'receiver_noise_figure_db':args.receiver_nf,'fading':False,'scheduler':'PfFfMacScheduler',
        'cqi_source':('PDCCH signal and PDSCH interference; UsePdschForCqiGeneration=true' if args.mixed_cqi else 'PDCCH signal and PDCCH interference; UsePdschForCqiGeneration=false'),
        'mixed_cqi_enabled':bool(args.mixed_cqi),
        'radio_trace_period_subframes':97,
        'attachment':f'automatic initial radio-based cell selection with EPC; UE DL EARFCN {args.dl_earfcn}',
        'dl_application':f'512-byte UDP payload every {args.udp_interval_ms:g} ms, starting at 0.3 s' if args.traffic else 'disabled; radio-only screening',
        'interpretation':'Diagnostic assumed scenario, not operator reconstruction or calibrated coverage.'}
    (out/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
