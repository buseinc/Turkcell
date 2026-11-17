"""WSL: regression first, then frozen candidates, resumable. Never edits earlier runs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import csv
import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D15 = HERE.parent/'15_ta_yerlesim_2026-11-16'
SIM = HERE/'simulation'
ARTIFACTS = ['sectors.csv','ues.csv','radio_samples.csv','sinr_components.csv','measurements.csv','prb_usage.csv']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    temp.replace(path)


def load_module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def watch_progress():
    """Refresh the existing report without touching simulator inputs or outputs."""
    screening = json.loads((HERE/'screening.json').read_text(encoding='utf-8'))
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    names = [f"{c['label']}_draw{seed}" for c in screening['native_candidates'] for _,seed in plan['draws']]
    report = HERE/'SONUCLAR.md'
    start_marker, end_marker = '<!-- RUN_PROGRESS -->', '<!-- END_RUN_PROGRESS -->'
    while True:
        # The final summarizer owns the report after the comparison has been produced.
        if (HERE/'comparison.json').exists():
            return
        active_runner = False
        for proc in Path('/proc').glob('[0-9]*'):
            try:
                args = (proc/'cmdline').read_bytes().decode(errors='replace').split('\0')
                if int(proc.name)!=os.getpid() and any(Path(a).name=='study.py' for a in args) and '--watch-progress' not in args:
                    active_runner = True
                    break
            except (OSError,ValueError):
                pass
        rows, completed, running = [], 0, 0
        for name in names:
            folder = SIM/'results'/name
            if (folder/'result.json').exists():
                completed += 1
                status, point = 'Tamamlandı', '4,00 / 4 saniye'
            elif (folder/'run.log').exists():
                status = 'Çalışıyor' if active_runner else 'Koşu süreci durmuş; kontrol gerekli'
                running += int(active_runner)
                sample = 0.0
                csv_path = folder/'radio_samples.csv'
                if csv_path.exists():
                    with csv_path.open('rb') as stream:
                        stream.seek(max(0,csv_path.stat().st_size-8192))
                        lines = stream.read().decode(errors='replace').splitlines()
                    for line in reversed(lines):
                        try:
                            if len(line.split(','))!=7: continue
                            sample = float(line.split(',')[0])
                            break
                        except ValueError:
                            pass
                point = f'En az {sample:.2f} / 4 saniye (yaklaşık %{100*sample/4:.0f})'.replace('.',',')
            else:
                status, point = 'Sırada', '—'
            rows.append(f'| {name} | {status} | {point} |')
        now = datetime.now(timezone(timedelta(hours=3))).strftime('%H:%M:%S')
        status_line = f'**Durum: {completed}/{len(names)} koşu tamamlandı; {running} koşu çalışıyor. Son kontrol: {now} (Türkiye saati).**'
        block = [start_marker,'', '| Koşu | Durum | Hesaplanan simülasyon zamanı |',
                 '|---|---|---|',*rows,'',
                 'Bu tablo 30 saniyede bir yenilenir. İlerleme, son yazılan ölçüm örneğine dayanır; dosya tamponlaması nedeniyle biraz geriden gelebilir. 4 saniye simülasyon süresidir, gerçek bekleme süresi değildir.',
                 '',end_marker]
        content = report.read_text(encoding='utf-8')
        lines = content.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('**Durum:'):
                lines[i] = status_line
                break
        content = '\n'.join(lines)
        if start_marker in content and end_marker in content:
            start = content.index(start_marker)
            end = content.index(end_marker)+len(end_marker)
            content = content[:start]+'\n'.join(block)+content[end:]
        # Do not overwrite a final report that appeared during this sample.
        if (HERE/'comparison.json').exists():
            return
        report.write_text(content+'\n',encoding='utf-8')
        if not active_runner:
            return
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--regression-only',action='store_true')
    args = parser.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    screening = json.loads((HERE/'screening.json').read_text(encoding='utf-8'))
    assert screening['gate_passed'], 'Screening has not passed'
    for name,h in plan['source_hashes'].items():
        assert sha(SIM/name)==h, name
    for name,h in plan['input_hashes'].items():
        assert sha(HERE/'inputs'/name)==h, name
    previous = load_module('ta_study',D15/'study.py')
    targets = previous.radio.read(HERE/'inputs/targets.csv')
    (HERE/'logs').mkdir(exist_ok=True)

    def run(name,az,seed,loss,tilt,vertical,build=False):
        up = HERE/'inputs'/f'ues_S0TA_{seed}.csv'
        count = len(previous.read(up))
        key = {'name':name,'az':az,'seed':seed,'indoor_loss_db':loss,'downtilt_deg':tilt,
               'vertical_pattern':vertical,'source_hashes':plan['source_hashes'],
               'input_hashes':plan['input_hashes'],'duration':4,'warmup':1}
        folder = SIM/'results'/name
        cache = folder/'experiment16_cache.json'
        cached = False
        if cache.exists():
            old = json.loads(cache.read_text())
            cached = old.get('key')==key and all((folder/n).exists() and sha(folder/n)==h for n,h in old.get('output_hashes',{}).items()) and bool(old.get('output_hashes'))
        build_manifest = SIM/'build/source_manifest.json'
        current_source = hashlib.sha256(b''.join((SIM/n).read_bytes() for n in
            ['sindirgi_baseline.cc','building-vertical-model.h','static-shadow-model.h'])).hexdigest()
        build_valid = (SIM/'build/sindirgi_baseline').exists() and build_manifest.exists()
        if build_valid:
            build_valid = json.loads(build_manifest.read_text()).get('source_sha256') == current_source
        needs_build = build and not build_valid
        if not cached or needs_build:
            cmd = [sys.executable,str(SIM/'run_baseline.py'),'--sites','0','--ues',str(count),
                   '--duration','4','--sites-file',str(HERE/'inputs'/f'sites_S0TA_{az}.csv'),
                   '--ue-file',str(up),'--mixed-cqi','1','--beamwidth','120','--exponent','3',
                   '--enb-power','49','--receiver-nf','9','--shadow-std','0','--dl-earfcn','1300',
                   '--udp-jitter','1','--name',name,'--indoor-loss',str(loss),'--downtilt',str(tilt),
                   '--vertical-pattern',str(vertical),'--measurement-ues','256']
            if not needs_build: cmd.append('--skip-build')
            print('START',name,flush=True)
            with (HERE/'logs'/f'{name}.log').open('w') as log:
                subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            save(cache,{'key':key,'output_hashes':{n:sha(folder/n) for n in ARTIFACTS}})
        return folder

    regression = run('regression_disabled_draw701',42,701,0,0,0,build=True)
    ref = D15/'simulation/results/S0TA_draw701'
    checks = {}
    for n in ARTIFACTS:
        old_bytes, new_bytes = (ref/n).read_bytes(), (regression/n).read_bytes()
        old_content, new_content = old_bytes.replace(b'\r\n',b'\n'), new_bytes.replace(b'\r\n',b'\n')
        checks[n] = {'new':sha(regression/n),'old':sha(ref/n),'equal':old_bytes==new_bytes,
                     'content_equal_after_CRLF_to_LF':old_content==new_content,
                     'old_CRLF_count':old_bytes.count(b'\r\n'),'new_CRLF_count':new_bytes.count(b'\r\n')}
    passed = all(c['content_equal_after_CRLF_to_LF'] for c in checks.values())
    save(HERE/'regression.json',{'passed':passed,'raw_bytes_passed':all(c['equal'] for c in checks.values()),
         'comparison':'Exact byte equality after CRLF-to-LF transport normalization only; no numeric tolerance, rounding or row reordering.',
         'files':checks})
    if not passed: raise RuntimeError('Byte regression failed; candidate runs forbidden')
    print('CONTENT REGRESSION PASSED (CRLF/LF recorded separately)',flush=True)
    if args.regression_only: return

    def one(c,az,seed):
        name = f"{c['label']}_draw{seed}"
        folder = run(name,az,seed,c['indoor_loss_db'],c['downtilt_deg'],c['vertical_pattern'])
        full = previous.radio.metrics(folder,1)
        metrics = previous.measurement_metrics(full,256)
        measured = [u for u in full['ues'] if u['ue_id']<256]
        prb = previous.read(folder/'prb_usage.csv')
        sites = metrics['sites']
        # Missing evaluation sites invalidate the result; no dropping hard-to-serve sites.
        missing = sorted(set(plan['train_sites']+plan['holdout_sites'])-set(sites))
        return {'case':dict(c,az=az,ue_seed=seed,name=name),
                'sites':sites,'missing_sites':missing,
                'training':previous.ev.evaluate(metrics,targets,'train'),
                'control':previous.ev.evaluate(metrics,targets,'holdout'),
                'measurement_connected':sum(bool(u['connected']) for u in measured),
                'measurement_with_dl':sum(u['dl_bytes']>0 for u in measured),
                'prb_mean_achieved':statistics.mean(float(r['dl_prb_utilization']) for r in prb)}
    results = []
    planned = len(screening['native_candidates'])*len(plan['draws'])
    def progress():
        report = HERE/'SONUCLAR.md'
        content = report.read_text(encoding='utf-8')
        lines = content.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('**Durum:'):
                lines[i] = f'**Durum: Eski sonuçla kontrol geçti (yalnız CRLF/LF farkı). Yeni koşular: {len(results)}/{planned} tamamlandı.**'
                break
        marker = '<!-- RUN_PROGRESS -->'
        if marker in '\n'.join(lines):
            text = '\n'.join(lines)
            start = text.index(marker)
            end = text.index('<!-- END_RUN_PROGRESS -->')+len('<!-- END_RUN_PROGRESS -->')
            text = text[:start]+text[end:]
        else:
            text = '\n'.join(lines)
        status = [marker,'','| Koşu | Durum |','|---|---|']
        done = {r['case']['name'] for r in results}
        for c in screening['native_candidates']:
            for _,seed in plan['draws']:
                name = f"{c['label']}_draw{seed}"
                status.append(f"| {name} | {'Tamamlandı' if name in done else 'Sırada veya çalışıyor'} |")
        status += ['','<!-- END_RUN_PROGRESS -->','']
        position = text.index('\n',text.index('**Durum:'))
        report.write_text(text[:position]+'\n\n'+'\n'.join(status)+text[position:]+'\n',encoding='utf-8')
    progress()
    with ThreadPoolExecutor(max_workers=max(1,args.workers)) as pool:
        futures = [pool.submit(one,c,az,seed) for c in screening['native_candidates'] for az,seed in plan['draws']]
        for f in as_completed(futures):
            results.append(f.result())
            save(HERE/'checkpoint.json',{'completed':len(results),'planned':len(futures),'results':results})
            progress()
            print('DONE',results[-1]['case']['name'],flush=True)
    save(HERE/'result.json',{'completed':True,'results':sorted(results,key=lambda r:r['case']['name'])})
    subprocess.run([sys.executable,str(HERE/'summarize.py')],check=True)


if __name__=='__main__':
    if '--watch-progress' in sys.argv:
        watch_progress()
    else:
        main()
