"""Prepare a separate, predeclared sector-removal pilot; leave S0 intact."""
from pathlib import Path
import csv
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]/'ana_proje'
FROZEN = PROJECT/'analysis/sindirgi/radio_study/frozen'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def main():
    sim = HERE/'simulation'
    inputs = HERE/'inputs'
    sim.mkdir(parents=True, exist_ok=True)
    inputs.mkdir(exist_ok=True)
    source = (PROJECT/'simulation/sindirgi_baseline.cc').read_text(encoding='utf-8')
    source = replace_once(source,
        'double rotation = std::numeric_limits<double>::quiet_NaN();',
        'double rotation = std::numeric_limits<double>::quiet_NaN();\n    uint32_t sectorCount = 3;')
    source = replace_once(source,
        '        if (limit && sites.size() == limit) break;',
        '        if (index.count("sector_count"))\n'
        '            sites.back().sectorCount=std::stoul(row.at(index.at("sector_count")));\n'
        '        if (sites.back().sectorCount < 1 || sites.back().sectorCount > 3)\n'
        '            throw std::runtime_error("sector_count must be 1, 2 or 3");\n'
        '        if (limit && sites.size() == limit) break;')
    source = replace_once(source, '    enbNodes.Create(3 * sites.size());',
        '    uint32_t sectorTotal = 0;\n'
        '    for (const auto& site : sites) sectorTotal += site.sectorCount;\n'
        '    enbNodes.Create(sectorTotal);')
    source = replace_once(source,
        '    for (size_t i = 0; i < sites.size(); ++i)',
        '    uint32_t enbIndex = 0;\n    for (size_t i = 0; i < sites.size(); ++i)')
    source = replace_once(source, 'sector < 3; ++sector', 'sector < sites[i].sectorCount; ++sector')
    source = replace_once(source, 'enbNodes.Get(i * 3 + sector)', 'enbNodes.Get(enbIndex++)')
    (sim/'sindirgi_baseline.cc').write_text(source, encoding='utf-8')
    runner = (PROJECT/'simulation/run_baseline.py').read_text(encoding='utf-8')
    runner = replace_once(runner, 'import argparse', 'import argparse\nimport csv')
    runner = replace_once(runner, "    result['model_assumptions']={",
        "    with args.sites_file.open() as stream:\n"
        "        sector_counts={r['site']:int(r.get('sector_count',3)) for r in csv.DictReader(stream)}\n"
        "    result['model_assumptions']={")
    runner = replace_once(runner, "'sectors_per_site':3", "'sectors_per_site':sector_counts")
    (sim/'run_baseline.py').write_text(runner, encoding='utf-8')
    shutil.copy2(PROJECT/'simulation/ns3_paths.py', sim/'ns3_paths.py')
    shutil.copy2(FROZEN/'ues.csv', inputs/'ues.csv')
    shutil.copy2(PROJECT/'analysis/sindirgi/radio_study/measured_site_targets.csv', inputs/'targets.csv')
    with (FROZEN/'sites.csv').open() as stream:
        sites = list(csv.DictReader(stream))
    with (inputs/'targets.csv').open() as stream:
        targets = list(csv.DictReader(stream))
    affected = sorted(t['site'] for t in targets if int(t['measured_cells']) == 2)
    assert affected == ['SITE_000482','SITE_000554']
    cases = []
    for count, name in [(3,'s0_three'),(2,'s1_two'),(1,'s1_one')]:
        rows = [dict(r, sector_count=count if r['site'] in affected else 3) for r in sites]
        path = inputs/(name+'.csv')
        with path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        cases.append({'name':name,'affected_site_sectors':count,
                      'total_sectors':sum(r['sector_count'] for r in rows),
                      'sites_sha256':digest(path)})
    plan = {
        'purpose':'Diagnostic pilot of sector-count ambiguity; no operator reconstruction claim.',
        'advisor_note':'main.tex: cell sayisina bakmadan 3 sektore boldum ama bakilmasi lazim',
        'affected_sites':affected, 'cases':cases,
        'sites':24,'ues':64,'duration_s':4.0,'warmup_s':1.0,'seed':42,'run':1,
        'fixed':'Same UE positions, site positions, 65-degree antennas, per-sector 46 dBm, Band 3, log-distance exponent 3, UDP probe, and surviving azimuths.',
        'sector_removal':'Retain original indices 0..count-1 and phi+120*index. Do not rotate or widen surviving beams.',
        'power_caveat':'Removing sectors reduces total site radiated power; remaining per-sector power is unchanged.',
        'scope_caveat':'One-sector case is a single 65-degree directional beam, not an omnidirectional replacement. Removed directions were fixed before simulation; alternative directions and rotations are not explored.',
        'carrier_caveat':'All cases are cochannel single-carrier. This does not implement or validate multi-carrier hypothesis S2.',
        'evaluation':'All eight previously observed sites, original equal-sector averaging; report missing sites and association changes. No tuning or replacement of frozen baseline.',
        'regression_gate':'Fresh modified-code S0 must match original 64-UE RSRP/SINR/RSRQ, serving site/sector, connection and received bytes before alternatives run.',
        'original_cpp_sha256':digest(PROJECT/'simulation/sindirgi_baseline.cc'),
        'experiment_cpp_sha256':digest(sim/'sindirgi_baseline.cc'),
        'ues_sha256':digest(inputs/'ues.csv'),'targets_sha256':digest(inputs/'targets.csv')}
    (HERE/'experiment_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    archive = sim/'archive'
    archive.mkdir(exist_ok=True)
    shutil.copy2(sim/'sindirgi_baseline.cc', archive/(plan['experiment_cpp_sha256']+'.cc'))
    print(json.dumps({'affected_sites':affected,'cases':cases},indent=2))


if __name__ == '__main__':
    main()
