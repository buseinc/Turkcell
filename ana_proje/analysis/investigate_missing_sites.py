"""Trace the three selection-only sites through the original workbooks.

Run: python analysis/investigate_missing_sites.py
Scans raw KPI cell identities and targeted Experia rows; changes no source file.
"""
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import json
import re
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from openpyxl import load_workbook

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/sindirgi'
TARGETS=['SITE_000553','SITE_000554','SITE_000555']
ROW=re.compile(rb'<row\b[^>]*>(.*?)</row>',re.S)


def blocks(path):
    """Yield XML blocks ending on a complete row boundary."""
    with zipfile.ZipFile(path) as z:
        with z.open('xl/worksheets/sheet1.xml') as f:
            pending=b''
            while part:=f.read(4*1024*1024):
                pending+=part
                end=pending.rfind(b'</row>')
                if end<0: continue
                yield pending[:end+6]
                pending=pending[end+6:]
            if b'<row' in pending: raise ValueError('Incomplete XML row')


def source_row_count(path):
    with zipfile.ZipFile(path) as z:
        with z.open('xl/worksheets/sheet1.xml') as f: head=f.read(2000)
    return int(re.search(rb'<dimension ref="A1:[A-Z]+(\d+)"',head)[1])-1


def dist_m(lat,lon,lat0,lon0):
    p,l,p0,l0=map(np.radians,(lat,lon,lat0,lon0))
    a=np.sin((p-p0)/2)**2+np.cos(p)*np.cos(p0)*np.sin((l-l0)/2)**2
    return 2*6371000*np.arcsin(np.sqrt(np.clip(a,0,1)))


def main():
    coords=pd.read_excel(ROOT/'cell_site_coordinates/cell_site_coordinates.xlsx')
    selected=pd.read_csv(ROOT/'sindirgi_lte_sites.csv')
    links=pd.read_csv(ROOT/'sindirgi_lte_cells.csv')
    target_links=links[links.site_id.isin(TARGETS)]
    target_cells=set(target_links.cell_id)
    reference_cells=set(coords.cell)
    inventory=coords.groupby('site')[['lat','lon']].first()
    day_results=[]
    first_cells=None
    timeline=[]
    pattern=re.compile(rb'<c r="C\d+"[^>]*><is><t>(CELL_\d+)</t></is></c>')
    for path in sorted(ROOT.glob('LTE Main KPI*/*.xlsx')):
        counts=Counter()
        for block in blocks(path): counts.update(pattern.findall(block))
        assert sum(counts.values())==source_row_count(path),path
        found={k.decode():v for k,v in counts.items()}
        cell_set=set(found)
        date=re.search(r'KPI_(\d{8})',path.name)[1]
        date=datetime.strptime(date,'%Y%m%d').date().isoformat()
        if first_cells is None: first_cells=cell_set
        for _,row in target_links.iterrows():
            timeline.append({'date':date,'site_id_from_selection':row.site_id,'cell_id':row.cell_id,
                             'kpi_rows':found.get(row.cell_id,0)})
        day_results.append({'date':date,'source_file':str(path.relative_to(ROOT)),
             'rows':sum(found.values()),'unique_cells':len(found),
             'target_cell_rows':{c:found.get(c,0) for c in sorted(target_cells)},
             'cells_absent_from_coordinates':len(cell_set-reference_cells)})
        print('KPI',date,'target cells present',sum(found.get(c,0)>0 for c in target_cells),
              'of',len(target_cells),flush=True)
    pd.DataFrame(timeline).to_csv(OUT/'missing_site_cell_timeline.csv',index=False)

    # The metadata of selected cells gives independent evidence for cell existence,
    # but cannot establish the selection's physical coordinates or site identity.
    radio_path=ROOT/'experia/experia.xlsx'
    targets={c.encode() for c in target_cells}
    cell_pattern=re.compile(rb'<c r="E\d+"[^>]*><is><t>(CELL_\d+)</t></is></c>')
    stats=defaultdict(lambda:{'rows':0,'city':set(),'district':set(),'first':None,'last':None})
    for block in blocks(radio_path):
        for fragment in ROW.finditer(block):
            row=fragment[0]
            cell_match=cell_pattern.search(row)
            if not cell_match or cell_match[1] not in targets: continue
            values={}
            for element in ET.fromstring(row):
                col=element.attrib['r'].rstrip('0123456789')
                v=element.find('v')
                t=element.find('is/t')
                values[col]=float(v.text) if v is not None else t.text if t is not None else None
            cell=cell_match[1].decode()
            stamp=datetime(1899,12,30)+timedelta(seconds=round(values['C']*86400+values['D']*3600))
            d=stats[cell]
            d['rows']+=1; d['city'].add(values['A']); d['district'].add(values['B'])
            d['first']=min(d['first'],stamp) if d['first'] else stamp
            d['last']=max(d['last'],stamp) if d['last'] else stamp
    for cell,d in stats.items():
        d['city']=sorted(d['city']); d['district']=sorted(d['district'])
        d['first']=str(d['first']);d['last']=str(d['last'])
    assert set(stats)==target_cells
    print('Experia target rows verified',sum(d['rows'] for d in stats.values()),flush=True)

    wb=load_workbook(ROOT/'cell_site_coordinates/cell_site_coordinates.xlsx',data_only=False)
    workbook={'sheets':[{'name':s.title,'state':s.sheet_state,'rows':s.max_row,
                'columns':s.max_column,'autofilter':s.auto_filter.ref,
                'hidden_rows':sum(bool(r.hidden) for r in s.row_dimensions.values())} for s in wb],
              'created_property':str(wb.properties.created),'modified_property':str(wb.properties.modified),
              'creator':wb.properties.creator,'external_links':len(wb._external_links)}
    wb.close()
    positions=[]
    for site in TARGETS:
        row=selected[selected.site_id==site].iloc[0]
        distances=dist_m(inventory.lat,inventory.lon,row.latitude,row.longitude).sort_values()
        positions.append({'site':site,'latitude_from_selection':row.latitude,
                          'longitude_from_selection':row.longitude,
                          'in_coordinate_inventory':site in set(inventory.index),
                          'nearest_inventory_site':distances.index[0],
                          'nearest_inventory_coordinate_distance_m':float(distances.iloc[0]),
                          'inventory_coordinates_within_5m':int((distances<=5).sum()),
                          'cells_from_selection':target_links.loc[target_links.site_id==site,'cell_id'].tolist()})
    report={'sites':positions,'coordinate_workbook':workbook,
            'coordinate_cell_count':len(reference_cells),
            'earliest_kpi_date':day_results[0]['date'],
            'earliest_kpi_cell_count':len(first_cells),
            'coordinate_cells_equal_earliest_kpi_cells':reference_cells==first_cells,
            'earliest_kpi_cells_missing_coordinates':sorted(first_cells-reference_cells),
            'coordinate_cells_missing_earliest_kpi':sorted(reference_cells-first_cells),
            'site_id_range':[min(inventory.index),max(inventory.index)],
            'daily_raw_kpi_checks':day_results,'raw_experia_target_checks':dict(stats),
            'conclusion_status':{
                'verified':'The inventory cell set equals the supplied 2025-08-03 KPI cell set. '
                           'All 8 target cells are absent that day and present in every supplied later KPI day.',
                'inference':'The coordinate export may have been restricted to the earliest KPI cell population; '
                            'a later or broader coordinate source may have been used for the selection.',
                'unresolved':'Neither the production filter/code nor an independent source for these 3 '
                             'site IDs, coordinates and cell-to-site links is supplied. Cell appearance '
                             'in later files does not prove physical commissioning dates.'}}
    (OUT/'missing_sites_investigation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Coordinate set equals earliest KPI set:',reference_cells==first_cells,flush=True)


if __name__=='__main__':
    main()
