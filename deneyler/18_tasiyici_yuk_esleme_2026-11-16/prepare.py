"""Freeze a load-only correction of experiment 17. Do not edit earlier experiments."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D17 = HERE.parent/'17_hoca_gruplamasi_2026-11-16'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    if (HERE/'plan.json').exists():
        raise RuntimeError('Plan already frozen; do not overwrite.')
    inputs, sim = HERE/'inputs',HERE/'simulation'
    inputs.mkdir(exist_ok=True); sim.mkdir(exist_ok=True)
    (sim/'build').mkdir(exist_ok=True)
    parent = json.loads((D17/'plan.json').read_text(encoding='utf-8'))
    regression = json.loads((D17/'regression.json').read_text(encoding='utf-8'))
    assert regression['passed'] and regression['model_checks']['passed']
    for name,h in parent['runtime']['simulation_hashes'].items():
        assert sha(D17/'simulation'/name)==h,name
        shutil.copy2(D17/'simulation'/name,sim/name)
    for name in ['sindirgi_baseline','source_manifest.json']:
        shutil.copy2(D17/'simulation/build'/name,sim/'build'/name)
    for az,seed in [[42,701],[7,702],[99,703]]:
        for name in [f'sites_G17_{az}.csv',f'ues_G17_{seed}.csv']:
            assert sha(D17/'inputs'/name)==parent['runtime']['input_hashes'][name]
            shutil.copy2(D17/'inputs'/name,inputs/name)
    shutil.copy2(D17/'inputs/targets.csv',inputs/'targets.csv')
    baseline = D17/'simulation/results/G17_draw701'
    cells = {r['synthetic_cell_id']:r for r in read(baseline/'sectors.csv')}
    prb = read(baseline/'prb_usage.csv')
    by_band = {band:statistics.mean(float(r['dl_prb_utilization']) for r in prb if cells[r['synthetic_cell_id']]['carrier']==band)
               for band in ['B3','B20','B1']}
    original = read(inputs/'ues_G17_701.csv')
    intervals = {float(r['udp_interval_ms']) for r in original if r['kind']=='load' and r['dl_earfcn']=='6400'}
    assert len(intervals)==1
    old_interval = intervals.pop()
    target = 0.233
    plan = {
        'status':'frozen_before_load_correction_runs',
        'question':'Match B20 PRB to the fixed KPI-derived load target, then assess the same G17 radio model without the previous load mismatch.',
        'target_prb':target,'pilot_relative_tolerance':0.05,'validation_relative_tolerance':0.10,
        'calibration_seed':701,'validation_seeds':[702,703],'draws':[[42,701],[7,702],[99,703]],
        'duration_s':4,'warmup_s':1,'max_new_calibration_runs':4,'interval_bounds_ms':[1.0,50.0],
        'only_adjust':'udp_interval_ms of the 14 kind=load, dl_earfcn=6400 rows. Every other value is preserved, including all B1 traffic.',
        'selection_rule':'First candidate in pilot +/-5% target is frozen; otherwise next interval = last_interval * achieved_B20_PRB / target, limited to [0.5,2] times last and absolute bounds. If observations bracket target, use secant interpolation in packet rate (1/interval) within bracket. No signal-error ranking.',
        'fit_basis':'Unweighted mean synthetic PRB across all 14 B20 cells on draw701, including 440 load cells. This sets offered load only; never read Experia RSRP/SINR target errors to choose a rate. No site-specific rate adjustments.',
        'baseline_point':{'interval_ms':old_interval,'prb_by_carrier':by_band},
        'unbounded_initial_prediction_ms':round(old_interval*by_band['B20']/target,6),
        'initial_interval_ms':round(max(old_interval*0.5,min(old_interval*2,old_interval*by_band['B20']/target)),6),
        'immutable':['C++ and wrapper source','99 cells and four strong-site layouts','all carrier frequencies/bandwidths/powers',
                     'all UE positions and counts','all per-UE camping frequencies','all 72 B3 and 13 B1 load intervals',
                     'all measurement-user traffic','mixed CQI, antenna parameters, propagation, noise, random draws'],
        'validation':'Reuse selected pilot701 without rerunning it, apply the same frozen interval to independent draws702/703. No correction based on validation results.',
        'load_acceptance':'B20 and B1 per-carrier mean PRB within +/-10% of .233 on each of all three draws; absolute whole-network mean PRB change vs S0 <=.03 on each draw. Report B3 separately unchanged.',
        'radio_interpretation':'Report S0, original G17 and load-matched L18. Load matching does not claim to fix RSRP or identify real RF configuration. Keep original G17 frozen acceptance thresholds as a separate diagnostic.',
        'source_hashes':{name:sha(sim/name) for name in parent['runtime']['simulation_hashes']},
        'initial_input_hashes':{p.name:sha(p) for p in sorted(inputs.glob('*.csv'))},
        'reused_build':{'binary_sha256':sha(sim/'build/sindirgi_baseline'),'source_manifest':json.loads((sim/'build/source_manifest.json').read_text()),
                        'origin':'experiment17, exact same binary and source; no C++ changes; no need for a new S0 simulation repeat'},
        'parent_plan_sha256':sha(D17/'plan.json'),'parent_result_sha256':sha(D17/'result.json'),
        'parent_regression_sha256':sha(D17/'regression.json'),
    }
    (HERE/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
    lines = ['# Deney 18 — taşıyıcı yükünü eşleme','',
             '**Durum: Yalnız yük düzeltme planı sabitlendi; kalibrasyon hazırlanıyor.**','',
             'Amaç, Deney 17’nin 800 MHz katmanındaki düşük doluluğu düzeltip aynı ağ yapısını benzer dolulukta karşılaştırmak. Hücre grupları, frekanslar, güçler, kullanıcı konumları ve taşıyıcı atamaları değişmeyecek.','',
             f"Başlangıç: 701 örneğinde B20 PRB {by_band['B20']:.5f}, hedef 0,233. Eski yük paket aralığı {old_interval:.6f} ms; ilk aday {plan['initial_interval_ms']:.6f} ms. Aralık küçüldükçe daha çok trafik verilir.",'',
             'Yalnız B20’deki 14 yapay yük kullanıcısının paket aralığı ayarlanır. B1 zaten hedefin ±%10 aralığında olduğu için değiştirilmez; B3 ve ölçüm kullanıcılarının trafiği de aynen korunur.','',
             'Ayarlama yalnız 701 örneğinin benzetim PRB’sine göre yapılır. 440 dahil bütün B20 hücrelerinin yük sayaçları kullanılır; hiçbir sahanın Experia sinyal hatası ayarı seçmekte kullanılmaz. Bu bir güç/frekans kalibrasyonu değildir.','',
             'Kural: En fazla dört yeni kalibrasyon koşusu; 701’de hedefin ±%5’ine ulaşan ilk aday sabitlenir. Sonra aynı aralık, ayarlamada kullanılmayan 702 ve 703 örneklerinde ±%10 sınırıyla kontrol edilir. Bu iki sonuç görüldükten sonra aralık değiştirilmez.','',
             'Simülasyon kodu ve çalıştırıcı Deney 17 ile dosya düzeyinde aynı. Önceden geçen 20 kod kontrolü ve S0 karşılaştırması kaynak/binary hash’leriyle taşındı. Yeni kod eklenmediği için S0’ın pahalı tam koşusu tekrar edilmeyecek; aynı binary’nin küçük kontrolleri yeniden çalıştırılacak.','',
             'Birinci başarılı pilot, 701’in nihai sonucu olarak kullanılacak; aynı koşu ikinci kez yapılmayacak. Önceki deneyler değiştirilmeyecek. Kalibrasyon planı plan.json, seçilen aralık calibration.json, nihai kıyas comparison.json içinde; kullanıcıya yönelik tek rapor bu dosyadır.']
    (HERE/'SONUCLAR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'initial_interval_ms':plan['initial_interval_ms'],'baseline_prb':by_band,'source_identical_to_17':True},indent=2))


if __name__=='__main__':
    main()
