"""WSL: step 3 of deneyler/29 - validation (A) and voice-capacity (B) runs from plan.json (resumable).

Usage: python3 study.py --part validation [--workers 3]
       python3 study.py --part stress --only V25_draw701,V50_draw701 [--workers 2]
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import importlib.util
import json
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
D15 = HERE.parent/'15_ta_yerlesim_2026-11-16'
SIM = HERE/'simulation'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(path, value):
    t = path.with_suffix('.tmp')
    t.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    t.replace(path)


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--part', choices=['validation', 'stress'], required=True)
    p.add_argument('--only')
    p.add_argument('--workers', type=int, default=1)
    args = p.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    assert json.loads((HERE/'regression.json').read_text())['passed'], 'regression not passed'
    for n, h in plan['source_hashes'].items():
        assert sha(SIM/n) == h, f'source changed after planning: {n}'
    for n, h in plan['input_hashes'].items():
        assert sha(HERE/'inputs'/n) == h, f'input changed after planning: {n}'
    (HERE/'logs').mkdir(exist_ok=True)
    R = plan['radio']
    new = ['--pathloss', R['pathloss'], '--exponent', '3', '--beamwidth', str(R['beamwidth']),
           '--enb-power', str(R['enb_power']), '--receiver-nf', str(R['receiver_nf']), '--shadow-std', '0',
           '--dl-earfcn', str(R['dl_earfcn']), '--ul-earfcn', str(R['ul_earfcn']), '--indoor-loss', str(R['indoor_loss']),
           '--downtilt', str(R['downtilt']), '--vertical-pattern', str(R['vertical_pattern']),
           '--vertical-beamwidth', str(R['vertical_beamwidth']), '--link-shadow-std', str(R['link_shadow_std']),
           '--antenna-3gpp', str(R['antenna_3gpp']), '--max-attenuation', str(R['max_attenuation']), '--evm', str(R['evm']),
           '--pf-buffer-aware', str(R['pf_buffer_aware'])]

    def run(c, extra, mues):
        folder = SIM/'results'/c['name']
        if (folder/'result.json').exists() and (folder/'ues.csv').exists():
            return folder
        ue = HERE/'inputs'/c['ue_file']
        with ue.open(encoding='utf-8-sig') as f:
            count = sum(1 for _ in f) - 1
        cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(count), '--duration', '4',
               '--sites-file', str(HERE/'inputs'/c['sites_file']), '--ue-file', str(ue), '--udp-jitter', '1',
               '--mixed-cqi', '1', '--measurement-ues', mues, '--name', c['name'], *new, *extra,
               '--shadow-seed', str(c['shadow_seed']), '--skip-build']
        print('START', c['name'], time.strftime('%H:%M:%S'), flush=True)
        t0 = time.time()
        with (HERE/'logs'/f'{c["name"]}.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        print('DONE', c['name'], f'{time.time() - t0:.0f} s', flush=True)
        return folder

    if args.part == 'validation':
        prev = module('ta_study', D15/'study.py')
        targets = prev.radio.read(HERE/'inputs/targets.csv')

        def one(c):
            folder = run(c, [], '256')
            full = prev.radio.metrics(folder, 1)
            metrics = prev.measurement_metrics(full, 256)
            measured = [u for u in full['ues'] if u['ue_id'] < 256]
            prb = prev.read(folder/'prb_usage.csv')
            return {'case': c, 'training': prev.ev.evaluate(metrics, targets, 'train'),
                    'control': prev.ev.evaluate(metrics, targets, 'holdout'),
                    'measurement_connected': sum(bool(u['connected']) for u in measured),
                    'prb_mean_achieved': statistics.mean(float(r['dl_prb_utilization']) for r in prb)}

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            results = list(pool.map(one, plan['validation_cases']))
        save(HERE/'result.json', {'completed': True, 'results': results})
        for r in results:
            print(r['case']['name'], 'holdout', {k: round(v, 2) for k, v in r['control']['mae_db'].items()},
                  'train', {k: round(v, 2) for k, v in r['training']['mae_db'].items()},
                  'connected', r['measurement_connected'], 'PRB', round(r['prb_mean_achieved'], 3))
    else:
        only = set(args.only.split(',')) if args.only else None
        cases = [c for c in plan['cases'] if only is None or c['name'] in only]
        srs = ['--srs-periodicity', str(plan['stress_srs_periodicity'])]
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            list(pool.map(lambda c: run(c, srs, '0'), cases))


if __name__ == '__main__':
    main()
