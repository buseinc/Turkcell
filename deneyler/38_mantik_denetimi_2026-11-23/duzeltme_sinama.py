"""Windows, fast model. deneyler/38 KURALLAR.md: three ways of applying the distance correction (A, S, C).
First the agreement with the measurements, then outages and roads. Writes duzeltme_sinama.json after each part."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent
D29, D33, D34 = DEN/'29_ihtiyaca_gore_zamanlayici_2026-11-19', DEN/'33_kesinti_ns3_2026-11-20', DEN/'34_yol_hareketi_2026-11-21'
D35, D37 = DEN/'35_bolge_secimi_2026-11-21', DEN/'37_edremit_kesinti_2026-11-22'
sys.path.insert(0, str(D37))
import hazirla as h  # noqa: E402
sys.path.insert(0, str(D35))
import sinamalar as sn  # noqa: E402
import senaryo as sc  # noqa: E402
import alan  # noqa: E402
m, hm = h.m, alan.hm
F = 0.03
MODES = ['A', 'S', 'C']
OUT = {}


def save():
    (HERE/'duzeltme_sinama.json').write_text(json.dumps(OUT, indent=1, ensure_ascii=False, default=float), encoding='utf-8')


def corr(k0, k1, d):
    return k0 + k1*np.log10(np.clip(d, 100, 15000))


def apply(net, mode, k0, k1, on=None):
    if mode == 'A':
        return net
    extra = net.ues['extra_loss_db'].to_numpy(float)
    base = net.fixed_db + extra[:, None]
    if mode == 'C':
        net.fixed_db = base - corr(k0, k1, net.d2)
        return net
    los = net.draw_los()
    r = base - np.where(los, net.los_db, net.nlos_db)
    if on is not None:
        r = np.where(on[None, :], r, -np.inf)
    srv = r.argmax(1)
    net.fixed_db = base - corr(k0, k1, net.d2[np.arange(len(r)), srv])[:, None]
    return net


def valid_edremit(mode):
    a3 = json.loads((D35/'adim3.json').read_text(encoding='utf-8'))
    k0, k1 = a3['models']['RMa']['k0_k1']
    t = pd.DataFrame(a3['targets'])
    prb = pd.Series(a3['site_prb'])
    fill = a3.get('fill_prb', 0.21)
    rows = []
    for seed in m.DRAWS:
        sec = pd.read_csv(D35/f'inputs/sectors_edremit_{seed}.csv')
        ues = pd.read_csv(D35/f'inputs/ues_edremit_RMa_{seed}.csv')
        net = apply(m.Model35(sec, ues, seed, 'RMa'), mode, k0, k1)
        r = net.rsrp(net.draw_los())
        srv = r.argmax(1)
        load = sec.site.map(prb).fillna(fill).to_numpy()
        ss = m.site_mean(sec, srv, sn.sinr_on(r, srv, load, F))
        rs = m.site_mean(sec, srv, r[np.arange(len(r)), srv])
        row = {}
        for g in ['train', 'test']:
            names = [s for s in a3[f'{g}_sites'] if s in ss]
            row[f'sinr_{g}'] = float(np.mean([abs(ss[s] - t.sinr[s]) for s in names]))
            row[f'rsrp_{g}'] = float(np.mean([abs(rs[s] - t.rsrp[s]) for s in names]))
        rows.append(row)
    return pd.DataFrame(rows).mean().to_dict()


def valid_sindirgi(mode):
    t = pd.read_csv(D29/'inputs/targets.csv').set_index('site')
    rcol = next(c for c in t.columns if 'rsrp' in c.lower())
    plan = json.loads((D29/'plan.json').read_text(encoding='utf-8'))
    q = json.loads((D33/'plan.json').read_text(encoding='utf-8'))['quake']
    b = sc.Builder(42, q)
    rows = []
    for c in plan['validation_cases']:
        fo = D29/'simulation/results'/c['name']
        sec = pd.read_csv(fo/'sectors.csv')
        sites = pd.read_csv(D29/'inputs'/c['sites_file']).set_index('site')
        sec['x_m'], sec['y_m'] = sec.site.map(sites.x_m), sec.site.map(sites.y_m)
        ues = pd.read_csv(D29/'inputs'/c['ue_file'])
        size = ues.packet_size_bytes.to_numpy(float) if 'packet_size_bytes' in ues else np.full(len(ues), 512.0)
        net = apply(alan.Network34(sec, ues, c['shadow_seed']), mode, b.k0, b.k1)
        sol = hm.solve(net, net.draw_los(), size, ues.udp_interval_ms.to_numpy(float))
        r, srv = net.rsrp(net.draw_los()), sol['serving']
        rep = sn.sinr_on(r, srv, sol['load'], F)
        d = pd.DataFrame({'site': sec.site.to_numpy()[srv][:256], 'sector': sec.sector.to_numpy()[srv][:256], 's': rep[:256],
                          'r': r[np.arange(len(r)), srv][:256]})
        g = d.groupby(['site', 'sector'])[['s', 'r']].mean().groupby('site').mean()
        row = {}
        for sp, name in [('train', 'train'), ('holdout', 'test')]:
            names = [s for s in t[t.split == sp].index if s in g.index]
            row[f'sinr_{name}'] = float(np.mean([abs(g.s[s] - t.sinr_target[s]) for s in names]))
            row[f'rsrp_{name}'] = float(np.mean([abs(g.r[s] - t[rcol][s]) for s in names]))
        rows.append(row)
    return pd.DataFrame(rows).mean().to_dict()


def outage_sindirgi(mode):
    plan = json.loads((D33/'plan.json').read_text(encoding='utf-8'))
    b = sc.Builder(42, plan['quake'])
    ues = pd.read_csv(D33/'inputs/ues_quake_42.csv')
    pk, iv = np.full(len(ues), 512.0), np.full(len(ues), plan['udp_interval_ms'])
    res = {}
    base = None
    for k in ['K0', 'K1', 'K2', 'K3']:
        off = plan['scenarios'][k]['off']
        on = b.cells_on(off)
        net = apply(alan.Network34(b.sec, ues, 42), mode, b.k0, b.k1, on)
        r = h.solve_f(net, pk, iv, on, F)
        nos = r['cqi'] == 0
        if k == 'K0':
            base = nos
            res[k] = {'all': float(nos.mean())}
            continue
        a = ues.home_site.isin(off).to_numpy()
        res[k] = {'off': off, 'around': float(nos[a].mean()), 'around_when_on': float(base[a].mean()), 'all': float(nos.mean()), 'users': int(a.sum())}
    return res


def outage_edremit(mode):
    plan = json.loads((D37/'plan.json').read_text(encoding='utf-8'))
    k0, k1 = plan['k0_k1']
    sites, _ = h.sites48()
    ues = pd.read_csv(D37/'inputs/ues_quake.csv')
    pk, iv = np.full(len(ues), 512.0), ues.udp_interval_ms.to_numpy(float)
    q = (ues.kind == 'quake').to_numpy()
    rows = []
    for seed in m.DRAWS:
        sec, _ = m.sectors_of(sites, seed)
        base = None
        for k, off in h.SCEN.items():
            on = ~sec.site.isin(off).to_numpy()
            net = apply(m.Model35(sec, ues, seed, 'RMa'), mode, k0, k1, on)
            nos = h.solve_f(net, pk, iv, on, F)['cqi'] == 0
            if k == 'E0':
                base = nos
                rows.append({'k': k, 'seed': seed, 'all': float(nos[q].mean())})
                continue
            a = q & ues.home_site.isin(off).to_numpy()
            rows.append({'k': k, 'seed': seed, 'around': float(nos[a].mean()), 'around_when_on': float(base[a].mean()),
                         'all': float(nos[q].mean()), 'users': int(a.sum())})
    return pd.DataFrame(rows).drop(columns='seed').groupby('k').mean().to_dict('index')


def road(mode):
    plan = json.loads((D33/'plan.json').read_text(encoding='utf-8'))
    b = sc.Builder(42, plan['quake'])
    ues = pd.read_csv(D33/'inputs/ues_quake_42.csv')
    pk, iv = np.full(len(ues), 512.0), np.full(len(ues), plan['udp_interval_ms'])
    res = {}
    for route, scen in [('A', 'K2'), ('B', 'K1')]:
        rt = pd.read_csv(D34/f'inputs/rota_{route}.csv')
        step = float(np.median(np.diff(rt.d_along_m)))
        for name in ['K0', scen]:
            on = b.cells_on(plan['scenarios'][name]['off'])
            nq = apply(alan.Network34(b.sec, ues, 42), mode, b.k0, b.k1, on)
            load = h.solve_f(nq, pk, iv, on, F)['load']
            nr = apply(alan.Network34(b.sec, rt, 42), mode, b.k0, b.k1, on)
            rr = np.where(on[None, :], nr.rsrp(nr.draw_los()), -np.inf)
            _, sched = h.sinr_f(rr, rr.argmax(1), load, F)
            bad = hm.mcs_from_sinr_db(sched)[1] == 0
            runs, cur = [], 0
            for v in bad:
                if v:
                    cur += 1
                elif cur:
                    runs.append(cur); cur = 0
            runs += [cur] if cur else []
            res[f'{route}_{name}'] = {'km_no_service': round(float(bad.sum()*step/1000), 2), 'longest_gap_km': round(max(runs, default=0)*step/1000, 2)}
    return res


def main():
    OUT['valid'] = {}
    for mode in MODES:
        OUT['valid'][mode] = {'edremit': valid_edremit(mode), 'sindirgi': valid_sindirgi(mode)}
        print('valid', mode, json.dumps(OUT['valid'][mode]), flush=True)
        save()
    a = OUT['valid']['A']['sindirgi']
    ok = {}
    for mode in MODES:
        e, s = OUT['valid'][mode]['edremit'], OUT['valid'][mode]['sindirgi']
        ok[mode] = bool(e['sinr_test'] <= 3 and e['rsrp_test'] <= 5 and s['sinr_test'] <= a['sinr_test'] + 1 and s['rsrp_test'] <= a['rsrp_test'] + 1)
    train = {x: sum(OUT['valid'][x][r][c] for r in ['edremit', 'sindirgi'] for c in ['sinr_train', 'rsrp_train']) for x in MODES}
    cand = [x for x in ['S', 'C'] if ok[x]]
    OUT['pass'], OUT['train_total'] = ok, train
    OUT['chosen'] = min(cand, key=train.get) if cand else None
    print('pass', ok, 'train', train, 'chosen', OUT['chosen'], flush=True)
    save()
    OUT['results'] = {}
    for mode in MODES:
        OUT['results'][mode] = {'sindirgi': outage_sindirgi(mode), 'edremit': outage_edremit(mode), 'road': road(mode)}
        print('results', mode, json.dumps(OUT['results'][mode], ensure_ascii=False), flush=True)
        save()


if __name__ == '__main__':
    main()
