"""Windows: analysis of the road runs exactly as written in hazirla_yol.py (step 3b).
Usage: py yol_analiz.py [case ...]   (default: the four Y_ cases). Writes yol_analiz.json and yol_analiz.png."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
RES = HERE/'simulation/results'
CONNECTED = 9          # LteUeRrc::CONNECTED_NORMALLY
BIN = 10.0


def db_mean(x):
    return 10*np.log10(np.mean(10**(np.asarray(x)/10)))


def analyse(case, ues_case, route, plan_case):
    f = RES/case
    r = pd.read_csv(HERE/f'inputs/rota_{route}.csv')
    ui = pd.read_csv(HERE/f'inputs/{ues_case}_ues.csv')
    veh = set(ui.ue_id[ui.kind == 'vehicle'])
    t_end = 1.0 + plan_case['stretch_m']/25.0
    tl = pd.read_csv(f/'serving_timeline.csv')
    tl = tl[tl.ue_id.isin(veh) & (tl.time_s >= 1.0) & (tl.time_s <= t_end)].copy()
    rs = pd.read_csv(f/'radio_samples.csv')
    rs = rs[rs.ue_id.isin(veh) & (rs.time_s >= 1.0) & (rs.time_s <= t_end)].copy()
    # position along the route: nearest route point to the vehicle position (timeline) / interpolated time (radio)
    rp = r[['x_m', 'y_m']].to_numpy()

    def along(x, y):
        d = (x[:, None] - rp[None, :, 0])**2 + (y[:, None] - rp[None, :, 1])**2
        return r.d_along_m.to_numpy()[d.argmin(1)]
    tl['s'] = along(tl.x_m.to_numpy(), tl.y_m.to_numpy())
    pos = {u: g.sort_values('time_s') for u, g in tl.groupby('ue_id')}
    rs['s'] = [np.interp(t, pos[u].time_s, pos[u].s) if u in pos else np.nan for u, t in zip(rs.ue_id, rs.time_s)]
    nb = int(np.ceil(r.d_along_m.iloc[-1]/BIN))
    tl['b'] = np.minimum((tl.s//BIN).astype(int), nb - 1)
    rs = rs.dropna(subset=['s'])
    rs['b'] = np.minimum((rs.s//BIN).astype(int), nb - 1)
    conn = tl.groupby('b').rrc_state.apply(lambda v: np.mean(v == CONNECTED)).reindex(range(nb))
    sinr = rs.groupby('b').sinr_db.apply(db_mean).reindex(range(nb))
    no_srv = (conn < 0.5) | (sinr < -6.7)
    covered = conn.notna()
    # handovers of the vehicles while driving
    ev = pd.read_csv(f/'handover_events.csv')
    ev = ev[ev.ue_id.isin(veh) & (ev.time_s >= 1.0) & (ev.time_s <= t_end)]
    ue_ok = ev[(ev.actor == 'UE') & (ev.event == 'END_OK')].sort_values('time_s')
    starts = ev[(ev.actor == 'UE') & (ev.event == 'START')].sort_values('time_s')
    fails = ev[ev.event.str.contains('Failure|ERROR')]
    pingpong = 0
    for u, g in starts.groupby('ue_id'):
        g = g.sort_values('time_s').to_numpy()
        cols = list(starts.columns)
        for i in range(1, len(g)):
            prev_src, prev_t = g[i - 1][cols.index('cell_id')], g[i - 1][cols.index('time_s')]
            if g[i][cols.index('target_cell_id')] == prev_src and g[i][cols.index('time_s')] - prev_t <= 5.0:
                pingpong += 1
    drive_km = len(veh)*plan_case['stretch_m']/1000
    pk = pd.read_csv(f/'packet_rx.csv')
    gaps = []
    for u in veh:
        t = np.sort(pk.time_s[(pk.ue_id == u) & (pk.time_s >= 1.0) & (pk.time_s <= t_end)].to_numpy())
        t = np.concatenate([[1.0], t, [t_end]])
        gaps.append(np.diff(t).max())
    lost_conn_veh = int(sum((g.rrc_state != CONNECTED).any() for _, g in tl.groupby('ue_id')))
    runs, cur = [], 0
    for v in no_srv.fillna(False).to_numpy():
        if v:
            cur += 1
        elif cur:
            runs.append(cur*BIN); cur = 0
    if cur:
        runs.append(cur*BIN)
    res = {'route_km': round(nb*BIN/1000, 2), 'bins_covered_share': float(covered.mean()),
           'km_no_service': round(float(no_srv.sum()*BIN/1000), 2), 'gaps': len(runs),
           'longest_gap_km': round(max(runs, default=0)/1000, 2),
           'km_not_connected': round(float((conn < 0.5).sum()*BIN/1000), 2),
           'km_sinr_below_cqi0': round(float((sinr < -6.7).sum()*BIN/1000), 2),
           'vehicles': len(veh), 'vehicles_ever_not_connected': lost_conn_veh,
           'handovers': int(len(ue_ok)), 'handovers_per_km': round(len(ue_ok)/drive_km, 2),
           'handover_starts': int(len(starts)), 'handover_failures': int(len(fails)), 'pingpong_5s': pingpong,
           'max_packet_gap_s_median_vehicle': float(np.median(gaps)), 'vehicles_gap_over_1s': int(np.sum(np.array(gaps) > 1.0))}
    prb = pd.read_csv(f/'prb_usage.csv').merge(pd.read_csv(f/'sectors.csv'))
    res['eval_prb'] = float(prb.dl_prb_utilization[prb.role == 'Evaluation'].mean())
    res['target_eval_prb'] = plan_case['target_eval_prb_mean']
    res['load_flag'] = abs(res['eval_prb'] - res['target_eval_prb']) > 0.05
    return res, no_srv, sinr, conn


def main():
    plan = json.loads((HERE/'yol_plan.json').read_text(encoding='utf-8'))
    rota = json.loads((HERE/'rota.json').read_text(encoding='utf-8'))
    cases = sys.argv[1:] or ['Y_A_K0', 'Y_A_K2', 'Y_B_K0', 'Y_B_K1']
    out = {}
    fig, axs = plt.subplots(2, 1, figsize=(11, 7))
    for case in cases:
        base = 'Y_A_K2' if case == 'S_A_K2' else case
        pc = dict(plan['cases'][base])
        if case == 'S_A_K2':
            pc['stretch_m'] = 2.0*25.0
        route, scen = pc['route'], pc['scenario']
        res, no_srv, sinr, conn = analyse(case, base, route, pc)
        res['fast_model_km_no_service'] = rota[route][scen]['km_no_service']
        res['fast_model_longest_gap_km'] = rota[route][scen]['longest_gap_km']
        out[case] = res
        print(case, res, flush=True)
        ax = axs[0 if route == 'A' else 1]
        x = np.arange(len(sinr))*BIN/1000
        ax.plot(x, sinr.to_numpy(), lw=0.7, label=f'{case}: {"kesinti yok" if scen == "K0" else "kesinti var"} '
                                                     f'(servissiz {res["km_no_service"]} km)')
        ax.set_title(f'Rota {route}: araçların gördüğü sinyal kalitesi (ns-3)')
    for ax in axs:
        ax.axhline(-6.7, color='red', ls='--', lw=0.8)
        ax.set_xlabel('yol boyunca km'); ax.set_ylabel('SINR (dB)'); ax.legend(fontsize=8)
    fig.tight_layout()
    tag = '_smoke' if cases == ['S_A_K2'] else ''
    fig.savefig(HERE/f'yol_analiz{tag}.png', dpi=120)
    (HERE/f'yol_analiz{tag}.json').write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float), encoding='utf-8')


if __name__ == '__main__':
    main()
