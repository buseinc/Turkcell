"""Windows: 10 KPI days for the sites of deneyler/09 plus SITE_000200 and SITE_000011, with the availability /
automatic / manual downtime split (operator data, local only). Resumable per day. Writes kpi41.csv.gz."""
from pathlib import Path
import glob
import sys

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
P = HERE.parent.parent/'ana_proje'
COLS = ['DATETIME', 'CELL', 'EUtranCell_Availability_PC_ERI', 'DownTime_Auto_PC_ERI', 'DownTime_Man_PC_ERI',
        'Avg_Sim_RRC_Connected_User_Num_ERI', 'DLTRF_VOLUME_MBYTE_ERI']


def main():
    sites = set(pd.read_csv(HERE.parent/'09_kpi_yuk_profili_2026-11-12/kpi_cells.csv.gz', usecols=['site']).site) | {'SITE_000200', 'SITE_000011'}
    cs = pd.read_excel(P/'cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('cell').set_index('cell').site
    cells = set(cs[cs.isin(sites)].index)
    tmp = HERE/'_parca'
    tmp.mkdir(exist_ok=True)
    parts = []
    for f in sorted(glob.glob(str(P/'LTE Main KPI_*'/'*.xlsx'))):
        part = tmp/(Path(f).stem.split()[-1] + '.csv.gz')
        if part.exists():
            k = pd.read_csv(part)
        else:
            k = pd.read_excel(f, usecols=COLS)
            k = k[k.CELL.isin(cells)]
            k.to_csv(part, index=False)
        parts.append(k)
        print(Path(f).name[:40], len(k), k.CELL.nunique(), flush=True)
    k = pd.concat(parts)
    k['site'] = k.CELL.map(cs)
    k.to_csv(HERE/'kpi41.csv.gz', index=False)
    print('written', len(k), 'rows', k.site.nunique(), 'sites', flush=True)


if __name__ == '__main__':
    main()
