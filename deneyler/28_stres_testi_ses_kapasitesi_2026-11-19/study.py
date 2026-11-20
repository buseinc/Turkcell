"""WSL: regression first, then the voice-capacity stress steps (resumable). Never edits earlier runs.

Usage: python3 study.py [--only V100_draw701,...] [--duration 4] [--workers 1] [--regression-only]
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
D16 = HERE.parent/'16_bina_anten_2026-11-16'
SIM = HERE/'simulation'
ARTIFACTS = ['sectors.csv', 'ues.csv', 'radio_samples.csv', 'sinr_components.csv', 'measurements.csv', 'prb_usage.csv']
SOURCES = ['sindirgi_baseline.cc', 'building-vertical-model.h', 'static-shadow-model.h', 'build_private_lte.py']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)


def rows(path):
    with path.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--only')
    p.add_argument('--duration', default='4')
    p.add_argument('--workers', type=int, default=1)
    p.add_argument('--regression-only', action='store_true')
    args = p.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for name, h in plan['source_hashes'].items():
        assert sha(SIM/name) == h, f'source changed after planning: {name}'
    for name, h in plan['input_hashes'].items():
        assert sha(HERE/'inputs'/name) == h, f'input changed after planning: {name}'
    (HERE/'logs').mkdir(exist_ok=True)
    R = plan['radio']

    def run(name, sites_file, ue_file, extra, build=False, duration='4', mues='0'):
        folder = SIM/'results'/name
        manifest = SIM/'build/source_manifest.json'
        current = hashlib.sha256(b''.join((SIM/n).read_bytes() for n in SOURCES)).hexdigest()
        built = (SIM/'build/sindirgi_baseline').exists() and manifest.exists() and \
            json.loads(manifest.read_text()).get('source_sha256') == current
        if (folder/'result.json').exists() and (folder/'ues.csv').exists():
            return folder
        count = len(rows(HERE/'inputs'/ue_file))
        cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(count), '--duration', duration,
               '--sites-file', str(HERE/'inputs'/sites_file), '--ue-file', str(HERE/'inputs'/ue_file),
               '--udp-jitter', '1', '--mixed-cqi', '1', '--measurement-ues', mues, '--name', name, *extra]
        if built or not build:
            cmd.append('--skip-build')
        print('START', name, time.strftime('%H:%M:%S'), flush=True)
        t0 = time.time()
        with (HERE/'logs'/f'{name}.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        print('DONE', name, f'{time.time() - t0:.0f} s', flush=True)
        return folder

    old = ['--beamwidth', '120', '--exponent', '3', '--enb-power', '49', '--receiver-nf', '9', '--shadow-std', '0',
           '--dl-earfcn', '1300', '--indoor-loss', '0', '--downtilt', '0', '--vertical-pattern', '0', '--link-shadow-std', '0']
    reg = run('regression_off_draw701', 'sites_S0TA_42.csv', 'ues_S0TA_701.csv', old, build=True, mues='256')
    ref = D16/'simulation/results/regression_disabled_draw701'
    checks = {n: (ref/n).read_bytes().replace(b'\r\n', b'\n') == (reg/n).read_bytes().replace(b'\r\n', b'\n') for n in ARTIFACTS}
    save(HERE/'regression.json', {'passed': all(checks.values()), 'reference': str(ref.relative_to(HERE.parent)), 'files': checks})
    if not all(checks.values()):
        raise RuntimeError('Regression failed; new runs forbidden')
    print('REGRESSION PASSED', flush=True)
    if args.regression_only:
        return

    new = ['--pathloss', R['pathloss'], '--exponent', '3', '--beamwidth', str(R['beamwidth']),
           '--enb-power', str(R['enb_power']), '--receiver-nf', str(R['receiver_nf']), '--shadow-std', '0',
           '--dl-earfcn', str(R['dl_earfcn']), '--ul-earfcn', str(R['ul_earfcn']), '--indoor-loss', str(R['indoor_loss']),
           '--downtilt', str(R['downtilt']), '--vertical-pattern', str(R['vertical_pattern']),
           '--vertical-beamwidth', str(R['vertical_beamwidth']), '--link-shadow-std', str(R['link_shadow_std']),
           '--antenna-3gpp', str(R['antenna_3gpp']), '--max-attenuation', str(R['max_attenuation']), '--evm', str(R['evm']),
           '--srs-periodicity', str(R['srs_periodicity'])]
    only = set(args.only.split(',')) if args.only else None
    cases = [c for c in plan['cases'] if only is None or c['name'] in only]
    suffix = '' if args.duration == '4' else f'_smoke{args.duration}s'

    def one(c):
        return run(c['name'] + suffix, c['sites_file'], c['ue_file'], new + ['--shadow-seed', str(c['shadow_seed'])],
                   duration=args.duration)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        list(pool.map(one, cases))


if __name__ == '__main__':
    main()
