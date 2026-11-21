"""Windows: freeze the ns-3 outage runs K0-K3 (and the link-adaptation check) before any run.

Predeclared design (written before the smoke run):
- Model: deneyler/29 ns-3 model unchanged (RMa, 3GPP antenna, EVM 8 %, distance correction, 8 dB link
  shadow, buffer-aware PF), antenna draw 42, SRS periodicity 320 (as the deneyler/28-29 stress runs, so many
  users per cell can attach). The only source change is an optional switch for ns-3's DL PHY traces (off in K).
- Load: 27 Oct 2025 earthquake (deneyler/32 deprem_yuku.py; all sites have KPI there and it is the quake of
  the real 482 outage). Users per site = KPI connected users per cell x sectors, placed by rule A of
  deneyler/32 senaryo.py (seed 33042). Every user one DL flow of 512-byte packets; common interval from the
  fast model so that the evaluation-cell PRB is the KPI earthquake value 0.23 without outage.
- Scenarios: K0 nothing off; K1 site 482 removed; K2 site 130 removed; K3 both removed. Same users in all.
- Service is judged with the deneyler/32 TANIMLAR.md step-1 radio criteria, NOT with packet delivery
  (ns-3 has no outer-loop link adaptation, so its packet losses at moderate load are not reliable; deneyler/29):
  no service = not RRC-connected, or mean reported SINR < -6.7 dB (CQI 0); weak = RSRP < -121.8 dBm
  (TS 36.101 REFSENS); overloaded cell = DL PRB use >= 0.95. Reported for all users and for the users placed
  around the removed site(s).
- K0 is accepted if the evaluation-cell mean PRB is within 0.15-0.35 (target 0.23); otherwise the K runs are
  still reported but the load is flagged.
- The ns-3 numbers are compared with the fast model on the same users (20 LOS draws, 5-95 % range).
- L25: deneyler/29 V25_draw701 re-run with identical inputs and DL PHY traces on. Check 1: voice.csv equal to
  deneyler/29 (the trace switch changes nothing). Check 2: for voice users with good reported SINR (> 3 dB),
  share of transport blocks received in error at light load; if the "CQI measured when neighbours are silent"
  explanation holds, errors should be far above the 10 % BLER the CQI targets.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DEN = HERE.parent
D29 = DEN/'29_ihtiyaca_gore_zamanlayici_2026-11-19'
sys.path.insert(0, str(DEN/'32_kesinti_hazirligi_2026-11-20'))
import senaryo as sc  # noqa: E402

SCEN = {'K0': [], 'K1': ['SITE_000482'], 'K2': ['SITE_000130'], 'K3': ['SITE_000482', 'SITE_000130']}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    b = sc.Builder(42, '2025-10-27')
    rng = np.random.default_rng(33042)
    ues = b.place('A', rng)
    out = pd.DataFrame({'ue_id': np.arange(len(ues)), 'x_m': ues.x_m.map(lambda v: f'{v:.9f}'),
                        'y_m': ues.y_m.map(lambda v: f'{v:.9f}'), 'z_m': '1.500000000', 'kind': 'quake',
                        'home_site': ues.home_site, 'distance_m': ues.distance_m.round(1),
                        'extra_loss_db': ues.extra_loss_db.map(lambda v: f'{v:.6f}'), 'dl_earfcn': 1651,
                        'packet_size_bytes': 512})
    tmp = HERE/'inputs/_tmp.csv'
    out.to_csv(tmp, index=False, lineterminator='\n')
    back = pd.read_csv(tmp)                           # rounded positions: what ns-3 will see
    net = b.network(back)
    los = [net.draw_los(np.random.default_rng(7 + i)) for i in range(3)]
    iv = b.calibrate_interval(net, los)
    out['udp_interval_ms'] = f'{iv:.6f}'
    tmp.unlink()
    out.to_csv(HERE/'inputs/ues_quake_42.csv', index=False, lineterminator='\n')
    sites = pd.read_csv(D29/'inputs/sites_S0TA_42.csv')
    for k, off in SCEN.items():
        sites[~sites.site.isin(off)].to_csv(HERE/'inputs'/f'sites_{k}.csv', index=False, lineterminator='\n')
    shutil.copy(D29/'inputs/ues_V25_701.csv', HERE/'inputs/ues_V25_701.csv')
    shutil.copy(D29/'inputs/sites_S0TA_42.csv', HERE/'inputs/sites_S0TA_42.csv')
    p29 = json.loads((D29/'plan.json').read_text(encoding='utf-8'))
    plan = {'radio': p29['radio'], 'srs_periodicity': 320, 'quake': '2025-10-27', 'udp_interval_ms': iv,
            'users': int(len(out)), 'users_by_site': out.home_site.value_counts().to_dict(),
            'scenarios': {k: {'off': v, 'sites_file': f'sites_{k}.csv', 'ue_file': 'ues_quake_42.csv'} for k, v in SCEN.items()},
            'link_check': {'name': 'L25', 'sites_file': 'sites_S0TA_42.csv', 'ue_file': 'ues_V25_701.csv',
                           'reference': str(D29/'simulation/results/V25_draw701')},
            'source_hashes': {n: sha(HERE/'simulation'/n) for n in ['sindirgi_baseline.cc', 'building-vertical-model.h',
                                                                    'static-shadow-model.h', 'run_baseline.py', 'build_private_lte.py']},
            'input_hashes': {q.name: sha(q) for q in sorted((HERE/'inputs').glob('*.csv'))},
            'rule': __doc__.split('Predeclared design (written before the smoke run):')[1].strip()}
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')
    print('users', len(out), 'interval ms', round(iv, 2), out.home_site.value_counts().head(8).to_dict())


if __name__ == '__main__':
    main()
