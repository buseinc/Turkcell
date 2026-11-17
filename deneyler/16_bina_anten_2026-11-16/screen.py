"""Fast RSRP screening on all 3 draws; holdout values never enter candidate selection."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd
from radio_model import received_power_w, link_metrics

HERE = Path(__file__).resolve().parent
D15 = HERE.parent / '15_ta_yerlesim_2026-11-16'


def vertical_loss(points, sectors, tilt, width=10):
    delta = sectors[['x_m','y_m','z_m']].to_numpy()[None,:,:] - points[:,None,:]
    elevation = np.rad2deg(np.arctan2(delta[:,:,2], np.hypot(delta[:,:,0],delta[:,:,1])))
    return np.minimum(12*((elevation-tilt)/width)**2,20)


def site_values(pw, sectors):
    lm = link_metrics(pw)
    serving = sectors.iloc[lm['serving']].reset_index(drop=True)
    frame = serving[['site','sector']].copy()
    frame['rsrp'] = lm['rsrp_dbm']
    # Same weighting as the native comparison: first users within cell, then cells within site.
    return frame.groupby(['site','sector']).rsrp.mean().groupby('site').mean()


def main():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for name, sha in plan['input_hashes'].items():
        assert hashlib.sha256((HERE/'inputs'/name).read_bytes()).hexdigest() == sha, name
    targets = pd.read_csv(HERE/'inputs/targets.csv').set_index('site').rsrp_target
    train = plan['train_sites']
    data, validation = [], []
    for az, seed in plan['draws']:
        folder = D15/'simulation/results'/f'S0TA_draw{seed}'
        sectors = pd.read_csv(folder/'sectors.csv')
        points = pd.read_csv(HERE/'inputs'/f'ues_S0TA_{seed}.csv').iloc[:256][['x_m','y_m','z_m']].to_numpy()
        pw = received_power_w(points,sectors)
        lm = link_metrics(pw)
        native = pd.DataFrame(json.loads((folder/'metrics.json').read_text())['ues']).set_index('ue_id').loc[range(256)]
        serv = sectors.iloc[lm['serving']]
        same = ((serv.site.to_numpy()==native.site.to_numpy()) & (serv.sector.to_numpy()==native.sector.to_numpy()))
        error = np.abs(lm['rsrp_dbm']-native.rsrp.to_numpy())
        validation.append({'seed':seed,'same_serving':bool(same.all()),'rsrp_max_error_db':float(error.max()),
                           'finite_all':bool(np.isfinite(error).all()),
                           'passed':bool(same.all() and np.isfinite(error).all() and error.max()<0.01)})
        data.append((sectors,points,pw))
    result = {'validation':validation,'gate_passed':all(v['passed'] for v in validation)}
    if not result['gate_passed']:
        (HERE/'screening.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        raise RuntimeError('Analytical baseline gate failed; no selection permitted.')
    grid = []
    for loss in plan['grid']['indoor_loss_db']:
        for tilt in plan['grid']['downtilt_deg']:
            errors = []
            valid = True
            for sectors,points,pw in data:
                adjusted = pw*10**(-(loss+vertical_loss(points,sectors,tilt))/10)
                values = site_values(adjusted,sectors).reindex(train)
                valid &= bool(values.notna().all())
                errors.append(float((values-targets.reindex(train)).abs().mean()))
            grid.append({'indoor_loss_db':loss,'downtilt_deg':tilt,
                         'training_rsrp_mae_db':float(np.mean(errors)) if valid else None,
                         'training_by_draw_db':errors,'valid':valid})
    winner = min((c for c in grid if c['valid']),key=lambda c:(c['training_rsrp_mae_db'],c['indoor_loss_db'],c['downtilt_deg']))
    # Winner is persisted before any native/held-out evaluation.
    candidates = [dict(label='combined',indoor_loss_db=winner['indoor_loss_db'],downtilt_deg=winner['downtilt_deg'],vertical_pattern=1),
                  dict(label='indoor_only',indoor_loss_db=winner['indoor_loss_db'],downtilt_deg=0,vertical_pattern=0),
                  dict(label='vertical_only',indoor_loss_db=0,downtilt_deg=winner['downtilt_deg'],vertical_pattern=1)]
    unique = {}
    for c in candidates:
        unique.setdefault((c['indoor_loss_db'],c['downtilt_deg'],c['vertical_pattern']),c)
    result.update({'grid':grid,'winner':winner,'native_candidates':list(unique.values()),
                   'interpretation':'Analytical RSRP screening only. No native network, SINR, load or holdout acceptance result yet.'})
    path = HERE/'screening.json'
    text = json.dumps(result,indent=2,allow_nan=False)
    if path.exists() and json.loads(path.read_text()) != result:
        raise RuntimeError('Existing selection differs; refusing to replace it.')
    path.write_text(text,encoding='utf-8')
    print(json.dumps({'gate_passed':True,'winner':winner,'native_candidates':result['native_candidates']},indent=2))
    # Mechanical checks: beam axis zero loss, half beamwidth 3 dB, cap 20 dB.
    assert math.isclose(min(12*(5/10)**2,20),3)


if __name__=='__main__':
    main()
