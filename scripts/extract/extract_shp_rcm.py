from pathlib import Path
import pandas as pd

import cftime
import salem

VARS = ['precip', 'tmean']
VARS2 = ['rain', 'temp']
RCMS = ['CNRM', 'CSIRO', 'EC-EARTH', 'HADGEM2', 'MPI']
EXPS=['RF', 'RCP45', 'RCP85']
RF_DATE_RANGE = slice('1986', '2005')
PROJ_DATE_RANGE = slice('2016', '2035')
PROJ_DATE_RANGE = slice('2006', '2099')

in_shp_dir = Path('input/shp/basins')
in_nc_dir = Path('input/nc/rcm')

out_xls_dir = Path('output/xls/rcm')
out_xls_dir.mkdir(parents=True, exist_ok=True)
out_csv_dir = Path('output/csv/rcm')
out_csv_dir.mkdir(parents=True, exist_ok=True)


in_shps = list(in_shp_dir.glob('*/*.shp'))

# basin loop
for basin_shp in in_shps:
    basin_gdf = salem.read_shapefile(basin_shp)     # read shp
    # experiment loop
    for exp_name in EXPS:
        if exp_name == 'RF':
            date_range = RF_DATE_RANGE
        else:
            date_range = PROJ_DATE_RANGE
        # variable loop
        for ivar, var_name in enumerate(VARS):
            ens_df = []
            out_csv_dir2 = out_csv_dir / '{}/{}/{}'.format(basin_shp.parent.name, exp_name, var_name)
            out_csv_dir2.mkdir(parents=True, exist_ok=True)
            # rcm loop
            for rcm_name in RCMS:
                print('Processing {} --> {} --> {} --> {}'.format(basin_shp.parent.name, exp_name, var_name, rcm_name))
                out_csv_file_name = out_csv_dir2 / '{}.csv'.format(rcm_name)
                if not out_csv_file_name.is_file():
                    #region read rcm input
                    nc_file = list(in_nc_dir.glob('{}_{}_{}_*.nc'.format(rcm_name, exp_name, var_name)))
                    if len(nc_file) == 0:
                        continue
                    nc_file = nc_file[0]
                    in_ds = salem.open_xr_dataset(nc_file).sel(time=date_range)
                    #endregion read rcm input

                    #region get region of interest
                    out_ds = in_ds.salem.subset(shape=basin_gdf, margin=1)
                    out_ds = out_ds.salem.roi(shape=basin_gdf, all_touched=True)
                    #endregion get region of interest

                    #region prepare data for writing
                    out_df = out_ds[var_name].to_dataframe().reset_index().groupby(['lat', 'lon']).filter(lambda x: not all(x[var_name].isna()))
                    if isinstance(out_df.iloc[0]['time'],cftime._cftime.DatetimeNoLeap) or isinstance(out_df.iloc[0]['time'],cftime._cftime.Datetime360Day):
                        out_df['time'] =  [pd.to_datetime(_dt.strftime(), errors='coerce') for _dt in out_df['time'].values]
                        out_df.dropna(subset=['time'], inplace=True)
                    
                    out_df['year'] = out_df['time'].dt.year
                    out_df['month'] = out_df['time'].dt.month
                    out_df['day'] = out_df['time'].dt.day
                    out_df.drop(columns=['time'], inplace=True)

                    if var_name == 'tmean':
                        out_df[var_name] -= 273.15
                    #endregion prepare data for writing

                    # out_df = pd.read_csv(Path('output/csv/rcm0') / '{}/{}/{}/{}.csv'.format(basin_shp.parent.name, exp_name, var_name, rcm_name), usecols=['lat', 'lon', 'year', 'month', 'day', var_name])
                    out_df.to_csv(out_csv_file_name, index=False)

