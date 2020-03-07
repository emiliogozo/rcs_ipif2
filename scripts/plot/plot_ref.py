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
EXP_NAME = 'RF'

in_shps = list(in_shp_dir.glob('*/*.shp'))

plt_props = dict(
    colors=dict(
        rain=dict(
            stn='gray',
            aphro='gold',
            mod='steelblue',
            mod_adj='blue'
        ),
        temp=dict(
            stn='gray',
            aphro='gold',
            mod='crimson',
            mod_adj='salmon'
        )
    ),
    labels=dict(
        stn='Station',
        aphro='APHRODITE',
        mod='RCM',
        mod_adj='RCM adjusted'
    ),
    linestyle=dict(
        stn='-',
        aphro='-',
        mod='-',
        mod_adj='--'
    )
)

for basin_shp in in_shps:
    print(basin_shp)
    basin_name = basin_shp.parent.name

    for ivar, var_name in enumerate(VARS):
        var_name2 = VARS2[ivar]
        var_name3 = var_name
        agg_func = 'mean'
        if var_name == 'rain':
            var_name3 = 'pr'
            agg_func = 'sum'

        print('Processing {}: {}'.format(basin_name, var_name2))

        stn_df = obs_df = mod_df = mod_adj_df = None

        #region load data
        #region load stn
        in_file = in_csv_dir  / 'stn/{}_stn_info.csv'.format(basin_name)
        if in_file.is_file():
            stn_info_df = pd.read_csv(in_file)

        in_file = in_csv_dir  / 'stn/{}.csv'.format(basin_name)
        if in_file.is_file():
            stn_df = pd.read_csv(in_file, usecols=['stn_code', 'lon', 'lat', 'year', 'month', 'day', var_name])
            stn_df.set_index(['year', 'month', 'day'], inplace=True)
            stn_df = stn_df.loc[(slice(*BL_PERIOD)), ]
            stn_df = stn_df.groupby(['year', 'month', 'day'])[var_name].mean()
            stn_df = stn_df.to_frame().reset_index()
            stn_df['grp'] = 'stn'
        #endregion load stn
        
        #region load obs
        in_file = in_xls_dir  / 'obs/{}_{}.xlsx'.format(basin_name, var_name2)
        sname = 'aphro'
        if in_file.is_file():
            obs_df = pd.read_excel(in_file, sheet_name=sname, index_col=[0,1,2,3,4], usecols=['lon', 'lat', 'year', 'month', 'day', var_name2])
            obs_df.rename(columns={
                var_name2: var_name
            }, inplace=True)
            obs_df = obs_df.reset_index().set_index(['year', 'month', 'day'])
            obs_df = obs_df.loc[(slice(*BL_PERIOD)), ]
            obs_df = obs_df.groupby(['year', 'month', 'day'])[var_name].mean()
            obs_df = obs_df.to_frame().reset_index()
            obs_df['grp'] = 'aphro'
        #endregion load obs

        #region load mod
        in_csvs = list((in_csv_dir  / 'rcm/{}/RF/{}'.format(basin_name, var_name2)).glob('*.csv'))
        if len(in_csvs):
            mod_df = []
            for in_csv in in_csvs:
                mod_df.append(pd.read_csv(in_csv).groupby(['lon', 'lat', 'year', 'month', 'day']).mean())
            mod_df = pd.concat(mod_df, axis=1)
            mod_df.columns = RCMS.keys()
            mod_df = mod_df.loc[(slice(None), slice(None), slice(*BL_PERIOD)), ]
            mod_df = mod_df.groupby(['year', 'month', 'day']).mean()
            mod_df.columns = var_name + mod_df.columns
            mod_df = pd.wide_to_long(df=mod_df.reset_index(), i=['year', 'month', 'day'], j='rcm', stubnames=[var_name], suffix='[-\w]+')[var_name]
            mod_df = mod_df.reorder_levels(['rcm', 'year', 'month', 'day'])
            mod_df = mod_df.reset_index()
            mod_df['grp'] = 'mod'
        #endregion load mod

        #region load mod adjusted
        in_csvs = list((in_csv_dir  / 'rcm_adj/{}/RF/{}/aphro'.format(basin_name, var_name2)).glob('*.csv'))
        if len(in_csvs):
            mod_adj_df = []
            for in_csv in in_csvs:
                _mod_adj_df = pd.read_csv(in_csv)
                _mod_adj_df = _mod_adj_df.groupby(['year', 'month', 'day']).mean()
                mod_adj_df.append(_mod_adj_df.loc[:, _mod_adj_df.columns.str.contains('_adj')])
            mod_adj_df = pd.concat(mod_adj_df, axis=1)
            mod_adj_df.columns = RCMS.keys()
            mod_adj_df = mod_adj_df.loc[(slice(*BL_PERIOD)), ]
            mod_adj_df.columns = var_name + mod_adj_df.columns
            mod_adj_df = pd.wide_to_long(df=mod_adj_df.reset_index(), i=['year', 'month', 'day'], j='rcm', stubnames=[var_name], suffix='[-\w]+')[var_name]
            mod_adj_df = mod_adj_df.reorder_levels(['rcm', 'year', 'month', 'day'])
            mod_adj_df = mod_adj_df.reset_index()
            mod_adj_df['grp'] = 'mod_adj'
        #endregion load mod adjusted
        #endregion load data

        plt_title = '{} - {}'.format(basin_name.capitalize(), var_name.capitalize())

        stat_df = pd.concat([stn_df, obs_df, mod_df, mod_adj_df], sort=False, ignore_index=True)
        stat_df['grp'] = pd.Categorical(stat_df['grp'], categories=['stn', 'aphro', 'mod', 'mod_adj'])

        #region plot daily dist
        fig, ax = plt.subplots(figsize=(14, 10))
        for grp_name, grp_df in stat_df.groupby('grp'):
            if grp_df.size == 0:
                continue
            # grp_name = _df['grp'][0]
            if var_name == 'rain':
                sns.distplot(
                    grp_df[var_name].dropna(),
                    kde=True, hist=False,
                    ax=ax,
                    kde_kws=dict(
                        color=plt_props['colors'][var_name][grp_name],
                        ls=plt_props['linestyle'][grp_name]),
                    label=plt_props['labels'][grp_name])
            else:
                sns.distplot(
                    grp_df[var_name].dropna(),
                    fit=norm, kde=False, hist=False,
                    ax=ax,
                    fit_kws=dict(
                        color=plt_props['colors'][var_name][grp_name],
                        ls=plt_props['linestyle'][grp_name]),
                    label=plt_props['labels'][grp_name])
        ax.set_title(plt_title)
        ax.set_xlabel('{long_name} ({units})'.format(**STN_VARS[var_name3]))
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width*0.8, box.height])
        ax.legend(loc='center right', bbox_to_anchor=(1.35, 0.9), ncol=1)
        out_img_file_name = out_img_dir / 'ref_dist/{}_{}.png'.format(basin_name, var_name)
        out_img_file_name.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_img_file_name)
        plt.close('all')
        #endregion plot daily dist

        # out_stat_file_name = out_stat_dir / '../daily/{}_{}.xlsx'.format(basin_name, var_name)
        # out_stat_file_name.parent.mkdir(parents=True, exist_ok=True)
        # writer = pd.ExcelWriter(out_stat_file_name)
        # for grp_name, grp_df in stat_df.groupby('grp'):
        #     grp_df.to_excel(writer, sheet_name=grp_name, index=False)
        # writer.save()
        # writer.close()

        #region stat daily
        out_stat_file_name = out_stat_dir / 'ref_daily/{}_{}.csv'.format(basin_name, var_name)
        out_stat_file_name.parent.mkdir(parents=True, exist_ok=True)
        stat_df.groupby('grp')[var_name].describe().to_csv(out_stat_file_name)
        #endregion stat daily

        #region stat monthly
        out_stat_file_name = out_stat_dir / 'ref_seasonal/{}_{}.csv'.format(basin_name, var_name)
        out_stat_file_name.parent.mkdir(parents=True, exist_ok=True)
        stat_df.groupby(['grp', 'month'])[var_name].describe().to_csv(out_stat_file_name)
        #endregion stat monthly

        #region plot seasonal
        stat_df2 = stat_df.copy()
        stat_df2.loc[stat_df2['rcm'].isna(), 'rcm'] = stat_df2.loc[stat_df2['rcm'].isna(), 'grp']
        stat_df2 = stat_df2.groupby(['grp', 'rcm', 'year', 'month'])[var_name].agg(agg_func).reset_index()
        plt_df = stat_df2.copy()
        plt_df['month'] = plt_df['month'].apply(lambda m: calendar.month_abbr[m])
        plt_df['month'] = pd.Categorical(plt_df['month'], categories=[calendar.month_abbr[m] for m in range(1, 13)])
        f = sns.relplot(x='month', y=var_name, hue='grp', style='grp', kind='line', data=plt_df, palette=plt_props['colors'][var_name], height=8, aspect=1.4, dashes=[(1,0), (1,0), (1,0), (4,2)])
        f.fig.suptitle(plt_title)
        f.set_axis_labels('Month', '{long_name} ({units})'.format(**STN_VARS[var_name3]))
        for ax in f.axes.flat:
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width*0.95, box.height])
        f._legend.texts[0].set_text('')
        for _t in f._legend.texts[1:]:
            _t.set_text(plt_props['labels'][_t.get_text()])
        f._legend.set_bbox_to_anchor([1, 0.9])
        out_img_file_name = out_img_dir / 'ref_seasonal/{}_{}.png'.format(basin_name, var_name)
        out_img_file_name.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_img_file_name)
        plt.close('all')
        #endregion plot seasonal
