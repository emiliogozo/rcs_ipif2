from pathlib import Path
import pandas as pd
import salem

import matplotlib.pyplot as plt
from matplotlib import ticker
import seaborn as sns

from _const_.default import *

sns.set_context('talk')
plt.style.use('seaborn-whitegrid')

VARS2 = ['tmean', 'precip']
RF_DATE_RANGE = slice(*BL_PERIOD)
PROJ_MID_DATE_RANGE = slice(*PROJ_PERIODS['mid'])

in_shp_dir = Path('input/shp/basins')
in_xls_dir = Path('output/xls/rcm')

out_img_dir = Path('output/img/boxplot')
out_img_dir.mkdir(parents=True, exist_ok=True)

out_stat_dir = Path('output/stat/boxplot')
out_stat_dir.mkdir(parents=True, exist_ok=True)

in_shps = list(in_shp_dir.glob('*/*.shp'))
in_shps = in_shps[1:]


stat_df = []
for basin_shp in in_shps:
    basin_gdf = salem.read_shapefile(basin_shp)     # read shp
    # experiment loop
    for exp_name in EXPS:
        # variable loop
        for ivar, var_name in enumerate(VARS):
            if exp_name == 'RF':
                date_range = RF_DATE_RANGE
            else:
                date_range = PROJ_MID_DATE_RANGE

            print('Processing {}: {} - {}'.format(basin_shp.parent.name, exp_name, VARS2[ivar]))
            
            in_xlsx_file_name = '{}/{}_{}_{}.xlsx'.format(str(in_xls_dir), basin_shp.parent.name, exp_name, VARS2[ivar])

            in_df = pd.read_excel(in_xlsx_file_name, sheet_name=list(RCMS.keys()), index_col=[0, 1, 2])
            in_df = pd.concat(in_df, axis=1)
            in_df.columns = list(RCMS.keys())
            in_df = in_df.loc[(date_range)]

            if var_name == 'rain':
                plt_color = sns.color_palette('Set3')[2]
                var_name2 = 'pr'
            elif var_name == 'temp':
                plt_color = sns.color_palette('Set3')[3]
                var_name2 = 'temp'
            else:
                continue

            plt_title = basin_shp.parent.name.capitalize()+' - '+STN_VARS[var_name2]['long_name']+' - '+exp_name

            in_df2 = in_df.copy()
            in_df2.columns = 'mod' + in_df2.columns
            in_df2.reset_index(inplace=True)
            in_df2 = pd.wide_to_long(df=in_df2, i=['year', 'month', 'day'], j='rcms', stubnames=['mod'], suffix='[-\w]+').reset_index()
            in_df2.rename(columns={'mod': var_name}, inplace=True)
            if (var_name == 'rain'):
                in_df2 = in_df2.groupby(['year', 'month', 'rcms'])[var_name].sum().reset_index()

            out_img_file_name = out_img_dir / '{}_{}_{}.png'.format(basin_shp.parent.name, exp_name, var_name)
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.boxplot(
                data=in_df2,
                x='month', y=var_name,
                color=plt_color,
                showmeans=True, meanprops={'marker': 'o', 'markerfacecolor': 'white', 'markeredgecolor': plt_color},
                ax=ax)
            ax.set_title(plt_title)
            ax.set_ylabel('{long_name} ({units})'.format(**STN_VARS[var_name2]))
            plt.tight_layout()
            plt.savefig(out_img_file_name)

            if (var_name == 'rain'):
                out_img_file_name = out_img_dir / '{}_{}_{}_logscale.png'.format(basin_shp.parent.name, exp_name, var_name)
                fig, ax = plt.subplots(figsize=(12, 8))
                sns.boxplot(
                    data=in_df2,
                    x='month', y=var_name,
                    color=plt_color,
                    showmeans=True, meanprops={'marker': 'o', 'markerfacecolor': 'white', 'markeredgecolor': plt_color},
                    ax=ax)
                ax.set_title(plt_title)
                ax.set_yscale('symlog')
                ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%d"))
                ax.set_ylabel('{long_name} ({units})'.format(**STN_VARS[var_name2]))
                plt.tight_layout()
                plt.savefig(out_img_file_name)
            
            plt.close('all')

            out_stat_file = out_stat_dir / '{}_{}_{}.csv'.format(basin_shp.parent.name, exp_name, var_name)
            _stat_df = in_df2.groupby('month')[var_name].agg('describe').copy()
            _stat_df['basin'] = basin_shp.parent.name
            _stat_df['exp'] = exp_name
            _stat_df['var'] = var_name
            _stat_df = _stat_df.reset_index().set_index(['basin', 'exp', 'var', 'month']
            stat_df.append(_stat_df)
            _stat_df.to_csv(out_stat_file)

stat_df = pd.concat(stat_df)

var_name = 'temp'
out_stat_df = stat_df.loc[(slice(None), slice(None), var_name), 'mean']
out_stat_df = out_stat_df.reset_index().pivot_table(index=['basin', 'month'], columns='exp', values='mean')
out_stat_file = out_stat_dir / '../{}_mon.csv'.format(var_name)
for col_name in ['RCP45', 'RCP85']:
    out_stat_df[col_name+'_anom'] = out_stat_df[col_name] - out_stat_df['RF']
out_stat_df[['RF', 'RCP45', 'RCP45_anom', 'RCP85', 'RCP85_anom']].to_csv(out_stat_file)

out2_stat_df = out_stat_df.groupby(['basin']).mean()
out_stat_file = out_stat_dir / '../{}_annual.csv'.format(var_name)
for col_name in ['RCP45', 'RCP85']:
    out2_stat_df[col_name+'_anom'] = out2_stat_df[col_name] - out2_stat_df['RF']
out2_stat_df[['RF', 'RCP45', 'RCP45_anom', 'RCP85', 'RCP85_anom']].to_csv(out_stat_file)

var_name = 'rain'
out_stat_df = stat_df.loc[(slice(None), slice(None), var_name), 'mean']
out_stat_df = out_stat_df.reset_index().pivot_table(index=['basin', 'month'], columns='exp', values='mean')
out_stat_file = out_stat_dir / '../{}_mon.csv'.format(var_name)
for col_name in ['RCP45', 'RCP85']:
    out_stat_df[col_name+'_anom'] = out_stat_df[col_name] - out_stat_df['RF']
out_stat_df[['RF', 'RCP45', 'RCP45_anom', 'RCP85', 'RCP85_anom']].to_csv(out_stat_file)

out2_stat_df = out_stat_df.groupby(['basin']).sum()
out_stat_file = out_stat_dir / '../{}_annual.csv'.format(var_name)
for col_name in ['RCP45', 'RCP85']:
    out2_stat_df[col_name+'_anom'] = out2_stat_df[col_name] - out2_stat_df['RF']
    out2_stat_df[col_name+'_panom'] = 100 * out2_stat_df[col_name+'_anom'] / out2_stat_df['RF']
out2_stat_df[['RF', 'RCP45', 'RCP45_anom', 'RCP45_panom', 'RCP85', 'RCP85_anom', 'RCP85_panom']].to_csv(out_stat_file)