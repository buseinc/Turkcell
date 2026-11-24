"""Windows: extract the 10 KPI days for the cells of the chosen districts (local operator data, never uploaded).
Usage: python suz.py <name> <DISTRICT_xxxx> [...]   -> kpi_<name>.csv.gz"""
from pathlib import Path
import glob
import sys

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
P = HERE.parent.parent/'ana_proje'
COLS = ['DATETIME', 'CELL', 'EUtranCell_Availability_PC_ERI', 'DownTime_Auto_PC_ERI', 'DownTime_Man_PC_ERI',
        'Avg_Sim_RRC_Connected_User_Num_ERI', 'DL_PRB_Util_%_ERI', 'DLTRF_VOLUME_MBYTE_ERI']


def main():
    name, districts = sys.argv[1], set(sys.argv[2:])
    e = pd.read_excel(P/'experia/experia.xlsx', usecols=['DISTRICT_NAME', 'FIRSTCELL'])
    dist = e.groupby('FIRSTCELL').DISTRICT_NAME.agg(lambda s: s.value_counts().index[0])
    cells = set(dist[dist.isin(districts)].index)
    site = pd.read_excel(P/'cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('cell').set_index('cell').site
    parts = []
    tmp = HERE/f'_parca_{name}'
    tmp.mkdir(exist_ok=True)
    for f in sorted(glob.glob(str(P/'LTE Main KPI_*'/'*.xlsx'))):
        part = tmp/(Path(f).stem.split()[-1] + '.csv.gz')
        if part.exists():  # resume: day already extracted
            k = pd.read_csv(part, parse_dates=['DATETIME'])
        else:
            k = pd.read_excel(f, usecols=COLS)
            k = k[k.CELL.isin(cells)]
            k.to_csv(part, index=False)
        parts.append(k)
        print(Path(f).name[:40], len(k), k.CELL.nunique(), flush=True)
    k = pd.concat(parts)
    k['district'] = k.CELL.map(dist)
    k['site'] = k.CELL.map(site)
    k.to_csv(HERE/f'kpi_{name}.csv.gz', index=False)
    print('written', len(k), 'rows', k.CELL.nunique(), 'cells')


if __name__ == '__main__':
    main()
