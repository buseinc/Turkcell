"""Freeze S0 handover integration and independent positive/negative protocol tests."""
from pathlib import Path
import csv
import hashlib
import json
import math
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = HERE.parent/'14_cok_tasiyici_s2_2026-11-15'
D17 = HERE.parent/'17_saha440_gruplama_2026-11-16'


def read(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def write(path,rows):
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (HERE/'plan.json').exists(): raise RuntimeError('Plan already frozen.')
    inputs,sim=HERE/'inputs',HERE/'simulation'
    inputs.mkdir(exist_ok=True);sim.mkdir(exist_ok=True)
    for name in ['ns3_paths.py','static-shadow-model.h']:
        shutil.copy2(BASE/'simulation'/name,sim/name)
    source=(BASE/'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    def change(old,new):
        nonlocal source
        assert source.count(old)==1,old[:80]
        source=source.replace(old,new)
    change('using namespace ns3;','using namespace ns3;\n#include "handover-support.h"')
    change('ConnectionTrace(uint32_t ue,uint64_t,uint16_t,uint16_t)',
           'ConnectionTrace(uint32_t ue,uint64_t imsi,uint16_t cell,uint16_t rnti)')
    change('    if (gConnectedAt.at(ue)<0) gConnectedAt[ue]=Simulator::Now().GetSeconds();',
           '    if (gConnectedAt.at(ue)<0) gConnectedAt[ue]=Simulator::Now().GetSeconds();\n    s0ho::Connection(ue,imsi,cell,rnti);')
    change('    bool verifyShadow=false;', '''    bool verifyShadow=false;
    bool enableHandover=false;
    std::string waypointFile;
    double handoverHysteresis=3.0;
    uint32_t handoverTttMs=256;''')
    change('    cmd.AddValue("verifyShadow",', '''    cmd.AddValue("handover", "Enable A3 RSRP handover and full-mesh X2", enableHandover);
    cmd.AddValue("waypoints", "Optional UE waypoint CSV: ue_id,time_s,x_m,y_m,z_m", waypointFile);
    cmd.AddValue("handoverHysteresis", "A3 RSRP hysteresis, dB", handoverHysteresis);
    cmd.AddValue("handoverTttMs", "A3 time-to-trigger, ms", handoverTttMs);
    cmd.AddValue("verifyShadow",''')
    change('    lte->SetSchedulerType("ns3::PfFfMacScheduler");', '''    lte->SetSchedulerType("ns3::PfFfMacScheduler");
    if (enableHandover)
    {
        lte->SetHandoverAlgorithmType("ns3::A3RsrpHandoverAlgorithm");
        lte->SetHandoverAlgorithmAttribute("Hysteresis",DoubleValue(handoverHysteresis));
        lte->SetHandoverAlgorithmAttribute("TimeToTrigger",TimeValue(MilliSeconds(handoverTttMs)));
    }''')
    change('    ueNodes.Create(ueCount);\n    mobility.Install(ueNodes);', '''    ueNodes.Create(ueCount);
    if (!waypointFile.empty())
        mobility.SetMobilityModel("ns3::WaypointMobilityModel","InitialPositionIsWaypoint",BooleanValue(false));
    mobility.Install(ueNodes);''')
    change('    enbNodes.Create(sectorTotal);', '''    if(enableHandover && multiCarrier)
        throw std::runtime_error("This integration validates intra-frequency S0 handover only");
    enbNodes.Create(sectorTotal);''')
    change('    NetDeviceContainer ueDevices;', '''    if (!waypointFile.empty())
    {
        std::ifstream input(waypointFile);
        if (!input) throw std::runtime_error("Cannot open waypoints");
        std::string line; std::getline(input,line);
        auto columns=Split(line);
        std::unordered_map<std::string,size_t> ix;
        for(size_t i=0;i<columns.size();++i) ix[columns[i]]=i;
        std::vector<std::vector<Waypoint>> points(ueCount);
        while(std::getline(input,line))
        {
            if(line.empty()) continue;
            const auto row=Split(line);
            const auto u=std::stoul(row.at(ix.at("ue_id")));
            const double t=std::stod(row.at(ix.at("time_s")));
            if(u>=ueCount || t<0 || t>duration+1e-8) throw std::runtime_error("Invalid waypoint UE/time");
            auto& list=points.at(u);
            if(!list.empty() && t<=list.back().time.GetSeconds()) throw std::runtime_error("Waypoints not increasing");
            list.emplace_back(Seconds(t),Vector(std::stod(row.at(ix.at("x_m"))),
                std::stod(row.at(ix.at("y_m"))),std::stod(row.at(ix.at("z_m")))));
        }
        for(uint32_t u=0;u<ueCount;++u)
        {
            auto mm=ueNodes.Get(u)->GetObject<WaypointMobilityModel>();
            const auto initial=mm->GetPosition();
            if(points[u].empty())
            {
                points[u].emplace_back(Seconds(0),initial);
                points[u].emplace_back(Seconds(duration),initial);
            }
            if(points[u].front().time!=Seconds(0) || CalculateDistance(initial,points[u].front().position)>1e-6)
                throw std::runtime_error("First waypoint must match fixed position at zero");
            for(const auto& p:points[u]) mm->AddWaypoint(p);
        }
    }
    NetDeviceContainer ueDevices;''')
    change('    gRadio.open(out("radio_samples.csv"));', '''    if(enableHandover || !waypointFile.empty())
    {
        s0ho::events.open(out("handover_events.csv"));
        s0ho::events << "time_s,actor,event,ue_id,imsi,cell_id,rnti,target_cell_id\\n" << std::setprecision(12);
        s0ho::timeline.open(out("serving_timeline.csv"));
        s0ho::timeline << "time_s,ue_id,x_m,y_m,z_m,cell_id,rnti,rrc_state,dl_bytes\\n" << std::setprecision(12);
        if(!waypointFile.empty())
        {
            s0ho::packets.open(out("packet_rx.csv"));
            s0ho::packets << "time_s,ue_id,packet_bytes\\n" << std::setprecision(12);
        }
        for(uint32_t u=0;u<ueCount;++u)
        {
            auto dev=ueDevices.Get(u)->GetObject<LteUeNetDevice>();
            s0ho::ueForImsi[dev->GetImsi()]=u;
            auto rrc=dev->GetRrc();
            if(!rrc->TraceConnectWithoutContext("HandoverStart",MakeBoundCallback(&s0ho::UeStart,u)) ||
               !rrc->TraceConnectWithoutContext("HandoverEndOk",MakeBoundCallback(&s0ho::UeEnd,u)) ||
               !rrc->TraceConnectWithoutContext("HandoverEndError",MakeBoundCallback(&s0ho::UeError,u)))
                throw std::runtime_error("Cannot connect UE handover traces");
        }
        for(uint32_t e=0;e<enbDevices.GetN();++e)
        {
            auto rrc=enbDevices.Get(e)->GetObject<LteEnbNetDevice>()->GetRrc();
            if(!rrc->TraceConnectWithoutContext("HandoverStart",MakeCallback(&s0ho::EnbStart)) ||
               !rrc->TraceConnectWithoutContext("HandoverEndOk",MakeCallback(&s0ho::EnbEnd)))
                throw std::runtime_error("Cannot connect eNB handover traces");
            for(const auto& name:{"HandoverFailureNoPreamble","HandoverFailureMaxRach","HandoverFailureLeaving","HandoverFailureJoining"})
                if(!rrc->TraceConnectWithoutContext(name,MakeBoundCallback(&s0ho::EnbError,std::string(name))))
                    throw std::runtime_error("Cannot connect eNB handover failure trace");
        }
    }
    gRadio.open(out("radio_samples.csv"));''')
    change('        sinks.push_back(server.Get(0)->GetObject<PacketSink>());', '''        sinks.push_back(server.Get(0)->GetObject<PacketSink>());
        if(s0ho::packets.is_open() && !sinks.back()->TraceConnectWithoutContext("Rx",MakeBoundCallback(&s0ho::PacketRx,u)))
            throw std::runtime_error("Cannot connect packet RX trace");''')
    change('    lte->Attach(ueDevices); // Automatic, radio-based initial cell selection with EPC.', '''    if(enableHandover) lte->AddX2Interface(enbNodes);
    lte->Attach(ueDevices); // Automatic, radio-based initial cell selection with EPC.
    if(s0ho::timeline.is_open())
        for(uint32_t u=0;u<ueCount;++u)
            Simulator::Schedule(Seconds(0),&s0ho::Sample,u,ueDevices.Get(u)->GetObject<LteUeNetDevice>(),
                ueNodes.Get(u)->GetObject<MobilityModel>(),sinks[u],duration);''')
    change('    uint32_t connected = 0, receiving = 0;', '''    s0ho::events.close(); s0ho::timeline.close(); s0ho::packets.close();
    uint32_t connected = 0, receiving = 0;''')
    (sim/'sindirgi_baseline.cc').write_text(source,encoding='utf-8')
    runner=(D17/'simulation/run_baseline.py').read_text(encoding='utf-8')
    runner=runner.replace("    parser.add_argument('--build-only'", """    parser.add_argument('--handover',type=int,choices=[0,1],default=0)
    parser.add_argument('--waypoints',type=Path)
    parser.add_argument('--handover-hysteresis',type=float,default=3)
    parser.add_argument('--handover-ttt-ms',type=int,default=256)
    parser.add_argument('--allow-final-disconnect',action='store_true')
    parser.add_argument('--build-only'""")
    runner=runner.replace("(HERE/'static-shadow-model.h').read_bytes()", "(HERE/'static-shadow-model.h').read_bytes()+(HERE/'handover-support.h').read_bytes()")
    runner=runner.replace("    run.append('--mixedCqi='", """    run += ['--handover='+str(args.handover),'--handoverHysteresis='+str(args.handover_hysteresis),
            '--handoverTttMs='+str(args.handover_ttt_ms)]
    if args.waypoints: run.append('--waypoints='+str(args.waypoints.resolve()))
    run.append('--mixedCqi='""")
    runner=runner.replace('        subprocess.run(run,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)', '''        completed=subprocess.run(run,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
        if completed.returncode and not (args.allow_final_disconnect and completed.returncode==2 and (out/'result.json').exists()):
            raise subprocess.CalledProcessError(completed.returncode,run)''')
    runner=runner.replace("    result['wall_seconds']=", """    result['process_exit_code']=completed.returncode
    result['handover']={'enabled':bool(args.handover),'algorithm':'A3RsrpHandoverAlgorithm' if args.handover else 'unchanged ns-3.44 NoOp default',
        'hysteresis_db':args.handover_hysteresis,'time_to_trigger_ms':args.handover_ttt_ms,
        'x2':'full mesh among logical sector eNB nodes' if args.handover else 'disabled',
        'waypoints_file':str(args.waypoints.resolve()) if args.waypoints else None,
        'waypoints_sha256':hashlib.sha256(args.waypoints.read_bytes()).hexdigest() if args.waypoints else None,
        'timeline_period_ms':100,'RRC_protocol':'ns-3 default ideal RRC; not a measured handover delay model'}
    result['wall_seconds']=""")
    (sim/'run_baseline.py').write_text(runner,encoding='utf-8')
    shutil.copy2(BASE/'inputs/targets.csv',inputs/'targets.csv')
    static,motion=[],[]
    for az,seed in [[42,701],[7,702],[99,703]]:
        for name in [f'sites_S0_{az}.csv',f'ues_S0_{seed}.csv']:
            shutil.copy2(BASE/'inputs'/name,inputs/name)
        sites=read(inputs/f'sites_S0_{az}.csv')
        pair=[next(r for r in sites if r['site']==site) for site in ['SITE_000441','SITE_000443']]
        write(inputs/f'sites_pair_{az}.csv',pair)
        a,b=pair
        ax,ay,bx,by=map(float,[a['x_m'],a['y_m'],b['x_m'],b['y_m']])
        start=(ax+.15*(bx-ax),ay+.15*(by-ay));end=(ax+.85*(bx-ax),ay+.85*(by-ay))
        travel=math.hypot(end[0]-start[0],end[1]-start[1])/15.0
        duration=math.ceil((travel+4)*1000)/1000
        ue={'ue_id':0,'x_m':f'{start[0]:.9f}','y_m':f'{start[1]:.9f}','z_m':'1.500000000',
            'kind':'measure','target_site':'','target_sector':'','target_prb':'','udp_interval_ms':'10.0','dl_earfcn':'1300'}
        write(inputs/f'ues_motion_{seed}.csv',[ue])
        waypoints=[{'ue_id':0,'time_s':f'{t:.9f}','x_m':f'{p[0]:.9f}','y_m':f'{p[1]:.9f}','z_m':'1.500000000'}
                   for t,p in [(0,start),(2,start),(2+travel,end),(duration,end)]]
        write(inputs/f'waypoints_{seed}.csv',waypoints)
        static.append({'name':f'S0_A3_draw{seed}','kind':'static','az':az,'seed':seed,'handover':1,
                       'sites':f'sites_S0_{az}.csv','ues_file':f'ues_S0_{seed}.csv','ues':328,'duration':4})
        for enabled in [0,1]:
            motion.append({'name':f'motion_{"A3" if enabled else "off"}_draw{seed}','kind':'motion','az':az,'seed':seed,
                           'handover':enabled,'sites':f'sites_pair_{az}.csv','ues_file':f'ues_motion_{seed}.csv',
                           'waypoints':f'waypoints_{seed}.csv','ues':1,'duration':duration,
                           'expected_source_site':'SITE_000441','expected_target_site':'SITE_000443'})
    plan={'status':'frozen_before_runs','scope':'S0 single-carrier B3 handover integration; other experiments unchanged',
          'algorithm':{'name':'A3RsrpHandoverAlgorithm','hysteresis_db':3,'time_to_trigger_ms':256,
                       'defaults_verified':'installed ns-3.44 source; original default NoOp is retained when off',
                       'X2':'Full mesh among 72 logical sector nodes in full S0 (2556 links); 6 nodes in pair test (15 links). Not a claim about real operator X2 topology.',
                       'inter_frequency_supported':False,'RRC':'existing default ideal RRC; measured interruption times are diagnostic only'},
          'regression':{'name':'regression_S0_off','sites':'sites_S0_42.csv','ues_file':'ues_S0_701.csv','ues':328,'duration':4,'handover':0,
                        'reference':str((BASE/'simulation/results/S0_draw701').relative_to(ROOT)).replace('\\','/'),
                        'files':['sectors.csv','ues.csv','radio_samples.csv','sinr_components.csv','measurements.csv','prb_usage.csv'],
                        'comparison':'Exact content after CRLF-to-LF only; no rounding or row reordering'},
          'static_cases':static,'motion_cases':motion,
          'motion_design':{'speed_m_s':15,'pair':['SITE_000441','SITE_000443'],'path':'15% to 85% of straight line, 2s dwell at both ends',
                           'traffic_interval_ms':10,'packet_bytes':512,'trace_period_ms':100,
                           'meaning':'Two-site isolated protocol check, same S0 radio settings/rotations; not a full 24-site mobility or disaster performance study.',
                           'no_manual_handover':'No HandoverRequest, forced target attach or network cut is used.'},
          'acceptance':{'regression_must_pass':True,
                        'static':'All 256 measurement users connected with DL, serving cells preserved, no handovers or failure events while stationary; per-UE RSRP max change <=.01 dB vs S0 on each draw.',
                        'motion_positive':'Each of 3 draws: initial connection at 441, exactly one automatic UE handover to 443, matching eNB start/end, zero UE/eNB handover errors, final connection at target, data before and after completion.',
                        'motion_negative':'Each of 3 handover-off runs uses same route/traffic and has zero handover starts/completions. Final disconnection is recorded, not hidden as a simulator failure.',
                        'max_handover_duration_s':0.10,'max_packet_gap_around_handover_s':0.25,
                        'no_post_result_tuning':'Hysteresis, TTT, routes and margins are not selected against outcomes.'},
          'radio':{'power_dbm':49,'beamwidth':120,'exponent':3,'nf_db':9,'mixed_cqi':1,'udp_jitter':1,'dl_earfcn':1300,'ul_earfcn':19300},
          'source_hashes':{p.name:sha(p) for p in sorted(sim.glob('*')) if p.is_file()},
          'input_hashes':{p.name:sha(p) for p in sorted(inputs.glob('*.csv'))},
          'documentation':'https://www.nsnam.org/docs/release/3.44/models/singlehtml/index.html'}
    (HERE/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
    report=['# Deney 19 — S0 için handover','', '**Durum: Plan sabitlendi; kod kontrolü ve koşular hazırlanıyor.**','',
            'S0’a isteğe bağlı X2 + A3 RSRP handover eklenir. Kapalıyken ns-3.44’ün eski NoOp davranışı aynen bırakılır. S0 radyo ayarları, 256 ölçüm + 72 yük kullanıcısı ve sabit konumlar korunur.','',
            'Histerezis 3 dB, komşunun üstünlüğünü sürdürme süresi 256 ms: kurulu ns-3.44 A3 varsayımları. Değer taraması yapılmayacak. X2, mantıksal sektör eNB düğümleri arasında tam bağlı kurulur; gerçek operatör komşuluk topolojisi iddiası yok.','',
            'Önce eski S0 kapalı koşusu altı CSV’de yalnız satır sonu normalizasyonuyla birebir tekrarlanacak. Sonra üç S0 örneğinde handover açıkken sabit kullanıcıların bağlantısı, hücresi ve sinyal gücünün korunduğu kontrol edilecek.','',
            'Pozitif/negatif hareket testi: S0’ın 441 ve 443 sahaları tek başına, aynı üç anten yönü örneğiyle kullanılır. Bir kullanıcı iki saha arasında 15 m/s hızla gider; iki uçta 2 saniye bekler. 10 ms aralıklı 512 bayt trafik veri sürekliliğini izler. Bu küçük test, tam ağın hareket veya deprem performansı iddiası değildir.','',
            'Her rotada handover kapalı ve açık koşulur. Açıkken 441→443 otomatik A3 geçişi, UE/eNB olaylarının eşleşmesi, hedefte bağlantı ve geçişten sonra veri beklenir. Kapalı koşuda handover olayı beklenmez; son bağlantı kaybı varsa açıkça raporlanır. Elle handover emri veya hedefe zorunlu bağlantı kullanılmaz.','',
            'Handover olayları, 100 ms hücre/konum zaman çizgisi ve hareket testinin paket alış zamanları kaydedilir. Son hücreye göre filtreleyen eski metrics() hareket testine uygulanmaz; bütün geçiş öncesi/sonrası veriler değerlendirilir.','',
            'Geçiş süresi ≤100 ms, geçiş çevresinde paket aralığı ≤250 ms tanısal kabul sınırlarıdır. Mevcut ideal RRC modeli gerçek şebekenin kesinti süresini ölçmez. Tüm karar kuralları koşudan önce plan.json dosyasına yazıldı.']
    (HERE/'SONUCLAR.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps({'regression':1,'static':len(static),'motion':len(motion),'motion_duration_s':motion[0]['duration'],'S0_unchanged_when_off':True},indent=2))


if __name__=='__main__':main()
