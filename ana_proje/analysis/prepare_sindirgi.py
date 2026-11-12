"""Verify the proposed region and export maps and local-metre coordinates.

Run from any directory: python analysis/prepare_sindirgi.py
Requires numpy, pandas, openpyxl, matplotlib, plotly and folium.
No source data are modified. Supplemental links retain their provenance.
"""
from pathlib import Path
import hashlib
import json
import platform

import folium
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from map_background import add_resilient_background

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis' / 'sindirgi'
LAT0, LON0 = 39.2461, 28.0697  # Reference supplied in the project; not a damage claim.
RADIUS_KM = 30.0  # Map/search display radius, not a radio coverage radius.
A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
COLORS = {'Evaluation': '#0072b2', 'Interference buffer': '#d55e00',
          'Unselected': '#8a929b'}


def haversine(lat, lon, lat_ref, lon_ref):
    p, l, p0, l0 = map(np.radians, (lat, lon, lat_ref, lon_ref))
    a = np.sin((p-p0)/2)**2 + np.cos(p)*np.cos(p0)*np.sin((l-l0)/2)**2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def ecef(lat, lon):
    """WGS84 surface coordinates; actual ground elevation is unavailable."""
    p, l = np.radians(lat), np.radians(lon)
    n = A / np.sqrt(1-E2*np.sin(p)**2)
    return np.column_stack((n*np.cos(p)*np.cos(l), n*np.cos(p)*np.sin(l),
                            n*(1-E2)*np.sin(p)))


def enu_rotation():
    p, l = np.radians(LAT0), np.radians(LON0)
    return np.array([[-np.sin(l), np.cos(l), 0],
                     [-np.sin(p)*np.cos(l), -np.sin(p)*np.sin(l), np.cos(p)],
                     [np.cos(p)*np.cos(l), np.cos(p)*np.sin(l), np.sin(p)]])


def local_enu(lat, lon):
    return (ecef(lat, lon)-ecef([LAT0], [LON0])) @ enu_rotation().T


def inverse_enu(points):
    xyz = points @ enu_rotation() + ecef([LAT0], [LON0])
    x, y, z = xyz.T
    horizontal = np.hypot(x, y)
    p = np.arctan2(z, horizontal*(1-E2))
    for _ in range(12):
        n = A / np.sqrt(1-E2*np.sin(p)**2)
        p = np.arctan2(z+E2*n*np.sin(p), horizontal)
    return np.degrees(p), np.degrees(np.arctan2(y, x))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_maps(candidates, chosen):
    local = candidates[candidates.within_display_radius].copy()
    # Self-contained site map with optional online background and offline grid.
    m = folium.Map(location=[LAT0, LON0], zoom_start=10, tiles=None,
                   control_scale=True)
    add_resilient_background(m,LAT0,LON0)
    groups = {role:folium.FeatureGroup(name=f'{role} ({int((local.role==role).sum())})')
              for role in COLORS}
    for _, row in local.iterrows():
        details = (f'<b>{row.site}</b><br>{row.role}<br>'
                   f'Reference distance: {row.distance_to_reference_km:.3f} km<br>'
                   f'East/North: {row.x_m:.1f} / {row.y_m:.1f} m<br>'
                   f'Coordinate source: {row.coordinate_source}<br>'
                   f'Radio cells with supplemental links: {int(row.linked_radio_cells)}')
        folium.CircleMarker([row.lat, row.lon], radius=7 if row.role!='Unselected' else 4,
                            color=COLORS[row.role], fill=True, fill_opacity=.85,
                            tooltip=f'{row.site} / {row.role}',
                            popup=folium.Popup(details, max_width=380)).add_to(groups[row.role])
        if row.coordinate_source == 'selection_csv':
            folium.CircleMarker([row.lat, row.lon], radius=11, color='#672c91',
                                weight=2, fill=False,
                                tooltip='Coordinate supplied only by selection CSV').add_to(groups[row.role])
    for g in groups.values():
        g.add_to(m)
    folium.Marker([LAT0, LON0], tooltip='Supplied reference / epicenter',
                  icon=folium.DivIcon(html='<span style="color:#a50026;font-size:32px">★</span>',
                                      icon_size=(30,35),icon_anchor=(15,20))).add_to(m)
    folium.Circle([LAT0, LON0], radius=RADIUS_KM*1000, color='#777777',
                  weight=1, dash_array='6 6', fill=False,
                  tooltip='30 km display radius; not radio coverage').add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[local.lat.min()-.015, local.lon.min()-.015],
                  [local.lat.max()+.015, local.lon.max()+.015]])
    m.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:25px;left:15px;z-index:1000;background:white;'
        'padding:12px;border:1px solid #aaa;max-width:390px;font:13px sans-serif">'
        '<b>Sindirgi: site selection check</b><br>Blue: evaluation; orange: buffer; '
        'grey: unselected.<br>Purple ring: coordinate from selection CSV only.<br>'
        'Reference and search circle do not indicate damage or radio coverage.<br>'
        'Only the optional Esri background needs internet; the site map also works offline.</div>'))
    m.save(str(OUT/'site_map.html'))

    # Fully self-contained interactive plot: no CDN, basemap or map API needed.
    fig = go.Figure()
    for role, color in COLORS.items():
        d = local[local.role==role]
        custom = d[['site','lat','lon','distance_to_reference_km','coordinate_source']].values
        fig.add_trace(go.Scatter(x=d.x_m/1000, y=d.y_m/1000, mode='markers',
                                marker={'size':11 if role!='Unselected' else 7,'color':color},
                                name=role, customdata=custom,
                                hovertemplate=('%{customdata[0]}<br>lat/lon: %{customdata[1]:.6f}, '
                                               '%{customdata[2]:.6f}<br>E/N: %{x:.3f}, %{y:.3f} km'
                                               '<br>Reference: %{customdata[3]:.3f} km'
                                               '<br>%{customdata[4]}<extra></extra>')))
    fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers', name='Reference',
                            marker={'symbol':'star','size':18,'color':'#a50026'}))
    supplemental = local[local.coordinate_source=='selection_csv']
    fig.add_trace(go.Scatter(x=supplemental.x_m/1000, y=supplemental.y_m/1000,
                            mode='markers', name='Selection-only coordinates',
                            marker={'symbol':'circle-open','size':18,'color':'#672c91'},
                            text=supplemental.site, hovertemplate='%{text}<extra></extra>'))
    fig.update_layout(title='Sindirgi: known sites within 30 km (not a coverage map)',
                      template='plotly_white', xaxis_title='East from reference (km)',
                      yaxis_title='North from reference (km)',
                      yaxis={'scaleanchor':'x','scaleratio':1}, height=800)
    fig.write_html(OUT/'topology_offline.html', include_plotlyjs=True)

    # Exportable scientific figure with geographic and equal-scale Cartesian views.
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig, axes = plt.subplots(1, 2, figsize=(15, 8), constrained_layout=True)
    for role, color in COLORS.items():
        d = local[local.role==role]
        size = 65 if role!='Unselected' else 22
        axes[0].scatter(d.lon, d.lat, s=size, c=color, label=role, zorder=3)
        axes[1].scatter(d.x_m/1000, d.y_m/1000, s=size, c=color, label=role, zorder=3)
    for ax, px, py in [(axes[0], LON0, LAT0),(axes[1],0,0)]:
        ax.scatter([px],[py],marker='*',s=200,c='#a50026',label='Supplied reference',zorder=5)
        ax.grid(alpha=.25)
    offsets={'SITE_000296':(-42,4),'SITE_000443':(6,-13),'SITE_000441':(-38,6),
             'SITE_000554':(6,6),'SITE_000553':(6,-13),'SITE_000200':(-40,-13),
             'SITE_000206':(6,5),'SITE_000480':(-40,-8)}
    for _, row in chosen.iterrows():
        for ax,x,y in [(axes[0],row.lon,row.lat),(axes[1],row.x_m/1000,row.y_m/1000)]:
            ax.annotate(row.site.removeprefix('SITE_'), (x,y),
                        xytext=offsets.get(row.site,(6,5)), textcoords='offset points',
                        fontsize=8,color=COLORS[row.role])
    for ax,x,y in [(axes[0],supplemental.lon,supplemental.lat),
                   (axes[1],supplemental.x_m/1000,supplemental.y_m/1000)]:
        ax.scatter(x,y,s=170,facecolors='none',edgecolors='#672c91',linewidth=1.5,zorder=4)
    axes[0].set(xlabel='Longitude (deg E)',ylabel='Latitude (deg N)',title='Geographic site positions')
    axes[0].set_aspect(1/np.cos(np.radians(LAT0)))
    axes[1].set(xlabel='East from reference (km)',ylabel='North from reference (km)',
                title='WGS84 local ENU; ground assumed flat')
    axes[1].set_aspect('equal')
    axes[0].legend(loc='upper left',fontsize=8)
    fig.suptitle('Sindirgi candidate and selected sites | 30 km display radius\n'
                 'Labels: SITE_ suffix. Purple ring: selection-only coordinate. No coverage/damage inference.',
                 fontsize=13)
    fig.savefig(OUT/'site_positions.png',dpi=180)
    fig.savefig(OUT/'site_positions.svg')
    plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    coordinate_path=ROOT/'cell_site_coordinates/cell_site_coordinates.xlsx'
    coords=pd.read_excel(coordinate_path)
    radio=pd.read_csv(ROOT/'analysis/radio_cell_summary.csv')
    selected=pd.read_csv(ROOT/'sindirgi_lte_sites.csv')
    links=pd.read_csv(ROOT/'sindirgi_lte_cells.csv')
    assert coords.cell.is_unique and selected.site_id.is_unique and links.cell_id.is_unique
    if set(links.cell_id)-set(radio.FIRSTCELL):
        raise ValueError('Selection refers to cells absent from Experia summary')
    inventory=coords.groupby('site').agg(lat=('lat','first'),lon=('lon','first'),
                                        inventory_cells=('cell','size')).reset_index()
    inventory['coordinate_source']='coordinate_inventory'
    inventory['role']='Unselected'
    inventory['selection_rank']=np.nan
    position_errors={}
    for _,row in selected.iterrows():
        mask=inventory.site==row.site_id
        if mask.any():
            pos=inventory.loc[mask].iloc[0]
            error=float(haversine(pos.lat,pos.lon,row.latitude,row.longitude)*1000)
            if error > .2:
                raise ValueError(f'Site coordinate conflict: {row.site_id}: {error:.3f} m')
            position_errors[row.site_id]=error
        else:
            inventory.loc[len(inventory)]={'site':row.site_id,'lat':row.latitude,
                'lon':row.longitude,'inventory_cells':np.nan,'coordinate_source':'selection_csv',
                'role':'Unselected','selection_rank':np.nan}
            mask=inventory.site==row.site_id
        inventory.loc[mask,'role']=row.role
        inventory.loc[mask,'selection_rank']=row['rank']

    linkage=links[['cell_id','site_id','role']].merge(
        radio[['FIRSTCELL','site','rows']],left_on='cell_id',right_on='FIRSTCELL',
        how='left',validate='one_to_one').rename(columns={'site':'inventory_site','rows':'full_period_rows'})
    conflicts=linkage.inventory_site.notna() & (linkage.inventory_site!=linkage.site_id)
    if conflicts.any():
        raise ValueError('Cell/site conflict between inventory and selection CSV')
    linkage['link_source']=np.where(linkage.inventory_site.isna(),'selection_csv','coordinate_inventory')
    linkage.to_csv(OUT/'selected_cell_linkage.csv',index=False)
    supplemented=radio.copy()
    lookup=links.set_index('cell_id').site_id
    supplemented['linked_site']=supplemented.site.fillna(supplemented.FIRSTCELL.map(lookup))
    stats=supplemented.groupby('linked_site').agg(linked_radio_cells=('FIRSTCELL','size'),
                                                linked_radio_rows=('rows','sum'))
    inventory=inventory.merge(stats,left_on='site',right_index=True,how='left',validate='one_to_one')
    inventory['linked_radio_cells']=inventory.linked_radio_cells.fillna(0).astype(int)
    inventory['radio_eligible']=inventory.linked_radio_cells>0
    inventory['distance_to_reference_km']=haversine(inventory.lat,inventory.lon,LAT0,LON0)
    xyz=local_enu(inventory.lat,inventory.lon)
    inventory['x_m'],inventory['y_m']=xyz[:,0],xyz[:,1]
    inventory['z_ground_m']=0.0
    inventory['enu_up_curvature_m']=xyz[:,2]  # Not ground elevation and not the ns-3 z input.
    evaluation=inventory[inventory.role=='Evaluation'].copy()
    inventory['distance_to_core_km']=[min(haversine(row.lat,row.lon,evaluation.lat,evaluation.lon))
                                       for _,row in inventory.iterrows()]
    inventory['within_display_radius']=inventory.distance_to_reference_km<=RADIUS_KM
    ranked_eval=inventory[inventory.radio_eligible].sort_values('distance_to_reference_km')
    eval_rank={site:i+1 for i,site in enumerate(ranked_eval.site)}
    ranked_buffer=inventory[inventory.radio_eligible & (inventory.role!='Evaluation')].sort_values('distance_to_core_km')
    buffer_rank={site:i+1 for i,site in enumerate(ranked_buffer.site)}
    inventory['reference_proximity_rank']=inventory.site.map(eval_rank)
    inventory['buffer_proximity_rank']=inventory.site.map(buffer_rank)
    chosen=inventory[inventory.role!='Unselected'].sort_values('selection_rank').copy()
    chosen=chosen.merge(selected[['site_id','observed_cells','hourly_records']],
                         left_on='site',right_on='site_id',validate='one_to_one').drop(columns='site_id')
    inventory.sort_values('distance_to_reference_km').to_csv(OUT/'candidate_sites.csv',index=False)
    chosen.to_csv(OUT/'sites_local.csv',index=False,float_format='%.9f')

    # Meaningful checks: invert the transform, test axes, preserve identity and rank.
    lat_back,lon_back=inverse_enu(xyz)
    roundtrip=float(max(np.max(abs(lat_back-inventory.lat)),np.max(abs(lon_back-inventory.lon))))
    assert roundtrip<1e-9 and np.max(abs(local_enu([LAT0],[LON0])))<1e-7
    east=local_enu([LAT0],[LON0+.001])[0]
    north=local_enu([LAT0+.001],[LON0])[0]
    assert east[0]>0 and north[1]>0 and abs(east[1])<.01 and abs(north[0])<.01
    eval_ok=set(ranked_eval.head(8).site)==set(evaluation.site)
    buffer_ok=set(ranked_buffer.head(8).site)==set(chosen[chosen.role=='Interference buffer'].site)
    assert eval_ok and buffer_ok
    delta=chosen.merge(selected[['site_id','km_to_epicenter','km_to_core']],left_on='site',right_on='site_id')
    dist_error=float(max(abs(delta.distance_to_reference_km-delta.km_to_epicenter).max(),
                         abs(delta.distance_to_core_km-delta.km_to_core).max()))
    assert dist_error<.0051
    points=chosen[['x_m','y_m']].to_numpy()
    planar=np.linalg.norm(points[:,None,:]-points[None,:,:],axis=2)
    sphere=haversine(chosen.lat.to_numpy()[:,None],chosen.lon.to_numpy()[:,None],
                     chosen.lat.to_numpy()[None,:],chosen.lon.to_numpy()[None,:])*1000
    mask=~np.eye(len(chosen),dtype=bool)
    relative=float(np.max(abs(planar[mask]-sphere[mask])/sphere[mask]))
    assert relative<.005  # Includes WGS84-vs-sphere model difference, not just projection error.
    summary={
        'known_sites':len(inventory),'radio_eligible_sites_with_supplement':int(inventory.radio_eligible.sum()),
        'sites_within_30km':int(inventory.within_display_radius.sum()),'selected_sites':len(chosen),
        'evaluation_is_nearest_8_known_eligible':eval_ok,'buffer_is_nearest_8_known_eligible':buffer_ok,
        'selection_only_coordinate_sites':chosen.loc[chosen.coordinate_source=='selection_csv','site'].tolist(),
        'supplemental_cell_links':int((linkage.link_source=='selection_csv').sum()),
        'unlocated_radio_cells_after_supplement':int(supplemented.linked_site.isna().sum()),
        'max_shared_coordinate_difference_m':max(position_errors.values()),
        'max_csv_distance_rounding_difference_km':dist_error,
        'max_enu_roundtrip_error_deg':roundtrip,
        'max_enu_planar_vs_spherical_distance_relative_difference':relative,
        'selected_pair_distance_range_m':[float(planar[mask].min()),float(planar.max())],
        'selected_extent_m':{'east':[float(chosen.x_m.min()),float(chosen.x_m.max())],
                             'north':[float(chosen.y_m.min()),float(chosen.y_m.max())]},
        'limitations':['Nearest-site checks apply only to known, located inventory plus selection supplements.',
                       'Unlocated Experia cells cannot enter the geographical ranking.',
                       'Selection-only coordinates/cell links are not independently verified.',
                       '30 km is a display radius; no coverage or damage is inferred.']}
    (OUT/'validation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    manifest={'reference':{'latitude':LAT0,'longitude':LON0,'ellipsoidal_height_m':0,
                           'source':'Project advisor/selection files; external epicenter not reverified'},
              'projection':{'datum_assumption':'WGS84','method':'geodetic -> ECEF -> local ENU',
                            'semi_major_axis_m':A,'inverse_flattening':1/F,
                            'x':'east metres','y':'north metres',
                            'z_ground_m':0,'z_note':'Flat scenario assumption; curvature U is not terrain.',
                            'reference_url':'https://gssc.esa.int/navipedia/index.php/Transformations_between_ECEF_and_ENU_coordinates'},
              'ranking_distance':{'method':'haversine','sphere_radius_km':6371.0,
                                   'reason':'Reproduce supplied selection distance convention'},
              'display_radius_km':RADIUS_KM,'python':platform.python_version(),
              'sources':[{'path':str(p.relative_to(ROOT)),'sha256':sha256(p)} for p in
                         [coordinate_path,ROOT/'analysis/radio_cell_summary.csv',
                          ROOT/'sindirgi_lte_sites.csv',ROOT/'sindirgi_lte_cells.csv']]}
    (OUT/'coordinate_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    write_maps(inventory,chosen)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
