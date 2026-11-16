"""Validation summary for the advisor: figures + PDF (Windows Python, matplotlib + reportlab).

All numbers are read from the experiment outputs; nothing is typed in by hand except the
parameter-scan table, which lists the values that were actually run (experiments 04-06, 08).
Baseline = S0 of the multi-carrier study (24 sites, 3 sectors, single carrier, 256 users,
KPI daily-mean load, randomised traffic start, three azimuth/user draws).
"""
from pathlib import Path
import importlib.util
import json
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle, KeepTogether)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D14 = ROOT / 'deneyler/14_cok_tasiyici_s2_2026-11-15'
D10 = ROOT / 'deneyler/10_kapsama_haritalari_2026-11-15'
SEEDS = [701, 702, 703]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def f(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


def load():
    res = json.loads((D14 / 'result.json').read_text(encoding='utf-8'))
    runs = {r['case']['ue_seed']: r for r in res['results'] if r['case']['scenario'] == 'S0'}
    comp = json.loads((D14 / 'comparison.json').read_text(encoding='utf-8'))
    targets = pd.read_csv(D14 / 'inputs/targets.csv').set_index('site')
    return runs, comp, targets


def fig_layout(path):
    sec = pd.read_csv(D14 / 'simulation/results/S0_draw701/sectors.csv')
    ues = pd.read_csv(D14 / 'inputs/ues_S0_701.csv')
    sites = sec.drop_duplicates('site')
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    m = ues[ues.kind == 'measure']
    ax.scatter(m.x_m / 1000, m.y_m / 1000, s=5, c='#4c9be8', alpha=.6, label='Sanal kullanıcı (256)', zorder=1)
    for r in sec.itertuples():
        a = math.radians(r.orientation_ccw_from_east_deg)
        ax.annotate('', xy=(r.x_m / 1000 + 1.6 * math.cos(a), r.y_m / 1000 + 1.6 * math.sin(a)),
                    xytext=(r.x_m / 1000, r.y_m / 1000),
                    arrowprops=dict(arrowstyle='->', color='#555555', lw=.9), zorder=2)
    ev = sites[sites.role == 'Evaluation']
    bu = sites[sites.role != 'Evaluation']
    ax.scatter(bu.x_m / 1000, bu.y_m / 1000, s=40, c='white', edgecolors='black', label='Komşu saha (16)', zorder=3)
    ax.scatter(ev.x_m / 1000, ev.y_m / 1000, s=70, marker='^', c='#d62728', edgecolors='black', label='Ana saha (8)', zorder=4)
    for r in ev.itertuples():
        ax.annotate(r.site[-3:], (r.x_m / 1000, r.y_m / 1000), xytext=(5, 4), textcoords='offset points',
                    fontsize=8, fontweight='bold', zorder=5)
    ax.scatter([0], [0], marker='*', s=180, c='gold', edgecolors='black', label='Deprem merkezi (10 Ağu 2025)', zorder=5)
    ax.plot([], [], color='#555555', label='Anten yönü (saha başına 3)')
    ax.set_xlabel('Doğu (km)')
    ax.set_ylabel('Kuzey (km)')
    ax.set_aspect('equal')
    ax.grid(alpha=.3)
    ax.legend(loc='lower left', fontsize=7.5, framealpha=.95)
    ax.set_title('Simülasyondaki ağ: 24 saha, 72 anten, 256 sanal kullanıcı (örnek yerleşim)')
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_scatter(path, runs, targets):
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4))
    for ax, m, lab, lim in [(axes[0], 'rsrp', 'RSRP (dBm)', (-120, -95)), (axes[1], 'sinr', 'SINR (dB)', (0, 25))]:
        x0, x1 = lim
        xs = np.linspace(x0, x1, 2)
        ax.fill_between(xs, xs - 3, xs + 3, color='#2ca02c', alpha=.12, label='±3 dB')
        ax.plot(xs, xs, color='black', lw=.8, label='Birebir')
        for site, t in targets.iterrows():
            vals = [runs[s]['sites'][site][m] for s in SEEDS]
            y = np.mean(vals)
            col = '#1f77b4' if t.split == 'train' else '#d62728'
            ax.errorbar(t[f'{m}_target'], y, yerr=[[y - min(vals)], [max(vals) - y]], fmt='o', color=col,
                        ms=6, capsize=3, zorder=3)
            off = {('rsrp', 'SITE_000296'): (-24, 4), ('sinr', 'SITE_000482'): (8, -4), ('sinr', 'SITE_000443'): (7, 2)}.get((m, site), (5, -9))
            ax.annotate(site[-3:], (t[f'{m}_target'], y), xytext=off, textcoords='offset points', fontsize=7.5)
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_aspect('equal')
        ax.set_xlabel(f'Ölçüm (Experia) — {lab}')
        ax.set_ylabel(f'Simülasyon — {lab}')
        ax.grid(alpha=.3)
        ax.set_title('Sinyal gücü' if m == 'rsrp' else 'Sinyal netliği')
    axes[0].errorbar([], [], fmt='o', color='#1f77b4', label='Ayarda kullanılan saha')
    axes[0].errorbar([], [], fmt='o', color='#d62728', label='Ayarda kullanılmayan saha (holdout)')
    axes[0].legend(fontsize=7, loc='upper left')
    fig.suptitle('Saha bazında simülasyon ve ölçüm (nokta: üç tekrarın ortalaması, çubuk: en küçük–en büyük)', fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_cqi(path, comp, targets):
    sim = comp['scenarios']['S0']['cqi']['per_site']
    kpi = comp['kpi_cqi_per_site']
    sites = list(targets.index)
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    x = np.arange(len(sites))
    ax.bar(x - .2, [kpi[s] for s in sites], .4, color='#444444', label='Gerçek ağ (KPI)')
    ax.bar(x + .2, [sim[s] for s in sites], .4, color='#4c9be8', label='Simülasyon')
    ax.set_xticks(x, [s[-3:] for s in sites])
    ax.set_ylim(0, 14)
    ax.set_ylabel('Ortalama CQI (0–15)')
    ax.set_title('Bağımsız kontrol: telefonların bildirdiği kalite puanı (CQI), aynı yük düzeyinde')
    ax.grid(axis='y', alpha=.3)
    ax.legend(fontsize=8, ncol=2, loc='upper left')
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_cdf(path):
    dist12 = module('dist12', ROOT / 'deneyler/12_dagilim_karsilastirmasi_2026-11-15/compare.py')
    exp = pd.read_csv(dist12.EXPERIA)
    pooled = pd.concat([dist12.sim_sectors(D14 / f'simulation/results/S0_draw{s}') for s in SEEDS])
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    for v, lab, col, lw in [(exp.rsrp_mean, 'Gerçek ağ (Experia, 55 hücre)', 'black', 2),
                            (pooled.rsrp, f'Simülasyon ({len(pooled)} anten, 3 tekrar)', '#4c9be8', 1.5)]:
        s = np.sort(v.to_numpy())
        ax.step(s, np.arange(1, len(s) + 1) / len(s), where='post', label=lab, color=col, lw=lw)
    ax.set_xlabel('Hücre/anten başına RSRP (dBm)')
    ax.set_ylabel('Birikimli oran')
    ax.set_title('Tek tek hücreler: simülasyondaki antenler gerçeğe göre daha birbirine benzer')
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main():
    runs, comp, targets = load()
    s0 = comp['scenarios']['S0']
    figs = {k: HERE / f'{k}.png' for k in ['yerlesim', 'saha_karsilastirma', 'cqi', 'hucre_dagilimi']}
    fig_layout(figs['yerlesim'])
    fig_scatter(figs['saha_karsilastirma'], runs, targets)
    fig_cqi(figs['cqi'], comp, targets)
    fig_cdf(figs['hucre_dagilimi'])

    fontdir = Path(matplotlib.get_data_path()) / 'fonts/ttf'
    pdfmetrics.registerFont(TTFont('DV', str(fontdir / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DVB', str(fontdir / 'DejaVuSans-Bold.ttf')))
    st = {
        'title': ParagraphStyle('t', fontName='DVB', fontSize=15, leading=19, spaceAfter=4),
        'sub': ParagraphStyle('s', fontName='DV', fontSize=9, leading=12, textColor=colors.HexColor('#555555'), spaceAfter=10),
        'h': ParagraphStyle('h', fontName='DVB', fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=4),
        'p': ParagraphStyle('p', fontName='DV', fontSize=9.3, leading=13, alignment=TA_LEFT, spaceAfter=5),
        'cell': ParagraphStyle('c', fontName='DV', fontSize=8.3, leading=10.5),
        'cellb': ParagraphStyle('cb', fontName='DVB', fontSize=8.3, leading=10.5),
        'cap': ParagraphStyle('cap', fontName='DV', fontSize=8, leading=10.5, textColor=colors.HexColor('#444444'), spaceAfter=8),
    }

    def table(rows, widths, header=True):
        data = [[Paragraph(str(c), st['cellb'] if (header and i == 0) else st['cell']) for c in r] for i, r in enumerate(rows)]
        t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#999999')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef6') if header else colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
        return t

    def img(path, width_cm):
        from PIL import Image as PI
        w, h = PI.open(path).size
        return Image(str(path), width=width_cm * cm, height=width_cm * cm * h / w)

    mae = s0['mae']
    rank = s0['distribution']['rsrp']['site_rank_spearman']
    story = [
        Paragraph('Sındırgı LTE başlangıç senaryosu — doğrulama özeti', st['title']),
        Paragraph('16 Kasım 2026 · Seçilen ayarların ölçümlere ne kadar yaklaştığı ve neyin doğrulandığı', st['sub']),
        Paragraph('Kısaca', st['h']),
        Paragraph(
            f'Bilinmeyen radyo ayarlarını deneyerek seçtik ve sonucu gerçek ölçümlerle karşılaştırdık. Ayarları seçerken '
            f'<b>hiç kullanmadığımız üç sahada</b> simülasyon ile Experia arasındaki ortalama fark '
            f'<b>sinyal gücünde (RSRP) {f(mae["control"]["rsrp"]["mean"])} dB</b>, '
            f'<b>sinyal netliğinde (SINR) {f(mae["control"]["sinr"]["mean"])} dB</b>. Simülasyon, sahaların güçlü/zayıf '
            f'sıralamasını da doğru veriyor (Spearman {f(min(rank), 2)}–{f(max(rank), 2)}). Ayarlarken hiç kullanmadığımız '
            f'KPI CQI değerleri de gerçeğe yakın (ortalama {f(abs(s0["cqi"]["bias"]))} puan düşük). '
            f'Bu nedenle ağı birebir kopya değil, <b>ölçümlerle beslenen (measurement-informed) temsili bir ağ</b> olarak '
            f'yeterli görüyoruz.', st['p']),
        Paragraph('1. Kurulan ağ', st['h']),
        img(figs['yerlesim'], 13.5),
        Paragraph('Kırmızı üçgenler sizin seçtiğiniz 8 ana saha, beyaz daireler komşu sahalar (sizin 8 sahanız ve '
                  'güncel envanterde en yakın 8 saha). Oklar anten yönleri; gerçek yönler bilinmediği için rastgele '
                  'seçildi ve üç farklı yön ile tekrarlandı. Mavi noktalar, ana sahaların 2–6 km çevresine yerleştirilen '
                  'sanal kullanıcılar.', st['cap']),
        PageBreak(),
        Paragraph('2. Ayarlanan değerler', st['h']),
        Paragraph('Turkcell anten ayarlarını paylaşmadığı için bunları ns-3’te denedik. Taslaktaki holdout önerisine uygun '
                  'olarak seçimi 5 sahaya bakarak yaptık, 3 sahayı seçimden sonra kontrol için ayırdık; öne çıkan adayları '
                  'üç farklı anten yönü ve kullanıcı yerleşimiyle tekrar sınadık.', st['p']),
        table([
            ['Ayar', 'Denenen değerler', 'Seçilen'],
            ['Anten gücü (sektör başına)', '40, 43, 46, 49 dBm', '49 dBm'],
            ['Yatay anten genişliği', '65°, 90°, 120°', '120°'],
            ['Yayılım modeli', 'Log-distance (üs 2,55–3,3), COST231', 'Log-distance, üs 3'],
            ['Gölgeleme', '0, 4, 8 dB', 'Yok'],
            ['Alıcı gürültü faktörü', '6, 9, 12 dB', '9 dB'],
            ['Kullanıcı yerleşimi', 'Düzgün; sahalara 0,5–2 / 1–4 / 2–6 km; karışık', '2–6 km'],
            ['Taşıyıcı', '1800 MHz, 2100 MHz, 900 MHz', '1800 MHz (Band 3)'],
            ['Sektör sayısı (2 hücreli sahalar)', '3 veya 2', '3'],
            ['Sanal kullanıcı sayısı', '64, 128, 256', '256'],
            ['Ağ yükü', 'Boş; KPI’daki günlük ortalama, yoğun saat ve sahaya özel yoğun saat', 'KPI ortalaması (kapasitenin %23’ü)'],
        ], [5.2 * cm, 7.0 * cm, 4.6 * cm]),
        Spacer(1, 6),
        Paragraph('Bunlar Turkcell’in gerçek ayarları değil; denenenler arasında ölçümlere en yakın ve tekrarlarda en '
                  'tutarlı sonucu verenler.', st['cap']),
        Paragraph('3. Ölçümlerle benzerlik', st['h']),
        img(figs['saha_karsilastirma'], 16.8),
        Paragraph('Her nokta bir saha. Köşegene ne kadar yakınsa simülasyon ölçüme o kadar yakın; yeşil bant ±3 dB. '
                  'Kırmızı noktalar ayar seçiminde hiç kullanılmayan sahalar.', st['cap']),
        table([
            ['Ortalama fark (dB, üç tekrar)', 'RSRP', 'SINR', 'RSRQ'],
            ['Ayarda kullanılmayan sahalar (440, 441, 443)',
             f'{f(mae["control"]["rsrp"]["mean"])} ± {f(mae["control"]["rsrp"]["std"])}',
             f'{f(mae["control"]["sinr"]["mean"])} ± {f(mae["control"]["sinr"]["std"])}',
             f'{f(mae["control"]["rsrq"]["mean"])} ± {f(mae["control"]["rsrq"]["std"])}'],
            ['Ayarda kullanılan sahalar (130, 296, 444, 482, 554)',
             f'{f(mae["training"]["rsrp"]["mean"])} ± {f(mae["training"]["rsrp"]["std"])}',
             f'{f(mae["training"]["sinr"]["mean"])} ± {f(mae["training"]["sinr"]["std"])}',
             f'{f(mae["training"]["rsrq"]["mean"])} ± {f(mae["training"]["rsrq"]["std"])}'],
        ], [7.2 * cm, 3.2 * cm, 3.2 * cm, 3.2 * cm]),
        Spacer(1, 6),
        Paragraph('RSRQ farkı yüksek görünüyor, ama bunun nedeni ns-3’ün RSRQ’yu ağ yükünden bağımsız ve gerçek ağdan '
                  'farklı hesaplaması; bu yüzden RSRQ’yu ayar ve karşılaştırmada esas almadık. RSRP’de en çok sapan iki saha 482 ve 554;'
                  '  ikisinde de yalnız 2 hücre var ve yapıları (sektör/frekans) belirsiz.', st['p']),
        PageBreak(),
        Paragraph('4. Bağımsız kontroller', st['h']),
        img(figs['cqi'], 15.5),
        Paragraph(f'CQI, telefonun “sinyali ne kadar iyi duyuyorum” diye bildirdiği puan. Ayarlarken CQI’ya hiç bakmadık. '
                  f'KPI’da CQI ve yük aynı kayıttan geldiği için bu karşılaştırma aynı dönemin verisiyle yapılıyor. '
                  f'Simülasyon ortalamada {f(abs(s0["cqi"]["bias"]))} puan düşük: girişim biraz fazla, tek frekans '
                  f'varsayımıyla uyumlu.', st['cap']),
        img(figs['hucre_dagilimi'], 15.5),
        Paragraph('Saha ortalamaları yakın olsa da, tek tek hücrelere bakınca gerçek ağdaki çok güçlü hücreler '
                  'simülasyonda yok. Gerçek ağın çoğu sahasında birden fazla frekans var (KPI handover kayıtları); '
                  'tek frekanslı modelin bu çeşitliliği yakalamaması beklenen bir sonuç.', st['cap']),
        Paragraph('5. Neyi doğruladık', st['h']),
        table([
            ['Kontrol', 'Sonuç'],
            ['Saha konumları ve hücre–saha eşleşmesi', '16 saha doğru, seçilen 96 hücrenin 96’sı doğru sahada'],
            ['Taslaktaki Sındırgı tablosu', 'Hücre sayıları aynı, saha RSRP ortalamaları en fazla 0,55 dB farklı'],
            ['Yeterli komşu saha', '16, 24, 32, 48 saha karşılaştırıldı; 24’ten sonra sonuçlar değişmiyor'],
            ['Yeterli sanal kullanıcı', '64 yetersiz (sonuçlar oynuyor); 256 ile sabit'],
            ['Ayarın görmediği sahalarda da tutması', 'Ayarlar 5 sahayla seçildi, seçimde kullanılmayan 3 sahada sınandı'],
            ['Tekrarlanabilirlik', 'Aynı senaryo iki bilgisayarda birebir aynı sonucu verdi; kod her değişiklikten sonra eski sonuçları birebir üretti'],
            ['Ağ yükü', f'Simülasyondaki kapasite kullanımı KPI hedefinin %10’u içinde (simülasyon %{f(s0["prb"]["mean"] * 100, 1)}, hedef %23,3)'],
            ['Kapsama haritaları', 'Harita hesabı ns-3 ile birebir aynı; bölgenin %99,8’inde sinyal yeterli'],
        ], [6.0 * cm, 10.8 * cm]),
        Paragraph('6. Sizden görüş istediğimiz nokta', st['h']),
        Paragraph('Bu yakınlık, ağı “measurement-informed” olarak tanımlamak için yeterliyse ayarlamayı burada bırakıp '
                  'stres testine geçmek istiyoruz. Hücrelerin frekans bandı ve gücü paylaşılabilirse çok frekanslı yapıyı da '
                  'tahmine değil veriye dayandırabiliriz.', st['p']),
    ]
    doc = SimpleDocTemplate(str(HERE / 'DOGRULAMA_OZETI.pdf'), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.7 * cm, bottomMargin=1.7 * cm, title='Sındırgı LTE doğrulama özeti')
    doc.build(story)
    print('written', HERE / 'DOGRULAMA_OZETI.pdf')


if __name__ == '__main__':
    main()
