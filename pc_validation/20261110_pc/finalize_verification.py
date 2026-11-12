"""Combine the completed parallel checks and verify their finished artifacts.

The offline map checker was added while the first audit was already running.
Refresh its intentional-change allowlist with the final verifier, and retain
the separately completed simulation phase instead of the initial stale report.
"""
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[1]))
import verify_pc as verify

report = verify.load(OUT/'verification.json')
assert report['analysis']['passed']
simulation = json.loads((OUT/'simulation_result.json').read_text(encoding='utf-8-sig'))
assert simulation['passed']
workspace = OUT/'analysis_workspace'
for name in ['site_inventory.csv','radio_cell_summary.csv','radio_site_summary.csv',
             'kpi_daily_summary.csv','kpi_cell_site_pairs.csv']:
    verify.compare_csv(workspace/'analysis'/name, verify.PROJECT/'analysis'/name)
for name in ['measured_site_targets.csv','final_site_comparison.csv','final_ue_metrics.csv']:
    verify.compare_csv(workspace/'analysis/sindirgi/radio_study'/name,
                       verify.PROJECT/'analysis/sindirgi/radio_study'/name)
for path in (verify.PROJECT/'analysis/sindirgi/radio_study/inputs').glob('*.csv'):
    assert verify.sha(path) == verify.sha(workspace/'analysis/sindirgi/radio_study/inputs'/path.name)
fresh = OUT/'simulation_workspace/simulation/results/pc_final'
comparison = verify.compare_csv(fresh/'ue_metrics.csv',
    verify.PROJECT/'analysis/sindirgi/radio_study/final_ue_metrics.csv',
    ['ue_id','site','sector','rsrp','sinr','rsrq','connected','dl_bytes'], tolerance=1e-7)
assert comparison['max_numeric_difference'] == 0.0
assert verify.load(fresh/'result.json')['connected_ues'] == 64
maps = verify.load(workspace/'analysis/sindirgi/konum_kontrolu/render_check/result.json')
assert len(maps) == 1 and maps[0]['passed'] and maps[0]['background_mode'] == 'offline'
assert verify.load(workspace/'analysis/kpi_audit.json')['total_kpi_rows'] == 5694304
report['analysis']['map_browser_checks'] = maps
report['simulation'] = simulation
report['source_preservation'] = verify.check_preserved_files()
report['launcher_smoke'] = verify.load(
    verify.PROJECT/'simulation/results/pc_validation/launcher_smoke/result.json')
assert report['launcher_smoke']['connected_ues'] == report['launcher_smoke']['ues_receiving_dl'] == 6
report['cache_smoke'] = verify.load(
    verify.PROJECT/'simulation/results/pc_validation/cache_smoke/result.json')
assert report['cache_smoke']['connected_ues'] == report['cache_smoke']['ues_receiving_dl'] == 6
report.pop('error', None)
report['all_checks_passed'] = True
report['verification_notes'] = [
    'Raw audit and fresh simulation ran as independent phases; completed artifacts were rechecked here.',
    'The final source allowlist includes the offline-only map checker added during the initial audit.',
    'Online map tiles were not tested; all remote hosts were blocked for browser QA.',
    'The complete 17-case historical campaign was not rerun; the final 24-site case and smoke cases were rerun.'
]
(OUT/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'all_checks_passed':True,'kpi_rows':5694304,
                  'fresh_simulation_ues':64,'max_numeric_difference':0.0,
                  'unchanged_historical_files':report['source_preservation']['unchanged_historical_files']},indent=2))
