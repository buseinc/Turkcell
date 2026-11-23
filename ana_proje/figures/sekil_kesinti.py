"""Taslak (main.tex) için iki şekil: yol_kesinti.png (deney 34, rota A) ve kesinti_karsilastirma.png (deney 33 + 37).
Kullanım: py sekil_kesinti.py"""
from pathlib import Path
import json
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DEN = HERE.parent.parent/'deneyler'
D34 = DEN/'34_yol_hareketi_2026-11-21'
sys.path.insert(0, str(D34))
import yol_analiz as ya  # noqa: E402

plt.rcParams.update({'font.size': 10})


def yol():
    plan = json.loads((D34/'yol_plan.json').read_text(encoding='utf-8'))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    out = {}
    for case, color, lab in [('Y_A_K0', '#1f77b4', '130 açık'), ('Y_A_K2', '#d95f02', '130 çökmüş')]:
        res, no_srv, sinr, conn = ya.analyse(case, case, 'A', plan['cases'][case])
        x = np.arange(len(sinr))*ya.BIN/1000
        y = sinr.to_numpy().copy()
        y[(conn < 0.5).to_numpy()] = np.nan
        ax.plot(x, y, lw=0.8, color=color, label=f'{lab}: servissiz yol {res["km_no_service"]:.1f} km'.replace('.', ','))
        out[case] = (x, no_srv.fillna(False).to_numpy())
    x, ns = out['Y_A_K2']
    for i in np.flatnonzero(ns):
        ax.axvspan(x[i], x[i] + ya.BIN/1000, color='#d95f02', alpha=0.12, lw=0)
    ax.axhline(-6.7, color='black', ls='--', lw=0.8)
    ax.text(0.1, -9.5, 'bu çizginin altında telefon veri alamıyor', fontsize=8.5)
    ax.annotate('burada araçların bağlantısı\ntamamen kopuyor', xy=(9.3, -29), xytext=(11.3, -31), fontsize=8.5,
                color='#d95f02', va='center', arrowprops={'arrowstyle': '->', 'color': '#d95f02'})
    ax.set_xlabel('130 sahasının yanından geçen il yolu boyunca mesafe (km)')
    ax.set_ylabel('araçtaki sinyal kalitesi (SINR, dB)')
    ax.set_title('130 çökünce il yolunda ne oluyor? (ns-3, 34 araç, gölgeli yerler servissiz)')
    ax.legend(loc='lower left', fontsize=9)
    ax.set_ylim(-37, 25)
    fig.tight_layout()
    fig.savefig(HERE/'yol_kesinti.png', dpi=150)


def karsilastirma():
    s = json.loads((DEN/'33_kesinti_ns3_2026-11-20/analiz.json').read_text(encoding='utf-8-sig'))['ns3']
    e = json.loads((DEN/'37_edremit_kesinti_2026-11-22/analiz.json').read_text(encoding='utf-8-sig'))
    rows = [('Sındırgı\n130 çöktü', s['K2']['around_off']), ('Sındırgı\n482 çöktü', s['K1']['around_off']),
            ('Edremit\n529 çöktü', e['E1']['around_off']), ('Edremit\n105 çöktü', e['E2']['around_off'])]
    on = [0.0, 0.0, e['E1']['around_off_when_on']['no_service'], e['E2']['around_off_when_on']['no_service']]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(rows))
    ax.bar(x - 0.2, [100*v for v in on], 0.4, color='#9ecae1', label='saha açıkken')
    off = [100*r['no_service'] for _, r in rows]
    ax.bar(x + 0.2, off, 0.4, color='#d95f02', label='saha çökünce')
    for i, (v, (_, r)) in enumerate(zip(off, rows)):
        ax.text(i + 0.2, v + 0.5, f'%{v:.0f}\n({round(r["no_service"]*r["users"])}/{r["users"]} kişi)', ha='center', fontsize=8.5)
    ax.axvline(1.5, color='grey', lw=0.8)
    ax.text(0.5, 23, 'seyrek kırsal bölge', ha='center', color='grey')
    ax.text(2.5, 23, 'sık kıyı bölgesi', ha='center', color='grey')
    ax.set_xticks(x, [r[0] for r in rows])
    ax.set_ylim(0, 26)
    ax.set_ylabel('çöken sahanın çevresinde\nservis alamayan kullanıcı (%)')
    ax.set_title('Aynı deprem yükünde bir saha çökünce (ns-3)')
    ax.legend(loc='upper right', bbox_to_anchor=(1, 0.88))
    fig.tight_layout()
    fig.savefig(HERE/'kesinti_karsilastirma.png', dpi=150)


if __name__ == '__main__':
    karsilastirma()
    yol()
