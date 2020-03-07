from pathlib import Path
import pandas as pd
import salem

import matplotlib.pyplot as plt
import seaborn as sns

from _const_.default import *

sns.set_context('talk')
sns.set_style('whitegrid')

in_csv_dir = Path('output/csv')
in_xls_dir = Path('output/xls')
in_shp_dir = Path('input/shp/basins')

out_img_dir = Path('output/img/rcm/compare_obs')
out_img_dir.mkdir(parents=True, exist_ok=True)

VARS2 = ['tmean', 'precip']
EXP_NAME = 'RF'

in_shps = list(in_shp_dir.glob('*/*.shp'))


for basin_shp in in_shps:
    print(basin_shp)
    basin_name = basin_shp.parent.name

    for ivar, var_name in enumerate(VARS):
        # if var_name == 'rain':
        #     continue
        var_name2 = VARS2[ivar]
        print('Processing {}: {}'.format(basin_name, var_name2))

        plt_stn_df = plt_obs_grd_df = plt_mod_df = None
        in_file = in_csv_dir  / 'stn/{}_stn_info.csv'.format(basin_name)
        if in_file.is_file():
            stn_info_df = pd.read_csv(in_file)

        in_file = in_csv_dir  / 'stn/{}.csv'.format(basin_name)
        if in_file.is_file():
            stn_df = pd.read_csv(in_file, usecols=['stn_code', 'lon', 'lat', 'year', 'month', 'day', var_name])
            stn_df = stn_info_df.merge(stn_df, left_on=['code'], right_on=['stn_code'], how='right')
            stn_df.rename(columns={
                'description': 'grp2'
            }, inplace=True)
            stn_df['grp1'] = 'stn'
            stn_df.set_index(['grp1', 'grp2', 'year', 'month', 'day'], inplace=True)
            stn_df = stn_df.loc[(slice(None), slice(None), slice(*BL_PERIOD)), ]
            stn_df = stn_df.groupby(['grp1', 'grp2', 'year', 'month', 'day'])[var_name].mean()
            if var_name == 'rain':
                plt_stn_df = stn_df.groupby(['grp1', 'grp2', 'year', 'month']).sum()
            elif var_name == 'temp':
                plt_stn_df = stn_df.groupby(['grp1', 'grp2', 'year', 'month']).mean()
        
        in_file = in_xls_dir  / 'obs/{}_{}.xlsx'.format(basin_name, var_name2)
        if in_file.is_file():
            obs_grd_df = pd.read_excel(in_file, sheet_name=None, index_col=[0,1,2,3,4], usecols=['lon', 'lat', 'year', 'month', 'day', var_name2])
            obs_grd_df = pd.concat(obs_grd_df, names=['grp2'])
            obs_grd_df.rename(columns={
                var_name2: var_name
            }, inplace=True)
            obs_grd_df['grp1'] = 'obs_grd'
            obs_grd_df = obs_grd_df.reset_index().set_index(['grp1', 'grp2', 'year', 'month', 'day'])
            # obs_grd_df.sort_index(inplace=True)
            obs_grd_df = obs_grd_df.loc[(slice(None), slice(None), slice(*BL_PERIOD)), ]
            # obs_grd_df.columns =  obs_grd_df.columns.get_level_values(0)
            obs_grd_df = obs_grd_df.groupby(['grp1', 'grp2', 'year', 'month', 'day'])[var_name].mean()
            if var_name == 'rain':
                plt_obs_grd_df = obs_grd_df.groupby(['grp1', 'grp2', 'year', 'month']).sum()
            elif var_name == 'temp':
                plt_obs_grd_df = obs_grd_df.groupby(['grp1', 'grp2', 'year', 'month']).mean()
        # plt_obs_grd_df = plt_obs_grd_df.groupby(['grp', 'month']).describe()
            
        in_csvs = list((in_csv_dir  / 'rcm/{}/RF/{}'.format(basin_name, var_name2)).glob('*.csv'))
        if len(in_csvs):
            mod_df = []
            for in_csv in in_csvs:
                mod_df.append(pd.read_csv(in_csv).groupby(['lon', 'lat', 'year', 'month', 'day']).mean())
            mod_df = pd.concat(mod_df, axis=1)
            mod_df.columns = RCMS.keys()
            mod_df = mod_df.loc[(slice(None), slice(None), slice(*BL_PERIOD)), ]
            mod_df = mod_df.groupby(['year', 'month', 'day']).mean()
            if var_name == 'rain':
                plt_mod_df = mod_df.groupby(['year', 'month']).sum()
            elif var_name == 'temp':
                plt_mod_df = mod_df.groupby(['year', 'month']).mean()

            plt_mod_df.columns = var_name + plt_mod_df.columns
            plt_mod_df['grp1'] = 'rcm'
            plt_mod_df = pd.wide_to_long(df=plt_mod_df.reset_index(), i=['grp1', 'year', 'month'], j='grp2', stubnames=[var_name], suffix='[-\w]+')[var_name]
            plt_mod_df = plt_mod_df.reorder_levels(['grp1', 'grp2', 'year', 'month']) 

        in_csv_dirs = list((in_csv_dir / 'rcm_adj/{}/RF/{}'.format(basin_name, var_name2)).glob('*'))
        plt_mod_adj_df = []
        for in_csv_dir2 in in_csv_dirs:
            in_csvs = list(in_csv_dir2.glob('*.csv'))
            if len(in_csvs):
                _mod_adj_df = []
                for in_csv in in_csvs:
                    _mod_adj_df.append(pd.read_csv(in_csv).groupby(['year', 'month', 'day'])['adjusted'].mean())
                _mod_adj_df = pd.concat(_mod_adj_df, axis=1)
                _mod_adj_df.columns = RCMS.keys()
                _mod_adj_df = _mod_adj_df.loc[(slice(*BL_PERIOD)), ]
                # mod_df = mod_df.groupby(['year', 'month', 'day']).mean()
                if var_name == 'rain':
                    _plt_mod_adj_df = _mod_adj_df.groupby(['year', 'month']).sum()
                elif var_name == 'temp':
                    _plt_mod_adj_df = _mod_adj_df.groupby(['year', 'month']).mean()

                _plt_mod_adj_df.columns = var_name + _plt_mod_adj_df.columns
                _plt_mod_adj_df['grp1'] = 'rcm_{}_adj'.format(in_csv_dir2.name)
                _plt_mod_adj_df = pd.wide_to_long(df=_plt_mod_adj_df.reset_index(), i=['grp1', 'year', 'month'], j='grp2', stubnames=[var_name], suffix='[-\w]+')[var_name]
                _plt_mod_adj_df = _plt_mod_adj_df.reorder_levels(['grp1', 'grp2', 'year', 'month'])
                plt_mod_adj_df.append(_plt_mod_adj_df)


        plt_df = pd.concat([plt_stn_df, plt_obs_grd_df, plt_mod_df]+plt_mod_adj_df).reset_index()

        plt_df.loc[plt_df['grp1']=='stn', 'grp'] = plt_df.loc[plt_df['grp1']=='stn', 'grp2']
        plt_df.loc[plt_df['grp1']=='obs_grd', 'grp'] = plt_df.loc[plt_df['grp1']=='obs_grd', 'grp2']
        plt_df.loc[plt_df['grp1'].str.contains('rcm'), 'grp'] = plt_df.loc[plt_df['grp1'].str.contains('rcm'), 'grp1']

        stn_cnt = plt_df.loc[plt_df['grp1']=='stn', 'grp'].nunique()
        grp_cnt = plt_df['grp'].nunique() - stn_cnt

        if var_name == 'rain':
            var_name3 = 'pr'
        else:
            var_name3 = var_name

        out_img_file_name = out_img_dir / '{}_{}.png'.format(basin_name, var_name)
        plt_title = '{} - {}'.format(basin_name.capitalize(), var_name.capitalize())
        fig, ax  = plt.subplots(figsize=(15,8))
        sns.boxplot(x='month', y=var_name, data=plt_df, hue='grp', palette=([(0.3,0.3,0.3)]*stn_cnt + sns.color_palette('Set3', grp_cnt)) , ax=ax)
        plt.legend(loc='center right', bbox_to_anchor=(1.25, 0.5), ncol=1)
        ax.set_title(plt_title)
        ax.set_ylabel('{long_name} ({units})'.format(**STN_VARS[var_name3]))
        if var_name == 'temp':
            ax.set_ylim(ymin=15, ymax=30)
        elif var_name == 'rain':
            ax.set_ylim(ymin=0, ymax=2000)
        fig.tight_layout()
        plt.savefig(out_img_file_name)
        plt.close('all')

            # out_img_file_name = out_img_dir / '{}_{}_{}_{}_nofliers.png'.format(basin_name, in_names[idx], exp_name.lower(), var_name)
            # plt_title = '{} - {} {}'.format(basin_name.capitalize(), exp_name, var_name.capitalize())
            # fig, ax  = plt.subplots(figsize=(15,8))
            # sns.boxplot(x='month', y=var_name, data=plt_df, hue='rcms', hue_order=col_names, showfliers=False, palette=([(0.3,0.3,0.3)] + sns.color_palette('Set3', 5)) , ax=ax)
            # plt.legend(loc='center right', bbox_to_anchor=(1.25, 0.5), ncol=1)
            # ax.set_title(plt_title)
            # ax.set_ylabel('{long_name} ({units})'.format(**STN_VARS[var_name2]))
            # fig.tight_layout()
            # plt.savefig(out_img_file_name)
            # plt.close('all')
