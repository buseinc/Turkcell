"""Windows: check K1 (KURALLAR.md). ns-3 RSRP of the serving cell per user vs the fast model (inputs/fast_42.csv).
Pass: per core site, |mean over its users of (ns-3 - fast)| averaged over sites <= 0.5 dB. Writes k1.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
RES = HERE/'simulation/results'


def main(name='K1'):
    out = RES/name
    fast = pd.read_csv(HERE/'inputs/fast_42.csv')
    sec = pd.read_csv(out/'sectors.csv')
    radio = pd.read_csv(out/'radio_samples.csv')
    cell_col = 'synthetic_cell_id'
    sid = sec.columns[0]
    per = radio.groupby('ue_id').agg(rsrp=('rsrp_dbm', 'median'), cell=(cell_col, 'last'), n=('rsrp_dbm', 'size'))
    m = fast.set_index('ue_id').join(per, how='left')
    m = m.join(sec.set_index(sid)[['site', 'sector']].rename(columns={'site': 'ns3_site', 'sector': 'ns3_sector'}), on='cell')
    p = m[m.kind == 'probe'].copy()
    p['diff'] = p.rsrp - p.rsrp_dbm
    same = (p.ns3_site == p.serving_site) & (p.ns3_sector == p.serving_sector)
    site = p.groupby('home_site')['diff'].mean()
    res = {'users_with_samples': int(p.rsrp.notna().sum()), 'users': len(p),
           'same_serving_cell_share': round(float(same.mean()), 4),
           'diff_db_same_cell': {'median': round(float(p['diff'][same].median()), 3),
                                 'mean_abs': round(float(p['diff'][same].abs().mean()), 3),
                                 'max_abs': round(float(p['diff'][same].abs().max()), 3)},
           'diff_db_all': {'median': round(float(p['diff'].median()), 3), 'mean_abs': round(float(p['diff'].abs().mean()), 3)},
           'site_mean_abs_db': round(float(site.abs().mean()), 3), 'site_max_abs_db': round(float(site.abs().max()), 3),
           'pass_site_le_0_5': bool(site.abs().mean() <= 0.5),
           'by_env_median_diff': p.groupby('env')['diff'].median().round(3).to_dict()}
    (HERE/f'{name.lower()}.json').write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main(*sys.argv[1:])
