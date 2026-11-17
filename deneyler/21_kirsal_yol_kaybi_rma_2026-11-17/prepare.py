"""Windows: freeze the rural path-loss follow-up of deneyler/20.

Predeclared design (written before any run of this experiment):
- Context: deneyler/20 used COST-231 Hata, whose >1.5 GHz branch is the urban/suburban formula with no
  rural correction; Sindirgi is rural. The simulated signal was 12-15 dB too weak.
- This choice is made AFTER seeing the deneyler/20 result. It is reported as such.
- Only change against deneyler/20 R_TA: path loss = 3GPP TR 38.901 RMa (rural macro), ns-3
  ThreeGppRmaPropagationLossModel with default h=5 m mean building height, W=20 m street width,
  RMa LOS probability (ThreeGppRmaChannelConditionModel, fixed per link), its own shadowing and building
  penetration off (shadowing stays the 8 dB static link shadow of deneyler/20), range enforcement off
  (users beyond 5 km NLOS / 10 km LOS are outside the RMa validity range and are counted and reported).
- Everything else identical to deneyler/20 R_TA: B3 EARFCN 1651, 49 dBm, 65 deg / 15 dBi cosine antenna,
  6 deg tilt with 3GPP vertical pattern, 8 dB shadow (seed = azimuth seed), NF 9 dB, no indoor loss,
  TA placement, same load users and 1.47 factor, three draws, 256 measured users, 4 s, 1 s warm-up.
- Regression first: with RMa not selected the copied simulator must reproduce deneyler/16
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
D20 = HERE.parent/'20_kaynakli_parametreler_2026-11-17'
DRAWS = [(42, 701), (7, 702), (99, 703)]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p20 = json.loads((D20/'plan.json').read_text(encoding='utf-8'))
    radio = dict(p20['radio'], pathloss='rma')
    sources = dict(p20['sources'], pathloss='3GPP TR 38.901 Table 7.4.1-1 RMa (h=5 m, W=20 m), LOS probability Table 7.4.2-1; chosen after deneyler/20')
    cases = [{'name': f'RMa_TA_draw{seed}', 'label': 'RMa_TA', 'az': az, 'ue_seed': seed,
              'sites_file': f'sites_S0TA_{az}.csv', 'ue_file': f'ues_R_TA_{seed}.csv', 'shadow_seed': az}
             for az, seed in DRAWS]
    for c in cases:
        assert sha(HERE/'inputs'/c['ue_file']) == p20['input_hashes'][c['ue_file']], 'UE file differs from deneyler/20'
    plan = {'draws': DRAWS, 'radio': radio, 'sources': sources, 'cases': cases,
            'train_sites': p20['train_sites'], 'holdout_sites': p20['holdout_sites'],
            'decision_rule': dict(p20['decision_rule'], scenario='RMa_TA'),
            'regression': p20['regression'],
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py']},
            'input_hashes': {p.name: sha(p) for p in sorted((HERE/'inputs').glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run of this experiment):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(len(cases), 'cases')


if __name__ == '__main__':
    main()
