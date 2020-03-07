import calendar
from pathlib import Path
import pandas as pd
import salem

from scipy.stats import norm

import matplotlib.pyplot as plt
import seaborn as sns

from _const_.default import *

sns.set_context('talk')
# sns.set_style('whitegrid')
sns.set_style('ticks')

in_csv_dir = Path('output/csv')
in_xls_dir = Path('output/xls')
in_shp_dir = Path('input/shp/basins')

out_img_dir = Path('output/img/rcm')
out_img_dir.mkdir(parents=True, exist_ok=True)
out_stat_dir = Path('output/stat/rcm')
out_stat_dir.mkdir(parents=True, exist_ok=True)

VARS2 = ['tmean', 'precip']

in_shps = list(in_shp_dir.glob('*/*.shp'))

grp_names = [
    ('RF', 'bl'),
    ('RCP45', 'mid'),
    ('RCP85', 'mid')
]

plt_props = {
    'colors': {
        'rain': {
            ('RF', 'bl'): 'black',
            ('RCP45', 'mid'): 'steelblue',
            ('RCP85', 'mid'): 'blue'
        },
        'temp': {
            ('RF', 'bl'): 'black',
            ('RCP45', 'mid'): 'crimson',
            ('RCP85', 'mid'):'salmon'
        }
    },
    'labels': {
        ('RF', 'bl'): 'Baseline',
        ('RCP45', 'mid'): 'RCP45 mid',
        ('RCP85', 'mid'): 'RCP85 mid'
    },
    'xlim': {
        'temp': {
            'abra': (10, 35),
            'apayao_abulug': (10, 35),
            'buayan': (10, 35),
            'jalaur': (15, 40),
            'ranao': (10, 35),
            'tagum_libuganon': (15, 40)
        }
    },
    'ylim': {
        'temp': {
            'abra': (0, 0.31),
            'apayao_abulug': (0, 0.25),
            'buayan': (0, 0.8),
            'jalaur': (0, 0.5),
            'ranao': (0, 0.9),
            'tagum_libuganon': (0, 0.8)
        }
    }
}

for basin_shp in in_shps:
    print(basin_shp)
    basin_name = basin_shp.parent.name

    for ivar, var_name in enumerate(VARS):
        var_name2 = VARS2[ivar]
        print('Processing {}: {}'.format(basin_name, var_name2))

        #region load data
        mod_df = []
        for exp_name in EXPS:
            in_csvs = list((in_csv_dir  / 'rcm_adj/{}/{}/{}/aphro'.format(basin_name, exp_name, var_name2)).glob('*.csv'))
            if len(in_csvs):
                for in_csv in in_csvs:
                    _mod_df = pd.read_csv(in_csv)
                    _mod_df['rcm'] = in_csv.name.split('.')[0]
                    _mod_df['exp'] = exp_name
                    _mod_df = _mod_df.groupby(['exp', 'rcm', 'year', 'month', 'day']).mean()
                    if exp_name == 'RF':
                        _mod_df.loc[(slice(None), slice(None), slice(*BL_PERIOD)), 'period'] = 'bl'
                    else:
                        for per_name, year_range in PROJ_PERIODS.items():
                            _mod_df.loc[(slice(None), slice(None), slice(*year_range)), 'period'] = per_name
                        _mod_df.rename(columns={
                            var_name2+'_adj_default': var_name2+'_adj'
                        }, inplace=True)
                        # _mod_df = _mod_df.dropna().reset_index()
                    mod_df.append(_mod_df)
                    
        mod_df = pd.concat(mod_df, sort=False)
        mod_df.loc[mod_df['period']=='bl', var_name2+'_adj_edcdf'] = mod_df.loc[mod_df['period']=='bl', var_name2+'_adj']
        #endregion load data

        plt_title = '{} - {}'.format(basin_name.capitalize(), var_name.capitalize())

        agg_func = 'mean'
        var_name3 = var_name
        if var_name == 'rain':
            var_name3 = 'pr'
            agg_func = 'sum'
        
        
        grp_mod_df = mod_df.groupby(['exp', 'period'])
        for dat_name in [var_name2, var_name2+'_adj', var_name2+'_adj_edcdf']:
            #region plot dist
            fig, ax = plt.subplots(figsize=(14, 10))
            for grp_name in grp_names:
                grp_df = grp_mod_df.get_group(grp_name)
                if grp_df.size == 0:
                    continue
                if var_name == 'rain':
                    sns.distplot(
                        grp_df[dat_name].dropna(),
                        kde=True, hist=False,
                        ax=ax,
                        kde_kws={'color': plt_props['colors'][var_name][grp_name]},
                        label=plt_props['labels'][grp_name])
                else:
                    sns.distplot(
                        grp_df[dat_name].dropna(),
                        fit=norm, kde=False, hist=False,
                        ax=ax,
                        fit_kws={'color': plt_props['colors'][var_name][grp_name]},
                        label=plt_props['labels'][grp_name])
            ax.set_title(plt_title)
            ax.set_xlabel('{long_name} ({units})'.format(**STN_VARS[var_name3]))
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width*0.8, box.height])
            if var_name == 'temp':
                ax.set_xlim(plt_props['xlim'][var_name][basin_name])
                ax.set_ylim(plt_props['ylim'][var_name][basin_name])
            ax.legend(loc='center right', bbox_to_anchor=(1.35, 0.9), ncol=1)
            out_img_file_name = out_img_dir / 'proj_dist/{}/{}_{}.png'.format(dat_name, basin_name, var_name)
            out_img_file_name.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(out_img_file_name)
            plt.close('all')
            #endregion plot dist

            #region stat daily
            out_stat_file_name = out_stat_dir / 'proj_daily/{}/{}_{}.csv'.format(dat_name, basin_name, var_name)
            out_stat_file_name.parent.mkdir(parents=True, exist_ok=True)
            stat_df = mod_df.groupby(['exp', 'period', 'day'])[dat_name].describe()
            stat_df.to_csv(out_stat_file_name)
            #endregion stat daily

            #region stat monthly
            out_stat_file_name = out_stat_dir / 'proj_seasonal/{}/{}_{}.csv'.format(dat_name, basin_name, var_name)
            out_stat_file_name.parent.mkdir(parents=True, exist_ok=True)
            stat_df = mod_df.groupby(['exp', 'rcm', 'period', 'year', 'month']).agg(agg_func)
            grp_by = ['exp', 'period', 'month']
            stat_df.groupby(grp_by)[dat_name].describe().to_csv(out_stat_file_name)
            #endregion stat monthly

            plt_df = stat_df.loc[(slice(None), slice(None), ['bl', 'mid']), dat_name].copy().to_frame().reset_index()
            plt_df['month'] = plt_df['month'].apply(lambda m: calendar.month_abbr[m])
            plt_df['month'] = pd.Categorical(plt_df['month'], categories=[calendar.month_abbr[m] for m in range(1, 13)])
            plt_df['grp'] = plt_df['exp'] + '_' + plt_df['period']
            c_pal = {'_'.join(name): prop for name, prop in plt_props['colors'][var_name].items()}
            hue_order = ['_'.join(name) for name, prop in plt_props['colors'][var_name].items()]
            legend_map = {'_'.join(name): prop for name, prop in plt_props['labels'].items()}
            f = sns.relplot(
                x='month', y=dat_name,
                hue='grp', hue_order=hue_order,
                kind='line', data=plt_df, palette=c_pal, height=8, aspect=1.4)
            f.fig.suptitle(plt_title)
            f.set_axis_labels('Month', '{long_name} ({units})'.format(**STN_VARS[var_name3]))
            for ax in f.axes.flat:
                box = ax.get_position()
                ax.set_position([box.x0, box.y0, box.width*0.95, box.height])
            for _t in f._legend.texts[1:]:
                _t.set_text(legend_map[_t.get_text()])
            f._legend.texts[0].set_text('')
            f._legend.set_bbox_to_anchor([1, 0.9])
            # plt.show()
            out_img_file_name = out_img_dir / 'proj_seasonal/{}/{}_{}.png'.format(dat_name, basin_name, var_name)
            out_img_file_name.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(out_img_file_name)
            plt.close('all')

            #region stat annual
            out_stat_file_name = out_stat_dir / 'proj_annual/{}/{}_{}.csv'.format(dat_name, basin_name, var_name)
            out_stat_file_name.parent.mkdir(parents=True, exist_ok=True)
            stat_df = mod_df.groupby(['exp', 'rcm', 'period', 'year']).agg(agg_func)
            grp_by = ['exp', 'period', 'year']
            stat_df.groupby(grp_by)[dat_name].describe().to_csv(out_stat_file_name)
            #endregion stat annual

            #region plot annual
            stat_df = mod_df.groupby(['exp', 'rcm', 'year']).agg(agg_func)
            plt_df = stat_df[dat_name].copy().to_frame().reset_index()
            # plt_df['grp'] = plt_df['exp']
            c_pal = {name[0]: prop for name, prop in plt_props['colors'][var_name].items()}
            hue_order = [name[0] for name, prop in plt_props['colors'][var_name].items()]
            legend_map = {name[0]: prop for name, prop in plt_props['labels'].items()}
            f = sns.relplot(
                x='year', y=dat_name,
                hue='exp', hue_order=hue_order,
                kind='line', data=plt_df, palette=c_pal, height=8, aspect=1.6)
            f.fig.suptitle(plt_title)
            f.set_axis_labels('', '{long_name} ({units})'.format(**STN_VARS[var_name3]))
            for ax in f.axes.flat:
                box = ax.get_position()
                ax.set_position([box.x0, box.y0, box.width*0.95, box.height])
            for _t in f._legend.texts[1:]:
                _t.set_text(legend_map[_t.get_text()])
            f._legend.texts[0].set_text('')
            f._legend.set_bbox_to_anchor([1, 0.9])
            # plt.show()
            out_img_file_name = out_img_dir / 'proj_annual/{}/{}_{}.png'.format(dat_name, basin_name, var_name)
            out_img_file_name.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(out_img_file_name)
            plt.close('all')
            #endregion plot annual
