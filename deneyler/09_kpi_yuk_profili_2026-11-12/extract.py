"""Filter the ten raw KPI workbooks to the cells of the simulated sites.

Windows Python (openpyxl). Output: kpi_cells.csv.gz, one row per cell x 15 min.
Sites: the 48-site topology of experiment 07 (covers the 24-site scenario and its buffer).
Cell->site link: current coordinate inventory (cell id), not SELECTION_0_NAME (constant label).
"""
from pathlib import Path
import csv
import gzip
import hashlib
import json
import time

import openpyxl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT / 'ana_proje'
D07 = ROOT / 'deneyler/07_guncel_envanter_kontrolu_2026-11-12'
KEEP = ['DATETIME', 'CELL', 'EUtranCell_Availability_PC_ERI', 'Avg_Sim_RRC_Connected_User_Num_ERI',
        'DL_PRB_Util_%_ERI', 'UL_PRB_Util_%_ERI', 'DLTRF_VOLUME_MBYTE_ERI', 'ULTRF_Volume_Mbyte',
        'DL_PDCP_USER_THPUT_ERI', 'DL_PDCP_Cell_Thput_ERI', 'Avg_CQI_ERI', 'ERAB_Drop_PC_ERI']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    with (D07 / 'inputs/sites_48_42.csv').open(encoding='utf-8-sig') as f:
        sites = {r['site']: r['role'] for r in csv.DictReader(f)}
    book = PROJECT / 'cell_site_coordinates/cell_site_coordinates.xlsx'
    w = openpyxl.load_workbook(book, read_only=True, data_only=True)
    it = w.active.values
    head = next(it)
    assert head[:2] == ('cell', 'site'), head
    cell_site = {r[0]: r[1] for r in it if r[1] in sites}
    w.close()
    files = sorted(PROJECT.glob('LTE Main KPI_*/*.xlsx'))
    assert len(files) == 10, files
    out = HERE / 'kpi_cells.csv.gz'
    manifest = {'sites': sites, 'cells': cell_site, 'inventory_sha256': sha(book), 'files': {}}
    with gzip.open(out, 'wt', newline='', encoding='utf-8') as g:
        wr = csv.writer(g)
        wr.writerow(['site', 'role'] + KEEP)
        for p in files:
            t = time.time()
            w = openpyxl.load_workbook(p, read_only=True, data_only=True)
            rows = w.active.values
            head = list(next(rows))
            idx = [head.index(k) for k in KEEP]
            ci = head.index('CELL')
            n = kept = 0
            for r in rows:
                n += 1
                site = cell_site.get(r[ci])
                if site is None:
                    continue
                kept += 1
                vals = [r[i] for i in idx]
                vals[0] = vals[0].isoformat(sep=' ') if hasattr(vals[0], 'isoformat') else vals[0]
                wr.writerow([site, sites[site]] + vals)
            w.close()
            manifest['files'][p.name] = {'rows': n, 'kept': kept, 'size': p.stat().st_size}
            print(p.name, n, kept, f'{time.time() - t:.0f}s', flush=True)
    (HERE / 'extract_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
