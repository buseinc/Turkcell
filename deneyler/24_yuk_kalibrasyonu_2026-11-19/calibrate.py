"""WSL: find the load factor for the deneyler/23 radio setup so that mean DL PRB matches the KPI target.

Predeclared calibration rule (written before any run of this experiment):
- Context: the load factor 1.47 was calibrated in deneyler/14 for the old S0 radio. With the deneyler/23 radio
  (RMa + distance correction + 3GPP antenna) the same load gives mean DL PRB 0.197 / 0.198 / 0.199, below the
  KPI daily-mean target 0.233 (deneyler/09). Lower load means less interference. Chosen after seeing
  deneyler/23 and reported as such.
- Target is the measured load only: mean DL PRB = 0.233. SINR, RSRP or CQI are NOT used in the calibration.
- Same method as deneyler/14: only draw 701 (azimuth 42) is used. Load-user UDP interval = factor / 0.233 ms
  (only kind=load rows change; measured users and everything else are copied from deneyler/23 inputs).
  Round 1: factor = 1.47 * 0.19706 / 0.233 (proportional step from the deneyler/23 draw-701 PRB).
  If round-1 PRB is within 0.233 +/- 5 % the factor is frozen; otherwise one more proportional step
  (factor * PRB_round1 / 0.233) is taken and frozen without checking further. At most two rounds.
- The frozen factor is then used for all three draws by prepare.py / study.py; the decision rule is unchanged.
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
D23 = HERE.parent/'23_uc_gpp_anten_deseni_2026-11-18'
TARGET, OLD, PRB23_701 = 0.233, 1.47, 0.19705555555554582


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
    R = json.loads((D23/'plan.json').read_text(encoding='utf-8'))['radio']
    ue = CAL/f'ues_{name}.csv'
    n = write_ues(HERE/'inputs/ues_DC_TA_701.csv', ue, factor)
    cmd = [sys.executable, str(SIM/'run_baseline.py'), '--sites', '0', '--ues', str(n), '--duration', '4',
           '--sites-file', str(HERE/'inputs/sites_S0TA_42.csv'), '--ue-file', str(ue),
           '--udp-jitter', '1', '--mixed-cqi', '1', '--measurement-ues', '256', '--name', name,
           '--pathloss', R['pathloss'], '--exponent', '3', '--beamwidth', str(R['beamwidth']),
           '--enb-power', str(R['enb_power']), '--receiver-nf', str(R['receiver_nf']), '--shadow-std', '0',
           '--dl-earfcn', str(R['dl_earfcn']), '--ul-earfcn', str(R['ul_earfcn']), '--indoor-loss', str(R['indoor_loss']),
           '--downtilt', str(R['downtilt']), '--vertical-pattern', str(R['vertical_pattern']),
           '--vertical-beamwidth', str(R['vertical_beamwidth']), '--link-shadow-std', str(R['link_shadow_std']),
           '--antenna-3gpp', str(R['antenna_3gpp']), '--max-attenuation', str(R['max_attenuation']),
           '--shadow-seed', '42', '--skip-build']
    with (CAL/f'{name}.log').open('w') as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (SIM/'results'/name/'prb_usage.csv').open() as f:
        return statistics.mean(float(r['dl_prb_utilization']) for r in csv.DictReader(f))


def main():
    rounds = []
    f1 = OLD * PRB23_701 / TARGET
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
