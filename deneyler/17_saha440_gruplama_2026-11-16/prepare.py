"""Read advisor grouping; prepare an explicit evidence gate before any new simulation.

No workbook is modified. Missing RF configuration stays missing, never filled from TA alone.
"""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import statistics
import sys
import math
import shutil
import openpyxl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SITE = 'SITE_000440'
SOURCE = ROOT/'ana_proje/sindirgi_site_cell_groups_v2.xlsx'
LAYERS = ROOT/'ana_proje/all_sites_cell_layers_v2.xlsx'
TEMPLATE = ROOT/'ana_proje/cellmapper_check_template.xlsx'
BASE = ROOT/'deneyler/14_cok_tasiyici_s2_2026-11-15'
MAP = 'https://www.cellmapper.net/map?MCC=286&MNC=1&type=LTE&latitude=39.21265&longitude=28.09685&zoom=16'


def records(path,sheet):
    workbook = openpyxl.load_workbook(path,read_only=True,data_only=True)
    try:
        values = iter(workbook[sheet].values)
        headers = next(values)
        return [dict(zip(headers,row)) for row in values]
    finally:
        workbook.close()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_runs():
    """Freeze all assumptions and inputs before native results, preserving recorded evidence."""
    import numpy as np
    import pandas as pd
    import importlib.util
    plan_path = HERE/'plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    if 'runtime' in plan:
        raise RuntimeError('Native run plan already frozen; refusing to overwrite.')
    sim = HERE/'simulation'
    sim.mkdir(exist_ok=True)
    for name in ['ns3_paths.py','static-shadow-model.h']:
        shutil.copy2(BASE/'simulation'/name,sim/name)
    source = (BASE/'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    def replace(old,new):
        nonlocal source
        assert source.count(old)==1, old[:100]
        source = source.replace(old,new)
    replace('    std::vector<std::string> carriers{"B3"};',
            '    std::vector<uint32_t> carrierSectorCounts;\n    std::vector<std::string> carriers{"B3"};')
    replace('if (name == "B20") return {6300, 24300, 50}; // 806 / 847 MHz, 10 MHz',
            'if (name == "B20") return {6400, 24400, 50}; // assumed 816 / 857 MHz, 10 MHz\n'
            '    if (name == "B1") return {100, 18100, 100}; // assumed 2120 / 1930 MHz, 20 MHz')
    replace('MakeDoubleChecker<double>(0.0));', '''MakeDoubleChecker<double>(0.0))
                                .AddAttribute("HighGain", "B1 relative free-space reference correction",
                                              DoubleValue(1.0),
                                              MakeDoubleAccessor(&SubGhzReferenceGain::m_highGain),
                                              MakeDoubleChecker<double>(0.0));''')
    replace('if (f->fc < 1e9) *it *= m_gain;',
            'if (f->fc < 1e9) *it *= m_gain;\n            else if (f->fc > 1.9e9) *it *= m_highGain;')
    replace('    double m_gain = 1.0;', '    double m_gain = 1.0;\n    double m_highGain = 1.0;')
    replace('sites.back().sectorCount > 3','sites.back().sectorCount > 4')
    replace('        if (limit && sites.size() == limit) break;', '''        if (index.count("carrier_sector_counts") && !row.at(index.at("carrier_sector_counts")).empty())
        {
            std::stringstream list(row.at(index.at("carrier_sector_counts")));
            std::string item;
            while (std::getline(list,item,';'))
            {
                const auto count = std::stoul(item);
                if (count < 1 || count > 4) throw std::runtime_error("Invalid per-carrier sector count");
                sites.back().carrierSectorCounts.push_back(count);
            }
            if (sites.back().carrierSectorCounts.size()!=sites.back().carriers.size())
                throw std::runtime_error("Carrier and sector-count lists differ");
            sites.back().sectorCount = *std::max_element(sites.back().carrierSectorCounts.begin(),sites.back().carrierSectorCounts.end());
        }
        if (limit && sites.size() == limit) break;''')
    replace('sectorTotal+=site.sectorCount*site.carriers.size();', '''if (site.carrierSectorCounts.empty()) sectorTotal+=site.sectorCount*site.carriers.size();
        else for (const auto n : site.carrierSectorCounts) sectorTotal+=n;''')
    replace('                const auto spec = CarrierFor(site.carriers[k], dlEarfcn, ulEarfcn);',
            '''                const auto count = site.carrierSectorCounts.empty() ? site.sectorCount : site.carrierSectorCounts.at(k);
                if (sector >= count) continue;
                const auto spec = CarrierFor(site.carriers[k], dlEarfcn, ulEarfcn);''')
    replace('const double orientation = phi + 120 * sector;',
            'const double orientation = site.carrierSectorCounts.empty() ? phi + 120.0 * sector : std::fmod(phi + 360.0/count * sector,360.0);')
    replace('GetDownlinkCarrierFrequency(6300)', 'GetDownlinkCarrierFrequency(6400)')
    replace('GetUplinkCarrierFrequency(24300)', 'GetUplinkCarrierFrequency(24400)')
    replace('dl->SetAttribute("Gain", DoubleValue(dlGain));', '''dl->SetAttribute("Gain", DoubleValue(dlGain));
        dl->SetAttribute("HighGain", DoubleValue(std::pow(LteSpectrumValueHelper::GetDownlinkCarrierFrequency(dlEarfcn) /
                                        LteSpectrumValueHelper::GetDownlinkCarrierFrequency(100),2)));''')
    replace('ul->SetAttribute("Gain", DoubleValue(ulGain));', '''ul->SetAttribute("Gain", DoubleValue(ulGain));
        ul->SetAttribute("HighGain", DoubleValue(std::pow(LteSpectrumValueHelper::GetUplinkCarrierFrequency(ulEarfcn) /
                                        LteSpectrumValueHelper::GetUplinkCarrierFrequency(18100),2)));''')
    replace('    bool verifyShadow=false;', '    bool verifyShadow=false;\n    bool verifyCarrierLayout=false;')
    replace('    cmd.AddValue("verifyShadow",',
            '    cmd.AddValue("verifyCarrierLayout", "Check new carrier layout and spectrum loss", verifyCarrierLayout);\n    cmd.AddValue("verifyShadow",')
    replace('    if(verifyShadow) { VerifyExperimentalShadowModel(); return 0; }',
            '    if(verifyCarrierLayout) { VerifyCarrierLayout(); return 0; }\n    if(verifyShadow) { VerifyExperimentalShadowModel(); return 0; }')
    marker = 'int\nmain(int argc, char* argv[])'
    replace(marker, '''static void
VerifyCarrierLayout()
{
    uint32_t checks=0;
    auto check = [&](double actual,double expected) {
        if (std::abs(actual-expected)>1e-10*std::max(1.0,std::abs(expected)))
            throw std::runtime_error("Carrier-layout verification failed");
        ++checks;
    };
    const auto b20=CarrierFor("B20",1300,19300), b1=CarrierFor("B1",1300,19300);
    check(LteSpectrumValueHelper::GetDownlinkCarrierFrequency(b20.dlEarfcn),816e6);
    check(LteSpectrumValueHelper::GetUplinkCarrierFrequency(b20.ulEarfcn),857e6);
    check(LteSpectrumValueHelper::GetDownlinkCarrierFrequency(b1.dlEarfcn),2120e6);
    check(LteSpectrumValueHelper::GetUplinkCarrierFrequency(b1.ulEarfcn),1930e6);
    check(b20.rb,50); check(b1.rb,100);
    Bands bands;
    for (double fc : {816e6,1815e6,2120e6}) {
        BandInfo b; b.fl=fc-90000; b.fc=fc; b.fh=fc+90000; bands.push_back(b);
    }
    auto params=Create<SpectrumSignalParameters>();
    params->psd=Create<SpectrumValue>(Create<SpectrumModel>(bands));
    for (auto it=params->psd->ValuesBegin();it!=params->psd->ValuesEnd();++it) *it=1.0;
    auto loss=CreateObject<SubGhzReferenceGain>();
    loss->SetAttribute("Gain",DoubleValue(std::pow(1815.0/816,2)));
    loss->SetAttribute("HighGain",DoubleValue(std::pow(1815.0/2120,2)));
    auto a=CreateObject<ConstantPositionMobilityModel>();
    auto b=CreateObject<ConstantPositionMobilityModel>();
    auto output=loss->CalcRxPowerSpectralDensity(params,a,b);
    check((*output)[0],std::pow(1815.0/816,2));
    check((*output)[1],1); check((*output)[2],std::pow(1815.0/2120,2));
    check((*params->psd)[0],1);
    std::set<double> angles;
    for (uint32_t i=0;i<4;++i) angles.insert(std::fmod(10+360.0/4*i,360.0));
    check(angles.size(),4); check(*angles.rbegin(),280);
    auto antenna=CreateObject<CosineAntennaModel>();
    for (double rotation : {10.0,114.674790846})
        for (uint32_t i=0;i<4;++i) {
            const double angle=std::fmod(rotation+360.0/4*i,360.0);
            antenna->SetAttribute("Orientation",DoubleValue(angle));
            check(angle>=0 && angle<360,1);
        }
    std::cout << "{\\"passed\\":true,\\"checks\\":" << checks << "}\\n";
}

int
main(int argc, char* argv[])''')
    source = source.replace('#include <sstream>','#include <sstream>\n#include <set>')
    (sim/'sindirgi_baseline.cc').write_text(source,encoding='utf-8')
    runner = (BASE/'simulation/run_baseline.py').read_text(encoding='utf-8')
    runner = runner.replace("    parser.add_argument('--skip-build'", "    parser.add_argument('--build-only',action='store_true')\n    parser.add_argument('--skip-build'")
    runner = runner.replace("hashlib.sha256((HERE/'sindirgi_baseline.cc').read_bytes()).hexdigest()",
                            "hashlib.sha256((HERE/'sindirgi_baseline.cc').read_bytes()+(HERE/'static-shadow-model.h').read_bytes()).hexdigest()")
    runner = runner.replace("    entry=next(v for v in commands if v['file'].endswith('/src/lte/examples/lena-simple-epc.cc'))",
                            "    entry=next((v for v in commands if v['file'].endswith('/src/lte/examples/lena-simple-epc.cc')),None)\n"
                            "    if entry is None: entry=next(v for v in commands if v['file'].endswith('/utils/perf/perf-io.cc'))")
    runner = runner.replace('    env=os.environ.copy()', '    if args.build_only: return\n    env=os.environ.copy()')
    runner = runner.replace("    result['model_assumptions']={", "    result['advisor_sector_layout']={r['site']:{'carriers':r.get('carriers','B3'),'sector_counts':r.get('carrier_sector_counts') or str(r.get('sector_count',3))} for r in site_rows}\n    result['model_assumptions']={")
    runner = runner.replace("'propagation_note':'1 m free-space reference at selected DL carrier; optional static shadow, no terrain'",
                            "'propagation_note':'S0 log-distance reference, with relative B20/B1 frequency corrections for DL and UL, inherited UL reference convention from experiment 14; no terrain'")
    (sim/'run_baseline.py').write_text(runner,encoding='utf-8')
    strong = [r['site'] for r in plan['strong_sites_in_current_region']]
    real_cells = pd.read_excel(LAYERS,sheet_name='Cells')
    mapping = []
    for site in strong:
        records_site = real_cells[real_cells.Site.eq(site)]
        blocks = []
        for block,group in records_site.groupby('Block'):
            ta = float(group['Experia median TA (km, x4.88 m)'].median())
            assert np.isfinite(ta)
            blocks.append({'site':site,'block':int(block),'sectors':len(group),'median_ta_km':ta,
                           'real_cells':group.Cell.tolist()})
        assert len(blocks)==3
        for band,block in zip(['B20','B3','B1'],sorted(blocks,key=lambda x:(-x['median_ta_km'],x['block']))):
            mapping.append(dict(block,assumed_band=band))
    # Assignment is frozen from source TA, never chosen against RSRP/SINR targets.
    spec = importlib.util.spec_from_file_location('radio17',ROOT/'deneyler/10_kapsama_haritalari_2026-11-15/radio_model.py')
    radio = importlib.util.module_from_spec(spec); spec.loader.exec_module(radio)
    inputs = HERE/'inputs'
    shutil.copy2(BASE/'inputs/targets.csv',inputs/'targets.csv')
    cases, allocations = [], {}
    for az,seed in [[42,701],[7,702],[99,703]]:
        sites = pd.read_csv(BASE/f'inputs/sites_S0_{az}.csv')
        sites['carrier_sector_counts']='3'
        for site in strong:
            mp = {r['assumed_band']:r for r in mapping if r['site']==site}
            counts = [mp[b]['sectors'] for b in ['B3','B20','B1']]
            assert counts[0]==3, 'B3 geometry must preserve existing three-sector load placement'
            sites.loc[sites.site.eq(site),'carriers']='B3;B20;B1'
            sites.loc[sites.site.eq(site),'carrier_sector_counts']=';'.join(map(str,counts))
            sites.loc[sites.site.eq(site),'sector_count']=max(counts)
        old = pd.read_csv(BASE/f'inputs/ues_S0_{seed}.csv',dtype=str,keep_default_na=False)
        ues = old.copy()
        baseline_sectors = pd.read_csv(BASE/f'simulation/results/S0_draw{seed}/sectors.csv')
        points = ues.iloc[:256][['x_m','y_m','z_m']].to_numpy(float)
        best = baseline_sectors.iloc[radio.received_power_w(points,baseline_sectors).argmax(axis=1)].site.to_numpy()
        assigned = np.full(256,1300)
        for site in strong:
            ids = np.flatnonzero(best==site)
            # No measured per-carrier user share is available: balanced split is an explicit assumption.
            for pos,u in enumerate(ids): assigned[u]=[1300,6400,100][pos%3]
        ues.loc[:255,'dl_earfcn']=assigned.astype(str)
        for site in strong:
            s = sites[sites.site.eq(site)].iloc[0]
            mp = {r['assumed_band']:r for r in mapping if r['site']==site}
            for layer,band in [(1,'B20'),(2,'B1')]:
                n = mp[band]['sectors']
                for sector in range(n):
                    angle = math.radians(float(s.rotation_deg)+360.0/n*sector)
                    row = dict(ue_id=str(len(ues)),x_m=f'{s.x_m+800*math.cos(angle):.9f}',
                               y_m=f'{s.y_m+800*math.sin(angle):.9f}',z_m='1.500000000',kind='load',
                               target_site=site,target_sector=str(sector+10*layer),target_prb='0.233000',
                               udp_interval_ms=f'{1.47/0.233*(2 if band=="B20" else 1):.6f}',dl_earfcn=str({'B20':6400,'B1':100}[band]))
                    ues.loc[len(ues)] = row
        assert len(ues)==355
        pd.testing.assert_frame_equal(ues.iloc[256:328].reset_index(drop=True),old.iloc[256:328].reset_index(drop=True))
        assert (ues.iloc[:256][['x_m','y_m','z_m']].to_numpy()==old.iloc[:256][['x_m','y_m','z_m']].to_numpy()).all()
        sites.to_csv(inputs/f'sites_G17_{az}.csv',index=False,float_format='%.9f')
        ues.to_csv(inputs/f'ues_G17_{seed}.csv',index=False)
        allocations[str(seed)]={str(k):int(v) for k,v in zip(*np.unique(assigned,return_counts=True))}
        cases.append(dict(name=f'G17_draw{seed}',az=az,seed=seed,ues=355))
    runtime = {
        'frozen_before_native_runs':True,'cases':cases,'block_band_mapping':mapping,
        'bands':{'B3':{'dl_earfcn':1300,'ul_earfcn':19300,'dl_mhz':1815,'ul_mhz':1720,'rb':100},
                 'B20':{'dl_earfcn':6400,'ul_earfcn':24400,'dl_mhz':816,'ul_mhz':857,'rb':50},
                 'B1':{'dl_earfcn':100,'ul_earfcn':18100,'dl_mhz':2120,'ul_mhz':1930,'rb':100}},
        'band_mapping_status':'TA-informed assumptions; not verified at project sites. B1 historical in regional example.',
        'frequency_choice':'Largest block median TA -> B20; middle -> B3; smallest -> B1. B3 remains S0 center frequency for controlled comparison; B20/B1 centers from regional example.',
        'power_dbm_per_cell':49,'beamwidth_deg':120,'max_gain_dbi':15,'exponent':3,'receiver_nf_db':9,
        'orientation_assumption':'Same frozen site rotation; 3-sector blocks 120-degree spacing, 4-sector blocks 90-degree spacing. Beamwidth 120 degrees on both.',
        'carrier_allocation':'Strongest S0 analytical B3 cell determines provisional site. For UEs provisionally at a strong site, balanced round-robin B3/B20/B1 by UE ID; others B3. Real band shares unknown; no inter-frequency automatic selection/CA/handover claimed.',
        'measurement_allocations':allocations,'load_cells':99,'baseline_load_cells':72,
        'load_rule':'All original 72 B3 load users copied unchanged; 27 new B20/B1 load users, 800m on boresight, target PRB .233. Interval (1.47/.233)*(100/RB) ms: double interval for B20 50 RB, unchanged for B1 100 RB. Frozen bandwidth normalization, no outcome-based calibration.',
        'interpretation':'Per-resource offered load held nominally constant, NOT constant total offered traffic/power/capacity. Equivalent traffic rises (72+14*.5+13)/72=1.27778; total cell count/power rises 99/72=1.375. Report achieved PRB separately.',
        'duration_s':4,'warmup_s':1,
        'input_hashes':{p.name:sha(p) for p in sorted(inputs.glob('*.csv'))},
        'simulation_hashes':{p.name:sha(p) for p in sorted(sim.glob('*')) if p.is_file()},
        'regression_inputs':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in
                             [BASE/'inputs/sites_S0_42.csv',BASE/'inputs/ues_S0_701.csv']},
        'baseline_reference':'deneyler/14_cok_tasiyici_s2_2026-11-15/simulation/results/S0_draw701',
        'no_new_handover_or_building_model':True,
    }
    plan['runtime']=runtime
    plan['status']='native_run_plan_frozen'
    plan_path.write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
    report = HERE/'SONUCLAR.md'
    text = report.read_text(encoding='utf-8')
    text = '\n'.join('**Durum: Tam senaryo ve varsayımlar sabitlendi; kod doğrulaması ve üç koşu hazırlanıyor.**'
                     if line.startswith('**Durum:') else line for line in text.splitlines())
    text += '\n\n## Koşudan önce sabitlenen senaryo\n\n'
    text += 'Dört güçlü sahanın blokları TA medyanına göre sıralandı: en yüksek TA → B20 (816 MHz), orta → B3 (1815 MHz), en düşük → B1 (2120 MHz). Bunlar hedef sahaların doğrulanmış bantları değil, hocanın izin verdiği varsayımlardır. B1 bölgesel örnekte tarihsel kayıttır. B3 merkezi S0 ile aynı tutuldu.\n\n'
    text += '| Saha | Kaynak blok | Sektör sayısı | TA medyanı (km) | Varsayılan bant |\n|---|---:|---:|---:|---|\n'
    for row in sorted(mapping,key=lambda r:(r['site'],r['block'])):
        text += f"| {row['site']} | {row['block']} | {row['sectors']} | {row['median_ta_km']:.3f} | {row['assumed_band']} |\n"
    text += '\nB3/B1 genişliği 20 MHz, B20 10 MHz; her hücre 49 dBm. Anten kazancı 15 dBi, yatay genişlik tümünde 120°. Dört sektörlü katmanda yön aralığı 90°, üçlüde 120° varsayıldı. Bina kaybı, dikey desen veya yeni handover eklenmedi.\n\n'
    text += '256 ölçüm kullanıcısının konumu aynen korundu. Önceki B3 sinyal hesabında güçlü sahaya bağlanacak kullanıcılar, kimlik sırasıyla üç taşıyıcıya dengeli dağıtıldı; diğerleri B3 kaldı. Gerçek taşıyıcı kullanıcı payları bilinmiyor, bu dağılım varsayım. ns-3 otomatik frekanslar arası seçim yaptığı iddia edilmiyor.\n\n'
    text += '72 eski yük kullanıcısı aynen korundu; 27 yeni hücreye birer yük kullanıcısı eklendi. 10 MHz B20 hücrelerinin paket aralığı 20 MHz hücrelerin iki katı seçildi; böylece dar taşıyıcıya bant genişliğiyle orantılı trafik verildi. Hedef PRB 0,233 ve eski 1,47 katsayısı korundu; sonuçlara bakarak ayar yapılmayacak. Toplam 99 hücre ve 355 kullanıcı var. Toplam yük trafiği yaklaşık %27,8, hücre sayısı ve toplam yapılandırılmış güç %37,5 artıyor. Gerçekleşen PRB ayrıca kontrol edilecek; sonuç yalnız frekans etkisi diye yorumlanmayacak.\n\n'
    text += 'Önce yeni bant ve sektör kodu kendi kontrollerinden geçecek; sonra S0 tek taşıyıcılı tam koşusu eski altı CSV ile yalnız CRLF/LF normalizasyonu sonrası birebir karşılaştırılacak. Geçmeden yeni üç koşu başlamayacak. Eşikler önceden plan.json içinde yazılı; sonuçlara bakarak ayar seçilmeyecek.\n'
    report.write_text(text,encoding='utf-8')
    print(json.dumps({'cells':99,'measurement_ues':256,'load_ues':99,'cases':cases,'allocations':allocations},indent=2))


def apply_advisor_clarification():
    """Explicit pre-run amendment after the user supplied the advisor's actual messages."""
    path = HERE/'plan.json'
    plan = json.loads(path.read_text(encoding='utf-8'))
    if 'runtime' in plan:
        raise RuntimeError('Native plan already frozen; do not reapply preparation-stage amendments.')
    sites = {r['Site']:r for r in records(LAYERS,'Sites')}
    strong = ['SITE_000198','SITE_000220','SITE_000224','SITE_000440']
    plan['status'] = 'advisor_clarified_TA_assumptions_allowed_no_simulation_started'
    plan['advisor_clarification'] = {
        'source':'User-provided advisor messages of 16 November 2026; pre-run amendment',
        'rule':'Strong sites use suggested groups; others use one 1800 MHz carrier and 3 sectors. Higher TA may be assigned lower frequency as an explicit assumption. CellMapper evidence is preferred, not a blanket prerequisite.',
        'manual_check_priority':['SITE_000440','SITE_000206','SITE_000224'],
        'verified_RF_fields_remain_empty':True}
    plan['verification']['mandatory_for_assumption_based_run'] = False
    plan['verification']['cautions'][-1] = 'Unobserved carriers may be modeled only as clearly labeled TA-informed assumptions, not as verified bands.'
    plan['strong_sites_in_current_region'] = [
        {'site':s,'blocks':sites[s]['Block sizes (ID order)'],
         'confidence':sites[s]['Site confidence'],'p_value':sites[s]['p-value']} for s in strong]
    plan['manual_check_sites'] = [
        {'site':s,'lat':sites[s]['Lat'],'lon':sites[s]['Lon'],
         'current_confidence':sites[s]['Site confidence'],
         'current_blocks':sites[s]['Block sizes (ID order)'],'observation':'not verified'}
        for s in ['SITE_000440','SITE_000206','SITE_000224']]
    plan['staged_scope'] = {
        'first':'440-only pilot as previously proposed, to isolate topology changes',
        'then':'Full advisor scenario: strong 198/220/224/440 with exact per-block sector counts; other sites one B3 carrier, 3 sectors. Do not silently round four-sector blocks to three.'}
    path.write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
    report = HERE/'SONUCLAR.md'
    text = report.read_text(encoding='utf-8')
    heading = '## Hocanın mesajlarıyla netleşen uygulama'
    text = text.split(heading)[0].rstrip()
    text = '\n'.join('**Durum: TA’ya göre açıkça varsayım olarak bant seçilebilir. CellMapper doğrulaması tamamlanmadı; yeni simülasyon henüz başlatılmadı.**'
                     if line.startswith('**Durum:') else line for line in text.splitlines())
    text = text.replace('**Devam için eksik bilgi:**','**Bant doğrulaması için eksik bilgi:**')
    addition = [heading,'',
        'Hoca, güçlü grupların önerildiği gibi kurulmasına; diğer sahaların tek taşıyıcı, 3 sektör, 1800 MHz kalmasına izin veriyor. Çok taşıyıcılı sahalarda yüksek TA’ya düşük frekans atanması deneme varsayımı olarak kullanılabilir. CellMapper gözlemi varsa tercih edilir; yokluğu bütün simülasyonu durdurma gerekçesi değildir.', '',
        'Mevcut 24 sahalık bölgenin güncel v2 dosyasında güçlü sahalar: **198 (3+3+3), 220 (4+3+4), 224 (3+4+3), 440 (3+3+3)**. Bunlardan yalnız 440 ana değerlendirme sahasıdır; diğer üçü komşu girişim sahalarıdır. Bütün 24 saha için yalnız 440’ın güçlü olduğunu söylemek doğru değildir.', '',
        '206 elle kontrol önceliğinde kalır; güncel v2 dosyasında güveni moderate, gruplaması 3+3+3+3’tür. Eski şablondaki 4+4+4 ve p-değeri güncel v2 ile aynı değildir.', '',
        'Önce daha önce önerilen 440 pilotu, ardından güçlü grupların tamamının uygulandığı senaryo hazırlanır. İlk pilotun diğer güçlü sahaları tek taşıyıcı tutması değişikliği ayırmak içindir; hocanın tam senaryosu olduğu iddia edilmez. Dört sektörlü bloklar üçe yuvarlanmaz.', '',
        '| Elle kontrol | Enlem | Boylam | Güncel v2 güveni |',
        '|---|---:|---:|---|']
    for site in plan['manual_check_sites']:
        link = f"https://www.cellmapper.net/map?MCC=286&MNC=1&type=LTE&latitude={site['lat']}&longitude={site['lon']}&zoom=16"
        addition.append(f"| [{site['site']}]({link}) | {site['lat']} | {site['lon']} | {site['current_confidence']} |")
    report.write_text(text+'\n\n'+'\n'.join(addition)+'\n',encoding='utf-8')
    print('Clarified existing plan/report; no files added, RF fields not verified, no run started.')


def main():
    if (HERE/'plan.json').exists():
        raise RuntimeError('Evidence snapshot exists; do not overwrite it silently.')
    cells = [r for r in records(SOURCE,'Cell groups') if r['Site']==SITE]
    summary = next(r for r in records(SOURCE,'Site summary') if r['Site']==SITE)
    site = next(r for r in records(LAYERS,'Sites') if r['Site']==SITE)
    legacy = next(r for r in records(TEMPLATE,'Sites to check') if r['Site']==SITE)
    assert len(cells)==9 and len({r['Cell'] for r in cells})==9
    assert {r['Cell number'] for r in cells}==set(range(6021,6030))
    grouped = defaultdict(list)
    for r in cells: grouped[int(r['Block'])].append(r)
    assert sorted(map(len,grouped.values()))==[3,3,3]
    inputs = HERE/'inputs'
    inputs.mkdir(exist_ok=True)
    out = []
    for block,rows in sorted(grouped.items()):
        for r in rows:
            out.append({'site':SITE,'cell':r['Cell'],'block':block,
                        'sector_azimuth_deg':'','verified_band':'','verified_dl_earfcn':'',
                        'verified_bandwidth_mhz':'','source_band_hypothesis':r['Candidate band (hypothesis)'],
                        'source_layer':r['Layer (sparse class)'],
                        'experia_median_ta_km':r['Experia median TA (km, x4.88 m)'],
                        'experia_mean_rsrp_dbm':r['Experia mean RSRP (dBm)']})
    csv_path = inputs/'cell_groups_440.csv'
    with csv_path.open('w',encoding='utf-8',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(out[0]))
        writer.writeheader(); writer.writerows(out)
    plan = {
        'status':'awaiting_external_band_evidence_no_simulation_started',
        'site':SITE,'coordinates':{'lat':site['Lat'],'lon':site['Lon']},
        'grouping':{'cells':9,'blocks':3,'cells_per_block':3,'confidence':summary['Confidence'],
                    'p_value':summary['p-value'],'evidence_kind':'statistical grouping hypothesis; not RF configuration'},
        'verification':{'method':'manual CellMapper viewing, no bulk scraping','url':MAP,
                        'matching_distance_threshold_m':300,
                        'status':'not_observed','reason':'Browser access host unavailable; native UI URL safety check stopped access; web reader cannot access interactive map.',
                        'required':['Matching tower coordinates and distance','LTE bands / EARFCNs shown and observation date',
                                    'Observed sector counts per carrier','Azimuths if available'],
                        'cautions':['No tower observation is not evidence of tower absence.',
                                    'A nearby public tower does not by itself map anonymized CELL IDs to EARFCNs.',
                                    'Current crowdsourced data may differ from 2025 KPI and 2026 Experia periods.',
                                    'If fewer than 3 carriers are observed, do not invent the others.']},
        'predeclared_experiment':{
            'baseline':'S0 of experiment 14, original 2–6 km placement (TA placement remains unresolved)',
            'question':'Does changing only the well-supported SITE_000440 carrier structure improve the representation?',
            'changed_site_only':SITE,
            'other_sites':'23 sites unchanged; S0 configuration and coordinates',
            'measurement_positions':'Reuse frozen S0 inputs; 256 measurement users, draws 701/702/703',
            'orientations':'Reuse rotations 42/7/99; do not infer azimuth from position within consecutive cell triples',
            'duration_s':4,'warmup_s':1,'seeds':[[42,701],[7,702],[99,703]],
            'load':'Keep original B3 load inputs; explicitly specify added-carrier load and verify achieved PRB before acceptance',
            'training_sites':['SITE_000130','SITE_000296','SITE_000444','SITE_000482','SITE_000554'],
            'holdout_sites':['SITE_000440','SITE_000441','SITE_000443'],
            'no_retuning':'No RF parameter selection from 440 RSRP/SINR; 440 remains held out for tuning. Topology evidence is an input.',
            'gate':'Before any run, freeze explicit verified or clearly labeled assumed carrier frequencies, bandwidths, powers, sector mapping, per-UE carrier selection and added-carrier load in a run plan. Do not present TA-derived band labels as verified.',
            'metrics':['Per-site RSRP/SINR signed errors and MAE by existing split','Per-carrier cell counts and serving-user shares',
                       'All measurement users connected and receiving downlink','Achieved PRB and total offered traffic',
                       'No RSRQ-based tuning; explain mixed-SINR sampling limitation'],
            'acceptance_before_any_run':{
                'holdout_mean_rsrp_improvement_db_min':0.5,
                'holdout_mean_sinr_degradation_db_max':0.5,
                'each_other_evaluation_site_rsrp_degradation_db_max':1.0,
                'per_draw_mean_prb_change_max':0.03,
                'measurement_users_connected':256,'measurement_users_receiving_dl':256},
            'regression':'If code changes are required, compare a local disabled-feature repeat to frozen S0 outputs; normalize CRLF/LF only, no numeric tolerance.',
        },
        'legacy_template_conflict':{'old_p_value':legacy['Site p-value'],'current_p_value':summary['p-value'],
                                    'resolution':'Use current v2 grouping statistics. Keep original template unchanged.'},
        'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [SOURCE,LAYERS,TEMPLATE,BASE/'plan.json']},
        'prepared_input_sha256':sha(csv_path),
    }
    (HERE/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
    lines = ['# Deney 17 — 440 sahasının hücre ve taşıyıcı yapısı','',
             '**Durum: Yerel inceleme ve deney taslağı hazır. CellMapper doğrulaması yapılmadı; yeni simülasyon başlatılmadı.**','',
             '## Kaynaklardan öğrendiklerimiz','',
             'Hocanın güncel v2 gruplamasında SITE_000440, 9 hücreden oluşan 3 üçlü blok içeriyor. Gruplama güçlü olarak işaretli (p=0,017). Bu istatistiksel destek, frekansların doğrulandığı anlamına gelmiyor.','',
             '| Blok | Hücreler | Üç hücrenin TA medyanlarının medyanı | Dosyadaki bant hipotezi |',
             '|---|---|---:|---|']
    for block,rows in sorted(grouped.items()):
        names = ', '.join(r['Cell'].replace('CELL_','') for r in rows)
        median = statistics.median(r['Experia median TA (km, x4.88 m)'] for r in rows)
        lines.append(f"| {block} | {names} | {median:.2f} km | {rows[0]['Candidate band (hypothesis)']} |")
    lines += ['', 'İlk iki blok aynı uzun menzil grubunda. Üçüncü blokta sinyal daha zayıf; tüm ağ analizinin yöntem notu, bu iki menzil sınıfının uzaklıklarının benzer olduğunu ve tek kapsama grubu gibi okunması gerektiğini belirtiyor. Bu nedenle bloklara yalnız TA sırasına bakarak kesin 800/900/1800 MHz atamak desteklenmiyor.', '',
              'Blok içindeki hücre sırası anten yönünü göstermiyor. Yeni bant/EARFCN, bant genişliği ve azimut alanları inputs/cell_groups_440.csv içinde boş bırakıldı. Kaynak Excel dosyaları değiştirilmedi.', '',
              'Kontrol şablonunda eski p=0,055 değeri var; güncel v2 değeri p=0,017. Yeni gruplama esas alındı.','',
              '## CellMapper kontrolü','',
              f'[440 koordinatında Turkcell LTE haritası]({MAP})','',
              'Koordinat: 39.21265 K, 28.09685 D. Yaklaşık 300 m içindeki aday kulelerde bant/EARFCN, bant başına hücre sayısı ve varsa anten yönleri incelenecek. Daha uzak kuleyle eşleşme belirsiz sayılacak.','',
              'Erişim denendi: tarayıcı bağlantı sunucusu kullanılamadı; yerel arayüz aracı adresi güvenilir biçimde belirleyemediği için durdu. Web okuyucu da etkileşimli haritayı açamadı. Kule ve bant gözlemi yok; bu, o konumda kule olmadığı anlamına gelmez. Toplu veri çekilmedi.','',
              '## Tek yeni senaryonun sınırı','',
              'Yalnız 440 sahasının taşıyıcı yapısı değiştirilecek; diğer 23 saha, S0 kullanıcı konumları ve radyo ayarları korunacak. Deney 16’daki bina kaybı eklenmeyecek. Üç anten/kullanıcı örneği kullanılacak.','',
              'Koşudan önce frekanslar, bant genişlikleri, güçler, taşıyıcıya kullanıcı atama kuralı ve yeni hücrelerin yükü açıkça sabitlenecek. Doğrulanamayan bilgi varsayım diye işaretlenecek; 3 taşıyıcıyı doldurmak için veri uydurulmayacak. Karşılaştırma ve kabul kuralları plan.json içinde kayıtlı.','',
              '440 ayarlamada kullanılmayan saha olarak kalır; buradaki sinyal sonuçlarına bakarak güç/frekans seçilmez. Gerçek yapı bilgisi modele girdi olarak kullanılabilir.','',
              '**Devam için eksik bilgi:** Aday CellMapper kulesinin koordinatı ve görünen LTE bant/EARFCN listesi. Üç gerçek hücre bloğunun bantlarla birebir eşlemesi ayrıca belirsizdir; kamu haritası bunu her zaman sağlayamaz.']
    (HERE/'SONUCLAR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Prepared 9 cells in 3 groups; RF fields intentionally unverified. No simulation started.')


if __name__=='__main__':
    if '--freeze-runs' in sys.argv:
        freeze_runs()
    elif '--advisor-update' in sys.argv:
        apply_advisor_clarification()
    else:
        main()
