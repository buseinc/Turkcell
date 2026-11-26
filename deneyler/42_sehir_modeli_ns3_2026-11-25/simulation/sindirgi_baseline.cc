// Geographically anchored, synthetic LTE/EPC diagnostic for installed ns-3.44.
// Cell IDs below are simulator-generated, not Turkcell cell IDs.
#include "ns3/antenna-module.h"
#include "ns3/lte-spectrum-value-helper.h"
#include "static-shadow-model.h"
#include "building-vertical-model.h"
#include "spatial-field.h"
#include "handover-support.h"
#include "env-select-loss.h"
#include "ns3/lte-chunk-processor.h"
#include "ns3/spectrum-value.h"
#include "ns3/spectrum-propagation-loss-model.h"
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

// Experiment 26: transmitter EVM (3GPP TS 36.104 Table 6.5.2-1, 64QAM 8 %) as distortion of the wanted
// signal. Implemented in a private copy of libns3-lte (build_private_lte.py): LteInterference adds
// g_lteEvm2 * rxSignal to the interference of every chunk. With g_lteEvm2 == 0 it is the ns-3.44 original.
namespace ns3
{
extern double g_lteEvm2;
extern int g_ltePfBufferAware; // experiment 29: buffer-aware PF scheduler (private lib)
extern double g_lteAlwaysOn;   // experiment 36: always-on share f in the reported SINR (private lib)
}

struct Site
{
    std::string id;
    std::string role;
    double x;
    double y;
    double rotation = std::numeric_limits<double>::quiet_NaN();
    uint32_t sectorCount = 3;
    std::vector<std::string> carriers{"B3"}; // experiment 14: optional ';'-separated carrier layers
};

// Experiment 14 (S2): carrier layers. B3 keeps the command-line EARFCNs (default 1300/19300).
struct CarrierSpec
{
    uint32_t dlEarfcn;
    uint32_t ulEarfcn;
    uint16_t rb;
};

static CarrierSpec
CarrierFor(const std::string& name, uint32_t b3Dl, uint32_t b3Ul)
{
    if (name == "B3") return {b3Dl, b3Ul, 100};
    if (name == "B20") return {6300, 24300, 50}; // 806 / 847 MHz, 10 MHz
    throw std::runtime_error("Unknown carrier " + name);
}

// Frequency-dependent free-space reference correction for sub-GHz layers. The log-distance model's
// reference loss is computed at the B3 DL carrier; bins below 1 GHz receive (fRef/fLow)^2.
class SubGhzReferenceGain : public SpectrumPropagationLossModel
{
  public:
    static TypeId GetTypeId()
    {
        static TypeId tid = TypeId("ns3::SindirgiSubGhzReferenceGain")
                                .SetParent<SpectrumPropagationLossModel>()
                                .AddConstructor<SubGhzReferenceGain>()
                                .AddAttribute("Gain", "Linear gain applied to bins below 1 GHz",
                                              DoubleValue(1.0),
                                              MakeDoubleAccessor(&SubGhzReferenceGain::m_gain),
                                              MakeDoubleChecker<double>(0.0));
        return tid;
    }

  private:
    Ptr<SpectrumValue> DoCalcRxPowerSpectralDensity(Ptr<const SpectrumSignalParameters> params,
                                                    Ptr<const MobilityModel>,
                                                    Ptr<const MobilityModel>) const override
    {
        auto psd = params->psd->Copy();
        auto f = psd->ConstBandsBegin();
        for (auto it = psd->ValuesBegin(); it != psd->ValuesEnd(); ++it, ++f)
            if (f->fc < 1e9) *it *= m_gain;
        return psd;
    }

    int64_t DoAssignStreams(int64_t) override { return 0; }

    double m_gain = 1.0;
};

NS_OBJECT_ENSURE_REGISTERED(SubGhzReferenceGain);

static std::map<uint16_t, uint16_t> gCellRb;



// Passive DL PRB counter (added in experiment 09): counts resource blocks carrying
// PDSCH power in each downlink data frame, per synthetic cell, after prbWarmup.
struct PrbCount
{
    uint64_t dataFrames = 0;
    uint64_t rbSubframes = 0;
};
static std::map<uint16_t, PrbCount> gPrb;
static double gPrbWarmup = 1.0;
static std::vector<double> gUeIntervalMs;
// Experiment 28: optional per-UE UDP packet size and voice (VoIP-like) delay/loss accounting.
static std::vector<uint32_t> gUePacketSize;
static std::vector<int> gUeVoice;
struct VoiceStat { uint64_t sent = 0, received = 0, onTime = 0; double delaySum = 0, delayMax = 0; };
static std::vector<VoiceStat> gVoice;
static double gVoiceWindowStart = 1.0, gVoiceWindowEnd = 1e9, gVoiceDeadline = 0.1;
static void VoiceTx(uint32_t u, Ptr<const Packet> p)
{
    const double t = Simulator::Now().GetSeconds();
    if (t >= gVoiceWindowStart && t <= gVoiceWindowEnd) gVoice[u].sent++;
}
static void VoiceRx(uint32_t u, Ptr<const Packet> p, const Address&)
{
    SeqTsHeader h;
    p->Copy()->RemoveHeader(h);
    const double ts = h.GetTs().GetSeconds();
    if (ts < gVoiceWindowStart || ts > gVoiceWindowEnd) return;
    const double d = Simulator::Now().GetSeconds() - ts;
    auto& s = gVoice[u];
    s.received++;
    s.delaySum += d;
    s.delayMax = std::max(s.delayMax, d);
    if (d <= gVoiceDeadline) s.onTime++;
}
static std::vector<uint32_t> gUeDlEarfcn; // experiment 14: optional per-UE camping carrier
static std::vector<double> gEnbOrientation; // experiment 23: orientation (deg ccw from east) per eNB node
static std::vector<double> gUeExtraLoss; // experiment 22: optional per-UE loss (dB) on all its links
static std::vector<int> gUeUrban;        // experiment 42: optional per-UE environment, 1 = city (UMa), 0 = rural (RMa)
static bool gUdpJitter = false;            // experiment 14: random UDP start offset within one interval

static void
DlTxObservation(Ptr<SpectrumSignalParameters> params)
{
    if (Simulator::Now().GetSeconds() < gPrbWarmup)
        return;
    auto data = DynamicCast<LteSpectrumSignalParametersDataFrame>(params);
    if (!data)
        return;
    uint32_t rbs = 0;
    for (auto it = data->psd->ConstValuesBegin(); it != data->psd->ConstValuesEnd(); ++it)
        rbs += *it > 0;
    auto& c = gPrb[data->cellId];
    c.dataFrames += 1;
    c.rbSubframes += rbs;
}

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
ConnectionTrace(uint32_t ue,uint64_t imsi,uint16_t cell,uint16_t rnti)
{
    s0ho::Connection(ue,imsi,cell,rnti); // experiment 34 (no-op unless the event file is open)
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
        if (index.count("sector_count")) sites.back().sectorCount=std::stoul(row.at(index.at("sector_count")));
        if (sites.back().sectorCount < 1 || sites.back().sectorCount > 3) throw std::runtime_error("Invalid sector count");
        if (index.count("carriers") && !row.at(index.at("carriers")).empty())
        {
            sites.back().carriers.clear();
            std::stringstream list(row.at(index.at("carriers")));
            std::string item;
            while (std::getline(list, item, ';'))
                if (!item.empty()) sites.back().carriers.push_back(item);
            if (sites.back().carriers.empty()) throw std::runtime_error("Empty carrier list");
        }
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
    double shadowSigma=0.0, receiverNf=9.0;
    double indoorLoss=0.0, downtilt=0.0, verticalBeamwidth=10.0;
    bool verticalPattern=false;
    bool antenna3gpp=false; // experiment 23: 3GPP TR 36.814 combined H+V pattern, Am=25 dB
    double maxAttenuation=25.0;
    double evm=0.0; // experiment 26: transmitter EVM fraction (0.08 = 8 %)
    double linkShadowSigma=0.0; // experiment 20: shadowing usable with any pathloss model
    uint32_t measurementUes=256;
    uint32_t dlEarfcn=1300, ulEarfcn=19300;
    uint64_t shadowSeed=42;
    bool verifyShadow=false;
    double enbPower = 46.0;
    double udpIntervalMs = 50.0;
    uint32_t srsPeriodicity = 0; // experiment 28: 0 keeps the ns-3 default
    bool dlPhyTraces = false; // experiment 33: ns-3 DlRxPhyStats.txt (MCS, TB size, correct) per TB
    // experiment 34 (DUZELTMELER.md): all off by default = experiment 33 behaviour
    bool spatialShadow=false, spatialLos=false, enableHandover=false;
    double shadowSpacing=120.0, losSpacing=60.0, handoverHysteresis=3.0, corrK0=0.0, corrK1=0.0;
    uint32_t handoverTttMs=256;
    std::string waypointFile, corrSitesFile;
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
    cmd.AddValue("spatialShadow", "Experiment 34: smooth link-shadow field (spacing shadowSpacing)", spatialShadow);
    cmd.AddValue("shadowSpacing", "Experiment 34: shadow field grid spacing, m", shadowSpacing);
    cmd.AddValue("spatialLos", "Experiment 34: RMa LOS state from a smooth field (spacing losSpacing)", spatialLos);
    cmd.AddValue("losSpacing", "Experiment 34: LOS field grid spacing, m", losSpacing);
    cmd.AddValue("handover", "Experiment 34: A3 RSRP handover and full-mesh X2 (as experiment 19)", enableHandover);
    cmd.AddValue("handoverHysteresis", "A3 RSRP hysteresis, dB", handoverHysteresis);
    cmd.AddValue("handoverTttMs", "A3 time-to-trigger, ms", handoverTttMs);
    cmd.AddValue("waypoints", "Experiment 34: UE waypoint CSV ue_id,time_s,x_m,y_m,z_m (listed UEs move)", waypointFile);
    cmd.AddValue("corrSites", "Experiment 34: CSV x_m,y_m of the full network for the moving-UE distance correction", corrSitesFile);
    cmd.AddValue("corrK0", "Experiment 34: distance correction k0 (dB)", corrK0);
    cmd.AddValue("corrK1", "Experiment 34: distance correction k1 (dB per decade)", corrK1);
    cmd.AddValue("dlPhyTraces", "Experiment 33: write ns-3 DL PHY reception traces (DlRxPhyStats.txt)", dlPhyTraces);
    cmd.AddValue("srsPeriodicity", "LteEnbRrc SRS periodicity (0 = ns-3 default); 320 allows many UEs per cell", srsPeriodicity);
    cmd.AddValue("voiceDeadlineMs", "Voice packet delay budget in ms (3GPP QCI 1: 100)", gVoiceDeadline);
    cmd.AddValue("enbPower", "Per-sector conducted Tx power dBm", enbPower);
    cmd.AddValue("shadowSigma", "Static per-link shadow std dB", shadowSigma);
    cmd.AddValue("receiverNf", "UE downlink receiver NF dB", receiverNf);
    cmd.AddValue("shadowSeed", "Coordinate-keyed shadow realization", shadowSeed);
    cmd.AddValue("dlEarfcn", "Common downlink carrier", dlEarfcn);
    cmd.AddValue("ulEarfcn", "Paired uplink carrier", ulEarfcn);
    cmd.AddValue("verifyShadow", "Verify experimental shadow implementation", verifyShadow);
    cmd.AddValue("prbWarmup", "Seconds before DL PRB counting starts", gPrbWarmup);
    cmd.AddValue("indoorLoss", "Fixed loss for measured UEs only, dB", indoorLoss);
    cmd.AddValue("downtilt", "Downward electrical tilt, degrees", downtilt);
    cmd.AddValue("verticalPattern", "Enable vertical attenuation", verticalPattern);
    cmd.AddValue("verticalBeamwidth", "Vertical 3 dB beamwidth", verticalBeamwidth);
    cmd.AddValue("antenna3gpp", "3GPP combined antenna pattern in the link loss (isotropic 15 dBi element)", antenna3gpp);
    cmd.AddValue("pfBufferAware", "Experiment 29: PF gives a UE only the RBGs its queue needs (0 = ns-3 original)", g_ltePfBufferAware);
    cmd.AddValue("alwaysOn", "Experiment 36: share f of full neighbour interference always in the reported SINR", g_lteAlwaysOn);
    cmd.AddValue("evm", "Transmitter EVM as fraction; adds EVM^2 x wanted signal to interference", evm);
    cmd.AddValue("maxAttenuation", "3GPP combined front-to-back cap Am, dB", maxAttenuation);
    cmd.AddValue("linkShadowSigma", "Static per eNB-UE shadow std dB on top of any pathloss (seed: shadowSeed)", linkShadowSigma);
    cmd.AddValue("measurementUes", "First N UEs receive indoor loss", measurementUes);
    cmd.AddValue("udpJitter", "Start each UDP client at a random offset within its interval", gUdpJitter);
    double enbHeight=30.0; // experiment 42: tower height (old runs 30 m)
    cmd.AddValue("enbHeight", "Experiment 42: eNB antenna height, m", enbHeight);
    double sigmaUmaLos=7.0, sigmaUmaNlos=7.0, sigmaRmaLos=4.0, sigmaRmaNlos=8.0; // experiment 42, TR 38.901
    cmd.AddValue("sigmaUmaLos", "Experiment 42: city shadow std, LOS, dB", sigmaUmaLos);
    cmd.AddValue("sigmaUmaNlos", "Experiment 42: city shadow std, NLOS, dB", sigmaUmaNlos);
    cmd.AddValue("sigmaRmaLos", "Experiment 42: rural shadow std, LOS, dB", sigmaRmaLos);
    cmd.AddValue("sigmaRmaNlos", "Experiment 42: rural shadow std, NLOS, dB", sigmaRmaNlos);
    cmd.Parse(argc, argv);
    e42::g_seed = shadowSeed; e42::g_losSpacing = losSpacing;
    if (evm < 0 || evm >= 1) throw std::runtime_error("Invalid EVM");
    if (g_lteAlwaysOn < 0 || g_lteAlwaysOn > 1) throw std::runtime_error("Invalid alwaysOn");
    g_lteEvm2 = evm * evm;
    if (srsPeriodicity) Config::SetDefault("ns3::LteEnbRrc::SrsPeriodicity", UintegerValue(srsPeriodicity));
    if (gVoiceDeadline > 1.0) gVoiceDeadline /= 1000.0; // given in ms
    if(verifyShadow) { VerifyExperimentalShadowModel(); return 0; }
    if (shadowSigma<0 || receiverNf<0) throw std::runtime_error("Invalid shadow/NF");
    if (beamwidth <= 0 || beamwidth > 180 || udpIntervalMs <= 0)
        throw std::runtime_error("Invalid antenna/load parameters");
    if (sitesFile.empty() || ueCount == 0 || duration < 1.0 ||
        (placement != "near-sites" && placement != "uniform") ||
        (pathloss != "log-distance" && pathloss != "okumura" && pathloss != "rma" && pathloss != "env"))
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
    if (enableHandover)
    {
        lte->SetHandoverAlgorithmType("ns3::A3RsrpHandoverAlgorithm");
        lte->SetHandoverAlgorithmAttribute("Hysteresis", DoubleValue(handoverHysteresis));
        lte->SetHandoverAlgorithmAttribute("TimeToTrigger", TimeValue(MilliSeconds(handoverTttMs)));
    }
    if (pathloss == "log-distance")
    {
        lte->SetPathlossModelType(TypeId::LookupByName(shadowSigma>0 ? "ns3::ExperimentStaticShadow" : "ns3::LogDistancePropagationLossModel"));
        lte->SetPathlossModelAttribute("Exponent", DoubleValue(exponent));
        const double carrierHz=LteSpectrumValueHelper::GetCarrierFrequency(dlEarfcn);
        const double referenceLoss = 20 * std::log10(4 * M_PI * carrierHz / 299792458.0);
        lte->SetPathlossModelAttribute("ReferenceDistance", DoubleValue(1.0));
        lte->SetPathlossModelAttribute("ReferenceLoss", DoubleValue(referenceLoss));
        if(shadowSigma>0) {
            lte->SetPathlossModelAttribute("Sigma",DoubleValue(shadowSigma));
            lte->SetPathlossModelAttribute("ShadowSeed",UintegerValue(shadowSeed));
        }
    }
    else if (pathloss == "okumura")
    {
        lte->SetPathlossModelType(TypeId::LookupByName("ns3::OkumuraHataPropagationLossModel"));
        lte->SetPathlossModelAttribute("CitySize", EnumValue(MediumCity));
    }
    else if (pathloss == "env")
    {
        // Experiment 42: per-UE environment, UMa or RMa from the UE file column env (env-select-loss.h).
        lte->SetPathlossModelType(TypeId::LookupByName("e42::EnvSelectLoss"));
    }
    else
    {
        // Experiment 21: 3GPP TR 38.901 RMa (rural macro), default h=5 m, W=20 m. Its own shadowing and
        // building penetration are off; shadowing comes from linkShadowSigma as in experiment 20.
        // One shared RMa channel-condition model gives each link a fixed LOS/NLOS state (UpdatePeriod 0).
        lte->SetPathlossModelType(TypeId::LookupByName("ns3::ThreeGppRmaPropagationLossModel"));
        lte->SetPathlossModelAttribute("ShadowingEnabled", BooleanValue(false));
        lte->SetPathlossModelAttribute("BuildingPenetrationLossesEnabled", BooleanValue(false));
        lte->SetPathlossModelAttribute("EnforceParameterRanges", BooleanValue(false));
        if (spatialLos)
        {
            auto cond = CreateObject<e34::SpatialRmaConditionModel>();
            cond->Configure(shadowSeed, losSpacing);
            lte->SetPathlossModelAttribute("ChannelConditionModel", PointerValue(cond));
        }
        else
            lte->SetPathlossModelAttribute("ChannelConditionModel",
                                           PointerValue(CreateObject<ThreeGppRmaChannelConditionModel>()));
    }
    lte->SetEnbDeviceAttribute("DlEarfcn", UintegerValue(dlEarfcn));
    lte->SetEnbDeviceAttribute("UlEarfcn", UintegerValue(ulEarfcn));
    lte->SetUeDeviceAttribute("DlEarfcn", UintegerValue(dlEarfcn));
    lte->SetEnbDeviceAttribute("DlBandwidth", UintegerValue(100));
    lte->SetEnbDeviceAttribute("UlBandwidth", UintegerValue(100));
    Config::SetDefault("ns3::LteEnbPhy::TxPower", DoubleValue(enbPower));
    Config::SetDefault("ns3::LteUePhy::TxPower", DoubleValue(23.0));
    Config::SetDefault("ns3::LteUePhy::NoiseFigure", DoubleValue(receiverNf));
    if (antenna3gpp)
    {
        // Experiment 23: the eNB element is isotropic with the 15 dBi peak gain; the 3GPP horizontal and
        // vertical pattern with its combined cap is applied per link in BuildingVerticalLoss.
        lte->SetEnbAntennaModelType("ns3::IsotropicAntennaModel");
        lte->SetEnbAntennaModelAttribute("Gain", DoubleValue(15.0));
    }
    else
    {
        lte->SetEnbAntennaModelType("ns3::CosineAntennaModel");
        lte->SetEnbAntennaModelAttribute("HorizontalBeamwidth", DoubleValue(beamwidth));
        lte->SetEnbAntennaModelAttribute("VerticalBeamwidth", DoubleValue(360.0));
        lte->SetEnbAntennaModelAttribute("MaxGain", DoubleValue(15.0));
    }

    NodeContainer enbNodes;
    uint32_t sectorTotal=0;
    bool multiCarrier = false;
    for(const auto& site:sites)
    {
        sectorTotal+=site.sectorCount*site.carriers.size();
        for (const auto& c : site.carriers) multiCarrier |= (c != "B3");
    }
    enbNodes.Create(sectorTotal);
    MobilityHelper mobility;
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(enbNodes);
    NetDeviceContainer enbDevices;
    std::ofstream sectors(out("sectors.csv"));
    sectors << "synthetic_cell_id,site,role,sector,x_m,y_m,z_m,orientation_ccw_from_east_deg";
    if (multiCarrier) sectors << ",carrier,dl_earfcn,bandwidth_rb";
    sectors << "\n" << std::setprecision(12);
    uint32_t enbIndex=0;
    for (size_t i = 0; i < sites.size(); ++i)
    {
        const double phi = std::isfinite(sites[i].rotation) ? sites[i].rotation : rotation->GetValue(0, 120);
        for (uint32_t sector = 0; sector < sites[i].sectorCount; ++sector)
        {
            const auto& site = sites[i];
            for (size_t k = 0; k < site.carriers.size(); ++k)
            {
                const auto spec = CarrierFor(site.carriers[k], dlEarfcn, ulEarfcn);
                lte->SetEnbDeviceAttribute("DlEarfcn", UintegerValue(spec.dlEarfcn));
                lte->SetEnbDeviceAttribute("UlEarfcn", UintegerValue(spec.ulEarfcn));
                lte->SetEnbDeviceAttribute("DlBandwidth", UintegerValue(spec.rb));
                lte->SetEnbDeviceAttribute("UlBandwidth", UintegerValue(spec.rb));
                auto node = enbNodes.Get(enbIndex++);
                node->GetObject<MobilityModel>()->SetPosition(Vector(site.x, site.y, enbHeight));
                const double orientation = phi + 120 * sector;
                if (!antenna3gpp) lte->SetEnbAntennaModelAttribute("Orientation", DoubleValue(orientation));
                gEnbOrientation.push_back(orientation);
                auto devices = lte->InstallEnbDevice(NodeContainer(node));
                enbDevices.Add(devices);
                const auto cell = devices.Get(0)->GetObject<LteEnbNetDevice>()->GetCellId();
                gCellRb[cell] = spec.rb;
                // Sector field stays the antenna direction for B3 (k=0); extra layers get +10*k so
                // each (sector, carrier) cell is a distinct group in the Python metrics.
                sectors << cell << ',' << site.id << ',' << site.role << ',' << sector + 10 * k << ','
                        << site.x << ',' << site.y << ',' << enbHeight << ',' << orientation;
                if (multiCarrier) sectors << ',' << site.carriers[k] << ',' << spec.dlEarfcn << ',' << spec.rb;
                sectors << '\n';
            }
        }
    }
    sectors.close();
    lte->SetEnbDeviceAttribute("DlEarfcn", UintegerValue(dlEarfcn));
    lte->SetEnbDeviceAttribute("UlEarfcn", UintegerValue(ulEarfcn));
    lte->SetEnbDeviceAttribute("DlBandwidth", UintegerValue(100));
    lte->SetEnbDeviceAttribute("UlBandwidth", UintegerValue(100));
    if (multiCarrier)
    {
        // Sub-GHz layers: free-space reference difference relative to the B3 reference loss.
        const double dlGain = std::pow(LteSpectrumValueHelper::GetDownlinkCarrierFrequency(dlEarfcn) /
                                       LteSpectrumValueHelper::GetDownlinkCarrierFrequency(6300), 2);
        const double ulGain = std::pow(LteSpectrumValueHelper::GetUplinkCarrierFrequency(ulEarfcn) /
                                       LteSpectrumValueHelper::GetUplinkCarrierFrequency(24300), 2);
        auto dl = CreateObject<SubGhzReferenceGain>();
        dl->SetAttribute("Gain", DoubleValue(dlGain));
        lte->GetDownlinkSpectrumChannel()->AddSpectrumPropagationLossModel(dl);
        auto ul = CreateObject<SubGhzReferenceGain>();
        ul->SetAttribute("Gain", DoubleValue(ulGain));
        lte->GetUplinkSpectrumChannel()->AddSpectrumPropagationLossModel(ul);
        std::cout << "Sub-GHz reference gain DL " << 10 * std::log10(dlGain) << " dB, UL "
                  << 10 * std::log10(ulGain) << " dB" << std::endl;
    }

    NodeContainer ueNodes;
    ueNodes.Create(ueCount);
    if (!waypointFile.empty())
        mobility.SetMobilityModel("ns3::WaypointMobilityModel","InitialPositionIsWaypoint",BooleanValue(false));
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
            if (ix.count("extra_loss_db"))
                gUeExtraLoss.push_back(std::stod(row.at(ix.at("extra_loss_db"))));
            if (ix.count("env"))
            {
                const auto& v = row.at(ix.at("env"));
                if (v != "UMa" && v != "RMa") throw std::runtime_error("env must be UMa or RMa");
                gUeUrban.push_back(v == "UMa");
            }
            // Optional per-UE DL UDP interval (experiment 09); absent column keeps udpIntervalMs.
            if (ix.count("udp_interval_ms"))
            {
                const double v = std::stod(row.at(ix.at("udp_interval_ms")));
                if (v <= 0) throw std::runtime_error("udp_interval_ms must be positive");
                gUeIntervalMs.push_back(v);
            }
            if (ix.count("dl_earfcn"))
                gUeDlEarfcn.push_back(std::stoul(row.at(ix.at("dl_earfcn"))));
            if (ix.count("packet_size_bytes"))
                gUePacketSize.push_back(std::stoul(row.at(ix.at("packet_size_bytes"))));
            if (ix.count("voice"))
                gUeVoice.push_back(std::stoi(row.at(ix.at("voice"))));
        }
        if (fixedPositions.size()!=ueCount) throw std::runtime_error("UE position count mismatch");
        if ((!gUePacketSize.empty() && gUePacketSize.size()!=ueCount) || (!gUeVoice.empty() && gUeVoice.size()!=ueCount))
            throw std::runtime_error("packet_size_bytes/voice count mismatch");
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
    // Experiment 34: waypoints (exp 19 format). Listed UEs move; the others stay at their fixed position.
    std::vector<uint32_t> movingUes;
    if (!waypointFile.empty())
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
            else movingUes.push_back(u);
            if(points[u].front().time!=Seconds(0) || CalculateDistance(initial,points[u].front().position)>1e-6)
                throw std::runtime_error("First waypoint must match fixed position at zero");
            for(const auto& p:points[u]) mm->AddWaypoint(p);
        }
    }
    std::vector<std::pair<double,double>> corrSites;
    if (!corrSitesFile.empty())
    {
        std::ifstream input(corrSitesFile);
        if (!input) throw std::runtime_error("Cannot open corrSites");
        std::string line; std::getline(input,line);
        auto columns=Split(line);
        std::unordered_map<std::string,size_t> ix;
        for(size_t i=0;i<columns.size();++i) ix[columns[i]]=i;
        while(std::getline(input,line))
            if(!line.empty()) { auto r=Split(line); corrSites.emplace_back(std::stod(r.at(ix.at("x_m"))),std::stod(r.at(ix.at("y_m")))); }
    }
    if (!movingUes.empty() && corrSites.empty())
        throw std::runtime_error("Moving UEs need corrSites/corrK0/corrK1 for the distance correction");
    if (indoorLoss < 0 || downtilt < 0 || downtilt > 90 || verticalBeamwidth <= 0 || linkShadowSigma < 0)
        throw std::runtime_error("Invalid building/vertical parameters");
    if (!gUeExtraLoss.empty() && gUeExtraLoss.size() != ueCount) throw std::runtime_error("extra_loss_db count mismatch");
    if (pathloss == "env")
    {
        if (gUeUrban.size() != ueCount) throw std::runtime_error("pathloss env needs the env column for every UE");
        if (!spatialShadow || !spatialLos) throw std::runtime_error("pathloss env needs spatialShadow and spatialLos");
        for (uint32_t u = 0; u < ueCount; ++u)
            e34::UeUrban()[PeekPointer(ueNodes.Get(u)->GetObject<MobilityModel>())] = gUeUrban[u] != 0;
    }
    if (antenna3gpp && (maxAttenuation <= 0 || gEnbOrientation.size() != enbNodes.GetN()))
        throw std::runtime_error("Invalid 3GPP antenna parameters");
    if (indoorLoss > 0 || verticalPattern || linkShadowSigma > 0 || !gUeExtraLoss.empty() || antenna3gpp)
    {
        if (measurementUes > ueCount) throw std::runtime_error("measurementUes exceeds ues");
        auto loss = CreateObject<BuildingVerticalLoss>();
        loss->Configure(enbNodes, ueNodes, measurementUes, indoorLoss,
                        verticalPattern, downtilt, verticalBeamwidth, linkShadowSigma, shadowSeed, gUeExtraLoss);
        if (antenna3gpp) loss->ConfigureAntenna(gEnbOrientation, beamwidth, verticalBeamwidth, downtilt, maxAttenuation);
        loss->ConfigureMoving(spatialShadow, shadowSpacing, ueNodes, movingUes, corrSites, corrK0, corrK1);
        if (pathloss == "env") loss->ConfigureEnvSigma({sigmaUmaLos, sigmaUmaNlos, sigmaRmaLos, sigmaRmaNlos}, losSpacing);
        lte->GetDownlinkSpectrumChannel()->AddSpectrumPropagationLossModel(loss);
        auto ulLoss = CreateObject<BuildingVerticalLoss>();
        ulLoss->Configure(enbNodes, ueNodes, measurementUes, indoorLoss,
                          verticalPattern, downtilt, verticalBeamwidth, linkShadowSigma, shadowSeed, gUeExtraLoss);
        if (antenna3gpp) ulLoss->ConfigureAntenna(gEnbOrientation, beamwidth, verticalBeamwidth, downtilt, maxAttenuation);
        ulLoss->ConfigureMoving(spatialShadow, shadowSpacing, ueNodes, movingUes, corrSites, corrK0, corrK1);
        if (pathloss == "env") ulLoss->ConfigureEnvSigma({sigmaUmaLos, sigmaUmaNlos, sigmaRmaLos, sigmaRmaNlos}, losSpacing);
        lte->GetUplinkSpectrumChannel()->AddSpectrumPropagationLossModel(ulLoss);
    }
    NetDeviceContainer ueDevices;
    if (gUeDlEarfcn.empty())
        ueDevices = lte->InstallUeDevice(ueNodes);
    else
    {
        if (gUeDlEarfcn.size() != ueCount) throw std::runtime_error("dl_earfcn count mismatch");
        for (uint32_t u = 0; u < ueCount; ++u)
        {
            lte->SetUeDeviceAttribute("DlEarfcn", UintegerValue(gUeDlEarfcn[u]));
            ueDevices.Add(lte->InstallUeDevice(NodeContainer(ueNodes.Get(u))));
        }
        lte->SetUeDeviceAttribute("DlEarfcn", UintegerValue(dlEarfcn));
    }
    if (enableHandover || !movingUes.empty())
    {
        s0ho::events.open(out("handover_events.csv"));
        s0ho::events << "time_s,actor,event,ue_id,imsi,cell_id,rnti,target_cell_id\n" << std::setprecision(12);
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
        if (!movingUes.empty())
        {
            s0ho::timeline.open(out("serving_timeline.csv"));
            s0ho::timeline << "time_s,ue_id,x_m,y_m,z_m,cell_id,rnti,rrc_state,dl_bytes\n" << std::setprecision(12);
            s0ho::packets.open(out("packet_rx.csv"));
            s0ho::packets << "time_s,ue_id,packet_bytes\n" << std::setprecision(12);
        }
    }
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
        if (s0ho::packets.is_open() && std::find(movingUes.begin(), movingUes.end(), u) != movingUes.end() &&
            !sinks.back()->TraceConnectWithoutContext("Rx", MakeBoundCallback(&s0ho::PacketRx, u)))
            throw std::runtime_error("Cannot connect moving-UE packet trace");
        UdpClientHelper client(ueAddresses.GetAddress(u),1100);
        client.SetAttribute("MaxPackets",UintegerValue(100000));
        client.SetAttribute("PacketSize",UintegerValue(gUePacketSize.empty() ? 512 : gUePacketSize.at(u)));
        const double intervalMs = gUeIntervalMs.empty() ? udpIntervalMs : gUeIntervalMs.at(u);
        client.SetAttribute("Interval",TimeValue(Seconds(intervalMs/1000.0)));
        auto sender = client.Install(remote);
        double start = .3;
        if (gUdpJitter)
        {
            static Ptr<UniformRandomVariable> jitter = [] {
                auto v = CreateObject<UniformRandomVariable>();
                v->SetStream(3);
                return v;
            }();
            start += jitter->GetValue(0, intervalMs / 1000.0);
        }
        sender.Start(Seconds(start));
        sender.Stop(Seconds(duration-.05));
        if (!gUeVoice.empty() && gUeVoice.at(u))
        {
            if (gVoice.empty())
            {
                gVoice.resize(ueCount);
                gVoiceWindowStart = gPrbWarmup;
                gVoiceWindowEnd = duration - .05 - .2; // packets sent later may still be in flight at the end
            }
            sender.Get(0)->TraceConnectWithoutContext("Tx", MakeBoundCallback(&VoiceTx, u));
            sinks.back()->TraceConnectWithoutContext("Rx", MakeBoundCallback(&VoiceRx, u));
        }
    }
    if (!lte->GetDownlinkSpectrumChannel()->TraceConnectWithoutContext(
            "TxSigParams", MakeCallback(&DlTxObservation)))
        throw std::runtime_error("Cannot connect DL PRB trace");
    if (enableHandover) lte->AddX2Interface(enbNodes); // experiment 34 (as experiment 19)
    lte->Attach(ueDevices); // Automatic, radio-based initial cell selection with EPC.
    if (s0ho::timeline.is_open())
        for (auto u : movingUes)   // experiment 34: 100 ms serving-cell timeline of the moving UEs only
            Simulator::Schedule(Seconds(0), &s0ho::Sample, u, ueDevices.Get(u)->GetObject<LteUeNetDevice>(),
                                ueNodes.Get(u)->GetObject<MobilityModel>(), sinks[u], duration);
    if (dlPhyTraces) lte->EnableDlRxPhyTraces(); // experiment 33 (fixed 21 Nov: was EnableDlPhyTraces, which writes only RSRP/SINR)
    Simulator::Stop(Seconds(duration));
    Simulator::Run();
    s0ho::events.close(); s0ho::timeline.close(); s0ho::packets.close();

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
    if (!gVoice.empty())
    {
        std::ofstream voice(out("voice.csv"));
        voice << "ue_id,synthetic_cell_id,rrc_connected,sent,received,on_time,mean_delay_ms,max_delay_ms\n" << std::setprecision(10);
        for (uint32_t u = 0; u < ueCount; ++u)
        {
            if (!gUeVoice.at(u)) continue;
            auto device = ueDevices.Get(u)->GetObject<LteUeNetDevice>();
            const auto& s = gVoice[u];
            voice << u << ',' << device->GetRrc()->GetCellId() << ','
                  << (device->GetRrc()->GetState() == LteUeRrc::CONNECTED_NORMALLY) << ',' << s.sent << ','
                  << s.received << ',' << s.onTime << ',' << (s.received ? 1000*s.delaySum/s.received : -1) << ','
                  << 1000*s.delayMax << '\n';
        }
    }
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
    std::ofstream prb(out("prb_usage.csv"));
    prb << "synthetic_cell_id,data_frames,rb_subframes,counted_subframes,dl_prb_utilization\n";
    prb << std::setprecision(12);
    const double counted = std::max(0.0, duration - gPrbWarmup) * 1000.0;
    for (uint32_t i = 0; i < enbDevices.GetN(); ++i)
    {
        const uint16_t cell = enbDevices.Get(i)->GetObject<LteEnbNetDevice>()->GetCellId();
        const auto c = gPrb.count(cell) ? gPrb.at(cell) : PrbCount{};
        prb << cell << ',' << c.dataFrames << ',' << c.rbSubframes << ',' << counted << ','
            << (counted > 0 ? c.rbSubframes / ((gCellRb.count(cell) ? gCellRb.at(cell) : 100) * counted) : 0.0) << '\n';
    }
    prb.close();
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

// Shadow header sha256: 9190b34909d65c3848aff3b04af1365ab8ff9c038d0fb09669c75632ab5eb445
