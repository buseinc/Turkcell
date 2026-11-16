"""Compile the local diagnostic against the existing ns-3.44 build and run it.

Run under WSL. Reuses compiler options from ns-3's stock EPC example;
does not copy or alter simulator source files.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
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
    parser.add_argument('--pathloss',choices=['log-distance','okumura'],default='log-distance')
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
    parser.add_argument('--skip-build',action='store_true')
    args=parser.parse_args()
    if Path(args.name).is_absolute() or '..' in Path(args.name).parts:
        raise ValueError('Run name must stay under results')
    assert (NS3/'VERSION').read_text().strip()=='3.44'
    out=HERE/'results'/args.name
    out.mkdir(parents=True,exist_ok=True)
    build=HERE/'build'
    build.mkdir(exist_ok=True)
    source_hash=hashlib.sha256((HERE/'sindirgi_baseline.cc').read_bytes()).hexdigest()
    binary=build/'sindirgi_baseline'
    build_manifest=build/'source_manifest.json'
    if args.skip_build:
        if (not binary.exists() or not build_manifest.exists()
                or json.loads(build_manifest.read_text())['source_sha256']!=source_hash
                or json.loads(build_manifest.read_text()).get('ns3_root')!=str(NS3)):
            raise RuntimeError('Build missing/stale; run once without --skip-build')
    commands=json.loads((NS3/'cmake-cache/compile_commands.json').read_text())
    entry=next(v for v in commands if v['file'].endswith('/src/lte/examples/lena-simple-epc.cc'))
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
    link=[command[0],str(obj),'-o',str(binary),'-L'+str(lib),'-Wl,-rpath,'+str(lib)]
    link+=['-l:libns3.44-'+m+'-default.so' for m in modules]
    if not args.skip_build:
        with (out/'link.log').open('w') as log:
            subprocess.run(link,cwd=HERE,stdout=log,stderr=subprocess.STDOUT,check=True)
        build_manifest.write_text(json.dumps({'source_sha256':source_hash,'ns3_version':'3.44','ns3_root':str(NS3)}))
    env=os.environ.copy()
    env['LD_LIBRARY_PATH']=str(lib)+':'+env.get('LD_LIBRARY_PATH','')
    run=[str(binary),'--sites='+str(args.sites_file.resolve()),
         '--output='+str(out),'--siteLimit='+str(args.sites),'--ues='+str(args.ues),
         '--duration='+str(args.duration),'--placement='+args.placement,
         '--pathloss='+args.pathloss,'--exponent='+str(args.exponent),'--traffic='+str(args.traffic)]
    run.append('--mixedCqi='+str(args.mixed_cqi))
    run += ['--shadowSigma='+str(args.shadow_std),'--receiverNf='+str(args.receiver_nf),
            '--shadowSeed='+str(args.shadow_seed),'--dlEarfcn='+str(args.dl_earfcn),'--ulEarfcn='+str(args.ul_earfcn)]
    run.append('--enbPower='+str(args.enb_power))
    run += ['--beamwidth='+str(args.beamwidth),'--udpIntervalMs='+str(args.udp_interval_ms)]
    if args.udp_jitter:run.append('--udpJitter=1')
    if args.ue_file:run.append('--uePositions='+str(args.ue_file.resolve()))
    print('Running',shlex.join(run),flush=True)
    started=time.perf_counter()
    with (out/'run.log').open('w') as log:
        subprocess.run(run,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    result=json.loads((out/'result.json').read_text())
    result['wall_seconds']=time.perf_counter()-started
    result['ns3_root']=str(NS3)
    result['command']=run
    result['compile_source']=str(HERE/'sindirgi_baseline.cc')
    result['source_sha256']=hashlib.sha256((HERE/'sindirgi_baseline.cc').read_bytes()).hexdigest()
    result['sites_sha256']=hashlib.sha256(args.sites_file.read_bytes()).hexdigest()
    result['ue_positions_file']=str(args.ue_file.resolve()) if args.ue_file else None
    result['ue_positions_sha256']=hashlib.sha256(args.ue_file.read_bytes()).hexdigest() if args.ue_file else None
    result['diagnostic_udp_enabled']=bool(args.traffic)
    if args.ue_file:result['placement']='fixed-csv'
    with args.sites_file.open() as stream:
        site_rows=list(csv.DictReader(stream))
    sector_counts={r['site']:int(r.get('sector_count') or 3) for r in site_rows}
    carriers={r['site']:(r.get('carriers') or 'B3') for r in site_rows}
    result['model_assumptions']={
        'stack':'classic LTE/EPC','sectors_per_site':sector_counts,'carriers':1 if set(carriers.values())=={'B3'} else carriers,
        'udp_start_jitter':bool(args.udp_jitter),
        'dl_earfcn':args.dl_earfcn,'ul_earfcn':args.ul_earfcn,'bandwidth_rb':100,
        'enb_conducted_tx_power_dbm':args.enb_power,'ue_configured_tx_power_dbm':23,
        'antenna':'CosineAntennaModel','horizontal_beamwidth_deg':args.beamwidth,
        'vertical_beamwidth_deg':360,'antenna_max_gain_dbi':15,
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
