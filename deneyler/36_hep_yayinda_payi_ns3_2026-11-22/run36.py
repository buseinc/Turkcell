"""WSL: ns-3 runs of deneyler/36 (always-on share f), deneyler/33 radio settings. --only picks cases, --build compiles first.
Cases are defined in CASES; --only picks them. --build compiles first."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
D33 = HERE.parent/'33_kesinti_ns3_2026-11-20'

D34 = HERE.parent/'34_yol_hareketi_2026-11-21'
# name: (sites file, ue file, duration s, extra run_baseline options)
CASES = {
    # check 1: f = 0, every switch off, must equal deneyler/34 results/R1_regresyon
    'R1_f0': (D33/'inputs/sites_S0TA_42.csv', D33/'inputs/ues_V25_701.csv', 1.0,
              ['--srs-periodicity', '320', '--dl-phy-traces', '1']),
    # check 2: f = 0.03 with the deneyler/34 R2_alan inputs (static users, smooth shadow + position LOS)
    'R2_f003': (D33/'inputs/sites_S0TA_42.csv', D33/'inputs/ues_V25_701.csv', 1.0,
                ['--srs-periodicity', '320', '--spatial-shadow', '1', '--spatial-los', '1', '--always-on', '0.03']),
    # check 2 as corrected in KURALLAR.md: 2 s so that ns-3 measures the cell PRB (from 1 s on)
    'R2b_f0': (D33/'inputs/sites_S0TA_42.csv', D33/'inputs/ues_V25_701.csv', 2.0,
               ['--srs-periodicity', '320', '--spatial-shadow', '1', '--spatial-los', '1']),
    'R2b_f003': (D33/'inputs/sites_S0TA_42.csv', D33/'inputs/ues_V25_701.csv', 2.0,
                 ['--srs-periodicity', '320', '--spatial-shadow', '1', '--spatial-los', '1', '--always-on', '0.03']),
}


def common():
    R = json.loads((D33/'plan.json').read_text(encoding='utf-8'))['radio']
    return ['--pathloss', R['pathloss'], '--exponent', '3', '--beamwidth', str(R['beamwidth']),
            '--enb-power', str(R['enb_power']), '--receiver-nf', str(R['receiver_nf']), '--shadow-std', '0',
            '--dl-earfcn', str(R['dl_earfcn']), '--ul-earfcn', str(R['ul_earfcn']), '--indoor-loss', str(R['indoor_loss']),
            '--downtilt', str(R['downtilt']), '--vertical-pattern', str(R['vertical_pattern']),
            '--vertical-beamwidth', str(R['vertical_beamwidth']), '--link-shadow-std', str(R['link_shadow_std']),
            '--antenna-3gpp', str(R['antenna_3gpp']), '--max-attenuation', str(R['max_attenuation']), '--evm', str(R['evm']),
            '--pf-buffer-aware', str(R['pf_buffer_aware']), '--udp-jitter', '1', '--mixed-cqi', '1',
            '--measurement-ues', '0', '--shadow-seed', '42']


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--only', required=True)
    a.add_argument('--workers', type=int, default=1)
    a.add_argument('--build', action='store_true')
    args = a.parse_args()
    (HERE/'logs').mkdir(exist_ok=True)

    def one(name):
        sites, ue, dur, extra = CASES[name]
        if (SIM/'results'/name/'result.json').exists():
            return name
        count = sum(1 for _ in Path(ue).open(encoding='utf-8')) - 1
        cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(count), '--duration', str(dur),
               '--sites-file', str(sites), '--ue-file', str(ue), '--name', name, *common(), *extra]
        if not args.build:
            cmd.append('--skip-build')
        print('START', name, time.strftime('%H:%M:%S'), flush=True)
        t0 = time.time()
        with (HERE/'logs'/f'{name}.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        print('DONE', name, f'{time.time() - t0:.0f} s', flush=True)
        return name

    names = args.only.split(',')
    if args.build:                       # compile once, before parallel runs
        one(names[0]); args.build = False; names = names[1:]
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        list(pool.map(one, names))


if __name__ == '__main__':
    main()
