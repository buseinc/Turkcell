#ifndef BUILDING_VERTICAL_MODEL_H
#define BUILDING_VERTICAL_MODEL_H
#include "ns3/spectrum-propagation-loss-model.h"
#include "ns3/spectrum-signal-parameters.h"
#include "ns3/spectrum-value.h"
#include "ns3/mobility-model.h"
#include "ns3/node-container.h"
#include <algorithm>
#include <array>
#include <unordered_map>
#include <cmath>
#include <set>

// Separable effective link loss; not a full building geometry or antenna array model.
class BuildingVerticalLoss : public ns3::SpectrumPropagationLossModel
{
public:
    static ns3::TypeId GetTypeId()
    {
        static ns3::TypeId tid = ns3::TypeId("ns3::SindirgiBuildingVerticalLoss")
            .SetParent<ns3::SpectrumPropagationLossModel>().AddConstructor<BuildingVerticalLoss>();
        return tid;
    }
    void Configure(const ns3::NodeContainer& enbs, const ns3::NodeContainer& ues,
                   uint32_t measured, double indoor, bool vertical, double tilt, double width,
                   double shadowSigma = 0.0, uint64_t shadowSeed = 42)
    {
        m_indoor = indoor; m_vertical = vertical; m_tilt = tilt; m_width = width;
        m_shadowSigma = shadowSigma; m_shadowSeed = shadowSeed;
        for (uint32_t i=0; i<enbs.GetN(); ++i)
            m_enbs.insert(ns3::PeekPointer(enbs.Get(i)->GetObject<ns3::MobilityModel>()));
        for (uint32_t i=0; i<measured; ++i)
            m_measured.insert(ns3::PeekPointer(ues.Get(i)->GetObject<ns3::MobilityModel>()));
    }
    static double VerticalLoss(double horizontalM, double heightM, double tilt, double width)
    {
        const double elevation = std::atan2(heightM, horizontalM)*180.0/M_PI;
        return std::min(12.0*std::pow((elevation-tilt)/width,2),20.0);
    }
private:
    ns3::Ptr<ns3::SpectrumValue> DoCalcRxPowerSpectralDensity(
        ns3::Ptr<const ns3::SpectrumSignalParameters> params,
        ns3::Ptr<const ns3::MobilityModel> a,
        ns3::Ptr<const ns3::MobilityModel> b) const override
    {
        auto out = params->psd->Copy();
        const bool ae = m_enbs.count(ns3::PeekPointer(a));
        const bool be = m_enbs.count(ns3::PeekPointer(b));
        if (ae == be) return out; // eNB-eNB and UE-UE links are unchanged.
        auto enb = ae ? a : b;
        auto ue = ae ? b : a;
        double loss = m_measured.count(ns3::PeekPointer(ue)) ? m_indoor : 0.0;
        if (m_vertical)
        {
            const auto e = enb->GetPosition(), u = ue->GetPosition();
            loss += VerticalLoss(std::hypot(e.x-u.x,e.y-u.y),e.z-u.z,m_tilt,m_width);
        }
        // Experiment 20: static per eNB-UE position Gaussian shadowing (same hash as ExperimentStaticShadow);
        // sectors of one site share a position and therefore one shadow value.
        if (m_shadowSigma > 0) loss -= Shadow(enb->GetPosition(), ue->GetPosition());
        const double factor = std::pow(10.0,-loss/10.0);
        for (auto it=out->ValuesBegin(); it!=out->ValuesEnd(); ++it) *it *= factor;
        return out;
    }
    static uint64_t Mix(uint64_t x)
    {
        x+=0x9e3779b97f4a7c15ULL;
        x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;
        x=(x^(x>>27))*0x94d049bb133111ebULL;
        return x^(x>>31);
    }
    // Returns a gain offset in dB (positive = stronger), reciprocal and deterministic.
    double Shadow(const ns3::Vector& pa, const ns3::Vector& pb) const
    {
        std::array<int64_t,3> x={llround(pa.x*1e6),llround(pa.y*1e6),llround(pa.z*1e6)};
        std::array<int64_t,3> y={llround(pb.x*1e6),llround(pb.y*1e6),llround(pb.z*1e6)};
        if(y<x)std::swap(x,y);
        uint64_t key=Mix(m_shadowSeed);
        for(auto value:x)key=Mix(key^static_cast<uint64_t>(value));
        for(auto value:y)key=Mix(key^static_cast<uint64_t>(value));
        auto found=m_cache.find(key);
        if(found!=m_cache.end())return found->second;
        const double u1=((Mix(key)>>11)+0.5)/9007199254740992.0;
        const double u2=((Mix(key^0xa0761d6478bd642fULL)>>11)+0.5)/9007199254740992.0;
        const double offset=m_shadowSigma*std::sqrt(-2*std::log(u1))*std::cos(2*M_PI*u2);
        m_cache.emplace(key,offset);
        return offset;
    }
    int64_t DoAssignStreams(int64_t) override { return 0; }
    std::set<const ns3::MobilityModel*> m_enbs, m_measured;
    double m_indoor=0, m_tilt=0, m_width=10, m_shadowSigma=0;
    uint64_t m_shadowSeed=42;
    mutable std::unordered_map<uint64_t,double> m_cache;
    bool m_vertical=false;
};
NS_OBJECT_ENSURE_REGISTERED(BuildingVerticalLoss);
#endif
