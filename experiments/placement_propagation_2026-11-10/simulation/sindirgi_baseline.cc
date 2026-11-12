// Geographically anchored, synthetic LTE/EPC diagnostic for installed ns-3.44.
// Cell IDs below are simulator-generated, not Turkcell cell IDs.
#include "ns3/antenna-module.h"
#include "ns3/lte-chunk-processor.h"
#include "ns3/spectrum-value.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/lte-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/propagation-module.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace ns3;

struct Site
{
    std::string id;
    std::string role;
    double x;
    double y;
    double rotation = std::numeric_limits<double>::quiet_NaN();
};



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
    double mixed=0;
    auto data = gDataInterfNoisePsd.at(ue);
    auto signalIt=s.ConstValuesBegin();
    for (uint32_t k=0;k<count;++k,++signalIt)
    {
        const double denom = (gDataFresh.at(ue) && data) ? (*data)[k] : noise;
        mixed += *signalIt / denom; // P_A=0 dB in the frozen baseline.
    }
    mixed /= count;

    gDiagnostic << Simulator::Now().GetSeconds() << ',' << ue << ',' << cell << ',' << rnti
        << ',' << count << ',' << gNoiseFigure.at(ue)
        << ',' << signal << ',' << denominator << ',' << interf << ',' << noise
        << ',' << signalSum*180000.0 << ',' << interf*count*180000.0 << ',' << noise*count*180000.0
        << ',' << 10*std::log10(rsrpW)+30 << ',' << 10*std::log10(signal*15000.0)+30
        << ',' << 10*std::log10(nativeSinr) << ',' << 10*std::log10(sinr)
        << ',' << 10*std::log10(snr) << ',' << 10*std::log10(interf/noise)
        << ',' << interf/denominator << ',' << 10*std::log10(signalSum/(2*(signalSum+denominatorSum)))
        << ',' << (maxSignal-minSignal)/signal << ',' << int(gDataFresh.at(ue))
        << ',' << (gDataAt.at(ue)<0 ? -1.0 : (now-gDataAt.at(ue))/1e6)
        << ',' << 10*std::log10(mixed) << ',' << int(gMixedCqi) << '\n';
}

static std::ofstream gRadio;
static uint64_t gRadioRows = 0;
struct Measurement
{
    uint16_t rnti=0, serving=0, best=0;
    double rsrp=std::numeric_limits<double>::quiet_NaN();
    double rsrq=std::numeric_limits<double>::quiet_NaN();
    double bestRsrp=-std::numeric_limits<double>::infinity();
};
static std::map<std::pair<uint32_t,int64_t>,Measurement> gMeasurements;
static std::vector<double> gConnectedAt;

static void
MeasurementTrace(uint32_t ue,uint16_t rnti,uint16_t cell,double rsrp,double rsrq,bool serving,uint8_t)
{
    if (!std::isfinite(rsrp)) return;
    auto& m=gMeasurements[{ue,Simulator::Now().GetNanoSeconds()}];
    m.rnti=rnti;
    if (rsrp>m.bestRsrp) { m.bestRsrp=rsrp; m.best=cell; }
    if (serving) { m.serving=cell; m.rsrp=rsrp; m.rsrq=rsrq; }
}

static void
ConnectionTrace(uint32_t ue,uint64_t,uint16_t,uint16_t)
{
    if (gConnectedAt.at(ue)<0) gConnectedAt[ue]=Simulator::Now().GetSeconds();
}

static std::vector<std::string>
Split(const std::string& line)
{
    // Input is the controlled, unquoted sites_local.csv export.
    std::vector<std::string> values;
    std::stringstream stream(line);
    std::string value;
    while (std::getline(stream, value, ','))
    {
        if (!value.empty() && value.back() == '\r') value.pop_back();
        values.push_back(value);
    }
    return values;
}

static std::vector<Site>
ReadSites(const std::string& path, uint32_t limit)
{
    std::ifstream input(path);
    if (!input) throw std::runtime_error("Cannot open sites file: " + path);
    std::string line;
    std::getline(input, line);
    const auto columns = Split(line);
    std::unordered_map<std::string, size_t> index;
    for (size_t i = 0; i < columns.size(); ++i) index[columns[i]] = i;
    std::vector<Site> sites;
    while (std::getline(input, line))
    {
        if (line.empty()) continue;
        const auto row = Split(line);
        sites.push_back({row.at(index.at("site")), row.at(index.at("role")),
                         std::stod(row.at(index.at("x_m"))),
                         std::stod(row.at(index.at("y_m")))});
        if (index.count("rotation_deg"))
            sites.back().rotation=std::stod(row.at(index.at("rotation_deg")));
        if (limit && sites.size() == limit) break;
    }
    if (sites.empty()) throw std::runtime_error("Empty site selection");
    if (limit && sites.size() != limit) throw std::runtime_error("Insufficient sites");
    return sites;
}

static void
RadioTrace(uint32_t ue, uint16_t cell, uint16_t rnti,
           double rsrpWatts, double sinrLinear, uint8_t cc)
{
    if (!cell || !rnti || !std::isfinite(rsrpWatts) || rsrpWatts <= 0 ||
        !std::isfinite(sinrLinear) || sinrLinear <= 0) return;
    gRadio << Simulator::Now().GetSeconds() << ',' << ue << ',' << cell << ','
           << rnti << ',' << 10 * std::log10(rsrpWatts) + 30 << ','
           << 10 * std::log10(sinrLinear) << ',' << static_cast<unsigned>(cc) << '\n';
    ++gRadioRows;
    WriteDiagnostic(ue, cell, rnti, rsrpWatts, sinrLinear);
}

int
main(int argc, char* argv[])
{
    std::string sitesFile;
    std::string output = "results";
    std::string placement = "near-sites";
    std::string uePositions;
    std::string pathloss = "log-distance";
    double exponent = 3.0;
    bool traffic = true;
    uint32_t siteLimit = 2;
    uint32_t ueCount = 6;
    uint32_t seed = 42;
    uint64_t run = 1;
    double duration = 1.2;
    double beamwidth = 65.0;
    double enbPower = 46.0;
    double udpIntervalMs = 50.0;
    CommandLine cmd(__FILE__);
    cmd.AddValue("sites", "Prepared sites_local.csv", sitesFile);
    cmd.AddValue("output", "Output directory", output);
    cmd.AddValue("siteLimit", "First N selected sites; zero means all", siteLimit);
    cmd.AddValue("ues", "Synthetic UE count", ueCount);
    cmd.AddValue("seed", "Random seed", seed);
    cmd.AddValue("run", "Random run", run);
    cmd.AddValue("duration", "Simulation seconds", duration);
    cmd.AddValue("placement", "near-sites or uniform (bounding rectangle)", placement);
    cmd.AddValue("uePositions", "Optional fixed UE CSV: ue_id,x_m,y_m,z_m", uePositions);
    cmd.AddValue("pathloss", "log-distance or okumura (COST231 branch at Band 3)", pathloss);
    cmd.AddValue("exponent", "Log-distance exponent", exponent);
    cmd.AddValue("traffic", "Enable diagnostic UDP downlink", traffic);
    cmd.AddValue("mixedCqi", "Use PDSCH interference in CQI", gMixedCqi);
    cmd.AddValue("beamwidth", "Horizontal beamwidth degrees", beamwidth);
    cmd.AddValue("udpIntervalMs", "UDP packet interval in ms", udpIntervalMs);
    cmd.AddValue("enbPower", "Per-sector conducted Tx power dBm", enbPower);
    cmd.Parse(argc, argv);
    if (beamwidth <= 0 || beamwidth > 180 || udpIntervalMs <= 0)
        throw std::runtime_error("Invalid antenna/load parameters");
    if (sitesFile.empty() || ueCount == 0 || duration < 1.0 ||
        (placement != "near-sites" && placement != "uniform") ||
        (pathloss != "log-distance" && pathloss != "okumura"))
        throw std::runtime_error("Invalid arguments");
    const auto sites = ReadSites(sitesFile, siteLimit);
    std::filesystem::create_directories(output);
    auto out = [&](const std::string& name) { return output + "/" + name; };
    RngSeedManager::SetSeed(seed);
    RngSeedManager::SetRun(run);
    auto rotation = CreateObject<UniformRandomVariable>();
    rotation->SetStream(0);
    auto spatial = CreateObject<UniformRandomVariable>();
    spatial->SetStream(1);

    auto lte = CreateObject<LteHelper>();
    auto epc = CreateObject<PointToPointEpcHelper>();
    lte->SetEpcHelper(epc);
    // Include neighbouring control channels in the initial radio diagnostic.
    // The default mixed CQI uses PDSCH interference, which is load-dependent.
    lte->SetAttribute("UsePdschForCqiGeneration", BooleanValue(gMixedCqi));
    lte->SetSchedulerType("ns3::PfFfMacScheduler");
    if (pathloss == "log-distance")
    {
        lte->SetPathlossModelType(TypeId::LookupByName("ns3::LogDistancePropagationLossModel"));
        lte->SetPathlossModelAttribute("Exponent", DoubleValue(exponent));
        const double referenceLoss = 20 * std::log10(4 * M_PI * 1815e6 / 299792458.0);
        lte->SetPathlossModelAttribute("ReferenceDistance", DoubleValue(1.0));
        lte->SetPathlossModelAttribute("ReferenceLoss", DoubleValue(referenceLoss));
    }
    else
    {
        lte->SetPathlossModelType(TypeId::LookupByName("ns3::OkumuraHataPropagationLossModel"));
        lte->SetPathlossModelAttribute("CitySize", EnumValue(MediumCity));
    }
    lte->SetEnbDeviceAttribute("DlEarfcn", UintegerValue(1300));
    lte->SetEnbDeviceAttribute("UlEarfcn", UintegerValue(19300));
    lte->SetUeDeviceAttribute("DlEarfcn", UintegerValue(1300));
    lte->SetEnbDeviceAttribute("DlBandwidth", UintegerValue(100));
    lte->SetEnbDeviceAttribute("UlBandwidth", UintegerValue(100));
    Config::SetDefault("ns3::LteEnbPhy::TxPower", DoubleValue(enbPower));
    Config::SetDefault("ns3::LteUePhy::TxPower", DoubleValue(23.0));
    lte->SetEnbAntennaModelType("ns3::CosineAntennaModel");
    lte->SetEnbAntennaModelAttribute("HorizontalBeamwidth", DoubleValue(beamwidth));
    lte->SetEnbAntennaModelAttribute("VerticalBeamwidth", DoubleValue(360.0));
    lte->SetEnbAntennaModelAttribute("MaxGain", DoubleValue(15.0));

    NodeContainer enbNodes;
    enbNodes.Create(3 * sites.size());
    MobilityHelper mobility;
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(enbNodes);
    NetDeviceContainer enbDevices;
    std::ofstream sectors(out("sectors.csv"));
    sectors << "synthetic_cell_id,site,role,sector,x_m,y_m,z_m,orientation_ccw_from_east_deg\n";
    sectors << std::setprecision(12);
    for (size_t i = 0; i < sites.size(); ++i)
    {
        const double phi = std::isfinite(sites[i].rotation) ? sites[i].rotation : rotation->GetValue(0, 120);
        for (uint32_t sector = 0; sector < 3; ++sector)
        {
            const auto& site = sites[i];
            auto node = enbNodes.Get(i * 3 + sector);
            node->GetObject<MobilityModel>()->SetPosition(Vector(site.x, site.y, 30.0));
            const double orientation = phi + 120 * sector;
            lte->SetEnbAntennaModelAttribute("Orientation", DoubleValue(orientation));
            auto devices = lte->InstallEnbDevice(NodeContainer(node));
            enbDevices.Add(devices);
            const auto cell = devices.Get(0)->GetObject<LteEnbNetDevice>()->GetCellId();
            sectors << cell << ',' << site.id << ',' << site.role << ',' << sector << ','
                    << site.x << ',' << site.y << ",30," << orientation << '\n';
        }
    }
    sectors.close();

    NodeContainer ueNodes;
    ueNodes.Create(ueCount);
    mobility.Install(ueNodes);
    double xmin = sites.front().x, xmax = xmin, ymin = sites.front().y, ymax = ymin;
    for (const auto& site : sites)
    {
        xmin = std::min(xmin, site.x); xmax = std::max(xmax, site.x);
        ymin = std::min(ymin, site.y); ymax = std::max(ymax, site.y);
    }
    if (xmax - xmin < 1) { xmin -= 1000; xmax += 1000; }
    if (ymax - ymin < 1) { ymin -= 1000; ymax += 1000; }
    std::vector<Vector> fixedPositions;
    if (!uePositions.empty())
    {
        std::ifstream input(uePositions);
        if (!input) throw std::runtime_error("Cannot open UE positions");
        std::string line; std::getline(input,line);
        auto header=Split(line);
        std::unordered_map<std::string,size_t> ix;
        for (size_t i=0;i<header.size();++i) ix[header[i]]=i;
        while (std::getline(input,line))
        {
            if (line.empty()) continue;
            auto row=Split(line);
            if (std::stoul(row.at(ix.at("ue_id")))!=fixedPositions.size())
                throw std::runtime_error("UE IDs must be sequential from zero");
            fixedPositions.emplace_back(std::stod(row.at(ix.at("x_m"))),
                std::stod(row.at(ix.at("y_m"))),std::stod(row.at(ix.at("z_m"))));
        }
        if (fixedPositions.size()!=ueCount) throw std::runtime_error("UE position count mismatch");
    }
    for (uint32_t u = 0; u < ueCount; ++u)
    {
        if (!fixedPositions.empty())
        {
            ueNodes.Get(u)->GetObject<MobilityModel>()->SetPosition(fixedPositions[u]);
            continue;
        }
        double x, y;
        if (placement == "near-sites")
        {
            const auto& centre = sites[u % sites.size()];
            const double angle = spatial->GetValue(0, 2 * M_PI);
            const double radius = std::sqrt(spatial->GetValue(250*250, 750*750));
            x = centre.x + radius * std::cos(angle);
            y = centre.y + radius * std::sin(angle);
        }
        else
        {
            x = spatial->GetValue(xmin, xmax);
            y = spatial->GetValue(ymin, ymax);
        }
        ueNodes.Get(u)->GetObject<MobilityModel>()->SetPosition(Vector(x,y,1.5));
    }
    auto ueDevices = lte->InstallUeDevice(ueNodes);
    gRadio.open(out("radio_samples.csv"));
    gRadio << "time_s,ue_id,synthetic_cell_id,rnti,rsrp_dbm,sinr_db,component_carrier\n";
    gRadio << std::setprecision(12);

    gConnectedAt.assign(ueCount,-1);
    gDiagnostic.open(out("sinr_components.csv"));
    gDiagnostic << "time_s,ue_id,synthetic_cell_id,rnti,rb_count,noise_figure_db,signal_psd_w_hz,interf_noise_psd_w_hz,interference_psd_w_hz,noise_psd_w_hz,signal_total_w,interference_total_w,noise_total_w,native_rsrp_dbm,reconstructed_rsrp_dbm,native_sinr_db,control_sinr_db,snr_db,inr_db,interference_fraction,rsrq_from_components_db,signal_rb_relative_spread,data_interference_fresh,data_age_ms,reconstructed_mixed_sinr_db,mixed_cqi_enabled\n";
    gDiagnostic << std::setprecision(17);
    gSignalPsd.resize(ueCount); gInterfNoisePsd.resize(ueCount);
    gDataInterfNoisePsd.resize(ueCount); gDataFresh.assign(ueCount,false); gDataAt.assign(ueCount,-1);
    gSignalAt.assign(ueCount,-1); gInterfAt.assign(ueCount,-1); gNoiseFigure.resize(ueCount);

    for (uint32_t u = 0; u < ueCount; ++u)
    {
        auto phy = ueDevices.Get(u)->GetObject<LteUeNetDevice>()->GetPhy();

        phy->SetAttribute("RsrpSinrSamplePeriod", UintegerValue(97));
        gNoiseFigure.at(u) = phy->GetNoiseFigure();
        auto diagnosticSignal = Create<LteChunkProcessor>();
        diagnosticSignal->AddCallback(MakeBoundCallback(&SignalObservation,u));
        phy->GetDlSpectrumPhy()->AddRsPowerChunkProcessor(diagnosticSignal);
        auto diagnosticInterference = Create<LteChunkProcessor>();
        diagnosticInterference->AddCallback(MakeBoundCallback(&InterfObservation,u));

        phy->GetDlSpectrumPhy()->AddInterferenceCtrlChunkProcessor(diagnosticInterference);
        auto diagnosticData = Create<LteChunkProcessor>();
        diagnosticData->AddCallback(MakeBoundCallback(&DataObservation,u));
        phy->GetDlSpectrumPhy()->AddInterferenceDataChunkProcessor(diagnosticData);
        auto resetObserver = Create<LteChunkProcessor>();
        resetObserver->AddCallback(MakeBoundCallback(&ResetAfterCtrl,u));
        phy->GetDlSpectrumPhy()->AddCtrlSinrChunkProcessor(resetObserver);


        if (!phy->TraceConnectWithoutContext("ReportCurrentCellRsrpSinr",
                                             MakeBoundCallback(&RadioTrace,u)))
            throw std::runtime_error("Cannot connect radio trace");
        if (!phy->TraceConnectWithoutContext("ReportUeMeasurements",MakeBoundCallback(&MeasurementTrace,u)))
            throw std::runtime_error("Cannot connect measurement trace");
        if (!ueDevices.Get(u)->GetObject<LteUeNetDevice>()->GetRrc()->TraceConnectWithoutContext(
            "ConnectionEstablished",MakeBoundCallback(&ConnectionTrace,u)))
            throw std::runtime_error("Cannot connect RRC trace");
    }

    InternetStackHelper internet;
    NodeContainer remoteNodes;
    remoteNodes.Create(1);
    internet.Install(remoteNodes);
    auto remote = remoteNodes.Get(0);
    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", DataRateValue(DataRate("100Gb/s")));
    p2p.SetChannelAttribute("Delay", TimeValue(MilliSeconds(10)));
    auto backhaul = p2p.Install(epc->GetPgwNode(),remote);
    Ipv4AddressHelper address;
    address.SetBase("1.0.0.0","255.0.0.0");
    address.Assign(backhaul);
    Ipv4StaticRoutingHelper routes;
    routes.GetStaticRouting(remote->GetObject<Ipv4>())->AddNetworkRouteTo(
        Ipv4Address("7.0.0.0"),Ipv4Mask("255.0.0.0"),1);
    internet.Install(ueNodes);
    const auto ueAddresses = epc->AssignUeIpv4Address(ueDevices);
    std::vector<Ptr<PacketSink>> sinks;
    for (uint32_t u = 0; u < ueCount; ++u)
    {
        routes.GetStaticRouting(ueNodes.Get(u)->GetObject<Ipv4>())->SetDefaultRoute(
            epc->GetUeDefaultGatewayAddress(),1);
        if (!traffic) { sinks.push_back(nullptr); continue; }
        PacketSinkHelper sink("ns3::UdpSocketFactory",
                              InetSocketAddress(Ipv4Address::GetAny(),1100));
        auto server = sink.Install(ueNodes.Get(u));
        server.Start(Seconds(.1));
        sinks.push_back(server.Get(0)->GetObject<PacketSink>());
        UdpClientHelper client(ueAddresses.GetAddress(u),1100);
        client.SetAttribute("MaxPackets",UintegerValue(100000));
        client.SetAttribute("PacketSize",UintegerValue(512));
        client.SetAttribute("Interval",TimeValue(Seconds(udpIntervalMs/1000.0)));
        auto sender = client.Install(remote);
        sender.Start(Seconds(.3));
        sender.Stop(Seconds(duration-.05));
    }
    lte->Attach(ueDevices); // Automatic, radio-based initial cell selection with EPC.
    Simulator::Stop(Seconds(duration));
    Simulator::Run();

    uint32_t connected = 0, receiving = 0;
    uint64_t bytes = 0;
    std::ofstream ues(out("ues.csv"));
    ues << "ue_id,imsi,x_m,y_m,z_m,synthetic_cell_id,rrc_connected,dl_bytes,connected_at_s\n";
    ues << std::setprecision(12);
    for (uint32_t u = 0; u < ueCount; ++u)
    {
        auto device = ueDevices.Get(u)->GetObject<LteUeNetDevice>();
        auto pos = ueNodes.Get(u)->GetObject<MobilityModel>()->GetPosition();
        const bool ok = device->GetRrc()->GetState() == LteUeRrc::CONNECTED_NORMALLY;
        const auto rx = sinks[u] ? sinks[u]->GetTotalRx() : 0;
        connected += ok;
        receiving += rx > 0;
        bytes += rx;
        ues << u << ',' << device->GetImsi() << ',' << pos.x << ',' << pos.y << ','
            << pos.z << ',' << device->GetRrc()->GetCellId() << ',' << ok << ',' << rx
            << ',' << gConnectedAt[u] << '\n';
    }
    ues.close();
    gRadio.close();
    gDiagnostic.close();
    std::ofstream measurements(out("measurements.csv"));
    measurements << "time_s,ue_id,rnti,synthetic_cell_id,rsrp_dbm,rsrq_db,best_cell_id,best_rsrp_dbm,serving_gap_db\n";
    measurements << std::setprecision(12);
    for (const auto& [key,m] : gMeasurements)
        measurements << key.second/1e9 << ',' << key.first << ',' << m.rnti << ',' << m.serving
                     << ',' << m.rsrp << ',' << m.rsrq << ',' << m.best << ',' << m.bestRsrp
                     << ',' << m.bestRsrp-m.rsrp << '\n';
    measurements.close();
    std::ostringstream result;
    result << "{\n  \"ns3_version\": \"3.44\",\n  \"seed\": " << seed
           << ",\n  \"run\": " << run << ",\n  \"physical_sites\": " << sites.size()
           << ",\n  \"synthetic_sectors\": " << enbDevices.GetN()
           << ",\n  \"ues\": " << ueCount << ",\n  \"connected_ues\": " << connected
           << ",\n  \"ues_receiving_dl\": " << receiving
           << ",\n  \"total_dl_bytes\": " << bytes
           << ",\n  \"radio_samples\": " << gRadioRows
           << ",\n  \"duration_s\": " << duration
           << ",\n  \"placement\": \"" << placement << "\"\n}\n";
    std::ofstream(out("result.json")) << result.str();
    std::cout << result.str();
    Simulator::Destroy();
    return connected && (!traffic || receiving) && gRadioRows ? 0 : 2;
}
