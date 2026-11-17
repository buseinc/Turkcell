"""Freeze experiment 16 without modifying earlier experiments."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D15 = ROOT / 'deneyler/15_ta_yerlesim_2026-11-16'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    if (HERE / 'plan.json').exists():
        raise RuntimeError('Plan already frozen; do not overwrite an existing experiment.')
    inp, sim = HERE / 'inputs', HERE / 'simulation'
    inp.mkdir(exist_ok=True)
    sim.mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'deneyler/10_kapsama_haritalari_2026-11-15/radio_model.py', HERE / 'radio_model.py')
    for p in (D15 / 'inputs').glob('*.csv'):
        shutil.copy2(p, inp / p.name)
    for name in ['ns3_paths.py', 'static-shadow-model.h']:
        shutil.copy2(D15 / 'simulation' / name, sim / name)
    # One source edit, two independently switchable effects. Disabled means no extra model.
    source = (D15 / 'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    source = source.replace('#include "static-shadow-model.h"',
                            '#include "static-shadow-model.h"\n#include "building-vertical-model.h"')
    source = source.replace('double shadowSigma=0.0, receiverNf=9.0;',
                            'double shadowSigma=0.0, receiverNf=9.0;\n'
                            '    double indoorLoss=0.0, downtilt=0.0, verticalBeamwidth=10.0;\n'
                            '    bool verticalPattern=false;\n    uint32_t measurementUes=256;')
    source = source.replace('cmd.AddValue("udpJitter",',
                            'cmd.AddValue("indoorLoss", "Fixed loss for measured UEs only, dB", indoorLoss);\n'
                            '    cmd.AddValue("downtilt", "Downward electrical tilt, degrees", downtilt);\n'
                            '    cmd.AddValue("verticalPattern", "Enable vertical attenuation", verticalPattern);\n'
                            '    cmd.AddValue("verticalBeamwidth", "Vertical 3 dB beamwidth", verticalBeamwidth);\n'
                            '    cmd.AddValue("measurementUes", "First N UEs receive indoor loss", measurementUes);\n'
                            '    cmd.AddValue("udpJitter",')
    marker = '    NetDeviceContainer ueDevices;'
    assert source.count(marker) == 1
    source = source.replace(marker, '''    if (indoorLoss < 0 || downtilt < 0 || downtilt > 90 || verticalBeamwidth <= 0)
        throw std::runtime_error("Invalid building/vertical parameters");
    if (indoorLoss > 0 || verticalPattern)
    {
        if (measurementUes > ueCount) throw std::runtime_error("measurementUes exceeds ues");
        auto loss = CreateObject<BuildingVerticalLoss>();
        loss->Configure(enbNodes, ueNodes, measurementUes, indoorLoss,
                        verticalPattern, downtilt, verticalBeamwidth);
        lte->GetDownlinkSpectrumChannel()->AddSpectrumPropagationLossModel(loss);
        auto ulLoss = CreateObject<BuildingVerticalLoss>();
        ulLoss->Configure(enbNodes, ueNodes, measurementUes, indoorLoss,
                          verticalPattern, downtilt, verticalBeamwidth);
        lte->GetUplinkSpectrumChannel()->AddSpectrumPropagationLossModel(ulLoss);
    }
''' + marker)
    (sim / 'sindirgi_baseline.cc').write_text(source, encoding='utf-8')
    runner = (D15 / 'simulation/run_baseline.py').read_text(encoding='utf-8')
    runner = runner.replace("    parser.add_argument('--skip-build'", """    parser.add_argument('--indoor-loss',type=float,default=0)
    parser.add_argument('--downtilt',type=float,default=0)
    parser.add_argument('--vertical-pattern',type=int,choices=[0,1],default=0)
    parser.add_argument('--vertical-beamwidth',type=float,default=10)
    parser.add_argument('--measurement-ues',type=int,default=256)
    parser.add_argument('--skip-build'""")
    # Include local headers in the build identity (the previous runner only hashes .cc).
    runner = runner.replace("hashlib.sha256((HERE/'sindirgi_baseline.cc').read_bytes()).hexdigest()",
                            "hashlib.sha256(b''.join(p.read_bytes() for p in [HERE/'sindirgi_baseline.cc', HERE/'building-vertical-model.h', HERE/'static-shadow-model.h'])).hexdigest()")
    runner = runner.replace("    run.append('--enbPower='", """    run += ['--indoorLoss='+str(args.indoor_loss),'--downtilt='+str(args.downtilt),
            '--verticalPattern='+str(args.vertical_pattern),'--verticalBeamwidth='+str(args.vertical_beamwidth),
            '--measurementUes='+str(args.measurement_ues)]
    run.append('--enbPower='""")
    runner = runner.replace("    result['model_assumptions']={", """    result['experiment16'] = {'indoor_loss_db':args.indoor_loss,'downtilt_deg':args.downtilt,
        'vertical_pattern':bool(args.vertical_pattern),'vertical_beamwidth_deg':args.vertical_beamwidth,
        'vertical_attenuation_cap_db':20,'measurement_ues':args.measurement_ues,
        'indoor_scope':'all measurement UEs, all links; excludes synthetic load UEs',
        'vertical_scope':'all eNB-UE links, DL and UL; horizontal cosine unchanged'}
    result['model_assumptions']={""")
    runner = runner.replace("    entry=next(v for v in commands if v['file'].endswith('/src/lte/examples/lena-simple-epc.cc'))",
                            "    entry=next((v for v in commands if v['file'].endswith('/src/lte/examples/lena-simple-epc.cc')),None)\n"
                            "    if entry is None:\n"
                            "        # This PC has LTE libraries but its current CMake configuration omits LTE examples.\n"
                            "        # A stock utility supplies the same executable compiler/profile/include flags.\n"
                            "        entry=next(v for v in commands if v['file'].endswith('/utils/perf/perf-io.cc'))")
    runner = runner.replace("'antenna':'CosineAntennaModel'", "'antenna':'CosineAntennaModel plus optional separable vertical loss'")
    runner = runner.replace("'vertical_beamwidth_deg':360", "'vertical_beamwidth_deg':args.vertical_beamwidth if args.vertical_pattern else 360")
    (sim / 'run_baseline.py').write_text(runner, encoding='utf-8')
    plan = {
        'status': 'frozen_before_runs', 'draws': [[42,701],[7,702],[99,703]],
        'measurement_ues':256, 'duration_s':4, 'warmup_s':1,
        'grid': {'indoor_loss_db':[0,6,12,18], 'downtilt_deg':[0,3,6,9]},
        'fixed_vertical_beamwidth_deg':10, 'fixed_vertical_cap_db':20,
        'train_sites':['SITE_000130','SITE_000296','SITE_000444','SITE_000482','SITE_000554'],
        'holdout_sites':['SITE_000440','SITE_000441','SITE_000443'],
        'selection': 'Analytical RSRP only, mean site MAE over the 5 tuning sites and all 3 draws; missing tuning site = invalid candidate. Tie: smaller indoor loss, then smaller tilt. No holdout metrics before selection.',
        'screen_gate':'At zero loss and disabled vertical pattern, analytical RSRP max absolute error <0.01 dB and serving cells identical for all 256 measured UEs of all 3 archived TA runs.',
        'native_cases':'Selected combined candidate, selected indoor loss only, selected tilt only, each on 3 draws; deduplicate equal cases. Plus one full archived TA repeat with both effects disabled.',
        'native_selection':'None: freeze analytical winner before native runs; do not choose another candidate from holdout results.',
        'acceptance':{'holdout_rsrp_improvement_over_TA_db':0.5,
                      'holdout_rsrp_no_worse_than_S0_by_db':0.5,
                      'holdout_sinr_no_worse_than_TA_by_db':1.0,
                      'all_measurement_ues_connected':True,
                      'all_measurement_ues_with_dl':True,
                      'absolute_PRB_change_max':0.03},
        'regression':'Byte equality of sectors.csv, ues.csv, radio_samples.csv, sinr_components.csv, measurements.csv, prb_usage.csv for archived S0TA_draw701 with disabled effects. Metadata/log paths and timing are excluded.',
        'assumptions':['Fixed building loss is an effective scenario assumption, not evidence that all Experia users are indoors.',
                       'Vertical loss = min(12*((downward elevation - tilt)/10)^2,20) dB, applied once per eNB-UE link; existing horizontal pattern and 15 dBi peak unchanged.',
                       'Synthetic load UEs remain outdoors; vertical pattern applies to them too. Load rate/factor unchanged, achieved PRB must be checked.',
                       'Constant indoor loss attenuates serving and interfering signals together; it need not fix interference-limited SINR.',
                       'Hourly TA averages and random directions do not reconstruct individual user positions; changed attachment remains a limitation.',
                       'These tests can reject hypotheses; they cannot identify true building loss or real antenna tilt.'],
        'input_hashes':{p.name:sha(p) for p in sorted(inp.glob('*.csv'))},
        'source_hashes':{p.name:sha(p) for p in sorted(sim.glob('*')) if p.is_file()},
        'reference':'https://www.nsnam.org/docs/release/3.44/models/ns-3-model-library.pdf',
    }
    (HERE / 'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Plan and copied inputs frozen.')


if __name__ == '__main__':
    main()
