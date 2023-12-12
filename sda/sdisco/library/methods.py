''' methods required to run the sda '''
import pandas as pd
import numpy as np
from bokeh.models import HoverTool
import panel as pn
import holoviews as hv
import datetime

def grab_metadata_text(filename, filesize, n_sel, xaxis, yaxis, bounds, df_sel, dataset):
    ''' creates the text for the meta data file saved with the selection'''

    # reformat the file size for better display
    if filesize < 0.01:
        filesize = "<0.01"
    else:
        filesize = f"{filesize:0.2f}"

    txt = f'''This file provides information about the CSV table saved as: {filename}

----ABOUT----
Creation date: {datetime.datetime.now()} UTC
File size: {filesize} MB
File type: CSV
Dataset: {dataset}

----SELECTION----
Number of selected sources:{n_sel}
X axis:{xaxis}
Y axis:{yaxis}
X bounds:{bounds[0]}, {bounds[2]}
Y bounds:{bounds[1]}, {bounds[3]}
Number of available spectra: {df_sel['spec_ID'].count()}

----SUMMARY STATISTICS----
{df_sel.drop(['spec_ID'], axis = 1).describe().transpose().to_string()}
'''

    return txt

def data_to_df(data):
    ''' prepares the data to be ingested into the bokeh app '''

    # create a dictionary
    data_dict = {}
    for key in data.keys():
        data_dict[key] = data[key]

    # open the data dictionary with the IDs
    data = {'gaia_id' : data_dict['gaia_id']}

    # list of the common data wanted
    data_keys = ['apo_id',
                 'X_umap',
                 'Y_umap',
                 'galactic_x',
                 'galactic_y',
                 'galactic_z',
                 'distance',
                 'new_ang',
                 'galactic_plane_coord',
                 'Mag',
                 'bprp_color',
                 'teff',
                 'logg',
                 'alpha_Fe',
                 'weirdness_score']

    for key in data_keys:

        # change the name of new_ang
        if key == 'new_ang':
            data['galactic_azimuth'] = data_dict['new_ang'].astype('float32')

        # add the alpha/Fe column (different name depending on the dataset)
        elif key == 'alpha_Fe':
            try:
                data[key] = data_dict['alpha'].astype('float32')
                # get rid of bad data for alpha abundances
                data['alpha_Fe'][data['alpha_Fe'] == -9999.] = np.nan
            except KeyError:
                data[key] = data_dict['ag'].astype('float32')
            except:
                pass

        # add the APOGEE ID when available
        elif key == 'apo_id':
            try:
                data[key] = data_dict[key]
            except KeyError:
                pass

        # use distance and azimuth angle to calculate galactic plane coordinates
        elif key == 'galactic_plane_coord':
            try:
                data['galactic_x_plane'] = data['distance']*np.cos(data['galactic_azimuth'])
                data['galactic_y_plane'] = data['distance']*np.sin(data['galactic_azimuth'])
            except KeyError:
                pass

        # add the UMAP coordinates (name depends upon the data set)
        elif key == 'X_umap':
            try:
                data[key] = data_dict[key].astype('float32')
            except KeyError:
                data[key] = data_dict['X_embedded'][:, 0].astype('float32')
            except:
                pass

        elif key == 'Y_umap':
            try:
                data[key] = data_dict[key].astype('float32')
            except KeyError:
                data[key] = data_dict['X_embedded'][:, 1].astype('float32')
            except:
                pass

        else:

            try:
                data[key] = data_dict[key].astype('float32')
            except KeyError:
                pass

    # Convert the gaia ID into the right format for the rvs table if necessary
    try:
        data['gaia_id'] = ['Gaia EDR3 '+str(int(id_i)) for id_i in data['gaia_id']]
    except ValueError:
        pass

    return pd.DataFrame(data)

def create_hover_tool(apo = False):
    ''' Tailor the hovertool tips to include APOGEE data when available '''

    if not apo:
        return HoverTool(
        tooltips=[
            ('Gaia ID', '@gaia_id'),
            ('Distance (pc)', '@distance'),
            ('Absolute G mag', '@Mag'),
            ('BP-RP color', '@bprp_color'),
       ],
        point_policy="follow_mouse"
    )


    return HoverTool(
        tooltips=[
            ('Gaia ID', '@gaia_id'),
            ('APOGEE ID', '@apo_id'),
            ('Distance (pc)', '@distance'),
            ('Absolute G mag', '@Mag'),
            ('BP-RP color', '@bprp_color'),
       ],
        point_policy="follow_mouse")

def grab_title():
    ''' return a text version of the title of the app '''

    txt = "<h2><span style='font-size:30px; color:#c58e0a;'>Dimensionality \
    reduction and similarity mapping for Gaia-RVS and APOGEE spectral data </h2>"

    return pn.pane.HTML(txt, width = 1000)


def grab_description():
    ''' return a text version of the desciption of the app '''

    txt = "<p><span style='font-size:15px; color:black;'> \
    The <b><span style='color:#534998;'> Control Panel</span></b> allows you to select\
    which dataset to visualise between the <b><span style='color:#534998;'> Gaia-RVS </span></b>\
    and the <b><span style='color:#534998;'> APOGEE </span></b> data. </br>\
    Using the <b><span style='color:#534998;'> Plot Type</span></b> selection menu, the data\
    can be displayed using several well known parameter spaces (e.g. UMAP, HR-diagram, etc...). </br>\
    Otherwise the desired X and Y axis can be selected to any \
    parameters listed in <b><span style='color:#534998;'> X-axis</span></b> and \
    <b><span style='color:#534998;'> Y-axis</span></b> which correspond to the data columns.</br>\
    The <b><span style='color:#534998;'> Colour by</span></b> list allows you to control the \
    parameter used to colour the data. </span></p>\
    <p><span style='font-size:15px; color:black;'>\
    The <b><span style='color:#534998;'> Selection Panel</span></b> allows you to \
    create a selection within the data using the <b><span style='color:#534998;'> X bounds</span></b> \
    and the <b><span style='color:#534998;'> Y Bounds</span></b> parameters.</br>\
    You can use the box select tool available in the \
    <b><span style='color:#534998;'> Main Data Visualisation Panel</span></b> to select sources.</br>\
    This selection can be saved as a csv file, \
    and the average spectra of the selected data can also be displayed and saved.</span></p>"

    return pn.pane.HTML(txt)

def get_quant(df):
    ''' get the column name of quantifiable data '''

    columns = df.columns
    discrete = [x for x in columns if df[x].dtype == object]
    continuous = [x for x in columns if x not in discrete]

    return [x for x in continuous if len(df[x].unique()) > 20]

def get_plot_type_axis(p_t):
    ''' return the x and y axis, as well
        as the labels for each of the plot type
        available '''

    if p_t == "UMAP":
        return "X_umap", "Y_umap", "X", "Y"
    if p_t == "Galactic side view":
        return "galactic_x", "galactic_y", "galactic x (pc)", "galactic y (pc)"
    if p_t == "Galactic plane":
        return "galactic_x_plane", "galactic_y_plane", "x (pc)", "y (pc)"
    if p_t == "HR diagram":
        return "bprp_color", "Mag", "BP-RP color (mag)", "Absolute G mag"

    return "", "", "", ""

def get_color_name(c_n):
    ''' return the name of the variable in the table
        versus that selected in the menu for the colour'''

    if c_n == "Weirdness score":
        return 'weirdness_score'
    if c_n == "Magnitude":
        return 'Mag'
    if c_n == "BP-RP color":
        return 'bprp_color'
    if c_n == "Distance":
        return 'distance'
    if c_n == "Realness score":
        return 'realness_score'
    if c_n == "Metallicity":
        return 'metallicity'
    if c_n == "Effective temperature":
        return 'teff'
    if c_n == "Log g":
        return 'logg'
    if c_n == "Alpha/Fe":
        return 'alpha_Fe'

    return None

def calc_avgspec(IDs, spec_dict):
    ''' display the average (with uncertainties) spectra of
        the selected sources '''

    # grab the wavelengths of the spectra
    WAVELENGTHS = spec_dict['lambda_nm']

    # keep only IDs with spectra
    IDs = IDs[IDs == IDs]
    IDs = IDs[spec_dict['spec'][IDs.values.astype('int')].mean(axis = 1) != 0.]
    n_ID = len(IDs) # number of sources with spectra

    if n_ID > 0:

        # calculate the mean, standard deviation and number of sources with spectra
        spec_avg = spec_dict['spec'][IDs.values.astype('int')].mean(axis = 0)
        spec_unc = spec_dict['spec'][IDs.values.astype('int')].std(axis = 0)

        return spec_avg, spec_unc, n_ID

    return [], [], 0

def draw_box(bounds):
    ''' draw the box for selection and
        extract the corresponding dataframe '''

    if bounds:

        # get the bounds of the box
        left, bottom, right, top = bounds

        # draw the box
        x = (left + right)/2.
        y = (top + bottom)/2.
        w = abs(left-right)
        h = abs(top-bottom)

        return hv.Box(x,y,(w,h)).opts(color='black',line_width=2, alpha = 0.9)

    return hv.Box(0,0,(5,5)).opts(color='black',line_width=2, alpha = 0.)

def get_bounds_from_tb(tb):
    ''' read the bounds from the text box '''

    # can be improved to accept more formatting
    try:
        left = tb.strip('][').split(',')[0]
    except:
        left = 'None'
    try:
        bottom = tb.strip('][').split(',')[1]
    except:
        bottom = 'None'
    try:
        right = tb.strip('][').split(',')[2]
    except:
        right = 'None'
    try:
        top = tb.strip('][').split(',')[3]
    except:
        top = 'None'

    bounds = (left, bottom, right, top)

    if 'None' not in bounds:

        # transform bounds from string to float
        bounds = [float(bound) for bound in bounds]

        # check that left < right and bottom < top, otherwise swap
        left, bottom, right, top = bounds
        if bottom > top:
            bottom, top = top, bottom
        if left > right:
            left, right = right, left

        return (left, bottom, right, top)

    return None
