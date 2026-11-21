"""WSL: run the frozen deneyler/33 cases with ns-3 (prepare.py first). --smoke runs K0 for 1.5 s only."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--only', default='K0,K1,K2,K3,L25')
    a.add_argument('--workers', type=int, default=5)
    a.add_argument('--smoke', action='store_true')
    a.add_argument('--smoke-duration', type=float, default=1.5)
    a.add_argument('--build', action='store_true', help='compile the scenario binary (first run only)')
    args = a.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for n, h in plan['source_hashes'].items():
        assert sha(SIM/n) == h, f'source changed after planning: {n}'
    for n, h in plan['input_hashes'].items():
        assert sha(HERE/'inputs'/n) == h, f'input changed after planning: {n}'
    R = plan['radio']
    common = ['--pathloss', R['pathloss'], '--exponent', '3', '--beamwidth', str(R['beamwidth']),
              '--enb-power', str(R['enb_power']), '--receiver-nf', str(R['receiver_nf']), '--shadow-std', '0',
              '--dl-earfcn', str(R['dl_earfcn']), '--ul-earfcn', str(R['ul_earfcn']), '--indoor-loss', str(R['indoor_loss']),
              '--downtilt', str(R['downtilt']), '--vertical-pattern', str(R['vertical_pattern']),
              '--vertical-beamwidth', str(R['vertical_beamwidth']), '--link-shadow-std', str(R['link_shadow_std']),
              '--antenna-3gpp', str(R['antenna_3gpp']), '--max-attenuation', str(R['max_attenuation']), '--evm', str(R['evm']),
              '--pf-buffer-aware', str(R['pf_buffer_aware']), '--udp-jitter', '1', '--mixed-cqi', '1',
              '--measurement-ues', '0', '--shadow-seed', '42']
    cases = {k: (v['sites_file'], v['ue_file'], ['--srs-periodicity', str(plan['srs_periodicity'])])
             for k, v in plan['scenarios'].items()}
    lc = plan['link_check']
    cases['L25'] = (lc['sites_file'], lc['ue_file'], ['--srs-periodicity', '320', '--dl-phy-traces', '1'])
    names = ['K0'] if args.smoke and args.only == 'K0,K1,K2,K3,L25' else args.only.split(',')
    (HERE/'logs').mkdir(exist_ok=True)

    def one(n):
        sites, uef, extra = cases[n]
        name = n + ('_smoke' if args.smoke else '')
        folder = SIM/'results'/name
        if (folder/'result.json').exists() and (folder/'ues.csv').exists():
            return name
        ue = HERE/'inputs'/uef
        count = sum(1 for _ in ue.open(encoding='utf-8')) - 1
        cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(count),
               '--duration', str(args.smoke_duration) if args.smoke else '4', '--sites-file', str(HERE/'inputs'/sites), '--ue-file', str(ue),
               '--name', name, *common, *extra] + ([] if args.build else ['--skip-build'])
        print('START', name, time.strftime('%H:%M:%S'), flush=True)
        t0 = time.time()
        with (HERE/'logs'/f'{name}.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        print('DONE', name, f'{time.time() - t0:.0f} s', flush=True)
        return name

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        list(pool.map(one, names))


if __name__ == '__main__':
    main()
