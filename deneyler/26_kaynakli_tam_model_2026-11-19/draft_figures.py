"""Windows: figures for ana_proje/main.tex (new model section). Reads committed result files only."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT/'ana_proje/figures'
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
# label offsets (points) to avoid collisions
OFF = {('rsrp', '443'): (-6, 8), ('rsrp', '296'): (-26, -3),
       ('sinr', '296'): (-26, 4), ('sinr', '554'): (6, -12), ('sinr', '441'): (6, -12),
       ('sinr', '482'): (-8, 9), ('sinr', '443'): (6, -12)}
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
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.grid(color=GRID, lw=.6)
    ax.axvspan(-122, -110, color=GRID, alpha=.45, lw=0)
    ax.text(-121, 47, 'Zayıf sinyal:\nkaliteyi arka plan\ngürültüsü belirliyor', fontsize=8, color=MUTED, va='top')
    ax.text(-108, 47, 'Güçlü sinyal: gerçek ağda kalite\n~20 dB\'de duruyor, daha iyi olmuyor', fontsize=8, color=MUTED, va='top')
    series = [(raw, ORANGE, '--', 'Model, verici kusuru yokken'),
              (evm, AQUA, '-', 'Model, verici kusuru eklenince (3GPP: %8)'),
              (exp, BLUE, '-', 'Gerçek ağ (Experia ölçümü)')]
    for ys, col, ls, lab in series:
        ax.plot(x, ys, ls, color=col, lw=2, marker='o', ms=8, mec='white', mew=1.5, label=lab)
    ax.axhline(21.9, color=MUTED, lw=.8, ls=':')
    ax.text(-121, 23.0, '%8 kusurla çıkılabilecek en yüksek: 21,9 dB', color=MUTED, fontsize=7.5)
    ax.annotate('', xy=(x[-1] + 2.5, exp[-1]), xytext=(x[-1] + 2.5, raw[-1]),
                arrowprops=dict(arrowstyle='<->', color=INK, lw=.9))
    ax.text(x[-1] + 4, (raw[-1] + exp[-1]) / 2, f'kusursuz verici\nvarsayınca\n{tr(raw[-1] - exp[-1], 0)} dB fazla', fontsize=8, color=INK, va='center')
    ax.set_xlim(-122, -64)
    ax.set_ylim(0, 48)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{b}…{b+10}' for b in bins])
    ax.set_xlabel('Sinyal gücü, RSRP (dBm)        zayıf  →  güçlü')
    ax.set_ylabel('Sinyal kalitesi, SINR (dB)')
    ax.legend(loc='upper left', bbox_to_anchor=(0.0, 0.80), frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG/'sinr_tavani.png', dpi=200)


def site_scatter():
    t = pd.read_csv(HERE/'inputs/targets.csv').set_index('site')
    c26 = json.loads((HERE/'comparison.json').read_text(encoding='utf-8'))
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 4.4))
    for ax, (m, lab, lim) in zip(axes, [('rsrp', 'Sinyal gücü, RSRP (dBm)', (-120, -90)), ('sinr', 'Sinyal kalitesi, SINR (dB)', (2, 22))]):
        ax.fill_between(lim, [lim[0]-3, lim[1]-3], [lim[0]+3, lim[1]+3], color=GRID, alpha=.7, lw=0)
        ax.plot(lim, lim, color=MUTED, lw=.8)
        for site in t.index:
            y = c26['FT_TA']['site_values'][m][site]
            test = t.loc[site, 'split'] == 'holdout'
            ax.plot(t.loc[site, f'{m}_target'], y, 'o', ms=8, mec='white', mew=1.5, color=ORANGE if test else BLUE)
            ax.annotate(site[-3:], (t.loc[site, f'{m}_target'], y), xytext=OFF.get((m, site[-3:]), (6, -10)),
                        textcoords='offset points', fontsize=7.5, color=INK)
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_aspect('equal')
        ax.set_xlabel(f'Gerçek ağ (Experia) — {lab}')
        ax.set_ylabel(f'Model — {lab}')
        mc = c26['FT_TA']['mae']['control'][m][0]
        ax.set_title(f'{lab.split(",")[0]}: test sahalarında ortalama fark {tr(mc)} dB', fontsize=8.5, color=INK)
    axes[0].plot([], [], 'o', color=BLUE, label='Diğer ana sahalar')
    axes[0].plot([], [], 'o', color=ORANGE, label='Test sahaları (440, 441, 443)')
    axes[0].plot([], [], 's', color=GRID, label='±3 dB içinde')
    axes[0].plot([], [], '-', color=MUTED, lw=.8, label='Çizgi üstü = birebir aynı')
    axes[0].legend(fontsize=7.5, loc='upper left', frameon=False)
    fig.tight_layout()
    fig.savefig(FIG/'kaynakli_model.png', dpi=200)


if __name__ == '__main__':
    sinr_curve()
    site_scatter()
    print('ok')
