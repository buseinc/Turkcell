// SINR -> wideband CQI table produced by ns-3.44's own LteAmc (default AmcModel, Vienna/MiErrorModel).
// Flat SINR over all 100 RBs, RBG size 4 (20 MHz), as in the Sindirgi scenario (no fading).
#include "ns3/core-module.h"
#include "ns3/lte-module.h"
#include "ns3/lte-spectrum-value-helper.h"

#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>

using namespace ns3;

int
main(int argc, char* argv[])
{
    std::string output = "cqi_table.csv";
    double minDb = -20, maxDb = 40, stepDb = 0.01;
    CommandLine cmd;
    cmd.AddValue("output", "CSV output", output);
    cmd.Parse(argc, argv);
    auto amc = CreateObject<LteAmc>();
    EnumValue<LteAmc::AmcModel> model;
    amc->GetAttribute("AmcModel", model);
    auto sm = LteSpectrumValueHelper::GetSpectrumModel(1300, 100);
    std::ofstream out(output);
    out << "sinr_db,cqi_mean,cqi_min,cqi_max,amc_model\n" << std::setprecision(10);
    const int n = static_cast<int>(std::round((maxDb - minDb) / stepDb));
    for (int i = 0; i <= n; ++i)
    {
        const double db = minDb + i * stepDb;
        SpectrumValue sinr(sm);
        sinr = std::pow(10.0, db / 10.0);
        auto cqi = amc->CreateCqiFeedbacks(sinr, 4);
        double sum = 0;
        int lo = 99, hi = -99;
        for (int c : cqi)
        {
            sum += c;
            lo = std::min(lo, c);
            hi = std::max(hi, c);
        }
        out << db << ',' << sum / cqi.size() << ',' << lo << ',' << hi << ',' << static_cast<int>(model.Get()) << '\n';
    }
    std::cout << "rows " << n + 1 << " model " << static_cast<int>(model.Get()) << std::endl;
    return 0;
}
