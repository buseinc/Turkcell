"""Windows: freeze the full sourced model runs of deneyler/26 (step 3, after correction.py and calibrate.py).

Predeclared design (written before any run of this experiment):
- Model: RMa (3GPP TR 38.901), 1850 MHz B3, 49 dBm, 65 deg / 15 dBi with the 3GPP TR 36.814 pattern
  (Am 25 dB, SLAv 20 dB, 6 deg tilt, 10 deg vertical), 8 dB link shadow, NF 9 dB, TA placement,
  transmitter EVM 8 % (3GPP TS 36.104 Table 6.5.2-1, 64QAM) inside the simulator's SINR,
  distance correction re-derived for this antenna by correction.py (deneyler/22 method),
  load factor frozen by calibrate.py (KPI PRB 0.233 on draw 701 only).
- Chosen after seeing deneyler/20-25 (in particular the EVM ceiling of deneyler/25); reported as such.
  No value is fitted to the SINR or RSRP of the evaluation sites.
- Regression first: with EVM 0 and the new options off the simulator (linked to the private patched
  libns3-lte) must reproduce deneyler/16 regression_disabled_draw701 byte for byte (after CRLF->LF).
- Same decision rule as deneyler/20: becomes the reference if held-out RSRP MAE <= 3 dB and SINR MAE <= 3 dB
  averaged over draws and all 256 measured users connect in every draw.
"""
from pathlib import Path
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
D24 = HERE.parent/'24_yuk_kalibrasyonu_2026-11-19'
DRAWS = [(42, 701), (7, 702), (99, 703)]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('cal', HERE/'calibrate.py')
    cal = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cal)
    c = json.loads((HERE/'calibration/calibration.json').read_text(encoding='utf-8'))
    corr = json.loads((HERE/'correction.json').read_text(encoding='utf-8'))
    factor = c['frozen_factor']
    cases = []
    for az, seed in DRAWS:
        out = HERE/'inputs'/f'ues_FT_TA_{seed}.csv'
        cal.write_ues(HERE/'inputs'/f'ues_EC_TA_{seed}.csv', out, factor)
        cases.append({'name': f'FT_TA_draw{seed}', 'label': 'FT_TA', 'az': az, 'ue_seed': seed,
                      'sites_file': f'sites_S0TA_{az}.csv', 'ue_file': out.name, 'shadow_seed': az})
    p24 = json.loads((D24/'plan.json').read_text(encoding='utf-8'))
    plan = {'draws': DRAWS, 'radio': dict(p24['radio'], evm=0.08),
            'sources': dict(p24['sources'], evm='3GPP TS 36.104 Table 6.5.2-1, 64QAM EVM 8 %',
                            distance_correction='deneyler/22 method re-derived for the 3GPP antenna (correction.py)',
                            load_factor='KPI mean DL PRB 0.233, calibrated on draw 701 (calibration/)'),
            'correction': corr, 'load_calibration': c, 'cases': cases,
            'train_sites': p24['train_sites'], 'holdout_sites': p24['holdout_sites'],
            'decision_rule': dict(p24['decision_rule'], scenario='FT_TA'), 'regression': p24['regression'],
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py', 'build_private_lte.py']},
            'input_hashes': {p.name: sha(p) for p in sorted((HERE/'inputs').glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run of this experiment):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(len(cases), 'cases, factor', factor)


if __name__ == '__main__':
    main()
