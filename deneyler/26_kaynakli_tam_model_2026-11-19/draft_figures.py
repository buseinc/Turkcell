"""Windows: figures for ana_proje/main.tex (sourced model section). Reads committed result files only."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT/'ana_proje/figures'
# label offsets (points) to avoid collisions
OFF = {('S0', 'rsrp', '296'): (-22, 6), ('S0', 'rsrp', '441'): (6, -12), ('FT_TA', 'rsrp', '443'): (-6, 8), ('FT_TA', 'rsrp', '296'): (-26, -3),
       ('FT_TA', 'sinr', '296'): (-26, 4), ('FT_TA', 'sinr', '554'): (6, -12), ('FT_TA', 'sinr', '441'): (6, -12),
       ('FT_TA', 'sinr', '482'): (-8, 9), ('FT_TA', 'sinr', '443'): (6, -12)}
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False})


def tr(x, nd=1):
    return f'{x:.{nd}f}'.replace('.', ',')


def sinr_curve():
    a = json.loads((ROOT/'deneyler/25_sinr_tavani_evm_2026-11-19/analysis.json').read_text())
    bins = [-125, -115, -105, -95, -85]
    x = [b + 5 for b in bins]
    exp = [a['experia']['by_rsrp_bin'][str(b)] for b in bins]
    c = a['runs']['LC_TA']['curve_by_rsrp_bin']
    raw = [c[str(b)]['native_sinr_db'] for b in bins]
    evm = [c[str(b)]['evm_sinr_db'] for b in bins]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.grid(color=GRID, lw=.6)
    for ys, col, ls, lab in [(raw, ORANGE, '--', 'Simülasyon, EVM yok'), (evm, AQUA, '-', 'Simülasyon, EVM %8'),
                             (exp, BLUE, '-', 'Experia (ölçüm)')]:
        ax.plot(x, ys, ls, color=col, lw=2, marker='o', ms=8, mec='white', mew=1.5, label=lab)
        dy = {'Simülasyon, EVM %8': 7, 'Experia (ölçüm)': -6}.get(lab, 0)
        ax.annotate(lab, (x[-1], ys[-1]), xytext=(9, dy), textcoords='offset points', va='center', color=INK, fontsize=8.5)
    ax.axhline(21.9, color=MUTED, lw=.8, ls=':')
    ax.text(-121, 23.0, '3GPP EVM tavanı 21,9 dB', color=MUTED, fontsize=8)
    ax.set_xlim(-122, -62)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{b}…{b+10}' for b in bins])
    ax.set_xlabel('RSRP aralığı (dBm)')
    ax.set_ylabel('Kullanıcı medyan SINR (dB)')
    ax.legend(loc='upper left', frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG/'sinr_tavani.png', dpi=200)


def site_scatter():
    t = pd.read_csv(HERE/'inputs/targets.csv').set_index('site')
    c26 = json.loads((HERE/'comparison.json').read_text(encoding='utf-8'))
    fig, axes = plt.subplots(2, 2, figsize=(7.6, 7.4))
    for col, (sc, title) in enumerate([('S0', 'Eski temel S0 (ayarlanmış değerler)'), ('FT_TA', 'Kaynaklı model')]):
        for row, (m, lab, lim) in enumerate([('rsrp', 'RSRP (dBm)', (-120, -90)), ('sinr', 'SINR (dB)', (2, 22))]):
            ax = axes[row][col]
            ax.fill_between(lim, [lim[0]-3, lim[1]-3], [lim[0]+3, lim[1]+3], color=GRID, alpha=.7, lw=0)
            ax.plot(lim, lim, color=MUTED, lw=.8)
            for site in t.index:
                y = c26[sc]['site_values'][m][site]
                hold = t.loc[site, 'split'] == 'holdout'
                ax.plot(t.loc[site, f'{m}_target'], y, 'o', ms=8, mec='white', mew=1.5, color=ORANGE if hold else BLUE)
                off = OFF.get((sc, m, site[-3:]), (6, -10))
                ax.annotate(site[-3:], (t.loc[site, f'{m}_target'], y), xytext=off, textcoords='offset points', fontsize=7.5, color=INK)
            ax.set_xlim(lim)
            ax.set_ylim(lim)
            ax.set_aspect('equal')
            ax.set_xlabel(f'Experia — {lab}')
            ax.set_ylabel(f'Simülasyon — {lab}')
            mc = c26[sc]['mae']['control'][m][0]
            ax.set_title(f'{title}\nayarda kullanılmayan sahalarda fark {tr(mc)} dB', fontsize=8.5, color=INK)
    axes[0][0].plot([], [], 'o', color=BLUE, label='Ayarda kullanılan saha')
    axes[0][0].plot([], [], 'o', color=ORANGE, label='Ayarda kullanılmayan saha')
    axes[0][0].plot([], [], 's', color=GRID, label='±3 dB bandı')
    axes[0][0].legend(fontsize=7.5, loc='upper left', frameon=False)
    fig.tight_layout()
    fig.savefig(FIG/'kaynakli_model.png', dpi=200)


if __name__ == '__main__':
    sinr_curve()
    site_scatter()
    print('ok')
