"""Read-only audit of the supplied XLSX sources; write summaries under analysis/.

Requires pandas, numpy and openpyxl. Run: python analysis/audit_dataset.py
The streaming reader handles the inline-string/numeric XLSX cells in these exports.
It refuses shared strings, formulas and unsupported types rather than misreading them.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import csv
import json
import re
import zipfile
from html import unescape

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis'
EVAL = ['SITE_000440', 'SITE_000441', 'SITE_000130', 'SITE_000296',
        'SITE_000443', 'SITE_000554', 'SITE_000482', 'SITE_000444']


def rows(path):
    # These exports use unprefixed OpenXML tags and inline strings. Stream row
    # fragments instead of building millions of XML elements for numeric cells.
    row_pattern = re.compile(rb'<row\b[^>]*>(.*?)</row>', re.S)
    cell_pattern = re.compile(rb'<c\b([^>]*?)(?:/>|>(.*?)</c>)', re.S)
    ref_pattern = re.compile(rb'\br="([A-Z]+)\d+"')
    type_pattern = re.compile(rb'\bt="([^"]+)"')
    value_pattern = re.compile(rb'<v>(.*?)</v>|<t(?:\s[^>]*)?>(.*?)</t>', re.S)
    positions = {bytes([65+i]):i for i in range(26)}
    with zipfile.ZipFile(path) as z:
        with z.open('xl/worksheets/sheet1.xml') as source:
            pending = b''
            while chunk := source.read(2**20):
                pending += chunk
                end = pending.rfind(b'</row>')
                if end < 0:
                    continue
                block, pending = pending[:end+6], pending[end+6:]
                for match in row_pattern.finditer(block):
                    values = []
                    for attributes, body in cell_pattern.findall(match[1]):
                        letters = ref_pattern.search(attributes)[1]
                        if letters not in positions:
                            raise ValueError('Unsupported column beyond Z')
                        index = positions[letters]
                        values.extend([None]*(index+1-len(values)))
                        kind = type_pattern.search(attributes)
                        kind = kind[1] if kind else b'n'
                        if b'<f' in body:
                            raise ValueError('Formula in source')
                        value = value_pattern.search(body)
                        if kind == b'inlineStr':
                            value = unescape(value[2].decode()) if value else None
                        elif kind == b'n':
                            value = float(value[1]) if value else None
                        else:
                            raise ValueError(f'Unsupported cell type {kind!r}')
                        values[index] = value
                    yield values
            if b'<row' in pending:
                raise ValueError('Incomplete row at EOF')


def date_serial(value):
    # Excel floating-point dates can differ from quarter-hours by a microsecond.
    return (datetime(1899, 12, 30) + timedelta(seconds=round(value*86400, 3))).isoformat(sep=' ')


def write_json(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                   allow_nan=False), encoding='utf-8')


def main():
    coords = pd.read_excel(ROOT/'cell_site_coordinates/cell_site_coordinates.xlsx')
    cmap = dict(zip(coords.cell, coords.site))
    sites = coords.groupby('site').agg(cells=('cell','size'), lat=('lat','first'),
                                      lon=('lon','first'))
    inventory = {
        'rows': len(coords), 'cells': coords.cell.nunique(), 'sites': len(sites),
        'unique_coordinates': len(coords[['lon','lat']].drop_duplicates()),
        'duplicate_cell_rows': int(coords.cell.duplicated().sum()),
        'nulls': coords.isna().sum().to_dict(),
        'sites_with_multiple_coordinates': int((coords.groupby('site').apply(
            lambda d: len(d[['lon','lat']].drop_duplicates()), include_groups=False)>1).sum()),
        'bounds': {c:[float(coords[c].min()),float(coords[c].max())] for c in ['lat','lon']},
        'cells_per_site_distribution': sites.cells.value_counts().sort_index().to_dict(),
    }
    sites.to_csv(OUT/'site_inventory.csv')
    write_json('coordinates_audit.json', inventory)
    print('COORDINATES',json.dumps(inventory),flush=True)

    radio_iter = rows(ROOT/'experia/experia.xlsx')
    header = next(radio_iter)
    radio = pd.DataFrame(radio_iter, columns=header)
    for c in ['HOUR_ID'] + header[5:]:
        radio[c] = pd.to_numeric(radio[c])
    if pd.api.types.is_numeric_dtype(radio.DATE_ID):
        radio['DATE_ID'] = pd.to_datetime(radio.DATE_ID, unit='D', origin='1899-12-30')
    else:
        radio['DATE_ID'] = pd.to_datetime(radio.DATE_ID)
    radio['timestamp'] = radio.DATE_ID+pd.to_timedelta(radio.HOUR_ID,unit='h')
    radio['site'] = radio.FIRSTCELL.map(cmap)
    key = ['DATE_ID','HOUR_ID','FIRSTCELL']
    rstats = {
        'rows':len(radio),'columns':header,'cells':radio.FIRSTCELL.nunique(),
        'matched_cells':radio.loc[radio.site.notna(),'FIRSTCELL'].nunique(),
        'unmatched_cells':sorted(set(radio.FIRSTCELL)-set(cmap)),
        'matched_rows':int(radio.site.notna().sum()),'matched_sites':radio.site.nunique(),
        'timestamp_min':str(radio.timestamp.min()),'timestamp_max':str(radio.timestamp.max()),
        'dates':{str(k):v for k,v in radio.DATE_ID.value_counts().sort_index().to_dict().items()},
        'hours':sorted(radio.HOUR_ID.unique().tolist()),
        'unique_timestamps':radio.timestamp.nunique(),
        'duplicate_key_extra_rows':int(radio.duplicated(key).sum()),
        'exact_duplicate_extra_rows':int(radio.duplicated(header).sum()),
        'nulls':radio[header].isna().sum().to_dict(),
        'numeric':radio[header[5:]].describe(percentiles=[.01,.05,.5,.95,.99]).to_dict(),
        'cities':radio.CITY_NAME.nunique(),'districts':radio.DISTRICT_NAME.nunique(),
        'cells_with_multiple_districts':int((radio.groupby('FIRSTCELL').DISTRICT_NAME.nunique()>1).sum()),
    }
    cell_radio = radio.groupby('FIRSTCELL').agg(
        site=('site','first'), rows=('timestamp','size'), hours=('timestamp','nunique'),
        rsrp_mean=(header[6],'mean'),rsrp_median=(header[6],'median'),
        sinr_mean=(header[5],'mean'),rsrq_mean=(header[7],'mean'),ta_mean=(header[8],'mean'))
    cell_radio.to_csv(OUT/'radio_cell_summary.csv')
    rs = cell_radio.groupby('site').agg(cells=('rows','size'),radio_rows=('rows','sum'),
         rsrp_mean_of_cell_means=('rsrp_mean','mean'),min_rows_per_cell=('rows','min'),
         max_rows_per_cell=('rows','max'))
    rs = sites.join(rs.drop(columns='cells').rename(columns={'radio_rows':'radio_rows'}))
    rs['radio_cells'] = cell_radio.groupby('site').size()
    rs.to_csv(OUT/'radio_site_summary.csv')
    evaluation = rs.reindex(EVAL).reset_index().astype(object)
    rstats['evaluation_sites'] = evaluation.where(pd.notna(evaluation), None).to_dict('records')
    rstats['evaluation_sites_missing_coordinates'] = sorted(set(EVAL)-set(sites.index))
    write_json('experia_audit.json', rstats)
    print('EXPERIA',json.dumps({k:v for k,v in rstats.items() if k not in ['numeric','unmatched_cells']}),flush=True)
    radio_cells = set(radio.FIRSTCELL)
    del radio

    all_kpi_cells, all_kpi_sites = set(),set()
    file_summaries=[]
    all_pairs=Counter()
    for path in sorted(ROOT.glob('LTE Main KPI*/*.xlsx')):
        iterator = rows(path)
        columns = next(iterator)
        seen, keys3 = {},set()
        times=Counter(); cells=Counter(); raw_sites=Counter(); pairs=Counter()
        duplicate=exact=conflicting=duplicate3=mismatch=unmatched=0
        n=0
        counts=np.zeros(21,dtype=np.int64)
        sums=np.zeros(21)
        minima=np.full(21,np.inf); maxima=np.full(21,-np.inf)
        outside=np.zeros(21,dtype=np.int64)
        batch=[]
        def update():
            a=np.asarray(batch,dtype=float)
            ok=np.isfinite(a)
            counts[:] += ok.sum(axis=0)
            sums[:] += np.where(ok,a,0).sum(axis=0)
            minima[:] = np.minimum(minima,np.where(ok,a,np.inf).min(axis=0))
            maxima[:] = np.maximum(maxima,np.where(ok,a,-np.inf).max(axis=0))
            outside[:] += ((a<0)|(a>1)).sum(axis=0)
            batch.clear()
        for row in iterator:
            row.extend([None]*(24-len(row)))
            t,s,c=row[:3]
            key=(t,c)
            signature=tuple(row)
            if key in seen:
                duplicate+=1
                if seen[key] == signature:
                    exact+=1
                else:
                    conflicting+=1
            else:
                seen[key]=signature
            k3=(t,s,c)
            if k3 in keys3: duplicate3+=1
            keys3.add(k3)
            n+=1; times[t]+=1; cells[c]+=1; raw_sites[s]+=1; pairs[(c,s)]+=1
            if c not in cmap: unmatched+=1
            elif cmap[c]!=s: mismatch+=1
            batch.append(row[3:])
            if len(batch)==25000: update()
        if batch: update()
        numeric={}
        for i,c in enumerate(columns[3:]):
            numeric[c]={'non_null':int(counts[i]),'missing':int(n-counts[i]),
                'min':float(minima[i]) if counts[i] else None,
                'max':float(maxima[i]) if counts[i] else None,
                'mean':float(sums[i]/counts[i]) if counts[i] else None,
                'outside_0_1':int(outside[i])}
        per_cell_sites=defaultdict(set)
        for (c,s),count in pairs.items():
            per_cell_sites[c].add(s)
        summary={
            'file':str(path.relative_to(ROOT)),'rows':n,'columns':columns,
            'timestamp_min':date_serial(min(times)), 'timestamp_max':date_serial(max(times)),
            'unique_timestamps':len(times),
            'interval_minutes':sorted(set(round((b-a)*1440,5) for a,b in zip(sorted(times), sorted(times)[1:]))),
            'rows_by_timestamp':{date_serial(k):v for k,v in sorted(times.items())},
            'cells':len(cells),'site_labels':len(raw_sites),
            'matched_coordinate_cells':len(set(cells)&set(cmap)),
            'unmatched_cells':sorted(set(cells)-set(cmap)),
            'matched_experia_cells':len(set(cells)&radio_cells),
            'unmatched_coordinate_rows':unmatched,
            'site_mismatch_rows_among_matched':mismatch,
            'duplicate_cell_timestamp_extra_rows':duplicate,
            'exact_duplicate_extra_rows':exact,
            'conflicting_cell_timestamp_extra_rows':conflicting,
            'duplicate_cell_site_timestamp_extra_rows':duplicate3,
            'cells_with_multiple_site_labels':sum(len(v)>1 for v in per_cell_sites.values()),
            'observations_per_cell_distribution':dict(sorted(Counter(cells.values()).items())),
            'site_label_row_counts':dict(raw_sites),
            'numeric':numeric,
        }
        all_kpi_cells.update(cells); all_kpi_sites.update(raw_sites); all_pairs.update(pairs)
        file_summaries.append(summary)
        write_json(path.parent.name+'_audit.json',summary)
        print('KPI',json.dumps({k:v for k,v in summary.items() if k not in [
            'columns','unmatched_cells','rows_by_timestamp','site_label_row_counts','numeric',
            'observations_per_cell_distribution']}),flush=True)
    with (OUT/'kpi_cell_site_pairs.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['cell','kpi_site','coordinate_site','rows','matches'])
        for (c,s),n in sorted(all_pairs.items()):
            writer.writerow([c,s,cmap.get(c),n,cmap.get(c)==s])
    overview={'total_kpi_rows':sum(f['rows'] for f in file_summaries),
              'unique_kpi_cells':len(all_kpi_cells),'unique_kpi_site_labels':len(all_kpi_sites),
              'coordinate_cells_in_kpi':len(set(cmap)&all_kpi_cells),
              'experia_cells_in_kpi':len(radio_cells&all_kpi_cells),
              'coordinate_cells_missing_in_experia':sorted(set(cmap)-radio_cells),
              'coordinate_cells_missing_in_kpi':sorted(set(cmap)-all_kpi_cells),
              'files':file_summaries}
    write_json('kpi_audit.json',overview)
    daily = [{'date':s['timestamp_min'][:10], 'rows':s['rows'], 'cells':s['cells'],
              'coordinate_cells':s['matched_coordinate_cells'],
              'unmatched_coordinate_cells':len(s['unmatched_cells']),
              'unmatched_coordinate_rows':s['unmatched_coordinate_rows'],
              'experia_cells':s['matched_experia_cells'],
              'duplicate_cell_timestamp_rows':s['duplicate_cell_timestamp_extra_rows']}
             for s in file_summaries]
    pd.DataFrame(daily).to_csv(OUT/'kpi_daily_summary.csv',index=False)
    print('COMPLETE',json.dumps({k:v for k,v in overview.items()
                                if k!='files' and not isinstance(v,list)}),flush=True)


if __name__=='__main__':
    main()
