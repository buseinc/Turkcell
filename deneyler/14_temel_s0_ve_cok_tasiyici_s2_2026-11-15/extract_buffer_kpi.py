"""Windows: per-cell handover-type shares for all 24 simulated sites (KPI), to classify buffer sites.

Output (not committed; derived from operator data): buffer_kpi_cells.csv.gz and site_frequency_hints.csv.
"""
from pathlib import Path
import csv
import gzip

import openpyxl
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT / 'ana_proje'
COLS = ['DATETIME', 'CELL', 'Avg_Sim_RRC_Connected_User_Num_ERI', 'DL_PRB_Util_%_ERI', 'Avg_RACH_TA_ERI',
        'Inter_Freq_Hand_Succ_PC', 'Intra_Freq_Hand_Succ_PC', 'IRAT_HO_Succ_PC']


def main():
    with (ROOT / 'deneyler/08_kullanici_orneklemi_2026-11-12/inputs/sites_24_42.csv').open(encoding='utf-8-sig') as f:
        roles = {r['site']: r['role'] for r in csv.DictReader(f)}
    w = openpyxl.load_workbook(PROJECT / 'cell_site_coordinates/cell_site_coordinates.xlsx', read_only=True)
    it = w.active.values
    next(it)
    cell_site = {r[0]: r[1] for r in it if r[1] in roles}
    w.close()
    out = HERE / 'buffer_kpi_cells.csv.gz'
    with gzip.open(out, 'wt', newline='', encoding='utf-8') as g:
        wr = csv.writer(g)
        wr.writerow(['site', 'role'] + COLS)
        for p in sorted(PROJECT.glob('LTE Main KPI_*/*.xlsx')):
            wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
            rows = wb.active.values
            head = list(next(rows))
            idx = [head.index(c) for c in COLS]
            ci = head.index('CELL')
            for r in rows:
                s = cell_site.get(r[ci])
                if s:
                    v = [r[i] for i in idx]
                    v[0] = v[0].isoformat(sep=' ') if hasattr(v[0], 'isoformat') else v[0]
                    wr.writerow([s, roles[s]] + v)
            wb.close()
            print(p.name, flush=True)
    d = pd.read_csv(out)
    cell = d.groupby(['site', 'role', 'CELL']).agg(
        users=('Avg_Sim_RRC_Connected_User_Num_ERI', 'mean'), rach_ta=('Avg_RACH_TA_ERI', 'mean'),
        interfreq=('Inter_Freq_Hand_Succ_PC', lambda s: s.notna().mean())).reset_index()
    site = cell.groupby(['site', 'role']).agg(cells=('CELL', 'size'),
                                             cells_interfreq=('interfreq', lambda s: int((s > .5).sum()))).reset_index()
    site['multi_frequency'] = site.cells_interfreq >= (site.cells / 2)
    missing = sorted(set(roles) - set(site.site))
    site = pd.concat([site, pd.DataFrame({'site': missing, 'role': [roles[m] for m in missing], 'cells': 0,
                                          'cells_interfreq': 0, 'multi_frequency': None})])
    site.to_csv(HERE / 'site_frequency_hints.csv', index=False)
    cell.to_csv(HERE / 'cell_frequency_hints.csv', index=False, float_format='%.3f')
    print(site.to_string())


if __name__ == '__main__':
    main()
