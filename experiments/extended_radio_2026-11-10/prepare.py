"""Freeze a broader native campaign, diverse hypotheses and common ensembles."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import shutil
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PROJECT=ROOT/'turkcell_tam_paket_2026-11-10'
PREVIOUS=ROOT/'experiments/placement_propagation_2026-11-10'
STUDY=PROJECT/'analysis/sindirgi/radio_study'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)


def structure(case):
    excluded={'name','category','profile','label','azimuth_seed','shadow_seed','spatial_seed','duration_s'}
    return json.dumps({k:v for k,v in case.items() if k not in excluded},sort_keys=True)


def main():
    inputs=HERE/'inputs';inputs.mkdir(parents=True,exist_ok=True)
    sim=HERE/'simulation';sim.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('placements',PREVIOUS/'prepare.py')
    placement_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(placement_module)
    source_sites=pd.read_csv(PREVIOUS/'inputs/sites.csv')
    for family in ['wide','near','far','uniform','mixed']:
        for seed in [20261109,701,702,703]:
            path=inputs/f'ues_{family}_{seed}.csv'
            if seed==20261109:shutil.copy2(PREVIOUS/'inputs'/f'ues_{family}.csv',path)
            else:placement_module.placement(family,seed,source_sites).to_csv(path,index=False,float_format='%.9f')
    shutil.copy2(PREVIOUS/'inputs/targets.csv',inputs/'targets.csv')
    for total,buffer in [(24,16),(32,24),(48,40)]:
        for az in [42,7,99]:
            source=STUDY/'inputs'/f'sites_b{buffer}_az{az}.csv'
            sites=pd.read_csv(source)
            for policy in ['three','two_small']:
                target=inputs/f'sites_{total}_{az}_{policy}.csv'
                if policy=='three':shutil.copy2(source,target)
                else:
                    changed=sites.copy()
                    changed['sector_count']=changed.site.map(lambda s:2 if s in ['SITE_000482','SITE_000554'] else 3)
                    changed.to_csv(target,index=False,float_format='%.9f')
                check=pd.read_csv(target)
                pd.testing.assert_frame_equal(check[['site','x_m','y_m']],sites[['site','x_m','y_m']])
    profiles={
        'A':{'family':'far','beamwidth_deg':120,'exponent':3.0,'power_dbm':49},
        'B':{'family':'wide','beamwidth_deg':120,'exponent':3.0,'power_dbm':46},
        'C':{'family':'far','beamwidth_deg':65,'exponent':2.7,'power_dbm':43}}
    defaults={'shadow_std_db':0.0,'ue_nf_db':9.0,'udp_interval_ms':50.0,'sector_policy':'three',
        'azimuth_seed':42,'shadow_seed':42,'spatial_seed':20261109,'dl_earfcn':1300,'ul_earfcn':19300}
    cases=[];seen=set()
    def add(profile,category,label,**changes):
        case={**defaults,**profiles[profile],**changes,'profile':profile,'category':category,'label':label,'duration_s':2.0}
        key=json.dumps({k:v for k,v in case.items() if k not in ['profile','category','label']},sort_keys=True)
        if key in seen:return
        seen.add(key);case['name']=f'screen_{len(cases):03d}';cases.append(case)
    for profile,base in profiles.items():
        for family in [base['family']]+[f for f in ['wide','near','far','uniform','mixed'] if f!=base['family']]:
            add(profile,'placement','UE '+family,family=family)
        for sigma in [4.0,8.0]:add(profile,'shadow','Static shadow '+str(sigma),shadow_std_db=sigma)
        for nf in [6.0,12.0]:add(profile,'receiver','Receiver NF '+str(nf),ue_nf_db=nf)
        for shift in [-.15,.15]:
            exponent=round(base['exponent']+shift,2)
            add(profile,'propagation','Exponent '+str(exponent),exponent=exponent)
        for shift in [-3,3]:
            power=base['power_dbm']+shift
            if 40<=power<=49:add(profile,'power','Power '+str(power),power_dbm=power)
        add(profile,'load','2.5x offered payload',udp_interval_ms=20.0)
        add(profile,'sector','Two sectors at the two 2-cell sites',sector_policy='two_small')
        add(profile,'azimuth','Alternate antenna rotation',azimuth_seed=7)
        if profile in ['A','B']:
            add(profile,'carrier','Single carrier Band 8 hypothesis',dl_earfcn=3600,ul_earfcn=21600)
            add(profile,'carrier','Single carrier Band 1 hypothesis',dl_earfcn=300,ul_earfcn=18300)
    source=(PREVIOUS/'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    source=replace_once(source,'#include "ns3/antenna-module.h"',
        '#include "ns3/antenna-module.h"\n#include "ns3/lte-spectrum-value-helper.h"\n#include "static-shadow-model.h"')
    source=replace_once(source,'double rotation = std::numeric_limits<double>::quiet_NaN();',
        'double rotation = std::numeric_limits<double>::quiet_NaN();\n    uint32_t sectorCount = 3;')
    source=replace_once(source,'        if (limit && sites.size() == limit) break;',
        '        if (index.count("sector_count")) sites.back().sectorCount=std::stoul(row.at(index.at("sector_count")));\n'
        '        if (sites.back().sectorCount < 1 || sites.back().sectorCount > 3) throw std::runtime_error("Invalid sector count");\n'
        '        if (limit && sites.size() == limit) break;')
    source=replace_once(source,'    double beamwidth = 65.0;',
        '    double beamwidth = 65.0;\n    double shadowSigma=0.0, receiverNf=9.0;\n'
        '    uint32_t dlEarfcn=1300, ulEarfcn=19300;\n    uint64_t shadowSeed=42;\n    bool verifyShadow=false;')
    source=replace_once(source,'    cmd.Parse(argc, argv);',
        '    cmd.AddValue("shadowSigma", "Static per-link shadow std dB", shadowSigma);\n'
        '    cmd.AddValue("receiverNf", "UE downlink receiver NF dB", receiverNf);\n'
        '    cmd.AddValue("shadowSeed", "Coordinate-keyed shadow realization", shadowSeed);\n'
        '    cmd.AddValue("dlEarfcn", "Common downlink carrier", dlEarfcn);\n'
        '    cmd.AddValue("ulEarfcn", "Paired uplink carrier", ulEarfcn);\n'
        '    cmd.AddValue("verifyShadow", "Verify experimental shadow implementation", verifyShadow);\n'
        '    cmd.Parse(argc, argv);\n'
        '    if(verifyShadow) { VerifyExperimentalShadowModel(); return 0; }\n'
        '    if (shadowSigma<0 || receiverNf<0) throw std::runtime_error("Invalid shadow/NF");')
    source=replace_once(source,'TypeId::LookupByName("ns3::LogDistancePropagationLossModel")',
        'TypeId::LookupByName(shadowSigma>0 ? "ns3::ExperimentStaticShadow" : "ns3::LogDistancePropagationLossModel")')
    source=replace_once(source,'const double referenceLoss = 20 * std::log10(4 * M_PI * 1815e6 / 299792458.0);',
        'const double carrierHz=LteSpectrumValueHelper::GetCarrierFrequency(dlEarfcn);\n'
        '        const double referenceLoss = 20 * std::log10(4 * M_PI * carrierHz / 299792458.0);')
    source=replace_once(source,'        lte->SetPathlossModelAttribute("ReferenceLoss", DoubleValue(referenceLoss));',
        '        lte->SetPathlossModelAttribute("ReferenceLoss", DoubleValue(referenceLoss));\n'
        '        if(shadowSigma>0) {\n'
        '            lte->SetPathlossModelAttribute("Sigma",DoubleValue(shadowSigma));\n'
        '            lte->SetPathlossModelAttribute("ShadowSeed",UintegerValue(shadowSeed));\n        }')
    source=replace_once(source,'SetEnbDeviceAttribute("DlEarfcn", UintegerValue(1300))', 'SetEnbDeviceAttribute("DlEarfcn", UintegerValue(dlEarfcn))')
    source=replace_once(source,'"UlEarfcn", UintegerValue(19300)', '"UlEarfcn", UintegerValue(ulEarfcn)')
    source=replace_once(source,'SetUeDeviceAttribute("DlEarfcn", UintegerValue(1300))', 'SetUeDeviceAttribute("DlEarfcn", UintegerValue(dlEarfcn))')
    source=replace_once(source,'    Config::SetDefault("ns3::LteUePhy::TxPower", DoubleValue(23.0));',
        '    Config::SetDefault("ns3::LteUePhy::TxPower", DoubleValue(23.0));\n'
        '    Config::SetDefault("ns3::LteUePhy::NoiseFigure", DoubleValue(receiverNf));')
    source=replace_once(source,'    enbNodes.Create(3 * sites.size());',
        '    uint32_t sectorTotal=0;\n    for(const auto& site:sites)sectorTotal+=site.sectorCount;\n'
        '    enbNodes.Create(sectorTotal);')
    source=replace_once(source,'    for (size_t i = 0; i < sites.size(); ++i)',
        '    uint32_t enbIndex=0;\n    for (size_t i = 0; i < sites.size(); ++i)')
    source=replace_once(source,'sector < 3; ++sector','sector < sites[i].sectorCount; ++sector')
    source=replace_once(source,'enbNodes.Get(i * 3 + sector)','enbNodes.Get(enbIndex++)')
    source+='\n// Shadow header sha256: '+digest(sim/'static-shadow-model.h')+'\n'
    (sim/'sindirgi_baseline.cc').write_text(source,encoding='utf-8')
    runner=(PREVIOUS/'simulation/run_baseline.py').read_text(encoding='utf-8')
    runner=replace_once(runner,'import argparse','import argparse\nimport csv')
    runner=replace_once(runner,"    parser.add_argument('--skip-build',action='store_true')",
        "    parser.add_argument('--shadow-std',type=float,default=0)\n"
        "    parser.add_argument('--receiver-nf',type=float,default=9)\n"
        "    parser.add_argument('--shadow-seed',type=int,default=42)\n"
        "    parser.add_argument('--dl-earfcn',type=int,default=1300)\n"
        "    parser.add_argument('--ul-earfcn',type=int,default=19300)\n"
        "    parser.add_argument('--skip-build',action='store_true')")
    runner=replace_once(runner,"    run.append('--mixedCqi='+str(args.mixed_cqi))",
        "    run.append('--mixedCqi='+str(args.mixed_cqi))\n"
        "    run += ['--shadowSigma='+str(args.shadow_std),'--receiverNf='+str(args.receiver_nf),\n"
        "            '--shadowSeed='+str(args.shadow_seed),'--dlEarfcn='+str(args.dl_earfcn),'--ulEarfcn='+str(args.ul_earfcn)]")
    runner=replace_once(runner,"    result['model_assumptions']={",
        "    with args.sites_file.open() as stream:\n"
        "        sector_counts={r['site']:int(r.get('sector_count',3)) for r in csv.DictReader(stream)}\n"
        "    result['model_assumptions']={")
    runner=replace_once(runner,"'sectors_per_site':3", "'sectors_per_site':sector_counts")
    runner=replace_once(runner,"'dl_earfcn':1300,'ul_earfcn':19300", "'dl_earfcn':args.dl_earfcn,'ul_earfcn':args.ul_earfcn")
    runner=replace_once(runner,"'shadowing':False,'fading':False",
        "'shadowing':{'type':'static reciprocal coordinate-keyed per-link Gaussian dB','std_db':args.shadow_std,'seed':args.shadow_seed},\n"
        "        'receiver_noise_figure_db':args.receiver_nf,'fading':False")
    runner=replace_once(runner,"'propagation_note':'1 m free-space reference at 1815 MHz for log-distance; COST231 MediumCity branch for okumura'",
        "'propagation_note':'1 m free-space reference at selected DL carrier; optional static shadow, no terrain' ")
    runner=replace_once(runner,"'attachment':'automatic initial radio-based cell selection with EPC; UE DL EARFCN explicitly 1300'",
        "'attachment':f'automatic initial radio-based cell selection with EPC; UE DL EARFCN {args.dl_earfcn}'")
    (sim/'run_baseline.py').write_text(runner,encoding='utf-8')
    shutil.copy2(PREVIOUS/'simulation/ns3_paths.py',sim/'ns3_paths.py')
    draws=[{'spatial_seed':701,'azimuth_seed':42,'shadow_seed':1001},
           {'spatial_seed':702,'azimuth_seed':7,'shadow_seed':1002},
           {'spatial_seed':703,'azimuth_seed':99,'shadow_seed':1003}]
    plan={'purpose':'Broader native uncertainty exploration and common-draw robustness selection.',
        'screening_cases':cases,'screening_count':len(cases),'screening_duration_s':2.0,'warmup_s':1.0,
        'reference':copy.deepcopy(cases[0]),'ensemble_draws':draws,'ensemble_duration_s':4.0,
        'selection_rule':'Screen using five training sites only: mean of RSRP/SINR/RSRQ MAE +10 dB per missing training site. Take best three distinct structural models plus reference A if absent. Structural identity excludes stochastic draws. Evaluate all shortlisted models on the same three 4-second UE/azimuth/shadow draws. Choose minimum mean(training score)+0.5*population std; if reference A is within 0.10 dB of minimum, recommend reference A for parsimony. Controls excluded; all control sites have been seen previously.',
        'final_rule':'Freeze recommendation before controls. Confirm the first predeclared ensemble draw (not the best draw) at 8 seconds on 24,32,48 total sites. Compare 4 vs 8 seconds and two adjacent buffer expansions.',
        'shadow_model':'Explicit experimental static zero-mean Gaussian dB offsets, reciprocal coordinate-keyed, common to colocated sectors, no temporal fading or spatial correlation between distinct UE positions. Not inferred terrain. Sigma 0 uses unchanged built-in log-distance model.',
        'carrier_model':'One common paired carrier per scenario, no carrier aggregation or inter-frequency handover. Band 8/1 are hypotheses; path-loss reference frequency and UE search carrier change consistently.',
        'fixed':'All data-defined site coordinates/IDs, original cell linkage, raw measurements, target CSV, split and roles. Topology expansions use existing inventory-derived files. Three supplemental coordinates remain unverified.',
        'interpretation':'Actual native runs counted separately from previous analytic screening. Do not select a favorable random seed. Report coverage, outliers and all tradeoffs. No operator reconstruction or capacity-validation claim.',
        'parallel_workers':4,'source_cpp_sha256':digest(sim/'sindirgi_baseline.cc'),
        'code_hashes':{p.name:digest(p) for p in [sim/'sindirgi_baseline.cc',sim/'static-shadow-model.h',sim/'run_baseline.py']},
        'original_cpp_sha256':digest(PROJECT/'simulation/sindirgi_baseline.cc'),
        'input_hashes':{p.name:digest(p) for p in inputs.glob('*.csv')}}
    (HERE/'experiment_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(json.dumps({'native_screening_cases':len(cases),'families':pd.Series([c['category'] for c in cases]).value_counts().to_dict(),
                      'ensemble_draws':draws,'selection_rule':plan['selection_rule']},indent=2))


if __name__=='__main__':main()
