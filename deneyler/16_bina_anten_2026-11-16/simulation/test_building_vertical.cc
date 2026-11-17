#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "building-vertical-model.h"
#include <iostream>
#include <stdexcept>

int main()
{
    using namespace ns3;
    NodeContainer enbs, ues;
    enbs.Create(2); ues.Create(2);
    MobilityHelper mh;
    mh.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mh.Install(enbs); mh.Install(ues);
    auto e = enbs.Get(0)->GetObject<MobilityModel>();
    auto e2 = enbs.Get(1)->GetObject<MobilityModel>();
    auto measured = ues.Get(0)->GetObject<MobilityModel>();
    auto load = ues.Get(1)->GetObject<MobilityModel>();
    e->SetPosition(Vector(0,0,30)); e2->SetPosition(Vector(10,0,30));
    measured->SetPosition(Vector(100,0,1.5)); load->SetPosition(Vector(100,0,1.5));
    Bands bands;
    BandInfo band; band.fl=1.8e9; band.fc=1.81e9; band.fh=1.82e9;
    bands.push_back(band);
    auto params = Create<SpectrumSignalParameters>();
    params->psd = Create<SpectrumValue>(Create<SpectrumModel>(bands));
    (*params->psd)[0]=2.0;
    int checks=0;
    auto check = [&](double actual, double expected) {
        if (std::abs(actual-expected)>1e-10) throw std::runtime_error("Link loss test failed");
        ++checks;
    };
    auto model = CreateObject<BuildingVerticalLoss>();
    model->Configure(enbs,ues,1,6,false,0,10);
    auto ratio = [&](Ptr<const MobilityModel> a, Ptr<const MobilityModel> b) {
        return (*model->CalcRxPowerSpectralDensity(params,a,b))[0]/2.0;
    };
    const double six=std::pow(10.0,-0.6);
    check(ratio(e,measured),six);
    check(ratio(measured,e),six);
    check(ratio(e,load),1);
    check(ratio(load,e),1);
    check(ratio(measured,load),1);
    check(ratio(e,e2),1);
    check((*params->psd)[0],2); // Input PSD must remain unchanged.
    model->Configure(enbs,ues,1,6,true,6,10);
    measured->SetPosition(Vector(28.5/std::tan(6*M_PI/180),0,1.5));
    check(ratio(e,measured),six); // On beam axis: no vertical loss.
    measured->SetPosition(Vector(28.5/std::tan(11*M_PI/180),0,1.5));
    check(ratio(e,measured),std::pow(10.0,-0.9)); // Half beamwidth: 3 dB.
    check(ratio(measured,e),std::pow(10.0,-0.9)); // Reciprocal UL.
    check(BuildingVerticalLoss::VerticalLoss(0,28.5,0,10),20); // Cap.
    model->Configure(enbs,ues,1,0,false,0,10);
    check(ratio(e,measured),1);
    std::cout << "{\"passed\":true,\"checks\":" << checks << "}\n";
    Simulator::Destroy();
}
