#ifndef S0_HANDOVER_SUPPORT_H
#define S0_HANDOVER_SUPPORT_H
#include "ns3/applications-module.h"
#include "ns3/lte-module.h"
#include "ns3/mobility-module.h"
#include <fstream>
#include <iomanip>
#include <map>

namespace s0ho {
static std::ofstream events, timeline, packets;
static std::map<uint64_t,uint32_t> ueForImsi;

static void Event(const std::string& actor,const std::string& event,uint32_t ue,
                  uint64_t imsi,uint16_t cell,uint16_t rnti,uint16_t target=0)
{
    if (!events.is_open()) return;
    events << ns3::Simulator::Now().GetSeconds() << ',' << actor << ',' << event << ','
           << ue << ',' << imsi << ',' << cell << ',' << rnti << ',' << target << '\n';
}
static void Connection(uint32_t u,uint64_t imsi,uint16_t cell,uint16_t rnti)
{ Event("UE","CONNECTION",u,imsi,cell,rnti); }
static void UeStart(uint32_t u,uint64_t imsi,uint16_t cell,uint16_t rnti,uint16_t target)
{ Event("UE","START",u,imsi,cell,rnti,target); }
static void UeEnd(uint32_t u,uint64_t imsi,uint16_t cell,uint16_t rnti)
{ Event("UE","END_OK",u,imsi,cell,rnti); }
static void UeError(uint32_t u,uint64_t imsi,uint16_t cell,uint16_t rnti)
{ Event("UE","END_ERROR",u,imsi,cell,rnti); }
static uint32_t Ue(uint64_t imsi) { return ueForImsi.at(imsi); }
static void EnbStart(uint64_t imsi,uint16_t cell,uint16_t rnti,uint16_t target)
{ Event("ENB","START",Ue(imsi),imsi,cell,rnti,target); }
static void EnbEnd(uint64_t imsi,uint16_t cell,uint16_t rnti)
{ Event("ENB","END_OK",Ue(imsi),imsi,cell,rnti); }
static void EnbError(std::string reason,uint64_t imsi,uint16_t rnti,uint16_t cell)
{ Event("ENB",reason,Ue(imsi),imsi,cell,rnti); }
static void PacketRx(uint32_t ue,ns3::Ptr<const ns3::Packet> packet,const ns3::Address&)
{
    packets << ns3::Simulator::Now().GetSeconds() << ',' << ue << ',' << packet->GetSize() << '\n';
}
static void Sample(uint32_t ue,ns3::Ptr<ns3::LteUeNetDevice> device,
                   ns3::Ptr<ns3::MobilityModel> mobility,ns3::Ptr<ns3::PacketSink> sink,double duration)
{
    const auto p=mobility->GetPosition();
    auto rrc=device->GetRrc();
    timeline << ns3::Simulator::Now().GetSeconds() << ',' << ue << ',' << p.x << ',' << p.y << ','
             << p.z << ',' << rrc->GetCellId() << ',' << rrc->GetRnti() << ','
             << static_cast<uint32_t>(rrc->GetState()) << ',' << (sink ? sink->GetTotalRx() : 0) << '\n';
    if (ns3::Simulator::Now().GetSeconds()+0.1 < duration)
        ns3::Simulator::Schedule(ns3::MilliSeconds(100),&Sample,ue,device,mobility,sink,duration);
}
}
#endif
