"""WSL: regression first, then the neighbour-site check runs (resumable). Never edits earlier runs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import importlib.util
import json
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
D15 = HERE.parent/'15_ta_yerlesim_2026-11-16'
D16 = HERE.parent/'16_bina_anten_2026-11-16'
SIM = HERE/'simulation'
ARTIFACTS = ['sectors.csv', 'ues.csv', 'radio_samples.csv', 'sinr_components.csv', 'measurements.csv', 'prb_usage.csv']
SOURCES = ['sindirgi_baseline.cc', 'building-vertical-model.h', 'static-shadow-model.h', 'build_private_lte.py']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temp.replace(path)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--regression-only', action='store_true')
    args = parser.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for name, h in plan['source_hashes'].items():
        assert sha(SIM/name) == h, f'source changed after planning: {name}'
    for name, h in plan['input_hashes'].items():
        assert sha(HERE/'inputs'/name) == h, f'input changed after planning: {name}'
    previous = load_module('ta_study', D15/'study.py')
    targets = previous.radio.read(HERE/'inputs/targets.csv')
    (HERE/'logs').mkdir(exist_ok=True)
    R = plan['radio']
    MU = plan['measurement_ues']

    def run(name, sites_file, ue_file, extra, build=False, mues=256):
        key = {'name': name, 'sites': sites_file, 'ues': ue_file, 'extra': extra, 'mues': mues,
               'source_hashes': plan['source_hashes'], 'input_hashes': plan['input_hashes']}
        folder = SIM/'results'/name
        cache = folder/'experiment27_cache.json'
        if cache.exists():
            old = json.loads(cache.read_text())
            if old.get('key') == key and all((folder/n).exists() and sha(folder/n) == h for n, h in old['output_hashes'].items()):
                return folder
        manifest = SIM/'build/source_manifest.json'
        current = hashlib.sha256(b''.join((SIM/n).read_bytes() for n in SOURCES)).hexdigest()
        built = (SIM/'build/sindirgi_baseline').exists() and manifest.exists() and \
            json.loads(manifest.read_text()).get('source_sha256') == current
        count = len(previous.read(HERE/'inputs'/ue_file))
        cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(count), '--duration', '4',
               '--sites-file', str(HERE/'inputs'/sites_file), '--ue-file', str(HERE/'inputs'/ue_file),
               '--udp-jitter', '1', '--mixed-cqi', '1', '--measurement-ues', str(mues), '--name', name, *extra]
        if built or not build:
            cmd.append('--skip-build')
        print('START', name, flush=True)
        with (HERE/'logs'/f'{name}.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        save(cache, {'key': key, 'output_hashes': {n: sha(folder/n) for n in ARTIFACTS}})
        return folder

    # Same command as deneyler/16 regression: old radio, link shadowing off (new code path inactive).
    old = ['--beamwidth', '120', '--exponent', '3', '--enb-power', '49', '--receiver-nf', '9', '--shadow-std', '0',
           '--dl-earfcn', '1300', '--indoor-loss', '0', '--downtilt', '0', '--vertical-pattern', '0', '--link-shadow-std', '0']
    reg = run('regression_off_draw701', 'sites_S0TA_42.csv', 'ues_S0TA_701.csv', old, build=True)
    ref = D16/'simulation/results/regression_disabled_draw701'
    checks = {n: {'old': sha(ref/n), 'new': sha(reg/n),
                  'content_equal_after_CRLF_to_LF': (ref/n).read_bytes().replace(b'\r\n', b'\n') == (reg/n).read_bytes().replace(b'\r\n', b'\n')}
              for n in ARTIFACTS}
    passed = all(c['content_equal_after_CRLF_to_LF'] for c in checks.values())
    save(HERE/'regression.json', {'passed': passed, 'reference': str(ref.relative_to(HERE.parent)), 'files': checks})
    if not passed:
        raise RuntimeError('Regression failed; new runs forbidden')
    print('REGRESSION PASSED', flush=True)
    if args.regression_only:
        return

    new = ['--pathloss', R['pathloss'], '--exponent', '3', '--beamwidth', str(R['beamwidth']),
           '--enb-power', str(R['enb_power']), '--receiver-nf', str(R['receiver_nf']), '--shadow-std', '0',
           '--dl-earfcn', str(R['dl_earfcn']), '--ul-earfcn', str(R['ul_earfcn']), '--indoor-loss', str(R['indoor_loss']),
           '--downtilt', str(R['downtilt']), '--vertical-pattern', str(R['vertical_pattern']),
           '--vertical-beamwidth', str(R['vertical_beamwidth']), '--link-shadow-std', str(R['link_shadow_std']),
           '--antenna-3gpp', str(R['antenna_3gpp']), '--max-attenuation', str(R['max_attenuation']), '--evm', str(R['evm'])]

    def one(case):
        folder = run(case['name'], case['sites_file'], case['ue_file'], new + ['--shadow-seed', str(case['shadow_seed'])], mues=MU)
        full = previous.radio.metrics(folder, 1)
        metrics = previous.measurement_metrics(full, MU)
        measured = [u for u in full['ues'] if u['ue_id'] < MU]
        prb = previous.read(folder/'prb_usage.csv')
        sites = metrics['sites']
        return {'case': case, 'sites': sites,
                'missing_sites': sorted(set(plan['train_sites'] + plan['holdout_sites'] + plan['neighbour_sites']) - set(sites)),
                'training': previous.ev.evaluate(metrics, targets, 'train'),
                'control': previous.ev.evaluate(metrics, targets, 'holdout'),
                'neighbour': previous.ev.evaluate(metrics, targets, 'neighbour'),
                'measurement_connected': sum(bool(u['connected']) for u in measured),
                'measurement_with_dl': sum(u['dl_bytes'] > 0 for u in measured),
                'prb_mean_achieved': statistics.mean(float(r['dl_prb_utilization']) for r in prb)}

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(one, c) for c in plan['cases']]
        for f in as_completed(futures):
            results.append(f.result())
            save(HERE/'checkpoint.json', {'completed': len(results), 'planned': len(futures), 'results': results})
            print('DONE', results[-1]['case']['name'], flush=True)
    save(HERE/'result.json', {'completed': True, 'results': sorted(results, key=lambda r: r['case']['name'])})


if __name__ == '__main__':
    main()
