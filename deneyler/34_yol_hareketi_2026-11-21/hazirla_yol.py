"""Windows: inputs of the moving-vehicle ns-3 runs (step 3b). Rule written before any of these runs:

- Model: deneyler/33 radio settings + DUZELTMELER.md switches on (smooth shadow, position LOS, moving-UE
  distance correction) + A3 handover (3 dB, 256 ms, as deneyler/19), antenna draw 42.
- Cases: Y_A_K0 / Y_A_K2 = route A (il yolu 10-31 past site 130), nothing off / 130 off;
         Y_B_K0 / Y_B_K1 = route B (D240 past site 482), nothing off / 482 off (contrast case).
  Routes from rota.py (OSM, within 6 km of the site).
- Background load: one load user per working cell, 800 m from its site on the sector boresight (as
  deneyler/26-29), interval = 0.2605 / target PRB (deneyler/29 frozen factor), target = that cell's DL PRB in
  the deneyler/33 ns-3 run of the same outage (K0, K1 or K2; minimum 0.01). The ~1473 earthquake users are
  not simulated one by one: a 40 s run with them would take days.
- Vehicles: the route is cut into equal stretches of about 1 km; in each stretch one vehicle per direction.
  Each waits 1 s at its start (attachment), drives its stretch at 25 m/s (90 km/h, Turkish limit for cars
  on single roads outside towns), then waits to the end. Duration = 1 + stretch/25 + 0.5 s. Each vehicle
  receives one 512-byte packet every 20 ms.
- Measured per vehicle (only while driving): position every 100 ms (serving_timeline), SINR samples
  (radio_samples, about every 97 ms), handover events, packets.
  Service on the road (main result, radio criteria of deneyler/32): a 10 m road bin is "no service" when the
  vehicles passing it were not RRC-connected or their mean reported SINR there was < -6.7 dB.
  Also reported: handovers per km, ping-pong (back to the previous cell within 5 s), handover failures,
  longest packet gap. Packet delivery is secondary (deneyler/33 L25: ns-3 packet losses are not understood).
- Load check: mean PRB of the evaluation cells within +-0.05 of the target mean; otherwise flagged.
- Comparison: km without service and gap positions vs the fast-model route profile (rota.json).
Writes inputs/yol_<case>_{ues,waypoints,sites}.csv and yol_plan.json."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D33 = HERE.parent/'33_kesinti_ns3_2026-11-20'
FACTOR = 0.2605345440100384
# Load calibration (before the full runs, only the load was looked at): the 3 s smoke S_A_K2 gave evaluation-cell
# PRB 0.142 for target 0.193 with the deneyler/29 factor (calibrated without the smooth shadow / position LOS).
# One proportional step as in deneyler/29: factor x 0.142/0.193. Checked again with a second smoke.
FACTOR = FACTOR*0.142/0.193
SPEED = 25.0
STRETCH = 1000.0
PKT_MS, PKT_B = 20, 512
CASES = {'Y_A_K0': ('A', 'K0'), 'Y_A_K2': ('A', 'K2'), 'Y_B_K0': ('B', 'K0'), 'Y_B_K1': ('B', 'K1')}


def main():
    corr = json.loads((HERE/'inputs/corr.json').read_text())
    sec_all = pd.read_csv(D33/'simulation/results/K0/sectors.csv')
    sites_all = pd.read_csv(D33/'inputs/sites_K0.csv').set_index('site')
    plan = {'rule': __doc__, 'cases': {}}
    for name, (route, scen) in CASES.items():
        sites = pd.read_csv(D33/'inputs'/f'sites_{scen}.csv')
        prb = pd.read_csv(D33/'simulation/results'/scen/'prb_usage.csv')
        sec = pd.read_csv(D33/'simulation/results'/scen/'sectors.csv').merge(prb, on='synthetic_cell_id')
        sec['x_m'] = sec.site.map(sites_all.x_m); sec['y_m'] = sec.site.map(sites_all.y_m)
        rows = []
        for _, c in sec.iterrows():
            a = np.radians(c.orientation_ccw_from_east_deg)
            target = max(float(c.dl_prb_utilization), 0.01)
            rows.append({'x_m': c.x_m + 800*np.cos(a), 'y_m': c.y_m + 800*np.sin(a), 'kind': 'load',
                         'target_site': c.site, 'target_sector': int(c.sector), 'target_prb': target,
                         'udp_interval_ms': FACTOR/target,   # ms, as deneyler/29
                         'packet_size_bytes': PKT_B, 'extra_loss_db': corr['k0'] + corr['k1']*np.log10(800.0)})
        r = pd.read_csv(HERE/f'inputs/rota_{route}.csv')
        L = r.d_along_m.iloc[-1]
        n = int(round(L/STRETCH))
        edges = np.linspace(0, L, n + 1)
        stretch = L/n
        drive = stretch/SPEED
        dur = 1.0 + drive + 0.5
        wps = []
        for direction in (+1, -1):
            for i in range(n):
                s0, s1 = (edges[i], edges[i + 1]) if direction > 0 else (edges[i + 1], edges[i])
                x0, y0 = np.interp(s0, r.d_along_m, r.x_m), np.interp(s0, r.d_along_m, r.y_m)
                vid = len(rows)
                rows.append({'x_m': x0, 'y_m': y0, 'kind': 'vehicle', 'target_site': '', 'target_sector': '',
                             'target_prb': '', 'udp_interval_ms': PKT_MS, 'packet_size_bytes': PKT_B, 'extra_loss_db': 0.0})
                ss = np.arange(s0, s1, 10.0*direction) if direction > 0 else np.arange(s0, s1, -10.0)
                ss = np.append(ss, s1)
                ts = 1.0 + np.abs(ss - s0)/SPEED
                xs, ys = np.interp(ss, r.d_along_m, r.x_m), np.interp(ss, r.d_along_m, r.y_m)
                wps.append(pd.DataFrame({'ue_id': vid, 'time_s': np.concatenate([[0.0], ts, [dur]]),
                                         'x_m': np.concatenate([[x0], xs, [xs[-1]]]),
                                         'y_m': np.concatenate([[y0], ys, [ys[-1]]]), 'z_m': 1.5,
                                         'direction': direction, 'stretch': i}))
        ues = pd.DataFrame(rows)
        ues.insert(0, 'ue_id', np.arange(len(ues)))
        ues['z_m'] = 1.5
        ues['dl_earfcn'] = 1651
        fmt = {'x_m': '{:.6f}', 'y_m': '{:.6f}', 'z_m': '{:.6f}', 'extra_loss_db': '{:.6f}'}
        u_out = ues[['ue_id', 'x_m', 'y_m', 'z_m', 'kind', 'target_site', 'target_sector', 'target_prb', 'udp_interval_ms',
                     'dl_earfcn', 'extra_loss_db', 'packet_size_bytes']].copy()
        for k, f in fmt.items():
            u_out[k] = u_out[k].map(lambda v, f=f: f.format(v))
        u_out['udp_interval_ms'] = u_out.udp_interval_ms.map(lambda v: f'{float(v):.6f}')
        w = pd.concat(wps, ignore_index=True)
        w = w.drop_duplicates(['ue_id', 'time_s'])
        meta = w[['ue_id', 'direction', 'stretch']].drop_duplicates()
        w_out = w[['ue_id', 'time_s', 'x_m', 'y_m', 'z_m']].copy()
        for k in ['time_s', 'x_m', 'y_m', 'z_m']:
            w_out[k] = w_out[k].map(lambda v: f'{v:.6f}')
        # first waypoint must equal the UE file position exactly as written
        u_out.to_csv(HERE/f'inputs/{name}_ues.csv', index=False, lineterminator='\n')
        w_out.to_csv(HERE/f'inputs/{name}_waypoints.csv', index=False, lineterminator='\n')
        sites.to_csv(HERE/f'inputs/{name}_sites.csv', index=False, lineterminator='\n')
        ev = sec.role == 'Evaluation'
        plan['cases'][name] = {'route': route, 'scenario': scen, 'duration_s': round(dur, 3), 'stretches': n,
                               'stretch_m': round(stretch, 1), 'vehicles': int((ues.kind == 'vehicle').sum()),
                               'load_users': int((ues.kind == 'load').sum()),
                               'target_eval_prb_mean': float(np.maximum(sec.dl_prb_utilization[ev], 0.01).mean()),
                               'vehicle_meta': meta.to_dict('list'),
                               'inputs': {f: hashlib.sha256((HERE/'inputs'/f).read_bytes()).hexdigest()
                                          for f in [f'{name}_ues.csv', f'{name}_waypoints.csv', f'{name}_sites.csv']}}
        print(name, {k: v for k, v in plan['cases'][name].items() if k not in ('vehicle_meta', 'inputs')})
    plan['source_hashes'] = {n: hashlib.sha256((HERE/'simulation'/n).read_bytes()).hexdigest()
                             for n in ['sindirgi_baseline.cc', 'building-vertical-model.h', 'spatial-field.h',
                                       'handover-support.h', 'run_baseline.py']}
    (HERE/'yol_plan.json').write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
