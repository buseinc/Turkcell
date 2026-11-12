"""WSL runner for the UE sample-size study (stdlib only). Resumable; see plan.json."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT / 'ana_proje'
D06 = ROOT / 'deneyler/06_genis_tarama_secilen_ayar_2026-11-10'
SIM = HERE / 'simulation'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


radio = module('radio08', PROJECT / 'simulation/run_radio_study.py')
ev = module('eval08', ROOT / 'deneyler/04_ortak_radyo_taramasi_2026-11-10/run_search.py')


def save(p, x):
    t = p.with_suffix('.tmp')
    t.write_text(json.dumps(x, indent=2, ensure_ascii=False), encoding='utf-8')
    t.replace(p)


def paired_subset(a, b):
    """Compare the UEs common to both runs (the smaller run's ids)."""
    left = {r['ue_id']: r for r in a['ues']}
    right = {r['ue_id']: r for r in b['ues']}
    ids = sorted(set(left) & set(right))
    for u in ids:
        assert abs(left[u]['x_m'] - right[u]['x_m']) < 1e-6 and abs(left[u]['y_m'] - right[u]['y_m']) < 1e-6
    out = {'paired_ues': len(ids),
           'same_serving_sector_fraction': sum(left[u]['site'] == right[u]['site'] and left[u]['sector'] == right[u]['sector'] for u in ids) / len(ids)}
    for m in ['rsrp', 'sinr', 'rsrq']:
        d = [abs(left[u][m] - right[u][m]) for u in ids if left[u][m] is not None and right[u][m] is not None]
        out[f'{m}_q95_abs_change_db'] = radio.quantile(d, .95)
        out[f'{m}_mean_change_db'] = statistics.mean(right[u][m] - left[u][m] for u in ids
                                                     if left[u][m] is not None and right[u][m] is not None)
    return out


def ues_per_site(m, sites):
    counts = {s: 0 for s in sites}
    for r in m['ues']:
        if r['site'] in counts and r['rsrp'] is not None:
            counts[r['site']] += 1
    return counts


def main():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    assert sha(SIM / 'sindirgi_baseline.cc') == plan['source_sha256']
    for name, h in plan['input_hashes'].items():
        assert sha(HERE / 'inputs' / name) == h, name
    targets = radio.read(HERE / 'inputs/targets.csv')
    evaluation = [t['site'] for t in targets]
    r = plan['radio']
    only = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
    workers = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 3

    def one(c):
        folder = SIM / 'results' / c['name']
        sp = HERE / f"inputs/sites_24_{c['az']}.csv"
        up = HERE / f"inputs/ues_far_{c['ue_seed']}_{c['ues']}.csv"
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
                   '--dl-earfcn', str(r['dl_earfcn']), '--udp-interval-ms', str(c['udp_interval_ms']),
                   '--name', c['name'], '--skip-build']
            print('START', c['name'], flush=True)
            with (HERE / 'logs').joinpath(c['name'] + '.log').open('w') as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
        res = json.loads((folder / 'result.json').read_text())
        m = radio.metrics(folder, c['warmup'])
        out = {'case': c, 'cached': cached, 'wall_seconds': res.get('wall_seconds'),
               'connected_ues': res.get('connected_ues'), 'ues': c['ues'],
               'ues_with_dl': sum(u['dl_bytes'] > 0 for u in m['ues']),
               'ues_per_evaluation_site': ues_per_site(m, evaluation),
               'sites': m['sites'],
               'training': ev.evaluate(m, targets, 'train'), 'control': ev.evaluate(m, targets, 'holdout')}
        if c['reproduce']:
            old = D06 / 'simulation/results' / c['reproduce']
            # Read-only: radio.metrics() would rewrite the historical metrics.json.
            previous = json.loads((old / 'metrics.json').read_text())
            assert previous['warmup_s'] == c['warmup']
            out['reproduction'] = paired_subset(previous, m)
        print('DONE', c['name'], 'train', out['training']['score'], flush=True)
        return out, m

    (HERE / 'logs').mkdir(exist_ok=True)
    cases = [c for c in plan['cases'] if only is None or c['name'] in only]
    results, metrics = [], {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(one, c) for c in cases]):
            out, m = f.result()
            results.append(out)
            metrics[out['case']['name']] = m
            save(HERE / 'checkpoint.json', {'completed': len(results), 'planned': len(cases), 'results': results})
    pairs = []
    for seed in sorted({c['ue_seed'] for c in cases}):
        sizes = sorted(c['ues'] for c in cases if c['ue_seed'] == seed)
        for a, b in zip(sizes, sizes[1:]):
            pairs.append({'ue_seed': seed, 'from_ues': a, 'to_ues': b,
                          **paired_subset(metrics[f'n{a}_draw{seed}'], metrics[f'n{b}_draw{seed}'])})
    save(HERE / 'result.json', {'completed': only is None, 'results': sorted(results, key=lambda x: (x['case']['ue_seed'], x['ues'])),
                                'paired_original_ues': pairs})
    print('COMPLETE', flush=True)


if __name__ == '__main__':
    main()
