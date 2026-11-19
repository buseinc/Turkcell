"""Windows: freeze the load-recalibrated runs (after calibrate.py has written calibration/calibration.json).

Predeclared design (written before any run of this experiment):
- Only change against deneyler/23 A3_TA: the load-user UDP interval uses the factor frozen by calibrate.py
  (target: KPI mean DL PRB 0.233 on draw 701 only; SINR/RSRP/CQI never used). Measured users, distance
  correction, 3GPP antenna, RMa and every other value are identical to deneyler/23.
- Regression first, same as before (new options off -> deneyler/16 regression_disabled_draw701 byte equal).
- Same decision rule as deneyler/20: becomes the reference if held-out RSRP MAE <= 3 dB and SINR MAE <= 3 dB
  averaged over draws and all 256 measured users connect in every draw.
- Chosen after seeing deneyler/23; reported as such.
"""
from pathlib import Path
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
D23 = HERE.parent/'23_uc_gpp_anten_deseni_2026-11-18'
DRAWS = [(42, 701), (7, 702), (99, 703)]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('cal', HERE/'calibrate.py')
    cal = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cal)
    c = json.loads((HERE/'calibration/calibration.json').read_text(encoding='utf-8'))
    factor = c['frozen_factor']
    cases = []
    for az, seed in DRAWS:
        out = HERE/'inputs'/f'ues_LC_TA_{seed}.csv'
        cal.write_ues(HERE/'inputs'/f'ues_DC_TA_{seed}.csv', out, factor)
        cases.append({'name': f'LC_TA_draw{seed}', 'label': 'LC_TA', 'az': az, 'ue_seed': seed,
                      'sites_file': f'sites_S0TA_{az}.csv', 'ue_file': out.name, 'shadow_seed': az})
    p23 = json.loads((D23/'plan.json').read_text(encoding='utf-8'))
    plan = {'draws': DRAWS, 'radio': p23['radio'], 'sources': dict(p23['sources'], load_factor='KPI mean DL PRB 0.233, calibrated on draw 701 (calibration/)'),
            'correction': p23['correction'], 'load_calibration': c, 'cases': cases,
            'train_sites': p23['train_sites'], 'holdout_sites': p23['holdout_sites'],
            'decision_rule': dict(p23['decision_rule'], scenario='LC_TA'), 'regression': p23['regression'],
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py']},
            'input_hashes': {p.name: sha(p) for p in sorted((HERE/'inputs').glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run of this experiment):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(len(cases), 'cases, factor', factor)


if __name__ == '__main__':
    main()
