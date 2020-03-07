import warnings

import numpy as np
from scipy import stats as st

def generate_distribution(data, dist_name='hist', bins=200):
    """Generate distribution"""

    _data = data[~np.isnan(data)] 

    out_dist = None
    out_params = None

    if dist_name=='hist':
        h = np.histogram(_data, bins=bins, density=True)
        out_dist = st.rv_histogram(h)
    else:
        y, x = np.histogram(_data, bins=bins, density=True)
        x = (x + np.roll(x, -1))[:-1] / 2.0
        # Try to fit the distribution

        try:
            # Ignore warnings from data that can't be fit
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                # fit dist to data
                out_dist = getattr(st, dist_name)
                out_params = out_dist.fit(_data)
        except Exception:
            return (None, None)
    return (out_dist, out_params)


def best_fit_distribution(data, distributions=None, bins=200):
    """Model data by finding best fit distribution to data"""
    # Get histogram of original data
    _data = data[~np.isnan(data)]
    y, x = np.histogram(_data, bins=bins, density=True)
    x = (x + np.roll(x, -1))[:-1] / 2.0

    if distributions is None:
        distributions = ['norm', 'lognorm', 'gamma']

    # Best holders
    best_dist = st.norm
    best_params = (0.0, 1.0)
    best_sse = np.inf

    for dist_name in distributions:
        # Try to fit the distribution
        # print(dist_name)
        try:
            # fit dist to data
            dist, params = generate_distribution(_data, bins=bins, dist_name=dist_name)

            # Separate parts of parameters
            arg = params[:-2]
            loc = params[-2]
            scale = params[-1]

            # Calculate fitted PDF and error with fit in distribution
            pdf = dist.pdf(x, loc=loc, scale=scale, *arg)
            sse = np.sum(np.power(y - pdf, 2.0))

            # identify if this distribution is better
            if best_sse > sse > 0:
                best_dist = dist
                best_params = params
                best_sse = sse
        except Exception:
            continue
        # print(dist, params)

    return (best_dist.name, best_params)
