"""Verify this PC using isolated outputs; preserve the supplied measurements/results."""
import argparse
import contextlib
import csv
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / 'turkcell_tam_paket_2026-11-10'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_preserved_files():
    changed_runners = {'simulation/run_baseline.py','simulation/run_stock_smoke.py',
                       'simulation/probe_environment.py','simulation/inspect_radio_models.py',
                       'analysis/check_map_render.py'}
    manifest = load(PROJECT/'PAKET_ICERIGI.json')['files']
    checked = 0
    for relative, expected in manifest.items():
        if relative in changed_runners:
            continue
        assert sha(PROJECT/relative) == expected['sha256'], f'Original file changed: {relative}'
        checked += 1
    return {'passed': True, 'unchanged_historical_files': checked,
            'intentionally_updated_runners': sorted(changed_runners)}


def wsl_path(path):
    path = path.resolve()
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


def run(command, cwd, logfile):
    print('RUN', ' '.join(map(str, command)), flush=True)
    started = time.perf_counter()
    with logfile.open('w', encoding='utf-8') as stream:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(list(map(str, command)), cwd=cwd, stdout=stream,
                                stderr=subprocess.STDOUT, env=env)
    if result.returncode:
        raise RuntimeError(f'Exit {result.returncode}; see {logfile}')
    print(f'PASS ({time.perf_counter()-started:.1f}s): {logfile.name}', flush=True)


def compare_csv(actual, expected, columns=None, tolerance=1e-8):
    import numpy as np
    import pandas as pd
    a, b = pd.read_csv(actual), pd.read_csv(expected)
    if columns is not None:
        a, b = a[columns], b[columns]
    pd.testing.assert_frame_equal(a, b, check_dtype=False, check_exact=False,
                                  rtol=tolerance, atol=tolerance)
    numeric = a.select_dtypes(include='number').columns
    differences = [float(np.nanmax(np.abs(a[c].to_numpy()-b[c].to_numpy())))
                   for c in numeric if a[c].notna().any()]
    return {'rows': len(a), 'max_numeric_difference': max(differences, default=0.0)}


def analysis_checks(out):
    packages = ['numpy','pandas','scipy','openpyxl','matplotlib','plotly','folium','branca']
    workspace = out / 'analysis_workspace'
    # Copy only code and small inputs/results. Raw sources remain read-only.
    shutil.copytree(PROJECT, workspace, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('*.xlsx','__pycache__','build','pc_validation'))
    for relative in ['cell_site_coordinates/cell_site_coordinates.xlsx',
                     'sindirgi_lte_site_selection.xlsx']:
        dest = workspace / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / relative, dest)
    spec = importlib.util.spec_from_file_location('pc_audit', PROJECT/'analysis/audit_dataset.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    audit.OUT = workspace / 'analysis'
    print('RUN full raw-source audit (12 main Excel files)', flush=True)
    started = time.perf_counter()
    with (out/'audit.log').open('w', encoding='utf-8') as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            audit.main()
    print(f'PASS raw-source audit ({time.perf_counter()-started:.1f}s)', flush=True)
    versions = {p: importlib.metadata.version(p) for p in packages}
    compared = {}
    for name in ['site_inventory.csv','radio_cell_summary.csv','radio_site_summary.csv',
                 'kpi_daily_summary.csv','kpi_cell_site_pairs.csv']:
        compared[name] = compare_csv(workspace/'analysis'/name, PROJECT/'analysis'/name)
    for script in ['prepare_sindirgi.py','compare_site_locations.py',
                   'explain_site_selection.py','prepare_radio_study.py','report_radio_study.py',
                   'check_map_render.py']:
        extra = ['--offline-only'] if script == 'check_map_render.py' else []
        run([sys.executable, workspace/'analysis'/script]+extra, workspace, out/(script+'.log'))
    for name in ['measured_site_targets.csv','final_site_comparison.csv','final_ue_metrics.csv']:
        compared[name] = compare_csv(workspace/'analysis/sindirgi/radio_study'/name,
                                     PROJECT/'analysis/sindirgi/radio_study'/name)
    original_inputs = PROJECT/'analysis/sindirgi/radio_study/inputs'
    for path in original_inputs.glob('*.csv'):
        assert sha(path) == sha(workspace/'analysis/sindirgi/radio_study/inputs'/path.name), path
    return {'passed': True, 'python': sys.version, 'packages': versions,
            'csv_comparisons': compared, 'prepared_input_hashes_match': True,
            'map_browser_checks': load(workspace/'analysis/sindirgi/konum_kontrolu/render_check/result.json'),
            'raw_kpi_rows': load(workspace/'analysis/kpi_audit.json')['total_kpi_rows']}


def simulation_checks(out, distro):
    # All fresh simulator outputs go to a separate project under this check folder.
    workspace = out/'simulation_workspace'
    for directory in ['simulation','analysis/sindirgi/radio_study/frozen']:
        shutil.copytree(PROJECT/directory, workspace/directory, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('results','build','__pycache__'))
    prefix = ['wsl','--distribution',distro,'--exec','python3']
    def sim(script, *args):
        run(prefix+[wsl_path(workspace/'simulation'/script)]+list(args), workspace,
            out/(script+'.log'))
    sim('probe_environment.py','--output',wsl_path(out/'environment.json'))
    sim('run_stock_smoke.py')
    frozen = workspace/'analysis/sindirgi/radio_study/frozen'
    sim('run_baseline.py','--sites','2','--ues','6','--duration','1.2',
        '--sites-file',wsl_path(frozen/'sites.csv'),'--name','pc_smoke')
    sim('run_baseline.py','--skip-build','--sites','0','--ues','64','--duration','4',
        '--sites-file',wsl_path(frozen/'sites.csv'),'--ue-file',wsl_path(frozen/'ues.csv'),
        '--pathloss','log-distance','--exponent','3','--traffic','1','--name','pc_final')
    spec = importlib.util.spec_from_file_location('pc_radio', PROJECT/'simulation/run_radio_study.py')
    radio = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(radio)
    fresh = workspace/'simulation/results/pc_final'
    metrics = radio.metrics(fresh, 1.0)
    actual = metrics['ues']
    with (fresh/'ue_metrics.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(actual[0]))
        writer.writeheader()
        writer.writerows(actual)
    columns = ['ue_id','site','sector','rsrp','sinr','rsrq','connected','dl_bytes']
    with (PROJECT/'analysis/sindirgi/radio_study/final_ue_metrics.csv').open() as stream:
        expected = list(csv.DictReader(stream))
    assert len(actual) == len(expected) == 64
    max_difference = 0.0
    for a, b in zip(actual, expected):
        for column in columns:
            if column == 'site':
                assert a[column] == b[column], (a['ue_id'], column)
            else:
                av, bv = float(a[column]), float(b[column])
                assert math.isclose(av, bv, rel_tol=1e-7, abs_tol=1e-7), (a['ue_id'], column, av, bv)
                max_difference = max(max_difference, abs(av-bv))
    agreement = {'rows': 64, 'max_numeric_difference': max_difference}
    result = load(fresh/'result.json')
    assert result['connected_ues'] == 64 and result['ues_receiving_dl'] == 60
    smoke = load(workspace/'simulation/results/pc_smoke/result.json')
    assert smoke['connected_ues'] == 6 and smoke['ues_receiving_dl'] == 6
    assert result['source_sha256'] == sha(PROJECT/'simulation/sindirgi_baseline.cc')
    return {'passed': True, 'distro': distro, 'ns3_version': result['ns3_version'],
            'stock_smoke': load(workspace/'simulation/results/stock_smoke/result.json'),
            'geographical_smoke': smoke, 'final_run': result,
            'comparison_with_original': agreement}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['all','analysis','simulation'], default='all')
    parser.add_argument('--run-id', default=datetime.now().strftime('%Y%m%d_%H%M%S'))
    parser.add_argument('--distro', default='Ubuntu-22.04')
    args = parser.parse_args()
    if Path(args.run_id).name != args.run_id or args.run_id in ('.','..'):
        parser.error('run-id must be a directory name')
    out = ROOT/'pc_validation'/args.run_id
    out.mkdir(parents=True, exist_ok=True)
    os.environ['MPLCONFIGDIR'] = str(out/'matplotlib_cache')
    path = out/'verification.json'
    report = load(path) if path.exists() else {'run_id':args.run_id}
    report['all_checks_passed'] = False
    try:
        if args.phase in ('all','analysis'):
            report['analysis'] = analysis_checks(out)
        if args.phase in ('all','simulation'):
            report['simulation'] = simulation_checks(out, args.distro)
        report['source_preservation'] = check_preserved_files()
        report.pop('error', None)
        report['all_checks_passed'] = all(report.get(k,{}).get('passed',False)
                                         for k in ['analysis','simulation'])
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        if path.exists():
            current = load(path)
            current.pop('error', None)
            current.update(report)
            report = current
        report['all_checks_passed'] = ('error' not in report and all(
            report.get(k,{}).get('passed',False) for k in ['analysis','simulation']))
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print('Report:', path, flush=True)


if __name__ == '__main__':
    main()
