#ifndef BUILDING_VERTICAL_MODEL_H
#define BUILDING_VERTICAL_MODEL_H
#include "ns3/spectrum-propagation-loss-model.h"
#include "ns3/spectrum-signal-parameters.h"
#include "ns3/spectrum-value.h"
#include "ns3/mobility-model.h"
#include "ns3/node-container.h"
#include <algorithm>
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
                   uint32_t measured, double indoor, bool vertical, double tilt, double width)
    {
        m_indoor = indoor; m_vertical = vertical; m_tilt = tilt; m_width = width;
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
        const double factor = std::pow(10.0,-loss/10.0);
        for (auto it=out->ValuesBegin(); it!=out->ValuesEnd(); ++it) *it *= factor;
        return out;
    }
    int64_t DoAssignStreams(int64_t) override { return 0; }
    std::set<const ns3::MobilityModel*> m_enbs, m_measured;
    double m_indoor=0, m_tilt=0, m_width=10;
    bool m_vertical=false;
};
NS_OBJECT_ENSURE_REGISTERED(BuildingVerticalLoss);
#endif
