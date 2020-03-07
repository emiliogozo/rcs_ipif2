from pathlib import Path
import pandas as pd
import geopandas as gpd
import salem
from geopandas.tools import sjoin

from _helper_.db import db_connect

IN_SHP_DIR = Path('input/shp/basins')

OUT_CSV_DIR = Path('output/csv')
OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = pd.to_datetime('1986-1-1 00:00:00').tz_localize('Asia/Manila')
END_DATE = pd.to_datetime('2006-1-1 00:00:00').tz_localize('Asia/Manila')
START_DATE_UTC = START_DATE.tz_convert('UTC')
END_DATE_UTC = END_DATE.tz_convert('UTC')

mng_db = db_connect('config/db.json')

out_csv_dir = Path('output/csv/stn')
out_csv_dir.mkdir(parents=True, exist_ok=True)

in_shps = list(IN_SHP_DIR.glob('*/*.shp'))

def_crs = {'init': 'epsg:4326'}

stn2_xlsx_file_name = Path('input/xls/stn/pagasa.xlsx')
stn_info2_df = pd.read_excel(stn2_xlsx_file_name, sheet_name='sta_info')
stn_info2_gdf = gpd.GeoDataFrame(stn_info2_df, geometry=gpd.points_from_xy(stn_info2_df['lon'], stn_info2_df['lat']), crs=def_crs)

for basin_shp in in_shps:
    buffer = 0.25
    basin_name = basin_shp.parent.name
    out_csv_file_name = out_csv_dir / '{}.csv'.format(basin_name)
    if not out_csv_file_name.is_file():
        print('Processing {}'.format(basin_name))
        basin_gdf = salem.read_shapefile(basin_shp).to_crs(def_crs)     # read shp
        basin_buf_gdf = basin_gdf.copy()
        basin_buf_gdf.geometry = basin_buf_gdf.buffer(buffer)
        shp_geom = basin_buf_gdf.geometry.values[0].__geo_interface__

        db_cm = mng_db['station_info']
        _stn_df = pd.DataFrame(list(db_cm.find(
            {
                'loc': {'$geoWithin': {'$geometry': shp_geom}},
                'src': 'pagasa'
            },
            {'_id': 0})))
        _df = pd.DataFrame()
        _df2 = pd.DataFrame()
        if _stn_df.size > 0:
            _stn_df['lon'] = _stn_df['loc'].apply(lambda pt: pt['coordinates'][0])
            _stn_df['lat'] = _stn_df['loc'].apply(lambda pt: pt['coordinates'][1])
            _stn_df = _stn_df[['lon', 'lat', 'code', 'description']].copy()

            stn_codes =  pd.to_numeric(_stn_df['code']).tolist()
            db_cm = mng_db['station_data']
            res = db_cm.aggregate([
                {'$match': {
                'stn_code': {'$in': stn_codes},
                'stn_src': 'pagasa',
                'timestamp': {
                    '$lt': END_DATE_UTC,
                    '$gte': START_DATE_UTC}}
                },
                {'$project': {
                '_id': 0,
                'stn_code': 1,
                'year': {'$year': {'$add': [ '$timestamp', 8 * 60 * 60 * 1000 ] }},
                'month': {'$month': {'$add': [ '$timestamp', 8 * 60 * 60 * 1000 ] }},
                'day': {'$dayOfMonth': {'$add': [ '$timestamp', 8 * 60 * 60 * 1000 ] }},
                'temp': {'$avg': ['$min_temperature', '$min_temperature']},
                'rain': 1}}
            ])
            _df = pd.DataFrame(list(res))
            _df = _stn_df.merge(_df, left_on=['code'], right_on=['stn_code'], how='right')
            _df = _df[['stn_code', 'lon', 'lat', 'year', 'month', 'day', 'rain', 'temp']].copy()

        _stn2_df = gpd.sjoin(stn_info2_gdf, basin_buf_gdf, how='inner')
        if _stn2_df.size > 0:
            _stn2_df.rename(columns={
                'sta_name': 'description',
                'id': 'code'
            }, inplace=True)
            _stn2_df = _stn2_df[['lon', 'lat', 'code', 'description']].copy()
            _df2 = pd.concat(pd.read_excel(stn2_xlsx_file_name, sheet_name=_stn2_df['description'].to_list()), names=['name', 'idx'])
            _df2 = _df2.reset_index().drop(columns=['idx'])
            _df2.columns = _df2.columns.str.lower()
            _df2 = _df2.loc[_df2['year'].between(START_DATE.year, (END_DATE.year-1)),]
            _df2 = _stn2_df.merge(_df2, left_on=['description'], right_on=['name'], how='right')        
            _df2.rename(columns={
                'code': 'stn_code',
                'tmin': 'tmn',
                'tmax': 'tmx',
                'rainfall': 'rain'
            }, inplace=True)
            for col_name in ['rain', 'tmx', 'tmn']:
                _df2.loc[_df2[col_name]=='T', col_name] = 0
                _df2.loc[_df2[col_name]==-2, col_name] = np.nan
            _df2['temp'] = (_df2['tmx'] + _df2['tmn']) / 2
            _df2  = _df2[_df.columns].copy()
            
        out_stn_df = pd.concat([_stn_df, _stn2_df], ignore_index=True, sort=False)
        out_stn_csv_file_name = out_csv_dir / '{}_stn_info.csv'.format(basin_name)
        out_stn_df.to_csv(out_stn_csv_file_name, index=False)
        out_df = pd.concat([_df, _df2], ignore_index=True, sort=False)
        out_df.to_csv(out_csv_file_name, index=False)
    