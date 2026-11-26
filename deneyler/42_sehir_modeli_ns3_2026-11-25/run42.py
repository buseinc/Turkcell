"""WSL: ns-3 runs of experiment 42 (KURALLAR.md). --only picks cases (comma list), --build compiles first.
K1: signal power, no traffic (signal quality is not run separately, KURALLAR.md)."""
from pathlib import Path
import argparse
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
SITES, UES = HERE/'inputs/sites_42.csv', HERE/'inputs/ues_42.csv'

RADIO = ['--pathloss', 'env', '--enb-height', '25', '--spatial-shadow', '1', '--spatial-los', '1',
         '--shadow-spacing', '50', '--los-spacing', '50', '--link-shadow-std', '0', '--shadow-std', '0',
         '--enb-power', '49', '--receiver-nf', '9', '--dl-earfcn', '1651', '--ul-earfcn', '19651',
         '--beamwidth', '65', '--downtilt', '6', '--vertical-pattern', '1', '--vertical-beamwidth', '10',
         '--antenna-3gpp', '1', '--max-attenuation', '25', '--evm', '0.08', '--always-on', '0.048',
         '--pf-buffer-aware', '1', '--mixed-cqi', '1', '--udp-jitter', '1', '--srs-periodicity', '320',
         '--indoor-loss', '0', '--measurement-ues', '0', '--shadow-seed', '42']
# name: (duration s, traffic)
CASES = {'K1': (1.0, 0)}   # scenario minimum 1 s


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--only', required=True)
    a.add_argument('--build', action='store_true')
    args = a.parse_args()
    (HERE/'logs').mkdir(exist_ok=True)
    for i, name in enumerate(args.only.split(',')):
        if (SIM/'results'/name/'result.json').exists():
            print('skip (done)', name)
            continue
        dur, traffic = CASES[name]
        count = sum(1 for _ in UES.open(encoding='utf-8')) - 1
        cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(count), '--duration', str(dur),
               '--sites-file', str(SITES), '--ue-file', str(UES), '--name', name, '--traffic', str(traffic), *RADIO]
        if not (args.build and i == 0):
            cmd.append('--skip-build')
        print('START', name, time.strftime('%H:%M:%S'), flush=True)
        t0 = time.time()
        with (HERE/'logs'/f'{name}.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        print('DONE', name, f'{time.time() - t0:.0f} s', flush=True)


if __name__ == '__main__':
    main()
