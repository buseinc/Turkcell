"""Windows: freeze the sourced-parameter scenario (advisor: use real-world values, not best-fitting ones).

Predeclared design (written before any run):
- Question: if every radio value comes from a published standard or an observed operator setting
  instead of our fit to Experia, how close does the simulation stay to the measurements?
- Nothing is tuned. No value below was chosen by looking at simulation-vs-Experia agreement.
  Radio values and their sources:
    * Path loss: COST-231 Hata (ns-3 OkumuraHataPropagationLossModel, >1.5 GHz branch, medium city /
      suburban C=0), eNB 30 m, UE 1.5 m. Replaces the fitted log-distance exponent 3.
    * Carrier: Turkcell B3 EARFCN 1651 (DL 1850.1 MHz, UL 19651), 20 MHz, as seen on CellMapper towers
      in Balikesir (17.11.2026). Replaces EARFCN 1300 (1815 MHz).
    * eNB power: 49 dBm total per 20 MHz carrier (3GPP TR 36.814, Table A.2.1.1-1). Unchanged value,
      now with a source instead of a sweep result.
    * Antenna: 65 deg horizontal 3 dB beamwidth (3GPP TR 36.814 / 36.942 sector antenna; typical panel
      data sheets), 15 dBi max gain (3GPP TR 36.942 macro). Replaces the fitted 120 deg.
      ns-3 CosineAntennaModel is kept for the horizontal pattern (no 25 dB front-to-back floor).
    * Vertical pattern: 3GPP form 12((theta - tilt)/10)^2, capped at 20 dB, 10 deg vertical beamwidth,
      6 deg downtilt (value suggested in the advisor's draft).
    * Shadowing: 8 dB static log-normal per eNB-UE link (3GPP TR 36.814 macro), seed = azimuth seed.
      Sectors of a site share the value. Replaces "no shadowing".
    * UE noise figure 9 dB (3GPP TR 36.814). Unchanged value.
    * No indoor loss (Experia indoor/outdoor share unknown; Hata is an outdoor empirical model).
- Users (two placements, both without tuning):
    * R_TA (primary): users at their Experia timing-advance distance (deneyler/15 placement).
    * R_S0yer (secondary): the old 2-6 km clusters (deneyler/14 S0), only to separate the radio effect
      from the placement effect. The 2-6 km clusters were themselves a fitted choice.
  Load users and the frozen 1.47 KPI load factor are copied unchanged (load comes from KPI PRB, not
  from radio agreement). Per-UE dl_earfcn is moved from 1300 to 1651; nothing else in the UE files changes.
- Three draws (azimuth/UE seeds 42/701, 7/702, 99/703), 256 measured users, 4 s, 1 s warm-up.
- Regression first: with link shadowing off the copied simulator must reproduce deneyler/16
  regression_disabled_draw701 byte for byte (after CRLF->LF). Otherwise no new runs.
- Comparison with S0 (deneyler/14) and S0TA (deneyler/15) on the same metrics: site MAE on tuning and
  held-out sites, signed errors, site ranking, cell distributions, KPI CQI, PRB.
- Decision rule (fixed now): R_TA becomes the new reference ("sourced baseline") if, averaged over the
  three draws, the held-out sites' RSRP MAE <= 3 dB and SINR MAE <= 3 dB, and all 256 measured users
  connect in every draw. Otherwise S0 stays the reference and R_TA is reported as the sourced variant.
  Either way no value is adjusted after seeing the results.
"""
from pathlib import Path
import csv
import hashlib
import json

HERE = Path(__file__).resolve().parent
SIM = HERE/'simulation'
DRAWS = [(42, 701), (7, 702), (99, 703)]
RADIO = {'pathloss': 'okumura', 'dl_earfcn': 1651, 'ul_earfcn': 19651, 'enb_power': 49, 'beamwidth': 65,
         'antenna_max_gain_dbi': 15, 'vertical_pattern': 1, 'downtilt': 6, 'vertical_beamwidth': 10,
         'link_shadow_std': 8, 'receiver_nf': 9, 'indoor_loss': 0, 'mixed_cqi': 1, 'udp_jitter': 1}
SOURCES = {
    'pathloss': 'COST-231 Hata (COST 231 final report eq. 4.4.3), ns-3 OkumuraHataPropagationLossModel',
    'dl_earfcn': 'CellMapper, Turkcell B3 primary carrier observed on Balikesir towers (17.11.2026)',
    'enb_power': '3GPP TR 36.814 Table A.2.1.1-1: 49 dBm for a 20 MHz carrier',
    'beamwidth': '3GPP TR 36.814/36.942 sector antenna, 65 deg horizontal HPBW',
    'antenna_max_gain_dbi': '3GPP TR 36.942 macro antenna 15 dBi',
    'vertical_pattern': '3GPP TR 36.814 vertical pattern form, 10 deg HPBW, 20 dB cap',
    'downtilt': 'advisor draft (6 deg)',
    'link_shadow_std': '3GPP TR 36.814 macro log-normal shadowing 8 dB',
    'receiver_nf': '3GPP TR 36.814 UE noise figure 9 dB'}
SCENARIOS = {'R_TA': 'S0TA', 'R_S0yer': 'S0'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    inputs = HERE/'inputs'
    cases = []
    for label, src in SCENARIOS.items():
        for az, seed in DRAWS:
            with (inputs/f'ues_{src}_{seed}.csv').open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            cols = list(rows[0].keys())
            assert {r['dl_earfcn'] for r in rows} == {'1300'}, 'unexpected carrier in UE file'
            for r in rows:
                r['dl_earfcn'] = '1651'
            out = inputs/f'ues_{label}_{seed}.csv'
            with out.open('w', encoding='utf-8', newline='') as f:
                w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n')
                w.writeheader()
                w.writerows(rows)
            cases.append({'name': f'{label}_draw{seed}', 'label': label, 'az': az, 'ue_seed': seed,
                          'sites_file': f'sites_{src}_{az}.csv', 'ue_file': out.name, 'ues': len(rows),
                          'shadow_seed': az})
    plan = {'draws': DRAWS, 'radio': RADIO, 'sources': SOURCES, 'cases': cases,
            'train_sites': ['SITE_000130', 'SITE_000296', 'SITE_000444', 'SITE_000482', 'SITE_000554'],
            'holdout_sites': ['SITE_000440', 'SITE_000441', 'SITE_000443'],
            'decision_rule': {'holdout_rsrp_mae_max_db': 3.0, 'holdout_sinr_mae_max_db': 3.0,
                              'all_measured_connected': True, 'scenario': 'R_TA'},
            'regression': {'reference': 'deneyler/16_bina_anten_2026-11-16/simulation/results/regression_disabled_draw701'},
            'source_hashes': {n: sha(SIM/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                      'static-shadow-model.h', 'run_baseline.py']},
            'input_hashes': {p.name: sha(p) for p in sorted(inputs.glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before any run):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print(len(cases), 'cases;', len(plan['input_hashes']), 'inputs hashed')


if __name__ == '__main__':
    main()
