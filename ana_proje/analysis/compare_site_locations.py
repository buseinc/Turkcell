"""Compare raw inventory positions with the advisor's selection independently.

Run: python analysis/compare_site_locations.py
No radio-data filter is applied. No selection coordinates are inserted into the
inventory being checked. Existing simulator inputs and source data are unchanged.
"""
from pathlib import Path
import hashlib
import json

import folium
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from prepare_sindirgi import LAT0,LON0,local_enu,inverse_enu,haversine
from map_background import add_resilient_background

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/sindirgi/konum_kontrolu'
RADIUS_KM=30.0
TOLERANCE_M=1.0  # Six-decimal selection coordinates are rounded; compare at metre precision.
ROLE_NAMES={'Evaluation':'Ana sahalar (8)','Interference buffer':'Komşu sahalar (8)'}
COLORS={'Evaluation':'#0072b2','Interference buffer':'#d55e00'}


def project(frame):
    frame=frame.copy()
    xyz=local_enu(frame.lat,frame.lon)
    frame['x_dogu_m']=xyz[:,0]
    frame['y_kuzey_m']=xyz[:,1]
    frame['enu_up_egirilik_m']=xyz[:,2]
    frame['merkeze_uzaklik_km']=haversine(frame.lat,frame.lon,LAT0,LON0)
    lat,lon=inverse_enu(xyz)
    assert max(np.max(abs(lat-frame.lat)),np.max(abs(lon-frame.lon)))<1e-9
    return frame


def geographic_map(inventory,selection,comparison):
    near=inventory[inventory.merkeze_uzaklik_km<=RADIUS_KM]
    rest=inventory[inventory.merkeze_uzaklik_km>RADIUS_KM]
    m=folium.Map(location=[LAT0,LON0],tiles=None,control_scale=True,zoom_start=10)
    add_resilient_background(m,LAT0,LON0)
    near_layer=folium.FeatureGroup(name=f'Ana Excel: 30 km içindeki {len(near)} saha',show=True)
    rest_layer=folium.FeatureGroup(name=f'Ana Excel: diğer {len(rest)} saha',show=False)
    for rows,layer in [(near,near_layer),(rest,rest_layer)]:
        for _,r in rows.iterrows():
            text=(f'<b>{r.site}</b><br>Kaynak: ana koordinat Excel’i<br>'
                  f'Enlem/boylam: {r.lat:.6f}, {r.lon:.6f}<br>'
                  f'x (doğu): {r.x_dogu_m:.2f} m<br>y (kuzey): {r.y_kuzey_m:.2f} m<br>'
                  f'Merkeze uzaklık: {r.merkeze_uzaklik_km:.3f} km')
            folium.CircleMarker([r.lat,r.lon],radius=4,color='#555555',weight=1,
                fill=True,fill_color='#777777',fill_opacity=.9,tooltip=f'Ana Excel: {r.site}',
                popup=folium.Popup(text,max_width=350)).add_to(layer)
        layer.add_to(m)
    for role,color in COLORS.items():
        layer=folium.FeatureGroup(name='ChatGPT seçimi: '+ROLE_NAMES[role],show=True)
        for _,r in selection[selection.role==role].iterrows():
            check=comparison.loc[comparison.site==r.site].iloc[0]
            status=('Ana Excel’de kimlik bulunamadı' if check.status=='missing_inventory_id'
                    else f'Ana Excel ile konum farkı: {check.coordinate_difference_m:.3f} m')
            text=(f'<b>{int(r["rank"])}. {r.site}</b><br>Kaynak: seçim CSV’si<br>{ROLE_NAMES[role]}<br>'
                  f'Enlem/boylam: {r.lat:.6f}, {r.lon:.6f}<br>'
                  f'x (doğu): {r.x_dogu_m:.2f} m<br>y (kuzey): {r.y_kuzey_m:.2f} m<br>{status}')
            folium.CircleMarker([r.lat,r.lon],radius=10,color=color,weight=3,fill=False,
                tooltip=f'Seçim: {r.site}',popup=folium.Popup(text,max_width=380)).add_to(layer)
        layer.add_to(m)
    missing=folium.FeatureGroup(name='Ana Excel’de bulunmayan seçimler (3)',show=True)
    for _,r in comparison[comparison.status=='missing_inventory_id'].iterrows():
        folium.Marker([r.lat,r.lon],tooltip=f'{r.site}: yalnızca seçim dosyasında koordinat var',
            icon=folium.DivIcon(html='<span style="font:bold 25px sans-serif;color:#8e24aa">×</span>',
                                icon_size=(20,26),icon_anchor=(10,15))).add_to(missing)
    missing.add_to(m)
    names=folium.FeatureGroup(name='Seçilen sahaların adları',show=False)
    for _,r in selection.iterrows():
        folium.Marker([r.lat,r.lon],icon=folium.DivIcon(
            html=f'<span style="white-space:nowrap;font:11px sans-serif;background:#ffffffd9">{r.site}</span>',
            icon_size=(110,16),icon_anchor=(-12,-8))).add_to(names)
    names.add_to(m)
    folium.Marker([LAT0,LON0],tooltip='Danışmanın verdiği deprem merkezi / (x,y)=(0,0)',
        icon=folium.DivIcon(html='<span style="font:bold 35px sans-serif;color:#a50026">★</span>',
                            icon_size=(30,35),icon_anchor=(15,20))).add_to(m)
    circles=folium.FeatureGroup(name='10 / 20 / 30 km mesafe çemberleri',show=True)
    for radius in [10,20,30]:
        folium.Circle([LAT0,LON0],radius=radius*1000,color='#777777',weight=1,
                      dash_array='5 5',fill=False,tooltip=f'Merkezden {radius} km').add_to(circles)
    circles.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[near.lat.min()-.02,near.lon.min()-.02],[near.lat.max()+.02,near.lon.max()+.02]])
    m.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:24px;left:14px;z-index:1000;background:white;'
        'padding:12px;border:1px solid #aaa;max-width:420px;font:13px sans-serif">'
        '<b>Ana koordinatlar ile ChatGPT seçimini karşılaştırma</b><br>'
        '● Gri nokta: ana koordinat Excel’i<br><span style="color:#0072b2">○ Mavi çember:</span> seçilen ana saha<br>'
        '<span style="color:#d55e00">○ Turuncu çember:</span> seçilen komşu saha<br>'
        '<span style="color:#8e24aa">× Mor çarpı:</span> ana Excel’de bulunamayan kimlik<br>'
        '13 çember gri noktalarla örtüşüyor; 3 seçim yalnızca ek dosyada.<br>'
        'Noktaya tıklayarak kaynak ve koordinat farkını görebilirsiniz.<br>'
        '<small>30 km gösterim sınırıdır. Çizim saha konumlarını gösterir.</small></div>'))
    m.save(str(OUT/'harita.html'))


def offline_plot(inventory,selection,comparison):
    near=inventory[inventory.merkeze_uzaklik_km<=RADIUS_KM]
    rest=inventory[inventory.merkeze_uzaklik_km>RADIUS_KM]
    fig=go.Figure()
    hover=('%{customdata[0]}<br>Enlem: %{customdata[1]:.6f}<br>Boylam: %{customdata[2]:.6f}'
           '<br>x/doğu: %{x:.1f} m<br>y/kuzey: %{y:.1f} m<extra>%{fullData.name}</extra>')
    for d,label,visible in [(near,'Ana Excel: yakın sahalar',True),(rest,'Ana Excel: diğer sahalar','legendonly')]:
        fig.add_trace(go.Scatter(x=d.x_dogu_m,y=d.y_kuzey_m,mode='markers',name=label,
            visible=visible,marker={'size':7,'color':'#777777'},customdata=d[['site','lat','lon']].values,
            hovertemplate=hover))
    for role,color in COLORS.items():
        d=selection[selection.role==role]
        fig.add_trace(go.Scatter(x=d.x_dogu_m,y=d.y_kuzey_m,mode='markers',
            name='Seçim: '+ROLE_NAMES[role],marker={'symbol':'circle-open','size':19,'color':color,'line':{'width':2}},
            customdata=d[['site','lat','lon']].values,hovertemplate=hover))
    d=comparison[comparison.status=='missing_inventory_id']
    fig.add_trace(go.Scatter(x=d.x_dogu_m,y=d.y_kuzey_m,mode='markers',name='Ana Excel’de yok (3)',
        marker={'symbol':'x','size':12,'color':'#8e24aa'},customdata=d[['site','lat','lon']].values,
        hovertemplate=hover))
    fig.add_trace(go.Scatter(x=[0],y=[0],mode='markers',name='Verilen deprem merkezi',
        marker={'symbol':'star','size':20,'color':'#a50026'}))
    def ranges(d):
        return {'xaxis.range':[float(d.x_dogu_m.min()-2000),float(d.x_dogu_m.max()+2000)],
                'yaxis.range':[float(d.y_kuzey_m.min()-2000),float(d.y_kuzey_m.max()+2000)]}
    fig.update_layout(title='Ana Excel ve ChatGPT seçimi — yerel Kartezyen koordinatlar',
        template='plotly_white',height=850,xaxis_title='x: doğu (metre)',yaxis_title='y: kuzey (metre)',
        yaxis={'scaleanchor':'x','scaleratio':1},
        updatemenus=[{'type':'buttons','direction':'right','x':0,'y':1.11,
            'buttons':[{'label':'Yakın çevre (30 km)','method':'update',
                        'args':[{'visible':[True,'legendonly',True,True,True,True]},ranges(near)]},
                       {'label':'Tüm ana envanter','method':'update',
                        'args':[{'visible':[True,True,True,True,True,True]},ranges(inventory)]}]}])
    fig.write_html(OUT/'kartezyen.html',include_plotlyjs=True)


def static_plot(inventory,selection,comparison):
    near=inventory[inventory.merkeze_uzaklik_km<=RADIUS_KM]
    fig,ax=plt.subplots(figsize=(11,9),constrained_layout=True)
    ax.scatter(near.x_dogu_m/1000,near.y_kuzey_m/1000,s=26,c='#777777',zorder=2)
    offsets={'SITE_000296':(-48,5),'SITE_000443':(8,-13),'SITE_000441':(-52,-9),
             'SITE_000480':(-52,-10),'SITE_000200':(-52,-12),'SITE_000206':(8,5)}
    for role,color in COLORS.items():
        d=selection[selection.role==role]
        ax.scatter(d.x_dogu_m/1000,d.y_kuzey_m/1000,s=145,facecolors='none',edgecolors=color,
                   linewidths=2,zorder=3)
        for _,r in d.iterrows():
            ax.annotate(r.site.removeprefix('SITE_'),(r.x_dogu_m/1000,r.y_kuzey_m/1000),
                xytext=offsets.get(r.site,(8,6)),textcoords='offset points',color=color,fontsize=8)
    d=comparison[comparison.status=='missing_inventory_id']
    ax.scatter(d.x_dogu_m/1000,d.y_kuzey_m/1000,marker='x',s=75,c='#8e24aa',zorder=4)
    ax.scatter([0],[0],marker='*',s=260,c='#a50026',zorder=4)
    legend=[Line2D([],[],marker='o',color='#777777',linestyle='',label='Ana Excel: 30 km içindeki 26 saha'),
            Line2D([],[],marker='o',markerfacecolor='none',color='#0072b2',linestyle='',markersize=10,
                   label='ChatGPT seçimi: 8 ana saha'),
            Line2D([],[],marker='o',markerfacecolor='none',color='#d55e00',linestyle='',markersize=10,
                   label='ChatGPT seçimi: 8 komşu saha'),
            Line2D([],[],marker='x',color='#8e24aa',linestyle='',label='Ana Excel’de kimliği bulunmayan 3 saha'),
            Line2D([],[],marker='*',color='#a50026',linestyle='',markersize=12,label='Verilen deprem merkezi = (0,0)')]
    fig.legend(handles=legend,loc='outside lower center',ncol=2,fontsize=9)
    ax.set(xlabel='x: merkeze göre doğu (km)',ylabel='y: merkeze göre kuzey (km)',aspect='equal')
    ax.grid(alpha=.2)
    ax.set_title('Ana koordinat Excel’i ile ChatGPT seçimi aynı düzlemde\n'
                 '13 seçim ham koordinatlarla örtüşüyor; 3 seçim yalnızca ek dosyada',fontsize=13)
    fig.savefig(OUT/'konum_karsilastirma.png',dpi=180)
    fig.savefig(OUT/'konum_karsilastirma.svg')
    plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'cell_site_coordinates/cell_site_coordinates.xlsx'
    selection_path=ROOT/'sindirgi_lte_sites.csv'
    cells=pd.read_excel(source)
    for col in ['lat','lon']:
        if (cells.groupby('site')[col].nunique()!=1).any():
            raise ValueError('Inventory site has inconsistent coordinates')
    inventory=cells.groupby('site').agg(lat=('lat','first'),lon=('lon','first'),
                                       cells=('cell','nunique')).reset_index()
    selected=pd.read_csv(selection_path).rename(columns={'site_id':'site','latitude':'lat','longitude':'lon'})
    assert inventory.site.is_unique and selected.site.is_unique
    for d in [inventory,selected]:
        assert np.isfinite(d[['lat','lon']]).all().all()
        assert d.lat.between(-90,90).all() and d.lon.between(-180,180).all()
    inventory=project(inventory)
    selection=project(selected)
    comparison=selection[['rank','site','role','lat','lon','x_dogu_m','y_kuzey_m']].merge(
        inventory[['site','lat','lon','x_dogu_m','y_kuzey_m']],on='site',how='left',
        suffixes=('','_inventory'),validate='one_to_one',indicator=True)
    comparison['coordinate_difference_m']=1000*haversine(comparison.lat,comparison.lon,
                                                        comparison.lat_inventory,comparison.lon_inventory)
    comparison['status']=np.select([comparison._merge=='left_only',
        comparison.coordinate_difference_m>TOLERANCE_M],['missing_inventory_id','different_coordinate'],
        default='match_within_1m')
    comparison=comparison.drop(columns='_merge')
    near=inventory[inventory.merkeze_uzaklik_km<=RADIUS_KM]
    # Independent checks: origin/axes and per-source cardinality after grouping/projection.
    assert np.max(abs(local_enu([LAT0],[LON0])))<1e-7
    assert local_enu([LAT0],[LON0+.001])[0,0]>0
    assert local_enu([LAT0+.001],[LON0])[0,1]>0
    assert len(inventory)==cells.site.nunique() and len(comparison)==len(selected)
    inventory.to_csv(OUT/'ana_envanter_kartezyen.csv',index=False)
    near.to_csv(OUT/'ana_envanter_yakin_30km.csv',index=False)
    selection.to_csv(OUT/'chatgpt_secimi_kartezyen.csv',index=False)
    comparison.to_csv(OUT/'eslesme_kontrolu.csv',index=False)
    summary={'reference':{'latitude':LAT0,'longitude':LON0,'x_m':0,'y_m':0},
        'display_radius_km':RADIUS_KM,'coordinate_tolerance_m':TOLERANCE_M,
        'inventory_sites':len(inventory),'inventory_sites_within_radius':len(near),
        'selection_sites':len(selection),'matches':int((comparison.status=='match_within_1m').sum()),
        'coordinate_conflicts':int((comparison.status=='different_coordinate').sum()),
        'selection_only_site_ids':comparison.loc[comparison.status=='missing_inventory_id','site'].tolist(),
        'max_shared_coordinate_difference_m':float(comparison.coordinate_difference_m.max()),
        'method':'WGS84 geodetic -> ECEF -> local ENU; ellipsoidal height assumed zero',
        'up_warning':'ENU up is curvature relative to the tangent plane, not measured terrain height.',
        'source_separation':'Inventory is built only from its XLSX; selected positions only from selection CSV.',
        'radio_filter_applied':False,
        'sources':[{'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                   for p in [source,selection_path]]}
    (OUT/'ozet.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    geographic_map(inventory,selection,comparison)
    offline_plot(inventory,selection,comparison)
    static_plot(inventory,selection,comparison)
    print(json.dumps(summary,indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
