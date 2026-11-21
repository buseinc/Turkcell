"""Windows: acceptance rules 1, 2 and 5 of DUZELTMELER.md from the ns-3 runs. Usage: py kabul_ns3.py 1|2|5
Writes kabul<n>.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
RES = HERE/'simulation/results'
D33 = HERE.parent/'33_kesinti_ns3_2026-11-20'


def k1():
    """Switches off: same content as deneyler/33 results/L25_smoke (1 s, same inputs)."""
    ref = D33/'simulation/results/L25_smoke'
    out = {}
    for f in ['radio_samples.csv', 'ues.csv', 'prb_usage.csv', 'voice.csv', 'DlRxPhyStats.txt', 'sectors.csv']:
        a = (RES/'R1_regresyon'/f).read_bytes().replace(b'\r\n', b'\n')
        b = (ref/f).read_bytes().replace(b'\r\n', b'\n')
        out[f] = a == b
    return {'files_equal': out, 'pass': all(out.values())}


def k2():
    """Switches on, static users: ns-3 serving-cell RSRP vs alan.Network34 (>= 99 % within 0.01 dB)."""
    import alan
    f = RES/'R2_alan'
    sec = pd.read_csv(f/'sectors.csv')
    sites = pd.read_csv(D33/'inputs/sites_S0TA_42.csv').set_index('site')
    sec['x_m'], sec['y_m'] = sec.site.map(sites.x_m), sec.site.map(sites.y_m)
    ues = pd.read_csv(D33/'inputs/ues_V25_701.csv')
    net = alan.Network34(sec, ues, 42)
    r = net.rsrp(net.draw_los())
    rs = pd.read_csv(f/'radio_samples.csv')
    g = rs.groupby(['ue_id', 'synthetic_cell_id']).rsrp_dbm.median().reset_index()
    col = {v: i for i, v in enumerate(sec.synthetic_cell_id)}
    model = r[g.ue_id.to_numpy(), [col[v] for v in g.synthetic_cell_id]]
    err = np.abs(model - g.rsrp_dbm.to_numpy())
    best = r.argmax(1)
    final = pd.read_csv(f/'ues.csv').set_index('ue_id').synthetic_cell_id
    same = np.mean([col[final[u]] == best[u] for u in final.index if final[u] in col])
    return {'links': int(len(g)), 'share_within_0.01db': float(np.mean(err < 0.01)), 'max_err_db': float(err.max()),
            'same_best_cell_share': float(same), 'los_share_links': float(net.los_fixed.mean()),
            'pass': bool(np.mean(err < 0.01) >= 0.99)}


def k5():
    """As deneyler/19: with handover an automatic 441 -> 443 A3 handover, UE and eNB events match, connected at
    the target, data after the handover; without handover no handover event."""
    out = {}
    sec = pd.read_csv(RES/'R5_ho_acik'/'sectors.csv').set_index('synthetic_cell_id').site
    for name in ['R5_ho_acik', 'R5_ho_kapali']:
        f = RES/name
        ev = pd.read_csv(f/'handover_events.csv')
        tl = pd.read_csv(f/'serving_timeline.csv')
        pk = pd.read_csv(f/'packet_rx.csv')
        ue_start = ev[(ev.actor == 'UE') & (ev.event == 'START')]
        ue_end = ev[(ev.actor == 'UE') & (ev.event == 'END_OK')]
        enb_end = ev[(ev.actor == 'ENB') & (ev.event == 'END_OK')]
        fails = ev[ev.event.str.contains('Failure|ERROR')]
        first, last = tl.cell_id[tl.cell_id > 0].iloc[0], tl.cell_id.iloc[-1]   # cell 0 = not yet connected
        row = {'first_site': sec.get(first), 'last_site': sec.get(last), 'ue_start': int(len(ue_start)),
               'ue_end_ok': int(len(ue_end)), 'enb_end_ok': int(len(enb_end)), 'failures': int(len(fails)),
               'last_rrc_state': int(tl.rrc_state.iloc[-1]), 'packets': int(len(pk))}
        if len(ue_end):
            t_end = ue_end.time_s.iloc[0]
            row['handover_ms'] = float((t_end - ue_start.time_s.iloc[0])*1000)
            row['packets_after'] = int((pk.time_s > t_end).sum())
            near = pk.time_s[(pk.time_s > t_end - 2) & (pk.time_s < t_end + 2)].to_numpy()
            row['max_gap_near_ms'] = float(np.diff(near).max()*1000) if len(near) > 1 else None
        out[name] = row
    on, off = out['R5_ho_acik'], out['R5_ho_kapali']
    out['pass'] = bool(on['first_site'] == 'SITE_000441' and on['last_site'] == 'SITE_000443' and on['ue_start'] >= 1
                       and on['ue_end_ok'] == on['ue_start'] and on['enb_end_ok'] == on['ue_end_ok'] and on['failures'] == 0
                       and on.get('packets_after', 0) > 0 and off['ue_start'] == 0)
    return out


if __name__ == '__main__':
    n = sys.argv[1]
    res = {'1': k1, '2': k2, '5': k5}[n]()
    (HERE/f'kabul{n}.json').write_text(json.dumps(res, indent=1, default=str), encoding='utf-8')
    print(json.dumps(res, indent=1, default=str))
