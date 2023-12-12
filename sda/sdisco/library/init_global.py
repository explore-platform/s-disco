''' initialise the global variables '''
import pandas as pd
import numpy as np

def init():
    global n_sel, iframe_html, df_sel, bounds, invert_yaxis, xaxis, yaxis,\
    xlabel, ylabel, color, spec_avg, spec_unc, df, spec_dict, alpha_mp, is_plotted

    # default global variables
    spec_dict = {'lambda_nm':np.array([0., 1.]), 'ID':np.array([])} # init for the dictionary with spectra
    n_sel = 0 # # of selected data
    # iframe_html = """
    #         <iframe src="https://www.wikipedia.org/" width="1150" height="1150" frameborder="0"></iframe>
    #         """ # Iframe
    df = pd.DataFrame({'x':[], 'y':[]}) # empty DF to initialise the df
    df_sel = pd.DataFrame({'x':[], 'y':[]}) # empty DF to initialise the df of selected data
    bounds = None # bounds of the selection box
    invert_yaxis = False # used for the HR diagram (mag needs to be reversed)
    xaxis = 'X_umap' # init for the main plot x axis
    yaxis = 'Y_umap' # init for the main plot y axis
    xlabel = 'X' # init for the name of the x axis
    ylabel = 'Y'# init for the name of the y axis
    color = 'None' # init for the colour of the data points
    spec_avg = [] # init for the average spectra
    spec_unc = [] # init for the avearge spectra uncertainties
    alpha_mp = 1 # init for the transparancy of the data on the main panel
    is_plotted = False # init a boolean value to whether the avg spectra is plotted or not