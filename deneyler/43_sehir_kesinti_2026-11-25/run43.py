"""WSL: ns-3 runs of experiment 43 (KURALLAR.md), 15:30, draw 42. Uses experiment 42's scenario and private lib.
N_C0: no outage. N_C2: 087 + 108 left out. --only picks cases (comma list)."""
from pathlib import Path
import argparse
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SIM = HERE.parent/'42_sehir_modeli_ns3_2026-11-25'/'simulation'
sys.path.insert(0, str(HERE.parent/'42_sehir_modeli_ns3_2026-11-25'))
from run42 import RADIO  # noqa: E402  (same radio settings as experiment 42)

UES = HERE/'inputs/ues_43.csv'
CASES = {'N_C0': (HERE/'inputs/sites_C0.csv', 1.0), 'N_C2': (HERE/'inputs/sites_C2.csv', 1.0)}   # scenario minimum 1 s


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--only', required=True)
    args = a.parse_args()
    (HERE/'logs').mkdir(exist_ok=True)
    for name in args.only.split(','):
        if (SIM/'results'/name/'result.json').exists():
            print('skip (done)', name)
            continue
        sites, dur = CASES[name]
        count = sum(1 for _ in UES.open(encoding='utf-8')) - 1
        cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(count), '--duration', str(dur),
               '--sites-file', str(sites), '--ue-file', str(UES), '--name', name, '--traffic', '1', *RADIO, '--skip-build']
        print('START', name, time.strftime('%H:%M:%S'), flush=True)
        t0 = time.time()
        with (HERE/'logs'/f'{name}.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        print('DONE', name, f'{time.time() - t0:.0f} s', flush=True)


if __name__ == '__main__':
    main()
