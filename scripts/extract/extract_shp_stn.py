from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import salem
from geopandas.tools import sjoin

IN_SHP_DIR = Path('input/shp/basins')

OUT_CSV_DIR = Path('output/csv')
OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = pd.to_datetime('1986-1-1 00:00:00').tz_localize('Asia/Manila')
END_DATE = pd.to_datetime('2006-1-1 00:00:00').tz_localize('Asia/Manila')
START_DATE_UTC = START_DATE.tz_convert('UTC')
END_DATE_UTC = END_DATE.tz_convert('UTC')

out_csv_dir = Path('output/csv/stn')
out_csv_dir.mkdir(parents=True, exist_ok=True)

in_shps = list(IN_SHP_DIR.glob('*/*.shp'))

def_crs = {'init': 'epsg:4326'}

stn_xlsx_file_name = Path('input/xls/stn/pagasa.xlsx')
stn_info_df = pd.read_excel(stn_xlsx_file_name, sheet_name='sta_info')
stn_info_gdf = gpd.GeoDataFrame(stn_info_df, geometry=gpd.points_from_xy(stn_info_df['lon'], stn_info_df['lat']), crs=def_crs)

for basin_shp in in_shps:
    buffer = 0.25
    basin_name = basin_shp.parent.name
    stn_info_csv_file_name = out_csv_dir / '{}_stn_info.csv'.format(basin_name)
    out_csv_file_name = out_csv_dir / '{}.csv'.format(basin_name)
    if not out_csv_file_name.is_file():
        print('Processing {}'.format(basin_name))
        basin_gdf = salem.read_shapefile(basin_shp).to_crs(def_crs)     # read shp
        basin_buf_gdf = basin_gdf.copy()
        basin_buf_gdf.geometry = basin_buf_gdf.buffer(buffer)

        stn_info_df = gpd.sjoin(stn_info_gdf, basin_buf_gdf, how='inner')
        out_df = pd.DataFrame()
        if stn_info_df.size > 0:
            stn_info_df.rename(columns={
                'sta_name': 'description',
                'id': 'code'
            }, inplace=True)
            stn_info_df = stn_info_df[['lon', 'lat', 'code', 'description']].copy()
            out_df = pd.concat(pd.read_excel(stn_xlsx_file_name, sheet_name=stn_info_df['description'].to_list()), names=['name', 'idx'])
            out_df = out_df.reset_index().drop(columns=['idx'])
            out_df.columns = out_df.columns.str.lower()
            out_df = out_df.loc[out_df['year'].between(START_DATE.year, (END_DATE.year-1)),]
            out_df = stn_info_df.merge(out_df, left_on=['description'], right_on=['name'], how='right')        
            out_df.rename(columns={
                'code': 'stn_code',
                'tmin': 'tmn',
                'tmax': 'tmx',
                'rainfall': 'rain'
            }, inplace=True)
            for col_name in ['rain', 'tmx', 'tmn']:
                out_df.loc[out_df[col_name]=='T', col_name] = 0
                out_df.loc[out_df[col_name]==-2, col_name] = np.nan
            out_df['temp'] = (out_df['tmx'] + out_df['tmn']) / 2
            out_df  = out_df[['lon', 'lat', 'stn_code', 'year', 'month', 'day', 'rain', 'temp']].copy()
            
            stn_info_df.to_csv(stn_info_csv_file_name, index=False)
            out_df.to_csv(out_csv_file_name, index=False)
    