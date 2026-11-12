"""Render the map normally and with its online tile host unavailable.

Uses installed Chrome in headless mode; writes only QA outputs under the map.
"""
from pathlib import Path
import html
from html.parser import HTMLParser
import json
import re
import subprocess
import argparse

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/'analysis/sindirgi/konum_kontrolu/harita.html'
OUT=MAP.parent/'render_check'
CHROME=Path('C:/Program Files/Google/Chrome/Application/chrome.exe')


class TileImages(HTMLParser):
    def __init__(self):
        super().__init__()
        self.visible=0

    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag!='img' or 'leaflet-tile-loaded' not in d.get('class',''):
            return
        if not d.get('src','').startswith('https://server.arcgisonline.com/'):
            return
        opacity=re.search(r'opacity:\s*([0-9.]+)',d.get('style',''))
        if opacity is None or float(opacity[1])>0:
            self.visible+=1


def capture(name,block_tiles,offline_only=False):
    args=[str(CHROME),'--headless=new','--disable-gpu','--no-first-run',
          '--no-default-browser-check','--disable-background-networking','--disable-sync',
          '--hide-scrollbars','--window-size=1440,1000','--virtual-time-budget=10000',
          '--user-data-dir='+str(OUT/(name+'_profile')),
          '--screenshot='+str(OUT/(name+'.png')),'--dump-dom']
    if offline_only:
        # Block every remote hostname: no location-derived tile requests leave the PC.
        args.append('--host-resolver-rules=MAP * ~NOTFOUND')
        args.append('--no-proxy-server')
    elif block_tiles:
        args.append('--host-resolver-rules=MAP server.arcgisonline.com ~NOTFOUND')
    args.append(MAP.as_uri())
    p=subprocess.run(args,capture_output=True,encoding='utf-8',errors='replace',timeout=45)
    (OUT/(name+'.html')).write_text(p.stdout,encoding='utf-8')
    (OUT/(name+'.log')).write_text(p.stderr,encoding='utf-8')
    status=re.search(r'<div\b[^>]*id="map_background_status"[^>]*>([^<]*)</div>',p.stdout)
    if not status:
        raise RuntimeError(f'{name}: map status missing; Chrome exit={p.returncode}')
    mode=re.search(r'data-map-background="([^"]+)"',status[0])[1]
    paths=len(re.findall(r'class="[^"]*\bleaflet-interactive\b',p.stdout))
    assert p.returncode==0 and mode in ['online','offline'],(name,p.returncode,mode)
    assert paths>=42,(name,paths)  # 26 inventory circles plus 16 selection circles.
    assert (OUT/(name+'.png')).stat().st_size>20000
    if block_tiles:
        assert mode=='offline',mode
    tiles=TileImages()
    tiles.feed(p.stdout)
    if mode=='online':
        assert tiles.visible>0,'Online background reported, but no visible image tile'
    return {'case':name,'background_mode':mode,'status':html.unescape(status[1]),
            'rendered_interactive_shapes':paths,'visible_background_tiles':tiles.visible,'passed':True}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline-only',action='store_true',
                        help='Block all remote hosts; test the local map fallback only')
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    text=MAP.read_text(encoding='utf-8')
    assert 'tile.openstreetmap.org/' not in text
    assert not re.search(r'<script\s+[^>]*src=',text)
    assert not re.search(r'<link\b[^>]*href="https?://',text)
    result=([capture('offline_all_hosts_blocked',True,offline_only=True)] if args.offline_only
            else [capture('normal',False),capture('tile_host_blocked',True)])
    (OUT/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=True))


if __name__=='__main__':
    main()
