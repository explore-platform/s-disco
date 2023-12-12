''' This is simply to merge the data files provided by Tel-Aviv at the beginning of October.
rvs_data_full_with_params4_highsnr_no_duplicates.npz: general info with corresponding GAIA IDs;
all_weirdness_scores_highsnr_no_nn_no_duplicates.npz: weirdness score with associated GAIA IDs (column named source_ids but it seems to be corresponding to GAIA IDs);
umap_embedding_25nn_highsnr_no_duplicates.npz: UMAP values (X and Y), but no corresponding GAIA IDs.

all merged into: rvs_data_highsnr_with_params_no_duplicates.npz
'''

import os
import numpy as np
import pandas as pd

import pdb

def npz_to_df(data):
    ''' create a dictionary out of an npz loaded file '''

    data_dict = {}
    for key in data.keys():
        data_dict[key] = data[key]

    return pd.DataFrame(data_dict)

path = '/mount/internal/work-st/projects/cee-080/1853-explore/sda/sdisco/data/'

DATA_FILE_root = 'rvs_data_full_with_params4_highsnr_no_duplicates.npz'
data = np.load(os.path.join(path, DATA_FILE_root), allow_pickle = True)
df_root = npz_to_df(data)
df_root['gaia_id'] = df_root['gaia_id'].astype('int') # convert ID to int

# UMAP
DATA_FILE_umap = 'umap_embedding_25nn_highsnr_no_duplicates.npz'
data = np.load(os.path.join(path, DATA_FILE_umap), allow_pickle = True)
# X_embedded is combined so split it in 2 (X_umap, Y_umap)
X_umap = data['X_embedded'][:,0]
Y_umap = data['X_embedded'][:,1]
df_umap = pd.DataFrame({'X_umap':X_umap, 'Y_umap':Y_umap})

# weirdness score
DATA_FILE_wscore = 'all_weirdness_scores_highsnr_no_nn_no_duplicates.npz'
data = np.load(os.path.join(path, DATA_FILE_wscore), allow_pickle = True)
df_wscore = npz_to_df(data)
df_wscore['source_ids'] = df_wscore['source_ids'].astype('int') # convert ID to int

# merge the two table (no IDs in the umap table, so assume a one to one relationship, confirmed by TelAviv People)
df_ML = pd.concat([df_wscore, df_umap], axis = 1)

# merge root and ML results
df_all = df_root.merge(df_ML, left_on = 'gaia_id', right_on = 'source_ids')

# save that as an npz file to comply with original design
np.savez(os.path.join('./rvs_data_highsnr_with_params_no_duplicates.npz'),
    gaia_id = df_all.to_numpy()[:,0],
    teff = df_all.to_numpy()[:,1],
    logg = df_all.to_numpy()[:,2],
    mh = df_all.to_numpy()[:,3],
    ag = df_all.to_numpy()[:,4],
    distance = df_all.to_numpy()[:,5],
    bprp_color = df_all.to_numpy()[:,6],
    Mag = df_all.to_numpy()[:,7],
    new_ang = df_all.to_numpy()[:,8],
    galactic_x = df_all.to_numpy()[:,9],
    galactic_y = df_all.to_numpy()[:,10],
    galactic_z = df_all.to_numpy()[:,11],
    rv = df_all.to_numpy()[:,12],
    rv_err = df_all.to_numpy()[:,13],
    astrometric_excess_noise = df_all.to_numpy()[:,14],
    phot_g_mean_flux_over_error = df_all.to_numpy()[:,15],
    rv_expected_sig_to_noise = df_all.to_numpy()[:,16],
    grvs_mag = df_all.to_numpy()[:,17],
    rvs_spec_sig_to_noise = df_all.to_numpy()[:,18],
    weirdness_score = df_all.to_numpy()[:,19],
    source_ids = df_all.to_numpy()[:,20],
    X_umap = df_all.to_numpy()[:,21],
    Y_umap = df_all.to_numpy()[:,22])

## TEST THAT IT SAVED THE CORRECT FILE
test_data = np.load(os.path.join('./rvs_data_highsnr_with_params_no_duplicates_ready.npz'), allow_pickle = True)
df_test = npz_to_df(test_data)
df_diff = np.nanmean(df_test - df_all)

if df_diff != 0.0:
    raise ValueError('The original and saved dataframe are not exactly the same.')
else:
    print('PASSED')
