"""WSL: re-calibrate the load factor for the full sourced model of deneyler/26 (step 2).

Predeclared calibration rule (written before any run of this experiment):
- Radio: deneyler/24 (RMa, 3GPP antenna, 8 dB shadow, ...) + transmitter EVM 8 % (3GPP TS 36.104) + the
  distance correction re-derived by correction.py (inputs/ues_EC_TA_*.csv). EVM lowers SINR and therefore
  spectral efficiency, so the load giving KPI PRB changes.
- Target is the measured load only: mean DL PRB = 0.233. SINR, RSRP or CQI are NOT used.
- Same method as deneyler/14 and /24: only draw 701. Load-user UDP interval = factor / 0.233 ms.
  Round 1: factor = 1.2432 (the deneyler/24 factor). If round-1 PRB is within 0.233 +/- 5 % it is frozen;
  otherwise one proportional step (factor * PRB_round1 / 0.233) is taken and frozen without further checks.
"""
from pathlib import Path
import csv
import json
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
CAL = HERE/'calibration'
D24 = HERE.parent/'24_yuk_kalibrasyonu_2026-11-19'
TARGET, START = 0.233, 1.2432260371959327


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


def run(name, factor):
    R = json.loads((D24/'plan.json').read_text(encoding='utf-8'))['radio']
    ue = CAL/f'ues_{name}.csv'
    n = write_ues(HERE/'inputs/ues_EC_TA_701.csv', ue, factor)
    cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(n), '--duration', '4',
           '--sites-file', str(HERE/'inputs/sites_S0TA_42.csv'), '--ue-file', str(ue),
           '--udp-jitter', '1', '--mixed-cqi', '1', '--measurement-ues', '256', '--name', name,
           '--pathloss', R['pathloss'], '--exponent', '3', '--beamwidth', str(R['beamwidth']),
           '--enb-power', str(R['enb_power']), '--receiver-nf', str(R['receiver_nf']), '--shadow-std', '0',
           '--dl-earfcn', str(R['dl_earfcn']), '--ul-earfcn', str(R['ul_earfcn']), '--indoor-loss', str(R['indoor_loss']),
           '--downtilt', str(R['downtilt']), '--vertical-pattern', str(R['vertical_pattern']),
           '--vertical-beamwidth', str(R['vertical_beamwidth']), '--link-shadow-std', str(R['link_shadow_std']),
           '--antenna-3gpp', str(R['antenna_3gpp']), '--max-attenuation', str(R['max_attenuation']),
           '--evm', '0.08', '--shadow-seed', '42', '--skip-build']
    with (CAL/f'{name}.log').open('w') as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (SIM/'results'/name/'prb_usage.csv').open() as f:
        return statistics.mean(float(r['dl_prb_utilization']) for r in csv.DictReader(f))


def main():
    rounds = []
    f1 = START
    p1 = run('cal_round1_draw701', f1)
    rounds.append({'factor': f1, 'prb': p1})
    print('round1', f1, p1, flush=True)
    frozen = f1
    if abs(p1 / TARGET - 1) > 0.05:
        frozen = f1 * p1 / TARGET
        p2 = run('cal_round2_draw701', frozen)
        rounds.append({'factor': frozen, 'prb': p2})
        print('round2', frozen, p2, flush=True)
    (CAL/'calibration.json').write_text(json.dumps({'target_prb': TARGET, 'rounds': rounds, 'frozen_factor': frozen,
                                                    'rule': __doc__.split('(written before any run of this experiment):')[1].strip()},
                                                   indent=2), encoding='utf-8')
    print('frozen', frozen)


if __name__ == '__main__':
    main()
