"""Self-contained Leaflet assets and an optional, resilient map background.

Site data and reference grid work from file:// without a network connection.
No OSM Standard tiles are requested or cached. The optional Esri background
only requests the current interactive viewport; service failures use the grid.
"""
from pathlib import Path
import base64
import re

import folium
from branca.element import Element,MacroElement,Template
import numpy as np

ASSETS=Path(__file__).resolve().parent/'map_assets'
ESRI_TILES='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
ESRI_ATTR=('Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; '
           'Esri, HERE, Garmin, Intermap, increment P Corp., GEBCO, USGS, FAO, NPS, NRCAN, '
           'GeoBase, IGN, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), '
           '&copy; OpenStreetMap contributors, GIS User Community')


class BackgroundFallback(MacroElement):
    _template=Template('''{% macro script(this, kwargs) %}
    (function () {
        const map = {{this._parent.get_name()}};
        const online = {{this.online.get_name()}};
        const grid = {{this.grid.get_name()}};
        const label = document.getElementById('map_background_status');
        const state = {mode: 'loading', loadedTiles: 0, tileErrors: 0};
        window.sindirgiMapDiagnostics = state;
        let guard;
        function show(mode, text) {
            state.mode = mode;
            label.dataset.mapBackground = mode;
            label.textContent = text;
        }
        function fallback() {
            clearTimeout(guard);
            if (map.hasLayer(online)) map.removeLayer(online);
            if (!map.hasLayer(grid)) grid.addTo(map);
            show('offline', 'Sade koordinat zemini: saha konumları çevrimdışı gösteriliyor.');
        }
        function watch() {
            clearTimeout(guard);
            state.loadedTiles = 0;
            state.tileErrors = 0;
            show('loading', 'Harita zemini yükleniyor; saha noktaları hazır.');
            guard = setTimeout(function () {
                if (map.hasLayer(online) && state.loadedTiles === 0) fallback();
            }, 6000);
        }
        online.on('tileload', function (event) {
            if (!map.hasLayer(online)) return;
            if (event.tile && event.tile.src.startsWith('data:')) return;
            state.loadedTiles++;
            clearTimeout(guard);
            show('online', 'Harita zemini: Esri. Saha noktaları yerel dosyalardan.');
        });
        online.on('tileerror', function () {
            state.tileErrors++;
            if (state.tileErrors >= 2 && map.hasLayer(online)) fallback();
        });
        map.on('baselayerchange', function (event) {
            if (event.layer === grid) {
                clearTimeout(guard);
                show('offline', 'Sade koordinat zemini: saha konumları çevrimdışı gösteriliyor.');
            } else if (event.layer === online) watch();
        });
        watch();
        if (!navigator.onLine) fallback();
    })();
    {% endmacro %}''')

    def __init__(self,online,grid):
        super().__init__()
        self._name='BackgroundFallback'
        self.online=online
        self.grid=grid


def add_resilient_background(m,lat0,lon0):
    """Call immediately after creating a folium.Map with tiles=None."""
    # Embed the small, versioned runtime. Copying the HTML alone remains valid.
    m.default_js=[]
    m.default_css=[]
    # Avoid tiles remaining transparent in file previews/headless renderers.
    m.options['fadeAnimation']=False
    css=(ASSETS/'leaflet.css').read_text(encoding='utf-8')
    for name in ['layers.png','layers-2x.png','marker-icon.png']:
        data=base64.b64encode((ASSETS/name).read_bytes()).decode()
        css=re.sub(r'url\([\'"]?images/'+re.escape(name)+r'[\'"]?\)',
                   'url(data:image/png;base64,'+data+')',css)
    m.get_root().header.add_child(Element('<style>'+css+'''
        .leaflet-container {background: #f6f8fa;}
        .leaflet-control-attribution {max-width: 58vw; font-size: 9px;}
    </style>'''),name='local_leaflet_css')
    for name in ['leaflet.js','jquery.min.js']:
        script=(ASSETS/name).read_text(encoding='utf-8').replace('</script','<\\/script')
        m.get_root().header.add_child(Element('<script>\n'+script+'\n</script>'),name='local_'+name)
    m.get_root().html.add_child(Element(
        '<div id="map_background_status" data-map-background="loading" '
        'style="position:fixed;top:12px;left:55px;z-index:1000;background:white;'
        'border:1px solid #aaa;border-radius:4px;padding:8px;max-width:360px;'
        'font:12px sans-serif">Harita zemini yükleniyor; saha noktaları hazır.</div>'))
    transparent='data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='
    online=folium.TileLayer(ESRI_TILES,attr=ESRI_ATTR,name='Esri topoğrafik harita (çevrimiçi)',
        max_zoom=19,overlay=False,show=True,error_tile_url=transparent,detect_retina=False)
    online.add_to(m)
    grid=folium.FeatureGroup(name='Sade koordinat zemini (çevrimdışı)',overlay=False,show=False)
    # Fixed reference lines cover the supplied inventory, not an external map.
    south,north=lat0-1.5,lat0+1.5
    west,east=lon0-2.5,lon0+2.5
    for lat in np.arange(np.floor(south*10)/10,north+.01,.1):
        folium.PolyLine([[float(lat),west],[float(lat),east]],color='#cbd5df',
                        weight=1,opacity=.65).add_to(grid)
    for lon in np.arange(np.floor(west*10)/10,east+.01,.1):
        folium.PolyLine([[south,float(lon)],[north,float(lon)]],color='#cbd5df',
                        weight=1,opacity=.65).add_to(grid)
    folium.PolyLine([[lat0,west],[lat0,east]],color='#8798a5',weight=1,dash_array='4 5').add_to(grid)
    folium.PolyLine([[south,lon0],[north,lon0]],color='#8798a5',weight=1,dash_array='4 5').add_to(grid)
    grid.add_to(m)
    m.add_child(BackgroundFallback(online,grid))
    return online,grid
