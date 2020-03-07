import os
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

IMG_DIR = Path('output/img')
STAT_DIR = Path('output/stat')
CSV_DIR = Path('/output/csv')

VARS = ['temp', 'rain']
GRID_OBS_VARS = ['ts', 'pr']
GRID_MOD_VARS = ['tas', 'pr']
# RCMS = ['CNRM', 'CSIRO', 'EC-EARTH', 'HADGEM2', 'MPI', 'PRECIS', 'RegCM4']
RCMS = {
    'CNRM': {'cal': 'standard'},
    'CSIRO': {'cal': 'standard'},
    'EC-EARTH': {'cal': 'standard'},
    'HADGEM2': {'cal': 'standard'},
    'MPI': {'cal': 'standard'}
}
PAGASA_RCMS = ['PRECIS', 'RegCM4']
EXPS = ['RF', 'RCP45', 'RCP85']
BL_PERIOD = [1986, 2005]
PROJ_PERIODS = {
    'early': [2016, 2035],
    'mid': [2046, 2065],
    'late': [2080, 2099]
}
CSV_NAMES = ['obs_stn', 'obs_grd', 'mod']

STN_VARS = {
    'temp': {
        'long_name': 'Temperature',
        'units': '$^\circ$C',
        'units2': '$^\circ$C'
    },
    'tmx': {
        'long_name': 'Maximum Temperature',
        'units': '$^\circ$C'
    },
    'rh': {
        'long_name': 'Relative Humidity',
        'units': '%'
    },
    'pr': {
        'long_name': 'Rainfall',
        'units': 'mm',
        'units2': '%'
    }
}
