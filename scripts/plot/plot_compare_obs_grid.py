from pathlib import Path
import pandas as pd
import salem

import matplotlib.pyplot as plt
import seaborn as sns

sns.set_context('talk')
sns.set_style('whitegrid')

in_xls_dir = Path('output/xls/obs')

out_img_dir = Path('output/img/obs/compare_grids')
out_img_dir.mkdir(parents=True, exist_ok=True)

var_name = 'precip'

in_files = list(in_xls_dir.glob('*.xlsx'))

dem_ds = salem.open_xr_dataset(Path('input/nc/dem/dem.nc'))

for in_file in in_files:
    print(in_file)
    in_xlsx = pd.ExcelFile(in_file)
    for ws_name in in_xlsx.sheet_names:
        in_df = pd.read_excel(in_xlsx, sheet_name=ws_name)
        in_hi_df = in_df.groupby(['lon', 'lat']).filter(lambda x: dem_ds.sel(lon=x.name[0],lat=x.name[1])['Band1'].values > 200)
        in_lo_df = in_df.groupby(['lon', 'lat']).filter(lambda x: dem_ds.sel(lon=x.name[0],lat=x.name[1])['Band1'].values <= 200)

        in_names = ['all', 'hi', 'lo']
        for idx, _in_df in enumerate([in_df, in_hi_df, in_lo_df]):
            if _in_df.size == 0:
                continue
            plt_df = _in_df.groupby(['lon', 'lat', 'year','month'])[var_name].sum().reset_index()
            plt_df['group'] = '('+plt_df['lat'].astype('str') + ', ' + plt_df['lon'].astype('str')+')'

            plt_df2 = _in_df.groupby(['year', 'month', 'day'])[var_name].mean().reset_index()
            plt_df2 = plt_df2.groupby(['year','month'])[var_name].sum().reset_index()
            plt_df2['group'] = 'Area Average'

            plt_df = pd.concat([plt_df2, plt_df], sort=False)

            basin_name = in_file.name.split('_')[0]
            if ws_name == 'aphro':
                src_name = 'Aphrodite'
            elif ws_name == 'trmm':
                src_name = 'TRMM'

            out_img_file_name = out_img_dir / '{}_{}_{}_{}.png'.format(basin_name, in_names[idx], src_name.lower(), var_name)
            plt_title = '{} - {} {}'.format(basin_name.capitalize(), src_name, var_name.capitalize())
            fig, ax  = plt.subplots(figsize=(15,8))
            sns.boxplot(x='month', y='precip', data=plt_df, hue='group', palette=([(0.3,0.3,0.3)] + sns.color_palette('Set3', 16)) , ax=ax)
            plt.legend(loc='center right', bbox_to_anchor=(1.25, 0.5), ncol=1)
            ax.set_title(plt_title)
            ax.set_ylabel('Rainfall (mm)')
            fig.tight_layout()
            plt.savefig(out_img_file_name)
            plt.close('all')

            out_img_file_name = out_img_dir / '{}_{}_{}_{}_nofliers.png'.format(basin_name, in_names[idx], src_name.lower(), var_name)
            plt_title = '{} - {} {}'.format(basin_name.capitalize(), src_name, var_name.capitalize())
            fig, ax  = plt.subplots(figsize=(15,8))
            sns.boxplot(x='month', y='precip', data=plt_df, hue='group', showfliers=False, palette=([(0.3,0.3,0.3)] + sns.color_palette('Set3', 16)) , ax=ax)
            plt.legend(loc='center right', bbox_to_anchor=(1.25, 0.5), ncol=1)
            ax.set_title(plt_title)
            ax.set_ylabel('Rainfall (mm)')
            fig.tight_layout()
            plt.savefig(out_img_file_name)
            plt.close('all')
