// Experiment 42: per-UE environment. Every link of a UE uses the TR 38.901 model of the UE's environment
// (e34::UeUrban: true = UMa, false = RMa), with ns-3's own ThreeGppUma / ThreeGppRma classes. Their own
// shadowing and building penetration are off (shadow: BuildingVerticalLoss; O2I/car: per-UE extra_loss_db).
// LOS state: e34 smooth field with the probability of the UE's environment. Links without a UE entry
// (eNB-eNB, UE-UE) use RMa.
#ifndef EXPERIMENT42_ENV_SELECT_LOSS_H
#define EXPERIMENT42_ENV_SELECT_LOSS_H

#include "spatial-field.h"

#include "ns3/boolean.h"
#include "ns3/double.h"
#include "ns3/pointer.h"
#include "ns3/propagation-loss-model.h"
#include "ns3/three-gpp-propagation-loss-model.h"

namespace e42 {
inline uint64_t g_seed = 42;         // set from main before the LTE helper creates the model
inline double g_losSpacing = 60.0;

class EnvSelectLoss : public ns3::PropagationLossModel
{
  public:
    static ns3::TypeId GetTypeId()
    {
        static ns3::TypeId tid =
            ns3::TypeId("e42::EnvSelectLoss")
                .SetParent<ns3::PropagationLossModel>()
                .AddConstructor<EnvSelectLoss>()
                .AddAttribute("Frequency", "Centre frequency in Hz, passed to both 3GPP models.",
                              ns3::DoubleValue(500.0e6),
                              ns3::MakeDoubleAccessor(&EnvSelectLoss::SetFrequency, &EnvSelectLoss::GetFrequency),
                              ns3::MakeDoubleChecker<double>());
        return tid;
    }
    EnvSelectLoss()
    {
        m_uma = Make<ns3::ThreeGppUmaPropagationLossModel>(true);
        m_rma = Make<ns3::ThreeGppRmaPropagationLossModel>(false);
    }
    void SetFrequency(double f)
    {
        m_frequency = f;
        m_uma->SetAttribute("Frequency", ns3::DoubleValue(f));
        m_rma->SetAttribute("Frequency", ns3::DoubleValue(f));
    }
    double GetFrequency() const { return m_frequency; }

  private:
    template <class T>
    static ns3::Ptr<ns3::ThreeGppPropagationLossModel> Make(bool uma)
    {
        auto m = ns3::CreateObject<T>();
        m->SetAttribute("ShadowingEnabled", ns3::BooleanValue(false));
        m->SetAttribute("BuildingPenetrationLossesEnabled", ns3::BooleanValue(false));
        m->SetAttribute("EnforceParameterRanges", ns3::BooleanValue(false));
        auto cond = ns3::CreateObject<e34::SpatialRmaConditionModel>();
        cond->Configure(g_seed, g_losSpacing, uma);
        m->SetAttribute("ChannelConditionModel", ns3::PointerValue(cond));
        return m;
    }
    double DoCalcRxPower(double txPowerDbm, ns3::Ptr<ns3::MobilityModel> a,
                         ns3::Ptr<ns3::MobilityModel> b) const override
    {
        const auto& env = e34::UeUrban();
        auto ue = a->GetPosition().z < b->GetPosition().z ? a : b;
        auto it = env.find(ns3::PeekPointer(ue));
        const bool urban = it != env.end() && it->second;
        return (urban ? m_uma : m_rma)->CalcRxPower(txPowerDbm, a, b);
    }
    int64_t DoAssignStreams(int64_t stream) override
    {
        int64_t n = m_uma->AssignStreams(stream);
        return n + m_rma->AssignStreams(stream + n);
    }
    ns3::Ptr<ns3::ThreeGppPropagationLossModel> m_uma, m_rma;
    double m_frequency = 500.0e6;
};
NS_OBJECT_ENSURE_REGISTERED(EnvSelectLoss);
} // namespace e42
#endif
