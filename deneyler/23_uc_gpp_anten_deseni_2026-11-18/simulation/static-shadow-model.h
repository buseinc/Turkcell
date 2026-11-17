// Explicit experimental static, reciprocal, per-site/UE lognormal shadow hypothesis.
// No terrain data is inferred. Colocated sectors share a shadow value.
#ifndef EXPERIMENT_STATIC_SHADOW_MODEL_H
#define EXPERIMENT_STATIC_SHADOW_MODEL_H
#include "ns3/propagation-loss-model.h"
#include "ns3/mobility-model.h"
#include "ns3/double.h"
#include "ns3/uinteger.h"
#include "ns3/constant-position-mobility-model.h"
#include "ns3/abort.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <unordered_map>
#include <iostream>

namespace ns3 {
class ExperimentStaticShadow : public PropagationLossModel
{
public:
    static TypeId GetTypeId()
    {
        static TypeId tid=TypeId("ns3::ExperimentStaticShadow")
            .SetParent<PropagationLossModel>().SetGroupName("Propagation")
            .AddConstructor<ExperimentStaticShadow>()
            .AddAttribute("Exponent","Log-distance exponent",DoubleValue(3.0),
                MakeDoubleAccessor(&ExperimentStaticShadow::m_exponent),MakeDoubleChecker<double>())
            .AddAttribute("ReferenceDistance","Reference distance in metres",DoubleValue(1.0),
                MakeDoubleAccessor(&ExperimentStaticShadow::m_referenceDistance),MakeDoubleChecker<double>())
            .AddAttribute("ReferenceLoss","Reference loss in dB",DoubleValue(37.6),
                MakeDoubleAccessor(&ExperimentStaticShadow::m_referenceLoss),MakeDoubleChecker<double>())
            .AddAttribute("Sigma","Static zero-mean Gaussian dB standard deviation",DoubleValue(0.0),
                MakeDoubleAccessor(&ExperimentStaticShadow::m_sigma),MakeDoubleChecker<double>())
            .AddAttribute("ShadowSeed","Coordinate-keyed shadow realization",UintegerValue(42),
                MakeUintegerAccessor(&ExperimentStaticShadow::m_seed),MakeUintegerChecker<uint64_t>());
        return tid;
    }
private:
    static uint64_t Mix(uint64_t x)
    {
        x+=0x9e3779b97f4a7c15ULL;
        x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;
        x=(x^(x>>27))*0x94d049bb133111ebULL;
        return x^(x>>31);
    }
    double Shadow(Ptr<MobilityModel> a,Ptr<MobilityModel> b) const
    {
        auto pa=a->GetPosition(),pb=b->GetPosition();
        std::array<int64_t,3> x={llround(pa.x*1e6),llround(pa.y*1e6),llround(pa.z*1e6)};
        std::array<int64_t,3> y={llround(pb.x*1e6),llround(pb.y*1e6),llround(pb.z*1e6)};
        if(y<x)std::swap(x,y);
        uint64_t key=Mix(m_seed);
        for(auto value:x)key=Mix(key^static_cast<uint64_t>(value));
        for(auto value:y)key=Mix(key^static_cast<uint64_t>(value));
        auto found=m_cache.find(key);
        if(found!=m_cache.end())return found->second;
        const double u1=((Mix(key)>>11)+0.5)/9007199254740992.0;
        const double u2=((Mix(key^0xa0761d6478bd642fULL)>>11)+0.5)/9007199254740992.0;
        const double offset=m_sigma*std::sqrt(-2*std::log(u1))*std::cos(2*M_PI*u2);
        m_cache.emplace(key,offset);
        return offset;
    }
    double DoCalcRxPower(double power,Ptr<MobilityModel> a,Ptr<MobilityModel> b) const override
    {
        const double distance=std::max(a->GetDistanceFrom(b),m_referenceDistance);
        const double nominal=power-m_referenceLoss-10*m_exponent*std::log10(distance/m_referenceDistance);
        return nominal+(m_sigma>0 ? Shadow(a,b) : 0.0);
    }
    int64_t DoAssignStreams(int64_t) override {return 0;}
    double m_exponent=3,m_referenceDistance=1,m_referenceLoss=37.6,m_sigma=0;
    uint64_t m_seed=42;
    mutable std::unordered_map<uint64_t,double> m_cache;
};
NS_OBJECT_ENSURE_REGISTERED(ExperimentStaticShadow);
inline void VerifyExperimentalShadowModel()
{
    auto a=CreateObject<ConstantPositionMobilityModel>();
    auto b=CreateObject<ConstantPositionMobilityModel>();
    auto c=CreateObject<ConstantPositionMobilityModel>();
    a->SetPosition(Vector(0,0,30));c->SetPosition(Vector(0,0,30));
    b->SetPosition(Vector(1000,1000,1.5));
    auto model=CreateObject<ExperimentStaticShadow>();
    model->SetAttribute("Sigma",DoubleValue(4));
    auto nominal=CreateObject<LogDistancePropagationLossModel>();
    nominal->SetAttribute("ReferenceLoss",DoubleValue(37.6));
    auto zero=CreateObject<ExperimentStaticShadow>();
    const double x=model->CalcRxPower(46,a,b);
    NS_ABORT_MSG_IF(std::abs(x-model->CalcRxPower(46,b,a))>1e-12,"Non-reciprocal shadow");
    NS_ABORT_MSG_IF(std::abs(x-model->CalcRxPower(46,c,b))>1e-12,"Colocated sectors differ");
    NS_ABORT_MSG_IF(std::abs(x-model->CalcRxPower(46,a,b))>1e-12,"Shadow changed in time");
    NS_ABORT_MSG_IF(std::abs(zero->CalcRxPower(46,a,b)-nominal->CalcRxPower(46,a,b))>1e-12,"Sigma zero differs");
    double sum=0,squares=0;
    for(int i=0;i<5000;++i)
    {
        b->SetPosition(Vector(500+(i%100)*50,500+(i/100)*50,1.5));
        const double offset=model->CalcRxPower(46,a,b)-nominal->CalcRxPower(46,a,b);
        sum+=offset;squares+=offset*offset;
    }
    const double mean=sum/5000,sd=std::sqrt(squares/5000-mean*mean);
    NS_ABORT_MSG_IF(std::abs(mean)>.25 || std::abs(sd-4)>.25,"Shadow distribution sanity failed");
    std::cout << "{\"passed\":true,\"reciprocal\":true,\"colocated_sectors_share_shadow\":true,"
        << "\"time_static\":true,\"sigma_zero_matches_log_distance\":true,\"samples\":5000,"
        << "\"sample_mean_db\":" << mean << ",\"sample_std_db\":" << sd << "}\n";
}
}
#endif
