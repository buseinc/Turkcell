"""Windows: voice-capacity summary per step and per evaluation cell (criteria from plan.json)."""
from pathlib import Path
import json
import sys

import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE/'simulation/results'


def main():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    cr = plan['criteria']
    suffix = sys.argv[1] if len(sys.argv) > 1 else ''
    out = {'criteria': cr, 'steps': []}
    for c in plan['cases']:
        f = RES/(c['name'] + suffix)
        if not (f/'voice.csv').exists():
            continue
        v = pd.read_csv(f/'voice.csv')
        sec = pd.read_csv(f/'sectors.csv')[['synthetic_cell_id', 'site']]
        prb = pd.read_csv(f/'prb_usage.csv')[['synthetic_cell_id', 'dl_prb_utilization']]
        v['talk'] = (v.rrc_connected == 1) & (v.sent > 0) & (v.on_time >= cr['user_can_talk_min_on_time_share']*v.sent)
        v = v.merge(sec, on='synthetic_cell_id', how='left')
        cells = v[v.rrc_connected == 1].groupby(['site', 'synthetic_cell_id']).agg(users=('talk', 'size'), can_talk=('talk', 'mean')).reset_index()
        cells = cells.merge(prb, on='synthetic_cell_id', how='left')
        cells['carries'] = cells.can_talk >= cr['cell_carries_min_satisfied_share']
        ev = cells[cells.site.isin(plan['eval_sites'])]
        step = {'name': c['name'] + suffix, 'voice_per_cell': c['voice_per_cell'], 'voice_users': int(len(v)),
                'not_connected': int((v.rrc_connected == 0).sum()),
                'can_talk_share': float(v.talk.mean()),
                'eval_cells': int(len(ev)), 'eval_cells_carrying': int(ev.carries.sum()),
                'median_delay_ms': float(v.loc[v.received > 0, 'mean_delay_ms'].median()),
                'eval_prb_mean': float(ev.dl_prb_utilization.mean()),
                'cells': ev.round(3).to_dict('records')}
        out['steps'].append(step)
        print(f"{step['name']}: {step['voice_users']} voice users, not connected {step['not_connected']}, "
              f"can talk {100*step['can_talk_share']:.1f} %, cells carrying {step['eval_cells_carrying']}/{step['eval_cells']}, "
              f"median delay {step['median_delay_ms']:.1f} ms, eval PRB {step['eval_prb_mean']:.2f}")
        print(ev.groupby('site').agg(users=('users', 'sum'), can_talk=('can_talk', 'mean'), prb=('dl_prb_utilization', 'mean')).round(2).to_string())
    (HERE/f'comparison{suffix}.json').write_text(json.dumps(out, indent=2, ensure_ascii=False, default=float), encoding='utf-8')


if __name__ == '__main__':
    main()
