"""Turkish introductory figure for the already-verified geographical selection.

Run: python analysis/explain_site_selection.py
Reads prepared tables; does not alter measurements or simulation inputs.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

OUT=Path(__file__).resolve().parent/'sindirgi'


def main():
    candidates=pd.read_csv(OUT/'candidate_sites.csv')
    chosen=pd.read_csv(OUT/'sites_local.csv')
    nearby=candidates[candidates.within_display_radius]
    fig,ax=plt.subplots(figsize=(10,10),constrained_layout=True)
    unselected=nearby[nearby.role=='Unselected']
    ax.scatter(unselected.x_m/1000,unselected.y_m/1000,s=40,c='#b6bbc1',zorder=2)
    for role,color in [('Evaluation','#0072b2'),('Interference buffer','#d55e00')]:
        group=chosen[chosen.role==role]
        ax.scatter(group.x_m/1000,group.y_m/1000,s=230,c=color,zorder=4)
        for _,r in group.iterrows():
            ax.text(r.x_m/1000,r.y_m/1000,str(int(r.selection_rank)),
                    ha='center',va='center',color='white',weight='bold',fontsize=9,zorder=5)
    ax.scatter([0],[0],marker='*',s=360,c='#a50026',zorder=5)
    ax.annotate('Verilen deprem merkezi\n39,2461 N / 28,0697 E',(0,0),
                xytext=(-105,17),textcoords='offset points',fontsize=9,
                arrowprops={'arrowstyle':'-','color':'#555555'})
    for site,offset in [('SITE_000220',(-95,12)),('SITE_000204',(40,12))]:
        r=nearby[nearby.site==site].iloc[0]
        ax.annotate(site,(r.x_m/1000,r.y_m/1000),xytext=offset,textcoords='offset points',
                    fontsize=8,color='#555555',arrowprops={'arrowstyle':'-','color':'#999999'})
    legend=[Line2D([],[],marker='o',linestyle='',color='#0072b2',markersize=10,
                   label='1–8: İncelenecek 8 ana saha'),
            Line2D([],[],marker='o',linestyle='',color='#d55e00',markersize=10,
                   label='9–16: Ana sahalara yakın 8 komşu (buffer)'),
            Line2D([],[],marker='o',linestyle='',color='#b6bbc1',markersize=7,
                   label='Gri: Bu seçimde alınmayan diğer adaylar'),
            Line2D([],[],marker='*',linestyle='',color='#a50026',markersize=13,
                   label='Yıldız: Verilen deprem merkezi')]
    ax.legend(handles=legend,loc='upper left',fontsize=9)
    ax.set(xlabel='Merkeze göre doğu yönü (km)',ylabel='Merkeze göre kuzey yönü (km)',
           aspect='equal')
    ax.grid(alpha=.2)
    ax.set_title('1. adım: Sahalar nerede ve bu 16 saha neden seçildi?\n'
                 'Her nokta bir fiziksel saha; sayılar seçim dosyasındaki sıra numarasıdır.',
                 fontsize=13,pad=15)
    fig.text(.5,.005,'Bilinen konumlar ve seçim ekleri birlikte kullanıldı. '
             'Bu şekil kapsama veya hasar haritası değildir.',ha='center',fontsize=9)
    fig.savefig(OUT/'01_saha_secimi.png',dpi=170,bbox_inches='tight')
    fig.savefig(OUT/'01_saha_secimi.svg',bbox_inches='tight')
    plt.close(fig)
    table=chosen[['selection_rank','site','role','lat','lon','distance_to_reference_km',
                  'distance_to_core_km','coordinate_source']].copy()
    table['selection_rank']=table.selection_rank.astype(int)
    table.to_csv(OUT/'01_saha_secimi.csv',index=False)
    print('Created introductory figure and selection table.')


if __name__=='__main__':
    main()
