// Experiment 34: spatially smooth random fields for moving users (DUZELTMELER.md).
// Per site (eNB position) a grid of N(0,1) node values with the given spacing; the value at a UE position
// is the bilinear mix of the 4 surrounding nodes divided by sqrt(sum of squared weights), so it is N(0,1)
// everywhere and continuous in position. Deterministic: (seed, salt, site position in mm, node index).
// The fast model (deneyler/34 alan.py) implements the same formula.
#ifndef EXPERIMENT34_SPATIAL_FIELD_H
#define EXPERIMENT34_SPATIAL_FIELD_H

#include "ns3/channel-condition-model.h"
#include "ns3/mobility-model.h"

#include <cmath>
#include <cstdint>
#include <unordered_map>
#include <utility>

namespace e34 {
inline uint64_t Mix(uint64_t x)
{
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}

inline double NodeValue(uint64_t seed, uint64_t salt, int64_t sx, int64_t sy, int64_t ix, int64_t iy)
{
    uint64_t key = Mix(seed ^ (salt * 0x632be59bd9b4e019ULL));
    for (int64_t v : {sx, sy, ix, iy}) key = Mix(key ^ static_cast<uint64_t>(v));
    const double u1 = ((Mix(key) >> 11) + 0.5) / 9007199254740992.0;
    const double u2 = ((Mix(key ^ 0xa0761d6478bd642fULL) >> 11) + 0.5) / 9007199254740992.0;
    return std::sqrt(-2 * std::log(u1)) * std::cos(2 * M_PI * u2);
}

// N(0,1) value of the field of the site at (ex, ey) at UE position (x, y).
inline double Field(uint64_t seed, uint64_t salt, double ex, double ey, double x, double y, double spacing)
{
    const int64_t sx = std::llround(ex * 1e3), sy = std::llround(ey * 1e3);
    const double gx = x / spacing, gy = y / spacing;
    const int64_t ix = static_cast<int64_t>(std::floor(gx)), iy = static_cast<int64_t>(std::floor(gy));
    const double fx = gx - ix, fy = gy - iy;
    const double w[4] = {(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy};
    const double g[4] = {NodeValue(seed, salt, sx, sy, ix, iy), NodeValue(seed, salt, sx, sy, ix + 1, iy),
                         NodeValue(seed, salt, sx, sy, ix, iy + 1), NodeValue(seed, salt, sx, sy, ix + 1, iy + 1)};
    double num = 0, den = 0;
    for (int k = 0; k < 4; ++k) { num += w[k] * g[k]; den += w[k] * w[k]; }
    return num / std::sqrt(den);
}

// Experiment 42: LOS probability of TR 38.901 Table 7.4.2-1 for RMa or (hUT <= 13 m) UMa, and the LOS
// state from the smooth field (salt 2), shared by the condition model and the per-link shadow std.
inline double Plos(double d2, bool uma)
{
    if (uma) return d2 <= 18 ? 1.0 : 18.0 / d2 + std::exp(-d2 / 63.0) * (1 - 18.0 / d2);
    return d2 <= 10 ? 1.0 : std::exp(-(d2 - 10) / 1000.0);
}
inline bool LosState(uint64_t seed, double spacing, double ex, double ey, double ux, double uy, bool uma)
{
    const double u = 0.5 * (1 + std::erf(Field(seed, 2, ex, ey, ux, uy, spacing) / std::sqrt(2.0)));
    return u < Plos(std::hypot(ex - ux, ey - uy), uma);
}
// Experiment 42: UE environment (true = city/UMa, false = rural/RMa), keyed by the UE mobility model.
inline std::unordered_map<const ns3::MobilityModel*, bool>& UeUrban()
{
    static std::unordered_map<const ns3::MobilityModel*, bool> m;
    return m;
}

// RMa LOS state that follows the UE position: LOS if Phi(field) < Plos(d2D) (TR 38.901 Table 7.4.2-1,
// correlation distance 60 m, section 7.6.3.3). The eNB is the higher end of the link; colocated sectors
// share a position and therefore one state.
class SpatialRmaConditionModel : public ns3::ChannelConditionModel
{
  public:
    static ns3::TypeId GetTypeId()
    {
        static ns3::TypeId tid = ns3::TypeId("e34::SpatialRmaConditionModel")
                                     .SetParent<ns3::ChannelConditionModel>()
                                     .AddConstructor<SpatialRmaConditionModel>();
        return tid;
    }
    void Configure(uint64_t seed, double spacing, bool uma = false) { m_seed = seed; m_spacing = spacing; m_uma = uma; }
    ns3::Ptr<ns3::ChannelCondition> GetChannelCondition(ns3::Ptr<const ns3::MobilityModel> a,
                                                         ns3::Ptr<const ns3::MobilityModel> b) const override
    {
        auto pa = a->GetPosition(), pb = b->GetPosition();
        if (pb.z > pa.z) std::swap(pa, pb);                       // pa: eNB
        const uint64_t key = Mix(reinterpret_cast<uintptr_t>(ns3::PeekPointer(a)) ^
                                 (static_cast<uint64_t>(reinterpret_cast<uintptr_t>(ns3::PeekPointer(b))) << 1));
        auto& e = m_cache[key];
        if (e.cond && e.ex == pa.x && e.ey == pa.y && e.ux == pb.x && e.uy == pb.y) return e.cond;
        auto c = ns3::CreateObject<ns3::ChannelCondition>();
        c->SetLosCondition(LosState(m_seed, m_spacing, pa.x, pa.y, pb.x, pb.y, m_uma) ? ns3::ChannelCondition::LOS
                                                                                     : ns3::ChannelCondition::NLOS);
        c->SetO2iCondition(ns3::ChannelCondition::O2O);
        e = {c, pa.x, pa.y, pb.x, pb.y};
        return c;
    }
    int64_t AssignStreams(int64_t) override { return 0; }

  private:
    uint64_t m_seed = 42;
    double m_spacing = 60.0;
    bool m_uma = false;
    struct Entry { ns3::Ptr<ns3::ChannelCondition> cond; double ex = 0, ey = 0, ux = 0, uy = 0; };
    mutable std::unordered_map<uint64_t, Entry> m_cache;
};
NS_OBJECT_ENSURE_REGISTERED(SpatialRmaConditionModel);
} // namespace e34
#endif
