"""Windows: does f = 0.03 change the deneyler/33 Sindirgi outage result? (KURALLAR.md, fast model, smooth
shadow + position LOS). Writes sindirgi_f.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
sys.path.insert(0, str(DEN/'32_kesinti_hazirligi_2026-11-20'))
sys.path.insert(0, str(DEN/'34_yol_hareketi_2026-11-21'))
import senaryo as sc  # noqa: E402
import alan  # noqa: E402
hm = alan.hm
D33 = DEN/'33_kesinti_ns3_2026-11-20'


def sinr_f(rsrp_dbm, serving, load, f, samples=100):
    """Reported SINR and SINR on the UE's own (scheduled) RBs, neighbour activity f + (1-f) x data (packed RBs)."""
    p = 10**(rsrp_dbm/10)
    u = np.arange(len(p))
    s = p[u, serving]
    interf = p.copy(); interf[u, serving] = 0.0
    x = (np.arange(samples) + 0.5)/samples
    act = f + (1 - f)*(x[:, None] < load[None, :]).astype(float)
    lin = s[:, None]/(hm.NOISE_MW + hm.EVM**2*s[:, None] + interf @ act.T)
    db = 10*np.log10(lin)
    own = x[None, :] < np.maximum(load[serving], hm.RBG/hm.N_RB)[:, None]
    return 10*np.log10(lin.mean(1)), (db*own).sum(1)/own.sum(1)


def main():
    plan = json.loads((D33/'plan.json').read_text(encoding='utf-8'))
    b = sc.Builder(42, plan['quake'])
    ues = pd.read_csv(D33/'inputs/ues_quake_42.csv')
    net = alan.Network34(b.sec, ues, 42)
    n = len(ues)
    pk, iv = np.full(n, 512.0), np.full(n, plan['udp_interval_ms'])
    pps = 1000.0/iv
    ev = b.sec.role.to_numpy() == 'Evaluation'
    out = {}
    for k, v in plan['scenarios'].items():
        on = b.cells_on(v['off'])
        r0 = hm.solve(net, net.draw_los(), pk, iv, cell_on=on)
        r = np.where(on[None, :], net.rsrp(net.draw_los()), -np.inf)
        srv = r0['serving']
        around = ues.home_site.isin(v['off']).to_numpy()
        row = {}
        for f in [0.0, 0.03]:
            _, sched = sinr_f(r, srv, r0['load'], f)
            mcs, cqi = hm.mcs_from_sinr_db(sched)
            nos = cqi == 0
            rb = hm.rb_per_packet(mcs, cqi, pk)
            dem = np.bincount(srv, weights=np.nan_to_num(rb)*pps, minlength=len(on))/(hm.N_RB*1000.0)
            row[f'f{f}'] = {'no_service_all': float(nos.mean()),
                            'no_service_around': float(nos[around].mean()) if around.any() else None,
                            'eval_load_recomputed': float(np.minimum(dem, 1)[ev & on].mean())}
        row['load_used'] = float(r0['load'][ev & on].mean())
        out[k] = row
        print(k, row, flush=True)
    worst = max(abs(out[k]['f0.03']['no_service_around'] - out[k]['f0.0']['no_service_around'])
                for k in out if out[k]['f0.0']['no_service_around'] is not None)
    out['max_change_around_pp'] = 100*worst
    out['rerun_ns3'] = bool(100*worst > 3.0)
    (HERE/'sindirgi_f.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    print('max change around off sites (pp)', round(100*worst, 2), 'rerun ns-3:', out['rerun_ns3'])


if __name__ == '__main__':
    main()
