"""Add passive S/I/N observation in a separate copy of the frozen S0 runner."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]/'ana_proje'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text,old,new):
    assert text.count(old) == 1,old
    return text.replace(old,new,1)


def main():
    sim = HERE/'simulation'
    inputs = HERE/'inputs'
    sim.mkdir(parents=True,exist_ok=True)
    inputs.mkdir(exist_ok=True)
    for name in ['sites.csv','ues.csv']:
        shutil.copy2(PROJECT/'analysis/sindirgi/radio_study/frozen'/name,inputs/name)
    for name in ['run_baseline.py','ns3_paths.py']:
        shutil.copy2(PROJECT/'simulation'/name,sim/name)
    runner = (sim/'run_baseline.py').read_text(encoding='utf-8')
    runner = replace_once(runner,"modules=['lte',", "modules=['spectrum','lte',")
    (sim/'run_baseline.py').write_text(runner,encoding='utf-8')
    source = (PROJECT/'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    source = replace_once(source,'#include "ns3/antenna-module.h"',
        '#include "ns3/antenna-module.h"\n#include "ns3/lte-chunk-processor.h"\n#include "ns3/spectrum-value.h"')
    extra = r'''
static std::ofstream gDiagnostic;
static std::vector<Ptr<SpectrumValue>> gSignalPsd, gInterfNoisePsd;
static std::vector<int64_t> gSignalAt, gInterfAt;
static std::vector<double> gNoiseFigure;

static void
SignalObservation(uint32_t ue, const SpectrumValue& value)
{
    gSignalPsd.at(ue) = value.Copy();
    gSignalAt.at(ue) = Simulator::Now().GetNanoSeconds();
}

static void
InterfObservation(uint32_t ue, const SpectrumValue& value)
{
    gInterfNoisePsd.at(ue) = value.Copy();
    gInterfAt.at(ue) = Simulator::Now().GetNanoSeconds();
}

static void
WriteDiagnostic(uint32_t ue, uint16_t cell, uint16_t rnti, double rsrpW, double nativeSinr)
{
    if (Simulator::Now().GetSeconds() < 1.0) return;
    const int64_t now = Simulator::Now().GetNanoSeconds();
    if (!gSignalPsd.at(ue) || !gInterfNoisePsd.at(ue) ||
        gSignalAt.at(ue) != now || gInterfAt.at(ue) != now)
        throw std::runtime_error("Diagnostic callbacks are not time-aligned");
    const auto& s = *gSignalPsd.at(ue);
    const auto& d = *gInterfNoisePsd.at(ue);
    const auto count = s.GetValuesN();
    if (count == 0 || count != d.GetValuesN())
        throw std::runtime_error("Diagnostic spectrum sizes differ");
    // Same thermal-noise formula as LteSpectrumValueHelper, with the actual UE NF.
    const double noise = std::pow(10.0, (-174.0 + gNoiseFigure.at(ue) - 30.0) / 10.0);
    double signalSum=0, denominatorSum=0, ratioSum=0;
    double minSignal=std::numeric_limits<double>::infinity(), maxSignal=0;
    auto a=s.ConstValuesBegin(); auto b=d.ConstValuesBegin();
    for (;a!=s.ConstValuesEnd();++a,++b)
    {
        if (*b <= 0 || *b < noise*(1-1e-8))
            throw std::runtime_error("Invalid interference-plus-noise PSD");
        signalSum += *a; denominatorSum += *b; ratioSum += *a / *b;
        minSignal=std::min(minSignal,*a); maxSignal=std::max(maxSignal,*a);
    }
    const double signal=signalSum/count, denominator=denominatorSum/count;
    const double interf=std::max(0.0,denominator-noise);
    const double snr=signal/noise, sinr=ratioSum/count;
    gDiagnostic << Simulator::Now().GetSeconds() << ',' << ue << ',' << cell << ',' << rnti
        << ',' << count << ',' << gNoiseFigure.at(ue)
        << ',' << signal << ',' << denominator << ',' << interf << ',' << noise
        << ',' << signalSum*180000.0 << ',' << interf*count*180000.0 << ',' << noise*count*180000.0
        << ',' << 10*std::log10(rsrpW)+30 << ',' << 10*std::log10(signal*15000.0)+30
        << ',' << 10*std::log10(nativeSinr) << ',' << 10*std::log10(sinr)
        << ',' << 10*std::log10(snr) << ',' << 10*std::log10(interf/noise)
        << ',' << interf/denominator << ',' << 10*std::log10(signalSum/(2*(signalSum+denominatorSum)))
        << ',' << (maxSignal-minSignal)/signal << '\n';
}
'''
    source = replace_once(source,'static std::ofstream gRadio;',extra+'\nstatic std::ofstream gRadio;')
    source = replace_once(source,'    ++gRadioRows;',
        '    ++gRadioRows;\n    WriteDiagnostic(ue, cell, rnti, rsrpWatts, sinrLinear);')
    source = replace_once(source,'    gConnectedAt.assign(ueCount,-1);',r'''
    gConnectedAt.assign(ueCount,-1);
    gDiagnostic.open(out("sinr_components.csv"));
    gDiagnostic << "time_s,ue_id,synthetic_cell_id,rnti,rb_count,noise_figure_db,signal_psd_w_hz,interf_noise_psd_w_hz,interference_psd_w_hz,noise_psd_w_hz,signal_total_w,interference_total_w,noise_total_w,native_rsrp_dbm,reconstructed_rsrp_dbm,native_sinr_db,reconstructed_sinr_db,snr_db,inr_db,interference_fraction,rsrq_from_components_db,signal_rb_relative_spread\n";
    gDiagnostic << std::setprecision(17);
    gSignalPsd.resize(ueCount); gInterfNoisePsd.resize(ueCount);
    gSignalAt.assign(ueCount,-1); gInterfAt.assign(ueCount,-1); gNoiseFigure.resize(ueCount);
''')
    source = replace_once(source,'        phy->SetAttribute("RsrpSinrSamplePeriod", UintegerValue(97));',r'''
        phy->SetAttribute("RsrpSinrSamplePeriod", UintegerValue(97));
        gNoiseFigure.at(u) = phy->GetNoiseFigure();
        auto diagnosticSignal = Create<LteChunkProcessor>();
        diagnosticSignal->AddCallback(MakeBoundCallback(&SignalObservation,u));
        phy->GetDlSpectrumPhy()->AddRsPowerChunkProcessor(diagnosticSignal);
        auto diagnosticInterference = Create<LteChunkProcessor>();
        diagnosticInterference->AddCallback(MakeBoundCallback(&InterfObservation,u));
        phy->GetDlSpectrumPhy()->AddInterferenceCtrlChunkProcessor(diagnosticInterference);
''')
    source = replace_once(source,'    gRadio.close();','    gRadio.close();\n    gDiagnostic.close();')
    (sim/'sindirgi_baseline.cc').write_text(source,encoding='utf-8')
    plan = {
        'purpose':'Audit S0 control-channel RSRP/SINR/RSRQ definitions and passively decompose S, I and N.',
        'baseline':'24 sites, 72 cochannel sectors, fixed 64 UEs, frozen S0 parameters, 4 seconds, same UDP probe.',
        'warmup_s':1.0,
        'observation':'Passive signal-PSD and control interference-plus-noise chunk processors; sampled at native 97-subframe PHY trace times.',
        'noise':'Use actual UE GetNoiseFigure and the installed helper formula 10^((-174 + NF - 30)/10) W/Hz.',
        'verification':'Same 64 UE results as frozen baseline; time-aligned PSDs; reconstruct native RSRP/SINR; independently compare RSRQ.',
        'decomposition':'I = (I+N) - N; classify I>N as interference dominated; S/N is an algebraic no-interference reference, not a new simulated network.',
        'spatial_attribution':'Analytical per-sector powers using the same frozen coordinates, CosineAntennaModel and log-distance model; use only if their S and sum(I) agree with passive observations.',
        'scope':'This audits the chosen synthetic control-channel model, not Experia equivalence or real operator interference.',
        'original_cpp_sha256':digest(PROJECT/'simulation/sindirgi_baseline.cc'),
        'diagnostic_cpp_sha256':digest(sim/'sindirgi_baseline.cc'),
        'input_hashes':{name:digest(inputs/name) for name in ['sites.csv','ues.csv']}}
    (HERE/'experiment_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print('Prepared passive diagnostic copy; original source unchanged.')


if __name__ == '__main__':
    main()
