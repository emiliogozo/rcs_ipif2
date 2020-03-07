from pathlib import Path
import pandas as pd

from _const_.default import *

from _helper_.qm import do_qmap

in_csv_dir = Path('output/csv')
in_xls_dir = Path('output/xls')
in_shp_dir = Path('input/shp/basins')

out_csv_dir = Path('output/csv')
out_csv_dir.mkdir(parents=True, exist_ok=True)

VARS2 = ['tmean', 'precip']
DATE_RANGE = slice(*BL_PERIOD)

in_shps = list(in_shp_dir.glob('*/*.shp'))

#region basin loop
for basin_shp in in_shps:
    basin_name = basin_shp.parent.name
    #region variable loop
    for ivar, var_name in enumerate(VARS):
        var_name2 = VARS2[ivar]
        print('Processing {}: {}'.format(basin_name, var_name2))

        #region load observed data
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
        #endregion load observed data

        #region observed data loop
        for obs_name in obs_grd_df.index.get_level_values(1).unique():
            #region rcm loop
            for rcm_name, rcm_dat in RCMS.items():
                #region exp loop
                for exp_name in EXPS:
                    #region load reference period
                    c_in_file = in_csv_dir  / 'rcm/{}/RF/{}/{}.csv'.format(basin_name, var_name2, rcm_name)
                    if not c_in_file.is_file():
                        continue
                    c_mod_df = pd.read_csv(c_in_file).groupby(['year', 'month', 'day'])[var_name2].mean()
                    #endregion load reference period
                    if exp_name != 'RF':
                        #region load projection
                        p_in_file = in_csv_dir  / 'rcm/{}/{}/{}/{}.csv'.format(basin_name, exp_name, var_name2, rcm_name)
                        if not p_in_file.is_file():
                            continue
                        p_mod_df = pd.read_csv(p_in_file).groupby(['year', 'month', 'day'])[var_name2].mean()
                        #endregion load projection 
                    
                    mod_adj_df = []
                    #region month loop
                    for imon in range(1, 13):
                        # get observed values for the specific month
                        _obs_df = obs_grd_df.loc[(slice(None), obs_name, slice(*BL_PERIOD), imon), ]

                        # get reference values from the model for the specific month
                        _c_mod_df = c_mod_df.loc[(slice(*BL_PERIOD), imon), ]
                        if exp_name == 'RF':
                            _mod_adj_df = _c_mod_df.copy()
                            _mod_adj_df.loc[:] = do_qmap(_obs_df.to_numpy(), _c_mod_df.to_numpy())
                            _mod_adj_df.name = _mod_adj_df.name + '_adj'
                        else:
                            _mod_adj_df = []
                            for adj_type in ['default', 'edcdf']:
                                _p_mod_df = p_mod_df.loc[(slice(None), imon), ]
                                __mod_adj_df = _p_mod_df.copy()
                                _, __mod_adj_df.loc[:] = do_qmap(_obs_df.to_numpy(), _c_mod_df.to_numpy(), _p_mod_df.to_numpy(), proj_adj_type=adj_type)
                                __mod_adj_df.name = __mod_adj_df.name + '_adj_' + adj_type
                                _mod_adj_df.append(__mod_adj_df)
                            _mod_adj_df = pd.concat(_mod_adj_df, axis=1)
                        
                        mod_adj_df.append(_mod_adj_df)
                    #endregion month loop
                    out_file = out_csv_dir  / 'rcm_adj/{}/{}/{}/{}/{}.csv'.format(basin_name, exp_name, var_name2, obs_name, rcm_name)
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    mod_adj_df = pd.concat(mod_adj_df, sort=True)
                    if exp_name == 'RF':
                        out_df = pd.concat([c_mod_df, mod_adj_df], axis=1)
                    else:
                        out_df = pd.concat([p_mod_df, mod_adj_df], axis=1)
                    out_df.to_csv(out_file)
                #endregion exp loop
            #endregion rcm loop
        #endregion observed data loop
    #endregion variable loop
#endregion basin loop
