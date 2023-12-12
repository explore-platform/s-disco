# MINIMAL EXAMPLE TO TEST COMPATIBILITY
# EXPECTED BEHAVIOUR: blank page with "test" written on it

# import bokeh
# from bokeh.models.widgets import Div
# from bokeh.io import curdoc
# curdoc().add_root(Div(text="test"))
###########################################################################

#######
# APP #
#######
import os
import json
import panel as pn
import panel.widgets as pnw
import numpy as np
import pandas as pd
from astropy.io import fits
import holoviews as hv
from holoviews.operation import decimate
from holoviews import streams  
import logging

from library import methods, init_global

# define a css class for the widget (get rid of borders)
css = '''
.my_widget_box {
    border: 0px;
}
'''

# define the extension to use
hv.extension('bokeh')

# init the global variables (from the init_global.py file)
init_global.init()

n_sel = init_global.n_sel # # of selected sources
df_sel = init_global.df_sel # init of the dataframe listing selected sources
df = init_global.df # df of the dataset (init)
bounds = init_global.bounds # bounds for the selection box
invert_yaxis = init_global.invert_yaxis # used when plotting the HR diagram to reverse Mag
xaxis = init_global.xaxis # init for the main plot x axis
yaxis = init_global.yaxis # init for the main plot y axis
xlabel = init_global.xlabel # init xlabel
ylabel = init_global.ylabel # init ylabel
color = init_global.color # parameter used to colour the data
spec_avg = init_global.spec_avg # init avg spectra
spec_unc = init_global.spec_unc # init avg spectra uncertainties
spec_dict = init_global.spec_dict # init for the dictionary with spectra
alpha_mp = init_global.alpha_mp # init for the transparancy of the data on the main panel
is_plotted = init_global.is_plotted # boolean for the plotting of the avg spec

def update_plot_type(event):
    ''' Callback function for the plot type '''

    global invert_yaxis, xaxis, yaxis, xlabel, ylabel, bounds

    type_i = ddm_type.value # value of the dropdown menu TYPE
    if type_i != '':

        # reset the drop down menu for the x and y axis
        # (can't be together with the plot type selected)
        ddm_xaxis.value = ''
        ddm_yaxis.value = ''

        # reset the bounds
        bounds = None
        tb_boundX.value = '[None, None]'
        tb_boundY.value = '[None, None]'

        # get the data and labels for each of the axis based on the type selected
        xaxis, yaxis, xlabel, ylabel = methods.get_plot_type_axis(type_i)

        # invert the y axis (MAG) if the HR diagram is selected
        invert_yaxis = False
        if type_i == 'HR diagram':
            invert_yaxis = True

        # generic update plot function
        update_plot(xaxis, yaxis, xlabel, ylabel, color, bounds, invert_yaxis)

def update_plot_axis(event):
    ''' Callback function to update the x and y axis '''

    global xaxis, yaxis, xlabel, ylabel, bounds, invert_yaxis

    if (ddm_xaxis.value != '') & (ddm_yaxis.value != ''):

        # reset the drop down menu for the plot type
        # (can't be together with the X/Y axis selected)
        ddm_type.value = ''

        # reset the bounds
        bounds = None
        tb_boundX.value = '[None, None]'
        tb_boundY.value = '[None, None]'

        xaxis = ddm_xaxis.value # value of the dropdown menu X-axis
        yaxis = ddm_yaxis.value # value of the dropdown menu Y-axis
        xlabel = ddm_xaxis.value # name of the dropdown menu X-axis
        ylabel = ddm_yaxis.value # name of the dropdown menu Y-axis

        # reset the invert y axis (only used for HR diagram)
        invert_yaxis = False
        # generic update plot function
        update_plot(xaxis, yaxis, xlabel, ylabel, color, bounds, invert_yaxis)

def update_plot_color(event):
    ''' Callback function for the colour of the points '''

    global color

    color = methods.get_color_name(ddm_color.value) # get the parameter of the new colour

    # generic update plot function
    update_plot(xaxis, yaxis, xlabel, ylabel, color, bounds, invert_yaxis)

def update_plot(x, y, xlabel, ylabel, color, bounds, invert_yaxis):
    ''' generic function to  update the plot once the new X/Y/Color/bounds
        have been defined '''

    # generate the plot
    points = create_plot(df, x, y, color, xlabel, ylabel,
        bounds = bounds, invert_yaxis = invert_yaxis)

    # pass it to the panel
    mainplot_pane.object = points

def update_df_sel():
    ''' Callback function for the selection based on the bounds text_box '''

    global n_sel, df_sel, bounds, alpha_mp

    # get the bounds (left, bottom. right, top)
    bounds = methods.get_bounds_from_tb(tb_bounds.value)

    if bounds:

        # tell the user that this is loading (displayed in the MultiSelect widget)
        ms_source_list.options = ['loading IDs...']

        # format the values of the bounds in the textbox
        tb_boundX.value = f'[{bounds[0]:.3f} , {bounds[2]:.3f}]'
        tb_boundY.value = f'[{bounds[1]:.3f} , {bounds[3]:.3f}]'

        # extract the dataframe of selected data
        df_sel = df.loc[(df[xaxis] >= bounds[0]) & (df[xaxis] <= bounds[2]) &
            (df[yaxis] >= bounds[1]) & (df[yaxis] <= bounds[3])]

        # increase the transparency of the main data points
        alpha_mp = 0.1

    # update the number of selected sources displayed
    n_sel =  len(df_sel) # n selected data
    div_selsum.object = f"<div><h3> Selection: </h3> {n_sel} selected sources. "

    # write the IDs of the selected sources, if any.
    if (n_sel == 0) and bounds:
        ms_source_list.options = ['No data found.']
    elif n_sel == 0:
        # reset the selection list to init
        with open('./static/widgets/ms_source_list.json', 'r') as f:
            ms = json.load(f)
        ms_source_list.options = ms['options']
    elif n_sel > 100000:
        ms_source_list.options = df_sel['gaia_id'].tolist()[0:3] + ['...',
        'Too many selected sources to list all of the', 'Gaia IDs.', ' ', 'Instead, you can save this list to a CSV',
        'file (see below the "save selected data as:"),', 'and explore the data using your favourite', 'CSV file reader.']
    else:
        ms_source_list.options = df_sel['gaia_id'].tolist()

def update_selection(event):
    ''' Callback function for the selection based on the bounds text_box '''

    # update the df_sel object
    update_df_sel()

    # generic update plot function
    update_plot(xaxis, yaxis, xlabel, ylabel, color, bounds, invert_yaxis)

def save_sel_data(event):
    ''' Callback function to save selected data to a CSV table '''

    if len(df_sel) > 0:

        # notify the user that it is saving if many data points are selected
        button_save_sel.name = 'saving...'

        # save df_sel to a CSV file
        df_sel.to_csv(os.path.join(service_user_app_data, tb_fname_save.value), index=False)

        # write a text file with the meta data
        filename = tb_fname_save.value # name of the CSV file
        filesize = os.path.getsize(os.path.join(service_user_app_data, tb_fname_save.value))/1e6 # size of the file

        text_metadata = methods.grab_metadata_text(filename, filesize, n_sel, xaxis,
            yaxis, bounds, df_sel, ddm_seldata.value)
        with open(os.path.join(service_user_app_data, tb_fname_save.value.split('.')[0]+'_info.txt'), 'w+') as f:
            f.write(text_metadata)

        button_save_sel.name = ''

def create_specavg(spec_avg, spec_unc, n_ID = 0):
    ''' given an average spectra and uncertainties, return the Curves '''

    # grab the wavelengths of the spectra
    WAVELENGTHS = spec_dict['lambda_nm']

    # options for the plot
    opts = dict(width=1150, height = 300, toolbar='above',
        xlabel='Wavelength (nm)', ylabel='Normalised Count', ylim = (None, 2.1), xlim = (WAVELENGTHS.min(), WAVELENGTHS.max()))

    if (len(spec_avg) == 0) and n_sel == 0 or not is_plotted:
        # default return
        title = ' '
        return hv.Curve([]).opts(**opts).opts(title = title)

    if len(spec_avg) == 0:
        # default return if no spectra were found
        title = f'No spectra were found for the {n_sel} selected sources'
        return hv.Curve([]).opts(**opts).opts(title = title)

    # define the average curve element
    hv_curve = hv.Curve(hv.Scatter((WAVELENGTHS, spec_avg),
        label='Mean average spectra')).opts(color='#063970', line_width=1.50, alpha = 0.8)

    # add the uncertainties curve elements if they exist
    if np.sum(spec_unc) > 0.:
        hv_curve *= hv.Curve(hv.Scatter((WAVELENGTHS, spec_avg+spec_unc),
            label='1 sigma uncertainties')).opts(color='#eab676', line_width = 1.50, alpha = 0.4)
        hv_curve *= hv.Curve((WAVELENGTHS, spec_avg-spec_unc)).opts(line_width=1.50,
            color='#eab676', alpha = 0.4)

    # update the title of the figure
    title = f'Average spectra of the selected sources ({n_ID} spectra found).'

    return hv_curve.opts(**opts).opts(title = title, show_legend=True)

def update_specavg(event):
    ''' callback function to update the average spectra on click '''

    global spec_avg, spec_unc, is_plotted

    if n_sel > 0:

        # modify the is_plotted boolean
        is_plotted = True

        # warning the user that it might take some time by changing the name of the button
        # if n_sel > 1000:
        button_plotspec.name = 'loading...'

        # get the average spectrum
        spec_avg, spec_unc, n_ID = methods.calc_avgspec(df_sel['spec_ID'], spec_dict)

        # update the curves
        hv_curve = create_specavg(spec_avg, spec_unc, n_ID = n_ID)

        # update the panel
        avgspec_pane.object = hv_curve

        # reset the button to its original name
        with open('./static/widgets/button_plotspec.json', 'r') as f:
            button = json.load(f)
        button_plotspec.name = button['name']

def save_specavg(event):
    ''' save the average RVS spectra of the selected sources '''

    if len(spec_avg) != 0.:

        # create a dataframe and save it as a csv file
        spec_df = pd.DataFrame({'wavelength': spec_dict['lambda_nm'],
            'spec_avg':spec_avg, 'spec_unc':spec_unc})
        spec_df.to_csv(os.path.join(service_user_app_data,
            tb_fname_saveavgspec.value), index=False)

def update_bounds(bounds):
    ''' Callback to update the text X-bounds and Y-bounds text boxes
        on using the box_select tool '''

    global is_plotted, spec_avg, spec_unc

    # update the avg spectra
    is_plotted = init_global.is_plotted
    spec_avg = init_global.spec_avg
    spec_unc = init_global.spec_unc
    avgspec_init = create_specavg(spec_avg, spec_unc)
    avgspec_pane.object = avgspec_init

    if bounds:

        # get the bounds
        left, bottom, right, top = bounds

        # format the values of the bounds in the textbox
        tb_bounds.value = f'[{left:.3f}, {bottom:.3f}, {right:.3f}, {top:.3f}]'

decimate.max_samples = 8000
def create_plot(df, x, y, color, xlabel, ylabel, bounds = None, invert_yaxis = False,
    hled = False):
    ''' Returns the scatter plot of x and y '''

    # options
    opts = dict(cmap='RdYlBu', line_color='black', size = 5, colorbar=True,
        width=600, height = 550, toolbar='above', alpha = alpha_mp)

    # Define the elements of the toolbox
    tools = ['undo, redo, box_select']

    # define the colour of the data points
    if color != 'None':
        opts['color'] = color

    # add the tailored HoverTool
    if 'apo_id' in df.keys():
        tools += [methods.create_hover_tool(apo = True)]
    else:
        tools += [methods.create_hover_tool()]
    opts['tools'] = tools

    # Block from plotting non-existing axis
    if x not in df.columns:
        return hv.Points([]).opts(xlabel=xlabel, ylabel=ylabel,
            title = 'X-Axis does not exist in the data set.').opts(**opts)
    if y not in df.columns:
        return hv.Points([]).opts(xlabel=xlabel, ylabel=ylabel,
            title = 'Y-Axis does not exist in the data set.').opts(**opts)

    # create the points object
    points = hv.Points(df, [x, y]).opts(invert_yaxis=invert_yaxis,
        xlabel=xlabel, ylabel=ylabel)

    # Declare a Bounds stream and add the update bounds callback
    box_select = streams.BoundsXY(source=points)
    box_select.add_subscriber(update_bounds)

    # if some bounds are defined change X/Y range to focus on the bounded area
    if bounds:
        left, bottom, right, top = bounds

        # dynamic range for the X and Y axis
        x_drange = abs(right - left)
        y_drange = abs(top - bottom)

        # Set the x and y ranges
        d_pad = 0.5
        x_range = (left - d_pad*x_drange, right + d_pad*x_drange)
        y_range = (bottom - d_pad*y_drange, top + d_pad*y_drange)

        # Apply the ranges to the plot for display
        opts['xlim'] = x_range
        opts['ylim'] = y_range

    # draw the box showing the selection (if bounds is None, nothing is drawn)
    box = methods.draw_box(bounds)

    # overplot selected sources as Points
    points_sel = hv.Points([]) # default when no selected data
    if len(df_sel) > 0:

        # create the points object for the selected sources
        points_sel = hv.Points(df_sel, [x,y]).opts(size = 8, color = '#534998', line_color = '#c58e0a')

        if len(df_sel) >= 8000:
            # more than 8000 selected sources (decimate)
            points_sel = decimate(points_sel)

    return decimate(points).opts(**opts) * box * points_sel

def update_dataset(event):
    ''' Callback for the dataset selection '''

    global df, df_sel, n_sel, spec_dict, alpha_mp, color

    # grab the correct dataset depending on selection
    if ddm_seldata.value == 'Gaia-RVS':
        DATA_FILE = 'rvs_data_highsnr_with_params_no_duplicates.npz'
    elif ddm_seldata.value == 'APOGEE':
        DATA_FILE = 'data_1000.npz'

    # load the data
    data = np.load(os.path.join(service_app_data, DATA_FILE), allow_pickle = True)
    df = methods.data_to_df(data) # formated dataframe

    # define the column that are quantifiable
    quantifiable = methods.get_quant(df)

    # Define the X/Y-axis menu, updating the list to the new dataset
    ddm_xaxis.options = [""]+quantifiable
    ddm_yaxis.options = [""]+quantifiable

    # Define the color dropdown menu (adapt to column available in the df)
    ddm_path = './static/widgets/ddm_color.json'
    with open(ddm_path, 'r') as f:
        ddm = json.load(f)

    # get only those available colours
    options_keep = []
    for option_i in ddm['options']:
        actual_name = methods.get_color_name(option_i)
        if actual_name in df.columns:
            options_keep.append(option_i)
    ddm_color.options = options_keep

    # redefine the "plot by" colour
    color = methods.get_color_name(ddm_color.value)

    # GET THE SPECTRA AND THEIR IDs
    # grab the correct spectra depending on the dataset (APOGEE versus RVS)
    if ddm_seldata.value == 'Gaia-RVS':

        DATA_FILE = 'spectra.fits' # fits file with the spectral data
        ID_FILE = 'GAIA_ID.csv' # file containing corresponding IDs for Gaia
        wav_min, wav_max = 800., 880. # min and max GAIA RVS wavelengths

        # cross match with the dataframe to get the corresponding spectra of each of the rows
        GAIA_ID_RVS = pd.read_csv(os.path.join(service_app_data, ID_FILE))
        GAIA_ID_RVS['source_id'] = ['Gaia EDR3 '+str(int(id_i)) for id_i in GAIA_ID_RVS['source_id']]
        GAIA_ID_RVS['index_1'] -= 1

        # add a spec_ID column to the main df to x-ref RVS spectra
        df = pd.merge(df, GAIA_ID_RVS, left_on = ['gaia_id'], right_on = ['source_id'],
            how = 'left').drop(labels = ['source_id'],axis = 'columns').rename(columns = {'index_1':'spec_ID'})

    elif ddm_seldata.value == 'APOGEE':

        DATA_FILE = 'fluxes.fits' # fits file with the spectral data
        wav_min, wav_max = 1500., 1700. # min and max APOGEE wavelengths

        # add the corresponding IDs to the dataframe (directly x-referenced for APOGEE)
        IDs = np.arange(len(df))
        df['spec_ID'] = IDs

    # open the fits file and create a dictionary with ID, spectra and wavelength
    with fits.open(os.path.join(service_app_data, DATA_FILE)) as hdu:
            spec = hdu[0].data
    IDs = np.arange(spec.shape[1])

    # get the corresponding wavelength
    WAVELENGTHS = np.linspace(wav_min, wav_max, spec.shape[0]) # this is hard coded, I don't like that

    # build a dictionary with all of the spectra
    spec_dict = {'ID':IDs, 'spec':spec.T, 'lambda_nm': WAVELENGTHS}

    # init the dataframe listing the selected sources
    df_sel = init_global.df_sel
    n_sel = init_global.n_sel
    # update the df_sel to nothing or to new data if same parameter space across data
    # bit intricated but the text box tb_bounds acts in the shadow
    # to keep selection accross dataset when necessary. So different options are required
    # depending if it is filled with None or not
    if not bounds:

        if tb_bounds.value == '[None, None, None, None]':

            # UPDATE THE CENTRAL PLOT
            update_plot(xaxis, yaxis, xlabel, ylabel, color, bounds, invert_yaxis)

        else:

            # make the most of reset selection (updating plots etc..)
            reset_selection(None)

    else:

        # update the selection df within the new data
        update_df_sel()

        # UPDATE THE CENTRAL PLOT
        update_plot(xaxis, yaxis, xlabel, ylabel, color, bounds, invert_yaxis)

        # auto plot the average spectra
        if is_plotted:
            update_specavg(None)

def reset_selection(event):
    ''' Callback for the reset selection buton '''

    global n_sel, df_sel, bounds, spec_avg, spec_unc, alpha_mp, is_plotted

    #reset the transparency of the main data points
    alpha_mp = init_global.alpha_mp

    # reset the df_sel and n_sel to init (empty dataframe and 0)
    df_sel = init_global.df_sel
    n_sel = init_global.n_sel

    # reset the bounds values to None
    with open('./static/widgets/tb_bound.json', 'r') as f:
        tb = json.load(f)
    tb_bounds.value = '[None, None, None, None]' # has a listener and runs update_df_sel
    tb_boundX.value = tb['value']
    tb_boundY.value = tb['value']

    # update the avg spectra
    is_plotted = init_global.is_plotted
    spec_avg = init_global.spec_avg
    spec_unc = init_global.spec_unc
    avgspec_init = create_specavg(spec_avg, spec_unc)
    avgspec_pane.object = avgspec_init

########
# MAIN #
########

##############
# INPUT DATA #
##############

# path to the input dir
service_app_data = os.environ.get('SERVICE_APP_DATA')

###################
# PATH TO OUTPUTS #
###################

# path to the output dir
service_user_app_data = os.environ.get('SERVICE_USER_APP_DATA')

######################
# Add the logo image #
######################
logo_path = "./static/images/logo_sdisco.png"
logo_image = pn.pane.PNG(logo_path, width=120, height=100)

#################################
# Add a description of the apps #
############################### #
app_title = methods.grab_title()
app_description = methods.grab_description()

######################################################
# Create the control panel with drop down menu       #
#                                                    #
# NAME DEF: ddm_: drop down menu, div_: plain text,  #
# ms_: multi-select box, tb_: text box (interactive) #
######################################################
# ddm data selection
with open('./static/widgets/ddm_seldata.json', 'r') as f:
    ddm = json.load(f)
ddm_seldata = pnw.Select(name=ddm['name'], value=ddm['value'], options=ddm['options'],
    width = ddm['width'])

# ddm TYPE
with open('./static/widgets/ddm_type.json', 'r') as f:
    ddm = json.load(f)
ddm_type = pnw.Select(name=ddm['name'], value=ddm['value'], options=ddm['options'],
    width = ddm['width'])

# ddm AXIS
with open('./static/widgets/ddm_axis.json', 'r') as f:
    ddm = json.load(f)
ddm_xaxis = pnw.Select(name='X'+ddm['name'], value=ddm['value'],
    options=ddm['options'], width = ddm['width'])
ddm_yaxis = pnw.Select(name='Y'+ddm['name'], value=ddm['value'],
    options=ddm['options'], width = ddm['width'])

# ddm COLOR
ddm_path = './static/widgets/ddm_color.json'
with open(ddm_path, 'r') as f:
    ddm = json.load(f)
ddm_color = pnw.Select(name=ddm['name'], value=ddm['value'], options=ddm['options'],
    width = ddm['width'])

# wrap all these into a widget box
title = pn.pane.Markdown("## Control Panel")
CP_widget = pn.WidgetBox(title, ddm_seldata, ddm_type, ddm_xaxis, ddm_yaxis, ddm_color, css_classes = ['my_widget_box'])

#############################################################################################
# Create the initial plot (UMAP, coloured weirdness ratio or Mag depending on availability) #
#############################################################################################
mainplot_init = create_plot(df, 'x', 'y', 'None', '', '') # initial plot
mainplot_pane = pn.pane.HoloViews(mainplot_init) # wrap it into a HV pane (easier interactions)

# wrap all these into a widget
title = pn.pane.Markdown("## Main Data Visualisation Panel")
dataplot_widget = pn.WidgetBox(title, mainplot_pane, css_classes = ['my_widget_box'])

##############################
# Create the selection panel #
##############################
# ms ID of selected sources
with open('./static/widgets/ms_source_list.json', 'r') as f:
    ms = json.load(f)
ms_source_list = pn.widgets.MultiSelect(value=ms['value'],
    options=ms['options'], width = ms['width'], height = ms['height'])

# Div and TextBox of the selected data
div_selsum = pn.pane.HTML(f" ")
div_boundX = pn.pane.Markdown(" #### X Bounds:")
div_boundY = pn.pane.Markdown(" #### Y Bounds:")
with open('./static/widgets/tb_bound.json', 'r') as f:
    tb = json.load(f)
tb_boundX = pn.widgets.TextInput(value=tb['value'], width = tb['width'])
tb_boundY = pn.widgets.TextInput(value=tb['value'], width = tb['width'])
tb_bounds = pn.widgets.TextInput(value="[None, None, None, None]")

# plot the average spectra of selected sources
with open('./static/widgets/button_plotspec.json', 'r') as f:
    button = json.load(f)
button_plotspec = pn.widgets.Button(icon = button['icon'], name = button['name'], button_type = button['type'],
    width = button['width'], button_style = button['bs'])

# div box save data as
div_savedata = pn.pane.Markdown(" #### Save selected data as:")

# filename of the csv file of the selected sources
with open('./static/widgets/tb_fname_save.json', 'r') as f:
    tb = json.load(f)
tb_fname_save = pn.widgets.TextInput(value=tb['filename'], width = tb['width'])

# button to save the table of selected data
with open('./static/widgets/button_save_sel.json', 'r') as f:
    button = json.load(f)
button_save_sel = pn.widgets.Button(button_type = button['type'],
    width = button['width'], icon = button['icon'])

# div box save average spectra as
div_savespec = pn.pane.Markdown(" #### Save average spectra as:")
# filename of the csv file of the average spectra
with open('./static/widgets/tb_fname_saveavgspec.json', 'r') as f:
    tb = json.load(f)
tb_fname_saveavgspec = pn.widgets.TextInput(value=tb['filename'], width = tb['width'])

# save the average spectra (with uncertainties)
with open('./static/widgets/button_save_avspec.json', 'r') as f:
    button = json.load(f)
button_save_avspec = pn.widgets.Button(button_type = button['type'],
    width = button['width'], icon = button['icon'])

# button to reset the selection
with open('./static/widgets/button_reset_sel.json', 'r') as f:
    button = json.load(f)
button_reset_sel = pn.widgets.Button(name = button['name'], button_type = button['type'],
    width = button['width'], button_style = button['bs'], icon = button['icon'])

# wrap all these into a widget
title = pn.pane.Markdown("## Selection Panel")
SP_top_widget = pn.WidgetBox(title, ms_source_list,
    div_selsum, pn.Row(div_boundX, tb_boundX),
    pn.Row(div_boundY, tb_boundY), button_plotspec, css_classes = ['my_widget_box'])
SP_bot_widget = pn.WidgetBox(pn.Row(div_savedata, tb_fname_save, button_save_sel),
    pn.Row(div_savespec, tb_fname_saveavgspec, button_save_avspec), button_reset_sel, css_classes = ['my_widget_box'])
SP_widget = pn.WidgetBox(SP_top_widget, SP_bot_widget, css_classes = ['my_widget_box'])

###############################################
# Create the panel of the average spectra #
###############################################
avgspec_init = create_specavg(spec_avg, spec_unc)
avgspec_pane = pn.pane.HoloViews(avgspec_init)

# wrap all these into a widget
title = pn.pane.Markdown("## Average spectrum of selected sources")
avgspec_widget = pn.WidgetBox(title, avgspec_pane, css_classes = ['my_widget_box'])

##################
# Add the IFRAME #
##################>
# Grab the URL
URL = f"""{"http" if os.environ.get('LOCAL') == 'true' else "https" }://{pn.state.curdoc.session_context.request._request.host.split(',')[0]}{os.path.join(os.environ.get("PATH_PREFIX"), "vis")}/"""
full_URL = URL + "#compressed=true&dataurl=" + URL + "sample_data/sdisco/sdisco.csv&config=NobwRAhgxgLglgewHZgFxg"+\
                 "GZwKYBsAmAyntrIkgKoAO+EM2YANGLTBGqJjgQHIQC2DdACdsEXEmwBnKQH0pUBKKYs6EKdhgBJJPmwAPNGAAMYAL6NwWPPj"+\
                 "6CjADVnZ+AI2z49+WQEYVrdU0dPUN0UwsrblsBITAnF3dPD1kAJn81DW1dAyNwyy4bO1iAcwg4CFk4fHS2TOCcsPN8614Yo3w"+\
                 "4KTYkKAZmALrs0JMmyMK29ABZCGKawKyQ3NGC1vt0VyphKllFXCU5wcXGiJXotbB6DAwDoKGlk5az2L3i2f6M26ORh6iio34AB"+\
                 "Y3BYNb7NX4TSBvVS1T6gvJjVaxSQAd1kECQ0IGcOGCNOf3QpVw0HgUFkhnesJBuOWjwJYCJJLgZIAnsD6jSfuNzoyyGSAF7su7H"+\
                 "AC6JykAFcqFQlDApABBJBIBBseDIKRoGDCCXYZiuCUwGDILTVdYwJAAWmJugUECo2CwSHEKgAbp0ACpwGC4WIACh8AEoAATW-C2+1"+\
                 "B32icSSGTyRSiRhB+JuDxeXxJlOJdMpJOlcqVfBJjpdDG9JPTYpJjZbHYIPbCJOXDBJl5VoOApMzJOo9GYvPiJlk-QD4l82Qs0dD"+\
                 "2T84MAEQ+MFQUhLigAdFApC6VPw7VQ4JiOOAoACMZJcEYAMJ0bDFJRs5jE9wXkRiCTSOQKJR9GF0Fn2owkAlVNhBULBcHoYQ506CB"+\
                 "XB9U0MHEDRmABKo9CQS9TyVPA0EQ3BkLATpL3rJQADEolwpDdTAURd2lA9imgqRYPgyj8Oo08pAAeSgKAJWEUQeliSYJQguAqFwZkv"+\
                 "TZE4TzPHD0Gveg72EB8wCfBS4mcVMkm8PxKT-AD0CAkCwLgCDsCgmC4I8NiCNQpIMKw887OooiSOEcibFc5haL3BimJY2zUDw+z1B4v"+\
                 "iBOwISjBEsSJKkmAZPyOTsJfMAlNve8VA09KszTZI0gMpKjLAEz3FA5hwMgwKbIQqiULQ6LMPkl9QrcqRiIbLyCB8miXH8zFatYkKGr"+\
                 "ATiIv4wTeli0T4ASqBpOWVKXMUm8VLU3KjHzCoqjmErkWAiqzIsqzmLqvqHPQlq0r69zuoo0b2N8gb6KG6yRvalDwt4qbopmqY5vEyT"+\
                 "FqS5bnM0zKNpy2DNJLboZuK-9DtMqrzJqj7gq+8amqc1q7s6jyevq57+ro-d3vOz6xom36opiwH4pBpbZIh9Koeyx9YfSyt9uRwCjssk"+\
                 "6MaprGadxm7Vux+6yMe7G-LexjMZJsLuLp6bhKBhaWZStmr3Wzn1O5owa22XZ9iR0ryqFtHTuGsXSau5q9aegiZc8uWxoVimldFlWOJ+y"+\
                 "KNdmpnEuS48XYyg3VJh58jGbPmrcFyquDt5XLoll3pcJh7vNd6jvYC9P8++tWg-+zXQ9B8OwBWyHo82430DbROUeO22RaC-3GscyWFOz"+\
                 "rrZbz+XXp9+3u-GwO-oZsA4vm5mwdZ-G1uUw2tvQQFW4F1HU87i6S5x3us7G93ib6wvKa7y6p-pgHZ61hea7r9mG9jzSZi34zk+Fy"+\
                 "zx4zo-l4DyJp7UmF9fZXwPrTcuM857AzDuDZeUdV4xy5nHYy2A0QYixGoA6292671-sXbGTs8a3QPqfEBBEwF-0gTfYOjN57wKXmQp"+\
                 "BWUUFGzQQyQc44KS-lwV-He1VCF+3-tdY+pMKHDy9qPIuIjaFl2nnfWB2tF660QRzdh68uFjlJBOT+ZVv4d2ERA4hmdAEnxzkPXqB9"+\
                 "qFEJpnQiuIdGHVwQSwjRjdOG8l0YKS2bcbYELOiY8WACyFANztYke5NZFBMdg4mBD8mEimYDMYoohShqgwsgLAsxUCcDpJCaM744xfm"+\
                 "UFyJEjhtLZmSH4MpTwKkJAKt4NItT6Q7ULLSCE5x4ZlgYC0yEvM+nnFNnWBsHTuSxAToM54CBXhjPKRvIEUyjAfyWegzBh5VnaOnI"+\
                 "YTZXjmR6N2dw7x5gkkXAQFQNAxhHwOhgJc5gKIqgwCBKgHwxgrnjWwHAYoAJbkvLecwfkHIjD6TAFIWUAAhNkqBwBaJUOoXougGKa"+\
                 "m1NgCwhEpDgq+QTSYB44D8DgPyB2BFsQwCKBqXJoLVwIA3FuMApyHm6AQCiE0Rg3SSnEASug5ALQgrZSy9AvLOiECNMoaFFx1AAGt"+\
                 "+XAFOQEaVpzFBIGyRwU54gVJegBPweVBlMjkplWiklwRmTSA4MYU5B5IJMmQO6fm6AhEpyoBAYQ8BxAAAkvkAkkt8+Ah5jIqnlGQF"+\
                 "0P5+AP2wOC7UUhUKYgDfAF0N5TRah1EY4QXFXAACtSByhVQZcip0kUH1cBGgExE3AHmwFxe0wg6D7HQPKHgc4VCdHDRKSNmFSAStc"+\
                 "AgfQMa4BxvoBPJkQbiA+jIMgNAx5xA+mEAANU6ECl5zANAjv7QuNgJo9WnLYMIYomge1jvQLi25yTA3xr6vajdi6IUsnpHMXNkEL1"+\
                 "gELS2gEq72C5NVQoaKHRfWJuokuzNHh5T6E6NmsAUTfWcGfvrZBHjNKFNjJ+BMP4Aj8IMYI9Gxj96mJCVLCxg8PZSNATIy+WH7EKN"+\
                 "vpXZxOsI7qNfqgzS+VdK+H0dbFO9qaHYbEeYiRliCMROkeB8BpHYnkfoffKu1Ha6R3cW-PKlTGmpBY4YgJHHglcdCXh4BhGqHEaE9"+\
                 "TETk0KNOLgS45hq1WHQ3o+lNpe1fF4P8exuxjszEaZ4-hs+NjdOqYM+rRxDCTOSagyvNhsH0rdJinZgR+DHNyM487bjbteMeciYNP"+\
                 "TRKA6ib8+JqjqiaNuLoxwzSvNItoeixhwJwn7Iudw25rT-GiOCe86rQzYnlGP1ceZmTVmTabDNh5JT6G06xbU-F1ziX3OUILl5pzzX"+\
                 "fPxIk7lqTtGYOyfjg6a4JXWM-wq-pqrOH+6afCRPWxw2fPQKUQk0zaj8sre683GZ2DVS2tKw58rTWOLVYO7Vo759pundm+dyjAXFtBY"+\
                 "s2vJuYGgSbeUzFmJe31M1fG3V47f24cZZa1ltrTDrudYK1oj+0PBt712x9-bbVDtWJR41mb6O5sXYW0-aTeOIe9iwQNsrQ20c9wR19pH"+\
                 "P3PPU-+7TwHxmVGM+WyF1bhIjn7N4Sh57W3k3ve56NxHHUJvaam4Lrnk9MvzZy+Lm7ku7tbPHGpeXScieYZJyr0havmCSPqzp7XlXheKK"+\
                 "B2Ljr9dbuFeszLgU7PXuc9d7bvu5PvuU9+y7m3uuMf6+BzJWVi5h0AfwOu8daK2UAHUNU8AQK+gmzbW0AnbZ27tJ7+19X-bADwAAlJlR"+\
                 "regbrRValA6AoDRnoLOjUZgRRAA"
iframe_pane = pn.pane.HTML(f"""
    <iframe
        src={full_URL}
        width="1150" height="1150" frameborder="0"
    />
""")


#####################
# Create the layout #
#####################
layout = pn.Column(pn.Column(pn.Row(logo_image, app_title), app_description),
   pn.Row(CP_widget, dataplot_widget, SP_widget), avgspec_widget, iframe_pane)

######################
# Display the layout #
######################
layout.servable('S-Disco')



#######################################
# add listeners for the control panel #
#######################################
ddm_seldata.param.watch(update_dataset, 'value')
ddm_type.param.watch(update_plot_type, 'value')
ddm_xaxis.param.watch(update_plot_axis, 'value')
ddm_yaxis.param.watch(update_plot_axis, 'value')
ddm_color.param.watch(update_plot_color, 'value')

#########################################
# add listeners for the selection panel #
#########################################
tb_bounds.param.watch(update_selection, 'value')
button_reset_sel.on_click(reset_selection)
button_save_sel.on_click(save_sel_data)
button_plotspec.on_click(update_specavg)
button_save_avspec.on_click(save_specavg)

###########################
# init with GAIA RVS data #
###########################
update_dataset(None)
