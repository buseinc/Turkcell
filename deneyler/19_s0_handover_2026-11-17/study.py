"""S0 regression, automatic A3 motion controls and full S0 integration on 3 draws."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import statistics
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SIM=HERE/'simulation'
BASE=HERE.parent/'14_cok_tasiyici_s2_2026-11-15'
BASE_FILES=['sectors.csv','ues.csv','radio_samples.csv','sinr_components.csv','measurements.csv','prb_usage.csv']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,value):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    temp.replace(path)


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


helpers=module('ho19_helpers',HERE.parent/'15_ta_yerlesim_2026-11-16/study.py')
read=helpers.read


def report_status(status,body=None):
    path=HERE/'SONUCLAR.md'
    text=path.read_text(encoding='utf-8')
    text='\n'.join(f'**Durum: {status}**' if x.startswith('**Durum:') else x for x in text.splitlines())
    if body is not None:
        marker='## Doğrulama sonuçları'
        text=text.split(marker)[0].rstrip()+'\n\n'+marker+'\n\n'+body
    path.write_text(text.rstrip()+'\n',encoding='utf-8')


def source_id():
    return hashlib.sha256(b''.join((SIM/n).read_bytes() for n in ['sindirgi_baseline.cc','static-shadow-model.h','handover-support.h'])).hexdigest()


def events(folder):
    path=folder/'handover_events.csv'
    return read(path) if path.exists() else []


def analyze_motion(case,folder,plan):
    ev=events(folder)
    user=read(folder/'ues.csv')[0]
    cells={r['synthetic_cell_id']:r for r in read(folder/'sectors.csv')}
    starts=[e for e in ev if e['actor']=='UE' and e['event']=='START']
    ends=[e for e in ev if e['actor']=='UE' and e['event']=='END_OK']
    errors=[e for e in ev if e['event']=='END_ERROR' or 'Failure' in e['event']]
    connections=[e for e in ev if e['actor']=='UE' and e['event']=='CONNECTION']
    initial=cells.get(connections[0]['cell_id'],{}).get('site') if connections else None
    final=cells.get(user['synthetic_cell_id'],{}).get('site')
    packets=read(folder/'packet_rx.csv')
    times=[float(r['time_s']) for r in packets]
    timeline=read(folder/'serving_timeline.csv')
    endpoint=read(HERE/'inputs'/case['waypoints'])[-1]
    reached=all(abs(float(user[k])-float(endpoint[k]))<1e-5 for k in ['x_m','y_m','z_m'])
    row={'case':case,'initial_site':initial,'final_site':final,'final_connected':int(user['rrc_connected']),
         'handover_starts':len(starts),'handover_completions':len(ends),'handover_errors':len(errors),
         'packets_received':len(times),'last_packet_time_s':times[-1] if times else None,
         'route_endpoint_reached':reached,'timeline_rows':len(timeline),
         'native_exit_code':json.loads((folder/'result.json').read_text())['process_exit_code']}
    checks={'route_endpoint_reached':reached,'initial_at_source':initial==case['expected_source_site']}
    if case['handover']:
        checks.update(exactly_one_automatic_handover=len(starts)==1 and len(ends)==1,
                      no_handover_errors=not errors,
                      target_connection=final==case['expected_target_site'] and int(user['rrc_connected'])==1)
        if len(starts)==1 and len(ends)==1:
            start,end=starts[0],ends[0]
            t0,t1=float(start['time_s']),float(end['time_s'])
            duration=t1-t0
            gaps=[b-a for a,b in zip(times,times[1:]) if a<=t1+1 and b>=t0-1]
            gap=max(gaps) if gaps else None
            src=cells[start['cell_id']]['site'];dst=cells[start['target_cell_id']]['site']
            enb_start=any(e['actor']=='ENB' and e['event']=='START' and e['cell_id']==start['cell_id'] and e['target_cell_id']==start['target_cell_id'] for e in ev)
            enb_end=any(e['actor']=='ENB' and e['event']=='END_OK' and e['cell_id']==end['cell_id'] for e in ev)
            row.update(handover_start_s=t0,handover_end_s=t1,handover_duration_s=duration,
                       source_cell=int(start['cell_id']),target_cell=int(start['target_cell_id']),
                       max_packet_gap_around_handover_s=gap,
                       packets_before=sum(t<t0 for t in times),packets_after=sum(t>t1+0.5 for t in times))
            checks.update(source_to_target=src==case['expected_source_site'] and dst==case['expected_target_site'] and end['cell_id']==start['target_cell_id'],
                          matching_enb_events=enb_start and enb_end,
                          bounded_handover_duration=0<=duration<=plan['acceptance']['max_handover_duration_s'],
                          data_before_and_after=row['packets_before']>0 and row['packets_after']>0,
                          bounded_packet_gap=gap is not None and gap<=plan['acceptance']['max_packet_gap_around_handover_s'])
    else:
        checks.update(no_handover_events=not starts and not ends and not errors,
                      initial_data_received=bool(times))
    row['checks']=checks;row['passed']=all(checks.values())
    return row


def analyze_static(case,folder):
    full=helpers.radio.metrics(folder,1)
    measured=helpers.measurement_metrics(full,256)
    old=json.loads((BASE/f"simulation/results/S0_draw{case['seed']}/metrics.json").read_text())
    before={u['ue_id']:u for u in old['ues']}
    current=full['ues']
    differences=[abs(u['rsrp']-before[u['ue_id']]['rsrp']) for u in current if u['rsrp'] is not None and before[u['ue_id']]['rsrp'] is not None]
    same=sum(u['site']==before[u['ue_id']]['site'] and u['sector']==before[u['ue_id']]['sector'] for u in current)
    meas=measured['ues'];ev=events(folder)
    handovers=[e for e in ev if e['event'] in ['START','END_OK','END_ERROR'] or 'Failure' in e['event']]
    connected=sum(bool(u['connected']) for u in meas);with_dl=sum(u['dl_bytes']>0 for u in meas)
    maximum=max(differences) if differences else None
    checks={'measurement_connected':connected==256,'measurement_receiving_dl':with_dl==256,
            'same_serving_cells':same==len(current),'no_stationary_handover_or_errors':not handovers,
            'same_rsrp':maximum is not None and maximum<=0.01}
    return {'case':case,'checks':checks,'passed':all(checks.values()),
            'measurement_connected':connected,'measurement_with_dl':with_dl,'unchanged_serving_ues':same,
            'total_ues':len(current),'rsrp_max_abs_change_db':maximum,'handover_events':len(handovers)}


def summarize():
    result=json.loads((HERE/'result.json').read_text(encoding='utf-8'))
    regression=json.loads((HERE/'regression.json').read_text(encoding='utf-8'))
    assert result['completed'] and len(result['motion_results'])==6 and len(result['static_results'])==3
    passed=regression['passed'] and all(r['passed'] for r in result['motion_results']+result['static_results'])
    positive=[r for r in result['motion_results'] if r['case']['handover']]
    negative=[r for r in result['motion_results'] if not r['case']['handover']]
    out={'integration_passed':passed,'regression_passed':regression['passed'],
         'motion_on_passed':all(r['passed'] for r in positive),'motion_off_passed':all(r['passed'] for r in negative),
         'full_S0_static_passed':all(r['passed'] for r in result['static_results']),
         'scope':'Automatic intra-frequency A3/X2 on S0; moving isolated pair is a protocol test, default ideal RRC.',
         'motion_results':result['motion_results'],'static_results':result['static_results']}
    save(HERE/'comparison.json',out)
    lines=['Handover kapalı tam S0 koşusunun altı CSV dosyası eski sonuçla aynı içerikte çıktı; yalnız CRLF/LF biçimi normalize edildi.','',
           '| Hareketli örnek | Handover | İlk saha | Son saha | Başlayan / biten | Geçiş süresi (ms) | Geçiş çevresinde en büyük paket aralığı (ms) | Kontrol |',
           '|---|---|---|---|---|---:|---:|---|']
    for r in sorted(result['motion_results'],key=lambda r:(r['case']['seed'],r['case']['handover'])):
        duration=r.get('handover_duration_s');gap=r.get('max_packet_gap_around_handover_s')
        lines.append(f"| {r['case']['seed']} | {'A3 açık' if r['case']['handover'] else 'Kapalı'} | {r['initial_site']} | {r['final_site']} | {r['handover_starts']}/{r['handover_completions']} | {duration*1000:.3f} | {gap*1000:.3f} | {'Geçti' if r['passed'] else 'Geçmedi'} |" if duration is not None and gap is not None else
                     f"| {r['case']['seed']} | {'A3 açık' if r['case']['handover'] else 'Kapalı'} | {r['initial_site']} | {r['final_site']} | {r['handover_starts']}/{r['handover_completions']} | — | — | {'Geçti' if r['passed'] else 'Geçmedi'} |")
    lines+=['','| Tam S0, A3 açık | Bağlanan ölçüm kullanıcısı | Veri alan | Hücresi korunan toplam kullanıcı | En büyük RSRP değişimi (dB) | Kontrol |',
            '|---|---:|---:|---:|---:|---|']
    for r in result['static_results']:
        lines.append(f"| {r['case']['seed']} | {r['measurement_connected']}/256 | {r['measurement_with_dl']}/256 | {r['unchanged_serving_ues']}/{r['total_ues']} | {r['rsrp_max_abs_change_db']:.8f} | {'Geçti' if r['passed'] else 'Geçmedi'} |")
    lines+=['','**Sonuç: '+('S0 için isteğe bağlı X2 + A3 RSRP handover doğrulandı.' if passed else 'Doğrulamanın tüm ölçütleri geçmedi; eksikler comparison.json içinde.')+'**','',
            'Hareket testinde geçiş emri verilmedi; A3 algoritması ölçüm koşuluyla otomatik karar verdi. UE ve eNB başlangıç/bitiş olayları, hedef hücre, paket alışları ve son bağlantı birlikte kontrol edildi.','',
            'Kaydedilen süreler mevcut ideal RRC modeline aittir; gerçek operatör gecikmesi veya deprem altında başarı oranı değildir. İki sahalık testte diğer 22 saha ve yük kullanıcıları yoktur. Tam S0 testleri sabit kullanıcılıdır; bu deney, tam ağda hareket/arıza/UAV performansını ayrıca kanıtlamaz. Frekanslar arası handover eklenmedi.','',
            'Yeni özellik varsayılan olarak kapalıdır; kaynak S0 ve eski deney dosyaları değiştirilmedi. Ayrıntılı olaylar simulation/results altındaki handover_events.csv, serving_timeline.csv ve hareket koşularının packet_rx.csv dosyalarındadır.']
    report_status('Handover doğrulaması tamamlandı. '+('Tüm kabul ölçütleri geçti.' if passed else 'Bazı kabul ölçütleri geçmedi.'),'\n'.join(lines))
    print(json.dumps({k:v for k,v in out.items() if k not in ['motion_results','static_results']},indent=2),flush=True)


def main():
    if '--summarize' in sys.argv:summarize();return
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for name,h in plan['source_hashes'].items():assert sha(SIM/name)==h,name
    for name,h in plan['input_hashes'].items():assert sha(HERE/'inputs'/name)==h,name
    (HERE/'logs').mkdir(exist_ok=True)
    manifest=SIM/'build/source_manifest.json'
    built=manifest.exists() and (SIM/'build/sindirgi_baseline').exists()
    if built:built=json.loads(manifest.read_text()).get('source_sha256')==source_id()
    if not built:
        with (HERE/'logs/build.log').open('w') as log:
            subprocess.run([sys.executable,str(SIM/'run_baseline.py'),'--build-only','--name','regression_S0_off'],stdout=log,stderr=subprocess.STDOUT,check=True)
    def run(case):
        folder=SIM/'results'/case['name']
        key={'source':source_id(),'case':case,'sites_sha256':sha(HERE/'inputs'/case['sites']),
             'ues_sha256':sha(HERE/'inputs'/case['ues_file']),'radio':plan['radio'],'A3':plan['algorithm']}
        if case.get('waypoints'):key['waypoints_sha256']=sha(HERE/'inputs'/case['waypoints'])
        cache=folder/'run_cache.json';cached=False
        if cache.exists():
            old=json.loads(cache.read_text())
            cached=old.get('key')==key and bool(old.get('outputs')) and all((folder/n).exists() and sha(folder/n)==h for n,h in old['outputs'].items())
        if not cached:
            cmd=[sys.executable,str(SIM/'run_baseline.py'),'--skip-build','--name',case['name'],
                 '--sites','0','--ues',str(case['ues']),'--duration',str(case['duration']),
                 '--sites-file',str(HERE/'inputs'/case['sites']),'--ue-file',str(HERE/'inputs'/case['ues_file']),
                 '--mixed-cqi','1','--udp-jitter','1','--beamwidth','120','--exponent','3','--enb-power','49',
                 '--receiver-nf','9','--shadow-std','0','--dl-earfcn','1300','--ul-earfcn','19300',
                 '--handover',str(case['handover']),'--handover-hysteresis','3','--handover-ttt-ms','256']
            if case.get('waypoints'):cmd+=['--waypoints',str(HERE/'inputs'/case['waypoints'])]
            if case.get('kind')=='motion' and not case['handover']:cmd+=['--allow-final-disconnect']
            print('START',case['name'],flush=True)
            with (HERE/'logs'/f"{case['name']}.log").open('w') as log:
                subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            files=BASE_FILES+['result.json']
            if case['handover'] or case.get('waypoints'):files+=['handover_events.csv','serving_timeline.csv']
            if case.get('waypoints'):files+=['packet_rx.csv']
            save(cache,{'key':key,'outputs':{n:sha(folder/n) for n in files}})
        return folder
    report_status('Önce handover kapalı S0 sonuçları doğrulanıyor.')
    case=plan['regression'];folder=run(case);ref=ROOT/case['reference']
    checks={n:{'old':sha(ref/n),'new':sha(folder/n),
               'equal':(ref/n).read_bytes().replace(b'\r\n',b'\n')==(folder/n).read_bytes().replace(b'\r\n',b'\n')} for n in case['files']}
    passed=all(c['equal'] for c in checks.values())
    save(HERE/'regression.json',{'passed':passed,'files':checks,'source_sha256':source_id(),
                                'normalization':'CRLF-to-LF only, no numeric tolerance'})
    if not passed:raise RuntimeError('Disabled S0 regression failed; no new cases will run.')
    print('REGRESSION PASSED',flush=True)
    motion=[];static=[]
    report_status('S0 eski sonuç kontrolü geçti; otomatik hareket testleri çalışıyor.')
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks={pool.submit(run,c):c for c in plan['motion_cases']}
        for future in as_completed(tasks):
            c=tasks[future];r=analyze_motion(c,future.result(),plan);motion.append(r)
            save(HERE/'checkpoint.json',{'phase':'motion','motion_results':motion,'static_results':static})
            print('DONE',c['name'],'passed',r['passed'],flush=True)
    if not all(r['passed'] for r in motion):
        save(HERE/'result.json',{'completed':False,'motion_results':motion,'static_results':static})
        raise RuntimeError('Motion protocol checks failed. Inspect checkpoint; full static runs not started.')
    report_status('Altı hareket kontrolü geçti; üç tam S0 örneği handover açıkken çalışıyor.')
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks={pool.submit(run,c):c for c in plan['static_cases']}
        for future in as_completed(tasks):
            c=tasks[future];r=analyze_static(c,future.result());static.append(r)
            save(HERE/'checkpoint.json',{'phase':'static','motion_results':motion,'static_results':static})
            print('DONE',c['name'],'passed',r['passed'],flush=True)
    save(HERE/'result.json',{'completed':True,
                           'motion_results':sorted(motion,key=lambda r:(r['case']['seed'],r['case']['handover'])),
                           'static_results':sorted(static,key=lambda r:r['case']['seed'])})
    summarize()


if __name__=='__main__':
    try:main()
    except Exception as exc:
        report_status('Çalışma durdu; hata kaydı incelenmeli.',str(exc))
        raise
