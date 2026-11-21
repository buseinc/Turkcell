"""Windows: inputs for acceptance rules 2 and 5 (DUZELTMELER.md).
- corr_sites.csv: the 24 sites (x_m, y_m) for the moving-UE distance correction; k0/k1 in corr.json.
- Rule 5 (as deneyler/19): sites 441 and 443 alone with the deneyler/33 antenna draw 42; one UE drives from
  15 % to 85 % of the straight line 441 -> 443 at 15 m/s with 2 s waits at both ends; one 512-byte packet
  every 10 ms."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D33 = HERE.parent/'33_kesinti_ns3_2026-11-20'
sys.path.insert(0, str(HERE.parent/'32_kesinti_hazirligi_2026-11-20'))
import senaryo as sc  # noqa: E402


def main():
    inp = HERE/'inputs'
    b = sc.Builder(42, '2025-10-27')
    sites = pd.read_csv(D33/'inputs/sites_S0TA_42.csv')
    sites[['site', 'x_m', 'y_m']].to_csv(inp/'corr_sites.csv', index=False, lineterminator='\n')
    (inp/'corr.json').write_text(json.dumps({'k0': b.k0, 'k1': b.k1}), encoding='utf-8')
    pair = sites[sites.site.isin(['SITE_000441', 'SITE_000443'])]
    pair.to_csv(inp/'sites_pair_42.csv', index=False, lineterminator='\n')
    a = pair[pair.site == 'SITE_000441'].iloc[0]
    c = pair[pair.site == 'SITE_000443'].iloc[0]
    p0 = np.array([a.x_m, a.y_m]) + 0.15*(np.array([c.x_m, c.y_m]) - np.array([a.x_m, a.y_m]))
    p1 = np.array([a.x_m, a.y_m]) + 0.85*(np.array([c.x_m, c.y_m]) - np.array([a.x_m, a.y_m]))
    travel = float(np.hypot(*(p1 - p0)))/15.0
    t = [0.0, 2.0, 2.0 + travel, 4.0 + travel]
    wp = pd.DataFrame({'ue_id': 0, 'time_s': [f'{v:.6f}' for v in t],
                       'x_m': [f'{v:.6f}' for v in [p0[0], p0[0], p1[0], p1[0]]],
                       'y_m': [f'{v:.6f}' for v in [p0[1], p0[1], p1[1], p1[1]]], 'z_m': '1.500000'})
    wp.to_csv(inp/'waypoints_test.csv', index=False, lineterminator='\n')
    ue = pd.DataFrame({'ue_id': [0], 'x_m': [f'{p0[0]:.6f}'], 'y_m': [f'{p0[1]:.6f}'], 'z_m': ['1.500000'],
                       'udp_interval_ms': [10], 'packet_size_bytes': [512], 'extra_loss_db': ['0.000000']})
    ue.to_csv(inp/'ues_hareket_test.csv', index=False, lineterminator='\n')
    print('k0 k1', b.k0, b.k1, 'travel s', round(travel, 3), 'duration', round(t[-1], 3))


if __name__ == '__main__':
    main()
