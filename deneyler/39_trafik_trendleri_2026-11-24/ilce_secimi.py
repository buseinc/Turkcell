"""Per district: how many KPI cells and connected users on a normal Monday (20 Oct 2025). Counts only."""
import glob
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
P = Path(r'C:\Users\20umu\OneDrive\Desktop\Turkcell\ana_proje')
e = pd.read_excel(P/'experia/experia.xlsx', usecols=['DISTRICT_NAME', 'FIRSTCELL'])
dist = e.groupby('FIRSTCELL').DISTRICT_NAME.agg(lambda s: s.value_counts().index[0])
c = pd.read_excel(P/'cell_site_coordinates/cell_site_coordinates.xlsx').drop_duplicates('cell').set_index('cell').site
k = pd.read_excel(glob.glob(str(P/'LTE Main KPI_20251020*'/'*.xlsx'))[0],
                  usecols=['DATETIME', 'CELL', 'EUtranCell_Availability_PC_ERI', 'Avg_Sim_RRC_Connected_User_Num_ERI'])
k['district'] = k.CELL.map(dist)
k['site'] = k.CELL.map(c)
print('KPI cells', k.CELL.nunique(), 'with district', k.dropna(subset=['district']).CELL.nunique())
g = k.dropna(subset=['district']).groupby('district')
cell_mean = k.groupby(['district', 'CELL']).Avg_Sim_RRC_Connected_User_Num_ERI.mean()
t = pd.DataFrame({'kpi_cells': g.CELL.nunique(), 'kpi_sites': g.site.nunique(),
                  'mean_users_per_cell': cell_mean.groupby('district').mean().round(1),
                  'total_users_day_mean': cell_mean.groupby('district').sum().round(0),
                  'avail_lt99_share': g.EUtranCell_Availability_PC_ERI.apply(lambda s: (s < 0.99).mean()).round(3)})
v = pd.read_csv(Path(r'C:\Users\20umu\OneDrive\Desktop\Turkcell\deneyler\35_bolge_secimi_2026-11-21\veri_kapsami.csv')).set_index('district')
t = t.join(v[['sites_per_100km2', 'mean_nearest_site_km', 'lat', 'lon']])
print(t.sort_values('total_users_day_mean', ascending=False).to_string())
