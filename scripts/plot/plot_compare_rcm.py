from pathlib import Path
import pandas as pd
import salem

import matplotlib.pyplot as plt
import seaborn as sns

from _const_.default import *

sns.set_context('talk')
sns.set_style('whitegrid')

in_csv_dir = Path('output/csv/rcm')
in_shp_dir = Path('input/shp/basins')

out_img_dir = Path('output/img/rcm/compare_rcms')
out_img_dir.mkdir(parents=True, exist_ok=True)

VARS2 = ['tmean', 'precip']
RF_DATE_RANGE = slice(*BL_PERIOD)
PROJ_MID_DATE_RANGE = slice(*PROJ_PERIODS['mid'])

in_shps = list(in_shp_dir.glob('*/*.shp'))

dem_ds = salem.open_xr_dataset(Path('input/nc/dem/dem.nc'))

# stat_df = []
for basin_shp in in_shps:
    print(basin_shp)
    basin_name = basin_shp.parent.name
    for exp_name in EXPS:
        if exp_name == 'RF':
            date_range = RF_DATE_RANGE
        else:
            date_range = PROJ_MID_DATE_RANGE
        for ivar, var_name in enumerate(VARS):
            print('Processing {}: {} - {}'.format(basin_name, exp_name, VARS2[ivar]))

            if var_name == 'rain':
                plt_color = sns.color_palette('Set3')[2]
                var_name2 = 'pr'
            elif var_name == 'temp':
                plt_color = sns.color_palette('Set3')[3]
                var_name2 = 'temp'
            else:
                continue
            
            in_csvs = list((in_csv_dir  / '{}/{}/{}'.format(basin_name, exp_name, VARS2[ivar])).glob('*.csv'))

            in_df = []
            for in_csv in in_csvs:
                in_df.append(pd.read_csv(in_csv).groupby(['lon', 'lat', 'year', 'month', 'day']).mean())
            in_df = pd.concat(in_df, axis=1)

            # in_df = pd.concat([pd.read_csv(in_csv, index_col=['lon', 'lat', 'year', 'month', 'day']) for in_csv in in_csvs], axis=1)
            in_df.columns = RCMS.keys()
            in_df = in_df.loc[(slice(None), slice(None), date_range), ]

            in_hi_df = in_df.groupby(['lon', 'lat']).filter(lambda x: dem_ds.sel(lon=x.name[0],lat=x.name[1])['Band1'].values > 200)
            in_lo_df = in_df.groupby(['lon', 'lat']).filter(lambda x: dem_ds.sel(lon=x.name[0],lat=x.name[1])['Band1'].values <= 200)

            in_names = ['all', 'hi', 'lo']
            for idx, _in_df in enumerate([in_df, in_hi_df, in_lo_df]):
                if _in_df.size == 0:
                    continue
            
                plt_df = _in_df.groupby(['year', 'month', 'day']).mean()
                col_names = ['Ensemble'] + plt_df.columns.to_list()
                plt_df['Ensemble'] = plt_df.mean(axis=1)

                if var_name == 'temp':
                    plt_df = plt_df.groupby(['year','month']).mean()
                elif var_name == 'rain':
                    plt_df = plt_df.groupby(['year','month']).sum()

                plt_df.columns = var_name + plt_df.columns
                plt_df = pd.wide_to_long(df=plt_df.reset_index(), i=['year', 'month'], j='rcms', stubnames=[var_name], suffix='[-\w]+').reset_index()

                # _stat_df = plt_df[var_name].describe()
                # _stat_df['basin'] = basin_name
                # _stat_df['exp'] = exp_name
                # _stat_df['var'] = var_name
                # stat_df.append(_stat_df)

                out_img_file_name = out_img_dir / '{}_{}_{}_{}.png'.format(basin_name, in_names[idx], exp_name.lower(), var_name)
                plt_title = '{} - {} {}'.format(basin_name.capitalize(), exp_name, var_name.capitalize())
                fig, ax  = plt.subplots(figsize=(15,8))
                sns.boxplot(x='month', y=var_name, data=plt_df, hue='rcms', hue_order=col_names, palette=([(0.3,0.3,0.3)] + sns.color_palette('Set3', 5)) , ax=ax)
                plt.legend(loc='center right', bbox_to_anchor=(1.25, 0.5), ncol=1)
                ax.set_title(plt_title)
                ax.set_ylabel('{long_name} ({units})'.format(**STN_VARS[var_name2]))
                if var_name == 'temp':
                    ax.set_ylim(ymin=15, ymax=30)
                elif var_name == 'rain':
                    ax.set_ylim(ymin=0, ymax=3500)
                fig.tight_layout()
                plt.savefig(out_img_file_name)
                plt.close('all')

                out_img_file_name = out_img_dir / '{}_{}_{}_{}_nofliers.png'.format(basin_name, in_names[idx], exp_name.lower(), var_name)
                plt_title = '{} - {} {}'.format(basin_name.capitalize(), exp_name, var_name.capitalize())
                fig, ax  = plt.subplots(figsize=(15,8))
                sns.boxplot(x='month', y=var_name, data=plt_df, hue='rcms', hue_order=col_names, showfliers=False, palette=([(0.3,0.3,0.3)] + sns.color_palette('Set3', 5)) , ax=ax)
                plt.legend(loc='center right', bbox_to_anchor=(1.25, 0.5), ncol=1)
                ax.set_title(plt_title)
                ax.set_ylabel('{long_name} ({units})'.format(**STN_VARS[var_name2]))
                if var_name == 'temp':
                    ax.set_ylim(ymin=15, ymax=30)
                elif var_name == 'rain':
                    ax.set_ylim(ymin=0, ymax=3500)
                fig.tight_layout()
                plt.savefig(out_img_file_name)
                plt.close('all')
