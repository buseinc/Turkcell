"""Predeclare a six-case exploratory antenna/load grid, before simulation."""
from pathlib import Path
import hashlib
import json
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PROJECT=ROOT/'turkcell_tam_paket_2026-11-10'
MIXED=ROOT/'experiments/mixed_cqi_2026-11-10'


def replace_once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sim=HERE/'simulation'
    sim.mkdir(parents=True,exist_ok=True)
    shutil.copytree(MIXED/'inputs',HERE/'inputs',dirs_exist_ok=True)
    shutil.copy2(PROJECT/'analysis/sindirgi/radio_study/measured_site_targets.csv',HERE/'inputs/targets.csv')
    shutil.copy2(MIXED/'simulation/ns3_paths.py',sim/'ns3_paths.py')
    source=(MIXED/'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    source=replace_once(source,'    double duration = 1.2;',
        '    double duration = 1.2;\n    double beamwidth = 65.0;\n    double udpIntervalMs = 50.0;')
    source=replace_once(source,'    cmd.Parse(argc, argv);',
        '    cmd.AddValue("beamwidth", "Horizontal beamwidth degrees", beamwidth);\n'
        '    cmd.AddValue("udpIntervalMs", "UDP packet interval in ms", udpIntervalMs);\n'
        '    cmd.Parse(argc, argv);\n'
        '    if (beamwidth <= 0 || beamwidth > 180 || udpIntervalMs <= 0)\n'
        '        throw std::runtime_error("Invalid antenna/load parameters");')
    source=replace_once(source,'"HorizontalBeamwidth", DoubleValue(65.0)',
        '"HorizontalBeamwidth", DoubleValue(beamwidth)')
    source=replace_once(source,'TimeValue(MilliSeconds(50))','TimeValue(Seconds(udpIntervalMs/1000.0))')
    (sim/'sindirgi_baseline.cc').write_text(source,encoding='utf-8')
    runner=(MIXED/'simulation/run_baseline.py').read_text(encoding='utf-8')
    runner=replace_once(runner,"    parser.add_argument('--skip-build',action='store_true')",
        "    parser.add_argument('--beamwidth',type=float,default=65)\n"
        "    parser.add_argument('--udp-interval-ms',type=float,default=50)\n"
        "    parser.add_argument('--skip-build',action='store_true')")
    runner=replace_once(runner,"    run.append('--mixedCqi='+str(args.mixed_cqi))",
        "    run.append('--mixedCqi='+str(args.mixed_cqi))\n"
        "    run += ['--beamwidth='+str(args.beamwidth),'--udpIntervalMs='+str(args.udp_interval_ms)]")
    runner=replace_once(runner,"'horizontal_beamwidth_deg':65", "'horizontal_beamwidth_deg':args.beamwidth")
    runner=replace_once(runner,"'512-byte UDP payload every 50 ms, starting at 0.3 s'",
        "f'512-byte UDP payload every {args.udp_interval_ms:g} ms, starting at 0.3 s'")
    (sim/'run_baseline.py').write_text(runner,encoding='utf-8')
    cases=[{'name':f'b{width}_t{interval}','beamwidth_deg':width,'udp_interval_ms':interval,
            'offered_payload_mbps_per_ue':512*8/(interval/1000)/1e6,
            'offered_payload_mbps_all_64':64*512*8/(interval/1000)/1e6}
            for width in [65,90,120] for interval in [50,5]]
    plan={
        'purpose':'Exploratory measurement-informed search for joint RSRP/SINR/RSRQ agreement.',
        'cases':cases,'mixed_cqi':True,'duration_s':4.0,'warmup_s':1.0,
        'fixed':'Same 24 sites, 72 sectors, 64 UE positions, seed 42/run 1, original rotations, 46 dBm per sector, 15 dBi peak gain, single carrier, log-distance exponent 3, flat ground, no fading/shadowing.',
        'antenna_caveat':'Beamwidths are explicit scenario hypotheses, not inferred operator antennas; changing width while retaining peak gain changes off-boresight gains.',
        'load_caveat':'1x/10x synthetic offered payload, not inferred real demand, earthquake traffic or a KPI-calibrated load. No outage, capacity or service failure claims.',
        'selection_rule':'Use only the original five training sites. Score = arithmetic mean of training-site MAE for RSRP, SINR and RSRQ + 10 dB per training site missing any of these metrics. Retain all results and report each metric separately.',
        'score_caveat':'Equal weighting is an exploratory ranking convention, not an operator acceptance criterion. Also report Pareto tradeoffs and site/UE coverage.',
        'control_rule':'Three original control sites are excluded from ranking. They have been seen in previous studies, so this is not a blind external validation.',
        'no_baseline_replacement':True,
        'regression_gate':'New b65_t50 run must reproduce the prior mixed case on all 64 UEs before other cases.',
        'source_cpp_sha256':digest(sim/'sindirgi_baseline.cc'),
        'original_cpp_sha256':digest(PROJECT/'simulation/sindirgi_baseline.cc'),
        'input_hashes':{name:digest(HERE/'inputs'/name) for name in ['sites.csv','ues.csv','targets.csv']}}
    (HERE/'experiment_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(json.dumps({'cases':cases,'selection':plan['selection_rule']},indent=2))


if __name__=='__main__':main()
