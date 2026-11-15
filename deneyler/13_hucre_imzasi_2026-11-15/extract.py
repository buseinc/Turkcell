"""Windows: pull per-cell hourly Experia rows and per-cell 15-min KPI rows for the 8 evaluation sites.

Cell -> site link: current coordinate inventory (cell id). Outputs (not committed; operator data):
experia_cells.csv.gz, kpi_cells.csv.gz. Re-run to regenerate from the raw workbooks.
"""
from pathlib import Path
import csv
import gzip
import time

import openpyxl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT / 'ana_proje'
KPI_COLS = ['DATETIME', 'CELL', 'EUtranCell_Availability_PC_ERI', 'Avg_Sim_RRC_Connected_User_Num_ERI',
            'DL_PRB_Util_%_ERI', 'DLTRF_VOLUME_MBYTE_ERI', 'Avg_CQI_ERI', 'Avg_RACH_TA_ERI',
            'Intra_Freq_Hand_Succ_PC', 'Inter_Freq_Hand_Succ_PC', 'IRAT_HO_Succ_PC']


def rows(path):
    w = openpyxl.load_workbook(path, read_only=True, data_only=True)
    it = w.active.values
    head = list(next(it))
    for r in it:
        yield head, r
    w.close()


def main():
    with (ROOT / 'deneyler/09_kpi_yuk_profili_2026-11-12/inputs/targets.csv').open(encoding='utf-8-sig') as f:
        sites = {r['site'] for r in csv.DictReader(f)}
    cell_site = {}
    for head, r in rows(PROJECT / 'cell_site_coordinates/cell_site_coordinates.xlsx'):
        if r[1] in sites:
            cell_site[r[0]] = r[1]
    print('cells', len(cell_site), flush=True)

    t = time.time()
    with gzip.open(HERE / 'experia_cells.csv.gz', 'wt', newline='', encoding='utf-8') as g:
        w = csv.writer(g)
        first = True
        for head, r in rows(PROJECT / 'experia/experia.xlsx'):
            if first:
                ci = head.index('FIRSTCELL')
                w.writerow(['site'] + head)
                first = False
            s = cell_site.get(r[ci])
            if s:
                w.writerow([s] + [v.isoformat(sep=' ') if hasattr(v, 'isoformat') else v for v in r])
    print('experia', f'{time.time() - t:.0f}s', flush=True)

    with gzip.open(HERE / 'kpi_cells.csv.gz', 'wt', newline='', encoding='utf-8') as g:
        w = csv.writer(g)
        w.writerow(['site'] + KPI_COLS)
        for p in sorted(PROJECT.glob('LTE Main KPI_*/*.xlsx')):
            t = time.time()
            idx = None
            for head, r in rows(p):
                if idx is None:
                    idx = [head.index(k) for k in KPI_COLS]
                    ci = head.index('CELL')
                s = cell_site.get(r[ci])
                if s:
                    v = [r[i] for i in idx]
                    v[0] = v[0].isoformat(sep=' ') if hasattr(v[0], 'isoformat') else v[0]
                    w.writerow([s] + v)
            print(p.name, f'{time.time() - t:.0f}s', flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
