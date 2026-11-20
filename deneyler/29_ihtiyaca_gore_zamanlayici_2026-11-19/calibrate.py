"""WSL: step 1 of deneyler/29 - regression, then re-calibrate the load factor with the buffer-aware scheduler.

Why this experiment exists (deneyler/28, V25 step): ns-3's PF scheduler gives a UE every free RBG as long as
it has any data, so one 72-byte voice packet can occupy the whole 10 MHz band. In V25 the evaluation cells
looked 93 % busy, neighbours interfered on all RBs, median SINR of the voice users fell from 17 dB
(deneyler/26, normal load) to 6 dB and 21 % of them were below 0 dB (Experia hourly records: ~1 %).
A real eNB gives a voice packet 1-2 PRBs. Fix: the private libns3-lte gets a buffer-aware PF
(build_private_lte.py, patch 3, flag --pf-buffer-aware 1). Everything else is the deneyler/26 model.

Predeclared rule (written before any run of this experiment):
- Regression: with all new options off the simulator (linked to the private lib with three patches) must
  reproduce deneyler/16 regression_disabled_draw701 byte for byte (after CRLF->LF). Otherwise stop.
- Calibration: the scheduler change lowers the PRB a given traffic needs, so the load factor of deneyler/26
  (1.2432, KPI PRB 0.233) no longer gives the KPI load. Target is the measured load only: mean DL PRB 0.233
  on draw 701 (same inputs and method as deneyler/26: ues_EC_TA_701, load interval = factor / target_prb).
  SINR, RSRP and CQI are NOT used. Round 1 uses 1.2432; while |PRB/0.233 - 1| > 5 % a proportional step
  factor * PRB / 0.233 is taken, at most 4 rounds; the first round within 5 % is frozen, else the last.
"""
from pathlib import Path
import csv
import hashlib
import json
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
CAL = HERE/'calibration'
D16 = HERE.parent/'16_bina_anten_2026-11-16'
D26 = HERE.parent/'26_kaynakli_tam_model_2026-11-19'
ARTIFACTS = ['sectors.csv', 'ues.csv', 'radio_samples.csv', 'sinr_components.csv', 'measurements.csv', 'prb_usage.csv']
TARGET, START, MAX_ROUNDS = 0.233, 1.2432260371959327, 4
R = json.loads((D26/'plan.json').read_text(encoding='utf-8'))['radio']
NEW = ['--pathloss', R['pathloss'], '--exponent', '3', '--beamwidth', str(R['beamwidth']),
       '--enb-power', str(R['enb_power']), '--receiver-nf', str(R['receiver_nf']), '--shadow-std', '0',
       '--dl-earfcn', str(R['dl_earfcn']), '--ul-earfcn', str(R['ul_earfcn']), '--indoor-loss', str(R['indoor_loss']),
       '--downtilt', str(R['downtilt']), '--vertical-pattern', str(R['vertical_pattern']),
       '--vertical-beamwidth', str(R['vertical_beamwidth']), '--link-shadow-std', str(R['link_shadow_std']),
       '--antenna-3gpp', str(R['antenna_3gpp']), '--max-attenuation', str(R['max_attenuation']), '--evm', str(R['evm']),
       '--pf-buffer-aware', '1']


def write_ues(src, dst, factor):
    with src.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r['kind'] == 'load':
            r['udp_interval_ms'] = f'{factor / float(r["target_prb"]):.6f}'
    with dst.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def simulate(name, sites, ue_file, extra, log, build=False, mues='256', duration='4'):
    with ue_file.open(encoding='utf-8-sig') as f:
        n = sum(1 for _ in f) - 1
    cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(n), '--duration', duration,
           '--sites-file', str(sites), '--ue-file', str(ue_file), '--udp-jitter', '1', '--mixed-cqi', '1',
           '--measurement-ues', mues, '--name', name, *extra]
    if not build:
        cmd.append('--skip-build')
    with log.open('w') as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
    return SIM/'results'/name


def regression():
    old = ['--beamwidth', '120', '--exponent', '3', '--enb-power', '49', '--receiver-nf', '9', '--shadow-std', '0',
           '--dl-earfcn', '1300', '--indoor-loss', '0', '--downtilt', '0', '--vertical-pattern', '0', '--link-shadow-std', '0']
    reg = SIM/'results/regression_off_draw701'
    if not (reg/'prb_usage.csv').exists():
        simulate('regression_off_draw701', HERE/'inputs/sites_S0TA_42.csv', HERE/'inputs/ues_S0TA_701.csv', old,
                 CAL/'regression.log', build=True)
    ref = D16/'simulation/results/regression_disabled_draw701'
    checks = {n: (ref/n).read_bytes().replace(b'\r\n', b'\n') == (reg/n).read_bytes().replace(b'\r\n', b'\n') for n in ARTIFACTS}
    (HERE/'regression.json').write_text(json.dumps({'passed': all(checks.values()), 'reference': str(ref.relative_to(HERE.parent)),
                                                     'files': checks}, indent=2), encoding='utf-8')
    if not all(checks.values()):
        raise RuntimeError('Regression failed; new runs forbidden')
    print('REGRESSION PASSED', flush=True)


def main():
    CAL.mkdir(exist_ok=True)
    regression()
    rounds, factor, frozen = [], START, None
    for k in range(1, MAX_ROUNDS + 1):
        name = f'cal_round{k}_draw701'
        ue = CAL/f'ues_{name}.csv'
        write_ues(HERE/'inputs/ues_EC_TA_701.csv', ue, factor)
        res = simulate(name, HERE/'inputs/sites_S0TA_42.csv', ue, NEW + ['--shadow-seed', '42'], CAL/f'{name}.log')
        with (res/'prb_usage.csv').open() as f:
            prb = statistics.mean(float(r['dl_prb_utilization']) for r in csv.DictReader(f))
        rounds.append({'factor': factor, 'prb': prb})
        print(name, factor, prb, flush=True)
        if abs(prb/TARGET - 1) <= 0.05:
            frozen = factor
            break
        factor = factor*prb/TARGET
    if frozen is None:
        frozen = rounds[-1]['factor']
    (CAL/'calibration.json').write_text(json.dumps({'target_prb': TARGET, 'rounds': rounds, 'frozen_factor': frozen,
                                                    'within_5_percent': abs(rounds[-1]['prb']/TARGET - 1) <= 0.05,
                                                    'rule': __doc__.split('(written before any run of this experiment):')[1].strip()},
                                                   indent=2), encoding='utf-8')
    print('frozen', frozen)


if __name__ == '__main__':
    main()
