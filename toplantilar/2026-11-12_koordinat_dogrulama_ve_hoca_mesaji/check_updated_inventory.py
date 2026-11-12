"""Read-only coordinate workbook reconciliation; preserve historical experiments."""
from pathlib import Path
import csv, json, hashlib, math
from collections import defaultdict
import openpyxl

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PROJECT=ROOT/'ana_proje'
CURRENT=PROJECT/'cell_site_coordinates/cell_site_coordinates.xlsx'
OLD=ROOT/'pc_validation/20261110_pc/analysis_workspace/cell_site_coordinates/cell_site_coordinates.xlsx'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def read_book(p):
    w=openpyxl.load_workbook(p,read_only=True,data_only=True);s=w['Sheet1'];it=s.iter_rows(values_only=True)
    names=next(it);rows=[dict(zip(names,r),excel_row=i) for i,r in enumerate(it,2) if any(v is not None for v in r)]
    w.close();return rows
def distance(a,b):
    p,q=math.radians(a['lat']),math.radians(b['lat']);dlat=p-q;dlon=math.radians(a['lon']-b['lon'])
    return 6371000*2*math.asin(min(1,math.sqrt(math.sin(dlat/2)**2+math.cos(p)*math.cos(q)*math.sin(dlon/2)**2)))
def main():
    cur,old=read_book(CURRENT),read_book(OLD)
    cm={r['cell']:r for r in cur};om={r['cell']:r for r in old}
    groups=defaultdict(list)
    for r in cur:groups[r['site']].append(r)
    duplicate_cells=len(cur)-len(cm)
    conflicts=[s for s,rr in groups.items() if len({(r['lat'],r['lon']) for r in rr})>1]
    assert not duplicate_cells and not conflicts,(duplicate_cells,conflicts)
    assert all(r['cell'] and r['site'] and isinstance(r['lat'],(int,float)) and isinstance(r['lon'],(int,float)) and -90<=r['lat']<=90 and -180<=r['lon']<=180 for r in cur)
    changes=[{'cell':c,'old':om[c],'new':cm[c]} for c in om.keys()&cm.keys() if any(om[c][k]!=cm[c][k] for k in ['site','lat','lon'])]
    selected=read_csv(PROJECT/'sindirgi_lte_sites.csv');cells=read_csv(PROJECT/'sindirgi_lte_cells.csv')
    site_checks=[]
    for s in selected:
        rr=groups.get(s['site_id'],[]);sel={'lat':float(s['latitude']),'lon':float(s['longitude'])}
        site_checks.append({'site':s['site_id'],'role':s['role'],'current_cells':len(rr),
            'found':bool(rr),'distance_from_selection_m':distance(sel,rr[0]) if rr else None,
            'selection_lat':sel['lat'],'selection_lon':sel['lon'],
            'current_lat':rr[0]['lat'] if rr else None,'current_lon':rr[0]['lon'] if rr else None,
            'excel_rows':[r['excel_row'] for r in rr]})
    linkage=[{'cell':r['cell_id'],'expected_site':r['site_id'],'current_site':cm.get(r['cell_id'],{}).get('site'),
              'matches':cm.get(r['cell_id'],{}).get('site')==r['site_id']} for r in cells]
    radio=read_csv(PROJECT/'analysis/radio_cell_summary.csv');radio_ids={r['FIRSTCELL'] for r in radio}
    extra=sorted(set(groups)-{r['site'] for r in old})
    selected_ids={r['site_id'] for r in selected};origin={'lat':39.2461,'lon':28.0697}
    new_near=[{'site':s,'distance_to_reference_km':distance(groups[s][0],origin)/1000,'cells':len(groups[s])} for s in extra if distance(groups[s][0],origin)<=30000]
    candidates=[groups[s][0] for s in groups if any(r['cell'] in radio_ids for r in groups[s])]
    nearest=sorted(candidates,key=lambda r:distance(r,origin))[:8]
    core=[groups[r['site_id']][0] for r in selected if r['role']=='Evaluation' and r['site_id'] in groups]
    buffer=sorted([r for r in candidates if r['site'] not in {s['site'] for s in core}],key=lambda r:min(distance(r,s) for s in core))[:8]
    frozen_checks=[]
    all_buffer=sorted([rr[0] for s,rr in groups.items() if s not in {r['site'] for r in core}],key=lambda r:(min(distance(r,s) for s in core),r['site']))
    for count in [24,32,48]:
        rr=read_csv(ROOT/f'deneyler/06_genis_tarama_secilen_ayar_2026-11-10/inputs/sites_{count}_42_three.csv')
        historical={r['site']:r for r in read_csv(PROJECT/'analysis/sindirgi/candidate_sites.csv')}
        old_ids={r['site'] for r in rr};new_ids={r['site'] for r in core}|{r['site'] for r in all_buffer[:count-8]}
        frozen_checks.append({'total_sites':count,'missing_current':[r['site'] for r in rr if r['site'] not in groups],
            'new_nearest_topology_adds':sorted(new_ids-old_ids),'new_nearest_topology_drops':sorted(old_ids-new_ids),
            'maximum_coordinate_difference_m':max(distance({'lat':float(historical[r['site']]['lat']),'lon':float(historical[r['site']]['lon'])},groups[r['site']][0]) for r in rr if r['site'] in groups)})
    result={'checked_on':'2026-11-12','current_file':str(CURRENT.relative_to(ROOT)),'current_sha256':digest(CURRENT),
        'previous_file':str(OLD.relative_to(ROOT)),'previous_sha256':digest(OLD),
        'old_counts':{'cells':len(old),'sites':len({r['site'] for r in old})},
        'current_counts':{'cells':len(cur),'sites':len(groups)},'added_cells':len(cm.keys()-om.keys()),
        'removed_cells':sorted(om.keys()-cm.keys()),'changed_existing_rows':changes,'new_sites':extra,
        'duplicate_cell_count':duplicate_cells,'conflicting_site_coordinates':conflicts,
        'selected_site_checks':site_checks,'selected_cell_count':len(linkage),'selected_cell_matches':sum(r['matches'] for r in linkage),
        'selected_cell_mismatches':[r for r in linkage if not r['matches']],
        'radio_cell_count':len(radio_ids),'radio_cells_with_new_coordinates':len(radio_ids&cm.keys()),
        'radio_cells_without_new_coordinates':sorted(radio_ids-cm.keys()),
        'new_sites_within_30km':new_near,'nearest_eight_radio_sites':[r['site'] for r in nearest],
        'site549_buffer_rank':next(i for i,r in enumerate(all_buffer,1) if r['site']=='SITE_000549'),
        'evaluation_selection_still_matches':{r['site'] for r in nearest}=={r['site'] for r in core},
        'nearest_eight_buffer_sites':[r['site'] for r in buffer],
        'buffer_selection_still_matches':{r['site'] for r in buffer}=={r['site_id'] for r in selected if r['role']!='Evaluation'},
        'frozen_topology_checks':frozen_checks}
    (HERE/'coordinate_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
