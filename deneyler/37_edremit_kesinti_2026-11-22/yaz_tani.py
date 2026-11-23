"""Windows: two checks on the summer run (read-only). (1) Why has site 529 no users in the 10 Aug window?
(2) What fills the full core cells: many users, or a few users with poor signal? Writes yaz_tani.json."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hazirla as h  # noqa: E402
import yaz_yuku as y  # noqa: E402

kpi = pd.read_csv(h.D35/'kpi_cells.csv.gz', parse_dates=['DATETIME'])
k529 = kpi[kpi.site == 'SITE_000529']
win = k529[(k529.DATETIME >= y.WINDOW[0]) & (k529.DATETIME < y.WINDOW[1])]
days = k529.groupby(k529.DATETIME.dt.date)[h.U].agg(['count', 'mean']).round(2)
print('529 rows in the window:', len(win), '| users there:', win[h.U].describe()[['count', 'mean', 'max']].round(2).to_dict())
print(days.to_string())
all_w = kpi[(kpi.DATETIME >= y.WINDOW[0]) & (kpi.DATETIME < y.WINDOW[1])]
sites, sec, ues, _ = y.build()
core_sites = sites.site[sites.role != 'Extra buffer']
missing = sorted(set(core_sites) - set(all_w.site))
print('core sites without KPI rows in the window:', missing)
print('users per core site:', ues[ues.kind == 'quake'].home_site.value_counts().reindex(core_sites).fillna(0).astype(int).to_dict())

plan_iv = json.loads((HERE/'yaz_yuku.json').read_text(encoding='utf-8'))
iv = np.where(ues.kind == 'quake', plan_iv['quake_interval_ms'], plan_iv['load_interval_ms'])
pk = np.full(len(ues), 512.0)
pps = 1000.0/iv
out = {'core_sites_without_kpi': missing, 'full_core_cells': []}
for seed in y.SEEDS:
    sec_s, _ = h.m.sectors_of(sites, seed)
    net = h.m.Model35(sec_s, ues, seed, 'RMa')
    on = np.ones(len(sec_s), bool)
    res = h.solve_f(net, pk, iv, on, h.F_ON)
    rr = net.rsrp(net.draw_los())
    srv = rr.argmax(1)
    assert (srv == res['serving']).all()
    _, sched = h.sinr_f(rr, srv, res['load'], h.F_ON)
    mcs, cqi = h.hm.mcs_from_sinr_db(sched)
    use = np.nan_to_num(h.hm.rb_per_packet(mcs, cqi, pk))*pps/(h.hm.N_RB*1000.0)
    core = (sec_s.role != 'Extra buffer').to_numpy()
    for c in np.flatnonzero(core & (res['demand'] >= 0.95)):
        m = srv == c
        u = np.sort(use[m])[::-1]
        row = {'seed': seed, 'site': sec_s.site.iloc[c], 'role': sec_s.role.iloc[c], 'demand': round(float(res['demand'][c]), 2),
               'demand_without_load_users': round(float(use[m & (ues.kind == 'quake').to_numpy()].sum()), 3),
               'users': int(m.sum()), 'load_users': int((m & (ues.kind == 'load').to_numpy()).sum()),
               'top3_user_share': round(float(u[:3].sum()/u.sum()), 2), 'median_sinr': round(float(np.median(res['sinr'][m])), 1)}
        out['full_core_cells'].append(row)
        print(row)
(HERE/'yaz_tani.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
