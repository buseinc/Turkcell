"""WSL: ns-3 runs of deneyler/34 with the deneyler/33 radio settings (plan.json of 33).
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

# name: (sites file, ue file, duration s, extra run_baseline options)
CASES = {
    # acceptance 1: switches off, must equal deneyler/33 results/L25_smoke (1 s)
    'R1_regresyon': (D33/'inputs/sites_S0TA_42.csv', D33/'inputs/ues_V25_701.csv', 1.0,
                     ['--srs-periodicity', '320', '--dl-phy-traces', '1']),
    # acceptance 2: switches on, static users; ns-3 RSRP must equal alan.Network34
    'R2_alan': (D33/'inputs/sites_S0TA_42.csv', D33/'inputs/ues_V25_701.csv', 1.0,
                ['--srs-periodicity', '320', '--spatial-shadow', '1', '--spatial-los', '1']),
}
_CORR = json.loads((HERE/'inputs/corr.json').read_text()) if (HERE/'inputs/corr.json').exists() else {'k0': 0, 'k1': 0}
_MOVE = ['--spatial-shadow', '1', '--spatial-los', '1', '--waypoints', str(HERE/'inputs/waypoints_test.csv'),
         '--corr-sites', str(HERE/'inputs/corr_sites.csv'), '--corr-k0', repr(_CORR['k0']), '--corr-k1', repr(_CORR['k1'])]
# acceptance 5 (as deneyler/19): one UE drives 441 -> 443, handover on and off
CASES['R5_ho_acik'] = (HERE/'inputs/sites_pair_42.csv', HERE/'inputs/ues_hareket_test.csv', 102.409, _MOVE + ['--handover', '1'])
CASES['R5_ho_kapali'] = (HERE/'inputs/sites_pair_42.csv', HERE/'inputs/ues_hareket_test.csv', 102.409, _MOVE)
# step 3b road runs (hazirla_yol.py, yol_plan.json)
_YP = json.loads((HERE/'yol_plan.json').read_text(encoding='utf-8')) if (HERE/'yol_plan.json').exists() else {'cases': {}}


def _road(name, wp, dur):
    return (HERE/f'inputs/{name}_sites.csv', HERE/f'inputs/{name}_ues.csv', dur,
            ['--srs-periodicity', '320', '--spatial-shadow', '1', '--spatial-los', '1', '--handover', '1', '--waypoints', str(wp),
             '--corr-sites', str(HERE/'inputs/corr_sites.csv'), '--corr-k0', repr(_CORR['k0']), '--corr-k1', repr(_CORR['k1'])])


for _n, _c in _YP['cases'].items():
    CASES[_n] = _road(_n, HERE/f'inputs/{_n}_waypoints.csv', _c['duration_s'])
CASES['S_A_K2'] = _road('Y_A_K2', HERE/'inputs/S_A_K2_waypoints.csv', 3.0)   # smoke: first 3 s, for timing


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
