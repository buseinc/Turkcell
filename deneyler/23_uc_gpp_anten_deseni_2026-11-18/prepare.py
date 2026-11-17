"""Windows: freeze the 3GPP antenna-pattern follow-up of deneyler/22.

Predeclared design (written before any run of this experiment):
- Context: in deneyler/22 the data-derived distance correction brought RSRP close to Experia (held-out MAE
  3.5 dB, median identical) but SINR stayed ~8 dB too high: too little interference. The ns-3 cosine antenna
  used since deneyler/20 has no back/side-lobe floor, so interference from the back and sides of neighbouring
  sectors is attenuated without limit. This choice is made AFTER seeing deneyler/22 and is reported as such.
- Only change against deneyler/22 DC_TA: the eNB antenna pattern is the 3GPP TR 36.814 Table A.2.1.1-2
  macro pattern, applied per link (DL and UL, all users incl. load users):
      A_H = min(12 (phi/65)^2, 25),  A_V = min(12 ((theta - 6)/10)^2, 20),  A = min(A_H + A_V, 25) dB
  with 15 dBi peak gain (isotropic 15 dBi element + pattern loss). 65 deg horizontal, 10 deg vertical, 6 deg
  tilt and 15 dBi are the same sourced values as deneyler/20; Am = 25 dB and SLAv = 20 dB are the TR 36.814
  values. No value is fitted.
- Everything else identical to deneyler/22 DC_TA (RMa, 1850 MHz, 49 dBm, 8 dB link shadow, NF 9 dB, TA
  placement, same per-user distance correction file, load users and 1.47 factor, three draws, 4 s, 1 s warm-up).
- Regression first: with the new option off the copied simulator must reproduce deneyler/16
  regression_disabled_draw701 byte for byte (after CRLF->LF).
- Same decision rule as deneyler/20: becomes the reference if held-out RSRP MAE <= 3 dB and SINR MAE
  <= 3 dB averaged over draws and all 256 measured users connect in every draw. No value is adjusted after
  seeing the results.
"""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
D22 = HERE.parent/'22_veri_tabanli_mesafe_duzeltmesi_2026-11-17'
DRAWS = [(42, 701), (7, 702), (99, 703)]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p22 = json.loads((D22/'plan.json').read_text(encoding='utf-8'))
    radio = dict(p22['radio'], antenna_3gpp=1, max_attenuation=25)
    sources = dict(p22['sources'], antenna_pattern='3GPP TR 36.814 Table A.2.1.1-2: A=min(A_H+A_V,25), A_H cap 25, A_V cap 20; chosen after deneyler/22')
    cases = [{'name': f'A3_TA_draw{seed}', 'label': 'A3_TA', 'az': az, 'ue_seed': seed,
              'sites_file': f'sites_S0TA_{az}.csv', 'ue_file': f'ues_DC_TA_{seed}.csv', 'shadow_seed': az}
             for az, seed in DRAWS]
    for c in cases:
        assert sha(HERE/'inputs'/c['ue_file']) == p22['input_hashes'][c['ue_file']], 'UE file differs from deneyler/22'
    plan = {'draws': DRAWS, 'radio': radio, 'sources': sources, 'correction': p22['correction'], 'cases': cases,
            'train_sites': p22['train_sites'], 'holdout_sites': p22['holdout_sites'],
            'decision_rule': dict(p22['decision_rule'], scenario='A3_TA'), 'regression': p22['regression'],
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py']},
            'input_hashes': {p.name: sha(p) for p in sorted((HERE/'inputs').glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run of this experiment):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(len(cases), 'cases', radio)


if __name__ == '__main__':
    main()
