"""Prepare a matched control/mixed CQI comparison with passive references."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT/'ana_proje'
DIAG = ROOT/'deneyler/02_sinr_tanisi_2026-11-10'


def replace_once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sim = HERE/'simulation'
    sim.mkdir(parents=True,exist_ok=True)
    shutil.copytree(DIAG/'inputs',HERE/'inputs',dirs_exist_ok=True)
    for name in ['run_baseline.py','ns3_paths.py']:
        shutil.copy2(DIAG/'simulation'/name,sim/name)
    source = (DIAG/'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    source = replace_once(source,'static std::ofstream gDiagnostic;',r'''
static bool gMixedCqi = false;
static std::vector<Ptr<SpectrumValue>> gDataInterfNoisePsd;
static std::vector<bool> gDataFresh;
static std::vector<int64_t> gDataAt;

static void
DataObservation(uint32_t ue, const SpectrumValue& value)
{
    gDataInterfNoisePsd.at(ue)=value.Copy();
    gDataFresh.at(ue)=true;
    gDataAt.at(ue)=Simulator::Now().GetNanoSeconds();
}

static void
ResetAfterCtrl(uint32_t ue, const SpectrumValue&)
{
    // This observer runs AFTER the native CQI callback on every CTRL interval.
    gDataFresh.at(ue)=false;
}

static std::ofstream gDiagnostic;''')
    source = replace_once(source,'    const double snr=signal/noise, sinr=ratioSum/count;',r'''
    const double snr=signal/noise, sinr=ratioSum/count;
    double mixed=0;
    auto data = gDataInterfNoisePsd.at(ue);
    auto signalIt=s.ConstValuesBegin();
    for (uint32_t k=0;k<count;++k,++signalIt)
    {
        const double denom = (gDataFresh.at(ue) && data) ? (*data)[k] : noise;
        mixed += *signalIt / denom; // P_A=0 dB in the frozen baseline.
    }
    mixed /= count;
''')
    source = replace_once(source,
        "        << ',' << (maxSignal-minSignal)/signal << '\\n';",
        "        << ',' << (maxSignal-minSignal)/signal << ',' << int(gDataFresh.at(ue))\n"
        "        << ',' << (gDataAt.at(ue)<0 ? -1.0 : (now-gDataAt.at(ue))/1e6)\n"
        "        << ',' << 10*std::log10(mixed) << ',' << int(gMixedCqi) << '\\n';")
    source = replace_once(source,'    cmd.Parse(argc, argv);',
        '    cmd.AddValue("mixedCqi", "Use PDSCH interference in CQI", gMixedCqi);\n    cmd.Parse(argc, argv);')
    source = replace_once(source,'lte->SetAttribute("UsePdschForCqiGeneration", BooleanValue(false));',
        'lte->SetAttribute("UsePdschForCqiGeneration", BooleanValue(gMixedCqi));')
    source = replace_once(source,'reconstructed_sinr_db,snr_db', 'control_sinr_db,snr_db')
    source = replace_once(source,'signal_rb_relative_spread\\n";',
        'signal_rb_relative_spread,data_interference_fresh,data_age_ms,reconstructed_mixed_sinr_db,mixed_cqi_enabled\\n";')
    source = replace_once(source,'    gSignalPsd.resize(ueCount); gInterfNoisePsd.resize(ueCount);',
        '    gSignalPsd.resize(ueCount); gInterfNoisePsd.resize(ueCount);\n'
        '    gDataInterfNoisePsd.resize(ueCount); gDataFresh.assign(ueCount,false); gDataAt.assign(ueCount,-1);')
    source = replace_once(source,
        '        phy->GetDlSpectrumPhy()->AddInterferenceCtrlChunkProcessor(diagnosticInterference);',r'''
        phy->GetDlSpectrumPhy()->AddInterferenceCtrlChunkProcessor(diagnosticInterference);
        auto diagnosticData = Create<LteChunkProcessor>();
        diagnosticData->AddCallback(MakeBoundCallback(&DataObservation,u));
        phy->GetDlSpectrumPhy()->AddInterferenceDataChunkProcessor(diagnosticData);
        auto resetObserver = Create<LteChunkProcessor>();
        resetObserver->AddCallback(MakeBoundCallback(&ResetAfterCtrl,u));
        phy->GetDlSpectrumPhy()->AddCtrlSinrChunkProcessor(resetObserver);
''')
    (sim/'sindirgi_baseline.cc').write_text(source,encoding='utf-8')
    runner = (sim/'run_baseline.py').read_text(encoding='utf-8')
    runner = replace_once(runner,"    parser.add_argument('--skip-build',action='store_true')",
        "    parser.add_argument('--mixed-cqi',type=int,choices=[0,1],default=0)\n"
        "    parser.add_argument('--skip-build',action='store_true')")
    runner = replace_once(runner,"    if args.ue_file:run.append('--uePositions='+str(args.ue_file.resolve()))",
        "    run.append('--mixedCqi='+str(args.mixed_cqi))\n"
        "    if args.ue_file:run.append('--uePositions='+str(args.ue_file.resolve()))")
    runner = replace_once(runner,"'cqi_source':'PDCCH signal and PDCCH interference; UsePdschForCqiGeneration=false',",
        "'cqi_source':('PDCCH signal and PDSCH interference; UsePdschForCqiGeneration=true' if args.mixed_cqi else 'PDCCH signal and PDCCH interference; UsePdschForCqiGeneration=false'),\n"
        "        'mixed_cqi_enabled':bool(args.mixed_cqi),")
    (sim/'run_baseline.py').write_text(runner,encoding='utf-8')
    plan = {
        'purpose':'Compare control and mixed CQI definitions under the same frozen low-load scenario.',
        'cases':[{'name':'control','mixed_cqi':0},{'name':'mixed','mixed_cqi':1}],
        'fixed':'24 sites, 72 sectors, 64 fixed UEs, same seed/run, powers, azimuths, single carrier, log-distance exponent 3, 4 s, 512 bytes per UE every 50 ms.',
        'warmup_s':1.0,
        'feedback_caveat':'UsePdschForCqiGeneration changes CQI input to the scheduler; this is not only a passive change of exported measurement. Track DL bytes separately.',
        'passive_reference':'In both runs record control S/(I+N), native exported SINR, and mixed estimate reconstructed from data I+N freshness (or noise only).',
        'source_semantics':'GenerateMixedCqiReport consumes the latest data interference update once; absent an update it divides RS power by noise PSD. Frozen baseline P_A=0 dB.',
        'rb_caveat':'100 RB baseline has RBG modulo zero, so no trailing RB replacement is required for the mixed reconstruction.',
        'regression_gate':'New control run must reproduce original serving sectors, connection, DL bytes and radio values before mixed run.',
        'interpretation':'Diagnostic under low synthetic load; not evidence that mixed equals Experia or that network configuration improved.',
        'original_cpp_sha256':digest(PROJECT/'simulation/sindirgi_baseline.cc'),
        'experiment_cpp_sha256':digest(sim/'sindirgi_baseline.cc'),
        'input_hashes':{name:digest(HERE/'inputs'/name) for name in ['sites.csv','ues.csv']}}
    (HERE/'experiment_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print('Prepared control/mixed comparison without changing the original baseline.')


if __name__=='__main__':
    main()
