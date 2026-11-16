"""WSL runner for S0 vs S2 (stdlib only). Resumable; see plan.json."""
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import importlib.util
import json
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT / 'ana_proje'
SIM = HERE / 'simulation'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


radio = module('radio14', PROJECT / 'simulation/run_radio_study.py')
ev = module('eval14', ROOT / 'deneyler/04_ortak_radyo_taramasi_2026-11-10/run_search.py')


def read(p):
    with p.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def save(p, x):
    t = p.with_suffix('.tmp')
    t.write_text(json.dumps(x, indent=2, ensure_ascii=False), encoding='utf-8')
    t.replace(p)


def measurement_metrics(m, n):
    ues = [r for r in m['ues'] if r['ue_id'] < n]
    by_cell = defaultdict(list)
    for r in ues:
        if r['site'] is not None:
            by_cell[(r['site'], r['sector'])].append(r)
    by_site = defaultdict(list)
    for (site, _), rows in by_cell.items():
        by_site[site].append({k: radio.avg([r[k] for r in rows]) for k in ['rsrp', 'sinr', 'rsrq']})
    sites = {s: {k: radio.avg([r[k] for r in rows]) for k in ['rsrp', 'sinr', 'rsrq']} | {'active_cells': len(rows)}
             for s, rows in by_site.items()}
    return {'sites': sites, 'ues': ues}


def main():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    assert sha(SIM / 'sindirgi_baseline.cc') == plan['source_sha256']
    for name, h in plan['input_hashes'].items():
        assert sha(HERE / 'inputs' / name) == h, name
    targets = radio.read(HERE / 'inputs/targets.csv')
    r = plan['radio']
    only = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
    workers = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 3
    (HERE / 'logs').mkdir(exist_ok=True)

    def one(c):
        folder = SIM / 'results' / c['name']
        sp = HERE / f"inputs/sites_{c['scenario']}_{c['az']}.csv"
        up = HERE / f"inputs/ues_{c['scenario']}_{c['ue_seed']}.csv"
        cached = False
        if (folder / 'result.json').exists():
            res = json.loads((folder / 'result.json').read_text())
            cached = (res.get('sites_sha256') == sha(sp) and res.get('ue_positions_sha256') == sha(up)
                      and res.get('source_sha256') == plan['source_sha256'] and res.get('duration_s') == c['duration'])
        if not cached:
            cmd = [sys.executable, str(SIM / 'run_baseline.py'), '--sites', '0', '--ues', str(c['ues']),
                   '--duration', str(c['duration']), '--sites-file', str(sp), '--ue-file', str(up),
                   '--mixed-cqi', str(r['mixed_cqi']), '--beamwidth', str(r['beamwidth']), '--exponent', str(r['exponent']),
                   '--enb-power', str(r['enb_power']), '--receiver-nf', str(r['receiver_nf']), '--shadow-std', str(r['shadow_std']),
                   '--dl-earfcn', str(r['dl_earfcn']), '--udp-jitter', str(r['udp_jitter']), '--name', c['name'], '--skip-build']
            print('START', c['name'], flush=True)
            with (HERE / 'logs' / (c['name'] + '.log')).open('w') as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
        res = json.loads((folder / 'result.json').read_text())
        full = radio.metrics(folder, c['warmup'])
        m = measurement_metrics(full, c['measurement_ues'])
        sectors = read(folder / 'sectors.csv')
        cell_of = {(x['site'], int(x['sector'])): int(x['synthetic_cell_id']) for x in sectors}
        carrier_of = {int(x['synthetic_cell_id']): x.get('carrier', 'B3') for x in sectors}
        prb = {int(x['synthetic_cell_id']): float(x['dl_prb_utilization']) for x in read(folder / 'prb_usage.csv')}
        served = {int(x['ue_id']): int(x['synthetic_cell_id']) for x in read(folder / 'ues.csv')}
        ue_rows = read(up)
        cells = []
        for x in ue_rows:
            if x['kind'] != 'load':
                continue
            cid = cell_of[(x['target_site'], int(x['target_sector']))]
            cells.append({'cell': cid, 'site': x['target_site'], 'carrier': carrier_of[cid], 'target_prb': float(x['target_prb']),
                          'achieved_prb': prb[cid], 'load_ue_on_target': served[int(x['ue_id'])] == cid})
        meas = [u for u in full['ues'] if u['ue_id'] < c['measurement_ues']]
        on_b20 = sum(carrier_of.get(served[u['ue_id']], 'B3') == 'B20' for u in meas)
        out = {'case': c, 'cached': cached, 'wall_seconds': res.get('wall_seconds'),
               'connected_ues': res.get('connected_ues'),
               'measurement_connected': sum(u['connected'] for u in meas),
               'measurement_with_dl': sum(u['dl_bytes'] > 0 for u in meas),
               'measurement_on_b20': on_b20,
               'load_ues_on_target': sum(x['load_ue_on_target'] for x in cells), 'load_cells': len(cells),
               'prb_mean_achieved': statistics.mean(x['achieved_prb'] for x in cells),
               'prb_mean_achieved_by_carrier': {k: statistics.mean(x['achieved_prb'] for x in cells if x['carrier'] == k)
                                                for k in sorted({x['carrier'] for x in cells})},
               'cells': cells, 'sites': m['sites'],
               'training': ev.evaluate(m, targets, 'train'), 'control': ev.evaluate(m, targets, 'holdout')}
        print('DONE', c['name'], 'prb', round(out['prb_mean_achieved'], 3), flush=True)
        return out

    cases = [c for c in plan['cases'] if only is None or c['name'] in only]
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(one, c) for c in cases]):
            results.append(f.result())
            save(HERE / 'checkpoint.json', {'completed': len(results), 'planned': len(cases), 'results': results})
    save(HERE / 'result.json', {'completed': only is None,
                                'results': sorted(results, key=lambda x: (x['case']['scenario'], x['case']['ue_seed']))})
    print('COMPLETE', flush=True)


if __name__ == '__main__':
    main()
