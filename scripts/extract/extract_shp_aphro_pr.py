from pathlib import Path
import pandas as pd
import salem

VAR = 'pr'
# VARS2 = 'pr'
OBS = {
    'aphrodite_v1101_r2': {
        'var_name': 'precip',
        'start_year': '1986',
        'end_year': '1997',
        'lat_name': 'latitude',
        'lon_name': 'longitude'
    },
    'aphrodite_v1801_r1': {
        'var_name': 'precip',
        'start_year': '1998',
        'end_year': '2005',
        'lat_name': 'lat',
        'lon_name': 'lon'
    }
}

XLS_SHEET_NAME = 'aphro'

in_shp_dir = Path('input/shp/basins')
in_nc_dir = Path('input/nc/obs')

out_xls_dir = Path('output/xls/obs')
out_xls_dir.mkdir(parents=True, exist_ok=True)

in_shps = list(in_shp_dir.glob('*/*.shp'))  

# basin loop
for basin_shp in in_shps:
    print('Processing {} --> precip'.format(basin_shp.parent.name))
    basin_gdf = salem.read_shapefile(basin_shp)     # read shp

    out_xlsx_file_name = out_xls_dir / '{}_precip.xlsx'.format(basin_shp.parent.name)
    if out_xlsx_file_name.is_file():
        out_xlsx = pd.ExcelWriter(out_xlsx_file_name, mode='a')
        ws_names = [ws.title for ws in out_xlsx.book.worksheets]
        if (XLS_SHEET_NAME in ws_names):
            out_xlsx.close()
            continue
    else:
        out_xlsx = pd.ExcelWriter(out_xlsx_file_name)

    out_df = []
    for obs, obs_info in OBS.items():
        nc_file = list(in_nc_dir.glob('obs_{}_{}_*.nc'.format(obs, VAR)))
        if len(nc_file) == 0:
            continue
        nc_file = nc_file[0]
        in_ds = salem.open_xr_dataset(nc_file).sel(time=slice(obs_info['start_year'], obs_info['end_year']))

        #region get region of interest
        out_ds = in_ds.salem.subset(shape=basin_gdf, margin=1)
        out_ds = out_ds.salem.roi(shape=basin_gdf, all_touched=True)
        #endregion get region of interest

        _out_df = out_ds[obs_info['var_name']].to_dataframe().reset_index().groupby([obs_info['lat_name'], obs_info['lon_name']]).filter(lambda x: not all(x[obs_info['var_name']].isna()))
        _out_df.rename(columns={obs_info['lat_name']: 'lat', obs_info['lon_name']: 'lon'}, inplace=True)
        _out_df['src'] = obs
        out_df.append(_out_df)

    out_df = pd.concat(out_df)
    out_df['year'] = out_df['time'].dt.year
    out_df['month'] = out_df['time'].dt.month
    out_df['day'] = out_df['time'].dt.day
    out_df.drop(columns=['time'], inplace=True)

    out_df[['lon', 'lat', 'year', 'month', 'day', 'src', 'precip']].to_excel(out_xlsx, XLS_SHEET_NAME)
    out_xlsx.save()
    out_xlsx.close()
