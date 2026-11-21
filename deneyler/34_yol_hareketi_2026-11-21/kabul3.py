"""Windows: acceptance rule 3 of DUZELTMELER.md. Does the smooth shadow + position LOS keep the fit to the
real measurements? Fast model, the 3 deneyler/29 validation cases (normal load, 3 antenna draws).
Old = hizli_model.Network, mean over 20 LOS draws (as deneyler/31). New = Network34 (LOS fixed by position).
Metrics per case, then mean over the 3 cases:
- site SINR error vs Experia (train and test sites; deneyler/31 metric: mean SINR of the first 256 users,
  sector means averaged per site);
- site RSRP error vs Experia (same averaging, serving RSRP);
- median of sector-mean RSRP over all 24 evaluation cells (deneyler/26 reports Experia -104.2 dBm).
Pass: each new error <= old + 1 dB, and new median within 1 dB of -104.2."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
import alan  # noqa: E402
hm = alan.hm
D29 = HERE.parent/'29_ihtiyaca_gore_zamanlayici_2026-11-19'
EXPERIA_MEDIAN = -104.2


def site_mean(sec, cell_idx, value, n=256):
    d = pd.DataFrame({'site': sec.site.to_numpy()[cell_idx][:n], 'sector': sec.sector.to_numpy()[cell_idx][:n], 'v': value[:n]})
    return d.groupby(['site', 'sector']).v.mean()


def metrics(sec, r, targets):
    ev = sec.role.to_numpy() == 'Evaluation'
    sec_rsrp = site_mean(sec, r['serving'], r['rsrp'])
    out = {'sinr': site_mean(sec, r['serving'], r['sinr_db']).groupby('site').mean(),
           'rsrp': sec_rsrp.groupby('site').mean()}
    evs = set(sec.site[ev])
    res = {}
    for m in ['sinr', 'rsrp']:
        for split in ['train', 'holdout']:
            ss = [s for s in targets[targets.split == split].index if s in out[m]]
            res[f'{m}_{split}'] = float(np.mean([abs(out[m][s] - targets.loc[s, f'{m}_target']) for s in ss]))
    res['cell_rsrp_median'] = float(sec_rsrp[[s in evs for s, _ in sec_rsrp.index]].median())
    return res


def main():
    targets = pd.read_csv(D29/'inputs/targets.csv').set_index('site')
    plan = json.loads((D29/'plan.json').read_text(encoding='utf-8'))
    rows = []
    for c in plan['validation_cases']:
        f = D29/'simulation/results'/c['name']
        sec = pd.read_csv(f/'sectors.csv')
        sites = pd.read_csv(D29/'inputs'/c['sites_file']).set_index('site')
        sec['x_m'], sec['y_m'] = sec.site.map(sites.x_m), sec.site.map(sites.y_m)
        ues = pd.read_csv(D29/'inputs'/c['ue_file'])
        size = ues.packet_size_bytes.to_numpy(float) if 'packet_size_bytes' in ues else np.full(len(ues), 512.0)
        iv = ues.udp_interval_ms.to_numpy(float)
        old_net = hm.Network(sec, ues, c['shadow_seed'])
        rng = np.random.default_rng(1000 + c['shadow_seed'])
        old = pd.DataFrame([metrics(sec, hm.solve(old_net, old_net.draw_los(rng), size, iv, rng=rng), targets)
                            for _ in range(20)]).mean()
        new_net = alan.Network34(sec, ues, c['shadow_seed'])
        new = pd.Series(metrics(sec, hm.solve(new_net, new_net.draw_los(), size, iv), targets))
        los_share = float(new_net.los_fixed.mean())
        rows.append({'case': c['name'], 'old': old.round(3).to_dict(), 'new': new.round(3).to_dict(), 'los_share_new': los_share})
        print(c['name'], 'old', old.round(2).to_dict(), '\n   new', new.round(2).to_dict(), flush=True)
    o = pd.DataFrame([r['old'] for r in rows]).mean()
    n = pd.DataFrame([r['new'] for r in rows]).mean()
    checks = {k: bool(n[k] <= o[k] + 1.0) for k in ['sinr_train', 'sinr_holdout', 'rsrp_train', 'rsrp_holdout']}
    checks['median_within_1db'] = bool(abs(n['cell_rsrp_median'] - EXPERIA_MEDIAN) <= 1.0)
    out = {'mean_old': o.round(3).to_dict(), 'mean_new': n.round(3).to_dict(), 'checks': checks,
           'pass': all(checks.values()), 'cases': rows, 'rule': __doc__}
    (HERE/'kabul3.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print('mean old', o.round(2).to_dict()); print('mean new', n.round(2).to_dict()); print(checks, 'PASS' if out['pass'] else 'FAIL')


if __name__ == '__main__':
    main()
