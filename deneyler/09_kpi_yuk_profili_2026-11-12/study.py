"""WSL runner for the KPI-informed load study (stdlib only). Resumable; see plan.json."""
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
D08 = ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12'
SIM = HERE / 'simulation'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


radio = module('radio09', PROJECT / 'simulation/run_radio_study.py')
ev = module('eval09', ROOT / 'deneyler/04_ortak_radyo_taramasi_2026-11-10/run_search.py')


def save(p, x):
    t = p.with_suffix('.tmp')
    t.write_text(json.dumps(x, indent=2, ensure_ascii=False), encoding='utf-8')
    t.replace(p)


def read(p):
    with p.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def measurement_metrics(m, n_meas):
    """Same aggregation as radio.metrics (sector mean, then site mean) on measurement UEs only."""
    ues = [r for r in m['ues'] if r['ue_id'] < n_meas]
    by_sector = defaultdict(list)
    for r in ues:
        if r['site'] is not None:
            by_sector[(r['site'], r['sector'])].append(r)
    by_site = defaultdict(list)
    for (site, _), rows in by_sector.items():
        by_site[site].append({k: radio.avg([r[k] for r in rows]) for k in ['rsrp', 'sinr', 'rsrq']})
    sites = {s: {k: radio.avg([r[k] for r in rows]) for k in ['rsrp', 'sinr', 'rsrq']} | {'active_sectors': len(rows)}
             for s, rows in by_site.items()}
    return {'sites': sites, 'ues': ues}


def paired(a, b):
    left = {r['ue_id']: r for r in a['ues']}
    right = {r['ue_id']: r for r in b['ues']}
    ids = sorted(set(left) & set(right))
    for u in ids:
        assert abs(left[u]['x_m'] - right[u]['x_m']) < 1e-6 and abs(left[u]['y_m'] - right[u]['y_m']) < 1e-6
    out = {'paired_ues': len(ids),
           'same_serving_sector_fraction': sum(left[u]['site'] == right[u]['site'] and left[u]['sector'] == right[u]['sector'] for u in ids) / len(ids)}
    for k in ['rsrp', 'sinr', 'rsrq']:
        d = [right[u][k] - left[u][k] for u in ids if left[u][k] is not None and right[u][k] is not None]
        out[f'{k}_mean_change_db'] = statistics.mean(d)
        out[f'{k}_q95_abs_change_db'] = radio.quantile([abs(x) for x in d], .95)
    return out


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
        sp = HERE / f"inputs/sites_24_{c['az']}.csv"
        up = HERE / f"inputs/ues_{c['load']}_{c['ue_seed']}.csv"
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
                   '--dl-earfcn', str(r['dl_earfcn']), '--name', c['name'], '--skip-build']
            print('START', c['name'], flush=True)
            with (HERE / 'logs' / (c['name'] + '.log')).open('w') as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
        res = json.loads((folder / 'result.json').read_text())
        full = radio.metrics(folder, c['warmup'])
        m = measurement_metrics(full, c['measurement_ues'])
        ue_rows = {int(x['ue_id']): x for x in read(up)}
        served = {int(x['ue_id']): int(x['synthetic_cell_id']) for x in read(folder / 'ues.csv')}
        prb = {int(x['synthetic_cell_id']): float(x['dl_prb_utilization']) for x in read(folder / 'prb_usage.csv')}
        sectors = {int(x['synthetic_cell_id']): x for x in read(folder / 'sectors.csv')}
        load_rows = [x for x in ue_rows.values() if x['kind'] == 'load']
        cells = []
        for x in load_rows:
            cid = int(x['target_cell'])
            cells.append({'cell': cid, 'site': sectors[cid]['site'], 'role': sectors[cid]['role'],
                          'target_prb': float(x['target_prb']), 'achieved_prb': prb[cid],
                          'load_ue_on_target': served[int(x['ue_id'])] == cid})
        meas_dl = [u for u in full['ues'] if u['ue_id'] < c['measurement_ues']]
        base = json.loads((D08 / 'simulation/results' / c['baseline_08'] / 'metrics.json').read_text())
        out = {'case': c, 'cached': cached, 'wall_seconds': res.get('wall_seconds'),
               'connected_ues': res.get('connected_ues'),
               'measurement_connected': sum(u['connected'] for u in meas_dl),
               'measurement_with_dl': sum(u['dl_bytes'] > 0 for u in meas_dl),
               'load_ues_on_target': sum(x['load_ue_on_target'] for x in cells),
               'prb_mean_target': statistics.mean(x['target_prb'] for x in cells),
               'prb_mean_achieved': statistics.mean(x['achieved_prb'] for x in cells),
               'cells': cells, 'sites': m['sites'],
               'training': ev.evaluate(m, targets, 'train'), 'control': ev.evaluate(m, targets, 'holdout'),
               'paired_vs_08': paired(base, m)}
        print('DONE', c['name'], 'prb', round(out['prb_mean_achieved'], 3), flush=True)
        return out

    cases = [c for c in plan['cases'] if only is None or c['name'] in only]
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(one, c) for c in cases]):
            results.append(f.result())
            save(HERE / 'checkpoint.json', {'completed': len(results), 'planned': len(cases), 'results': results})
    save(HERE / 'result.json', {'completed': only is None,
                                'results': sorted(results, key=lambda x: (x['case']['ue_seed'], x['case']['load']))})
    print('COMPLETE', flush=True)


if __name__ == '__main__':
    main()
