import sys
import glob
import pylab
import numpy as np
import re

import matplotlib.cm as cmx
from pyrap.tables import table
from optparse import OptionParser
import matplotlib.colors as colors

from bokeh.plotting import figure
from bokeh.models.widgets import Div
from bokeh.layouts import row, column, gridplot, widgetbox
from bokeh.io import output_file, show, output_notebook, export_svgs
from bokeh.models import (Range1d, HoverTool, ColumnDataSource, LinearAxis,
                          FixedTicker, Legend, Toggle, CustomJS, Title,
                          CheckboxGroup, Select, Text)


def save_svg_image(img_name, figa, figb):
    """To save plots as svg

    Note: Two images will emerge

    """
    figa.output_backend = "svg"
    figb.output_backend = "svg"
    export_svgs([figa], filename="%s_%s".format(img_name, "(a).svg"))
    export_svgs([figb], filename="%s_%s".format(img_name, "(b).svg"))


def save_png_image(img_name, disp_layout):
    """To save plots as png

    Note: One image will emerge

    """
    export_pngs(img_name, disp_layout)


def determine_table(table_name):
    """Find pattern at end of string to determine table to be plotted.
       The search is not case sensitive

    """
    pattern = re.compile(r'\.(G|K|B)\d*$', re.I)
    found = pattern.search(table_name)
    try:
        result = found.group()
        return result.upper()
    except AttributeError:
        return -1


def color_denormalize(ycol):
    """Converting rgb values from 0 to 255"""
    ycol = np.array(ycol)
    ycol = np.array(ycol*255, dtype=int)
    ycol = ycol.tolist()
    ycol = tuple(ycol)[:-1]
    return ycol


def errorbar(fig, x, y, xerr=None, yerr=None, color='red',
             point_kwargs={}, error_kwargs={}):
    """Function to plot the error bars for both x and y.
       Takes in 3 compulsory parameters fig, x and y

    Inputs
    ------
    fig: the figure object
    x: list
        x_axis value
    y: list
        y_axis value
    xerr: list
        Errors for x axis, must be a list
    yerr: list
        Errors for y axis, must be a list
    color: str
        Color for the error bars


    Outputs
    -------
    h: fig.multi_line
        Returns a multiline object for external legend rendering

    """
    # Setting default return value
    h = None

    if xerr is not None:

        x_err_x = []
        x_err_y = []

        for px, py, err in zip(x, y, xerr):
            x_err_x.append((px - err, px + err))
            x_err_y.append((py, py))

        h = fig.multi_line(x_err_x, x_err_y, color=color, line_width=3,
                           level='underlay', visible=False, **error_kwargs)

    if yerr is not None:
        y_err_x = []
        y_err_y = []

        for px, py, err in zip(x, y, yerr):
            y_err_x.append((px, px))
            y_err_y.append((py - err, py + err))

        h = fig.multi_line(y_err_x, y_err_y, color=color, line_width=3,
                           level='underlay', visible=False, **error_kwargs)

    fig.legend.click_policy = 'hide'

    return h


def make_plots(source, ax1, ax2, color='purple', y1_err=None, y2_err=None):
    """Generate a plot

    Inputs
    ------

    source: ColumnDataSource
        Main data to plot
    ax1: figure
        First figure
    ax2: figure
        Second Figure
    color: str
        Data points' color
    y1_err: list
        y1 error data
    y2_err: list
        y2 error data

    Outputs
    -------
    (p1, p1_err, p2, p2_err ): tuple
        Tuple of glyphs

    """
    p1 = ax1.circle('x', 'y1', size=8, alpha=1, color=color, source=source,
                    nonselection_color='#7D7D7D', nonselection_fill_alpha=0.3)
    p1_err = errorbar(fig=ax1, x=source.data['x'], y=source.data['y1'],
                      color=color, yerr=y1_err)

    p2 = ax2.circle('x', 'y2', size=8, alpha=1, color=color, source=source,
                    nonselection_color='#7D7D7D', nonselection_fill_alpha=0.3)
    p2_err = errorbar(fig=ax2, x=source.data['x'], y=source.data['y2'],
                      color=color, yerr=y2_err)

    return p1, p1_err, p2, p2_err


def data_prep_G(masked_data, masked_data_err, doplot, corr):
    """Preparing the data for plotting

    Inputs
    ------
    masked_data: list
        Flagged data from CPARAM column to be plotted.
    masked_data_err : list
        Flagged data from the PARAMERR column to be plotted
    doplot: str
        Either 'ap' or 'ri'
    corr: int
        Correlation to plot (0,1 e.t.c)

    Outputs
    -------
    (y1_data_array, y1_error_data_array, y2_data_array, y2_error_data_array) : tuple
        Tuple with arrays of the different data

    """

    if doplot == 'ap':
        y1 = np.abs(masked_data)[:, 0, corr]
        y1_err = np.abs(masked_data_err)[:, 0, corr]
        y2 = np.angle(masked_data)[:, 0, corr]
        # Remove phase limit from -pi to pi
        y2 = np.unwrap(y2)
        y2 = np.rad2deg(y2)
        y2_err = None
    else:
        y1 = np.real(masked_data)[:, 0, corr]
        y1_err = np.abs(masked_data_err)[:, 0, corr]
        y2 = np.imag(masked_data)[:, 0, corr]
        y2_err = None

    return y1, y1_err, y2, y2_err


def data_prep_B(masked_data, masked_data_err, doplot, corr):
    """Preparing the data for plotting

    INPUTS
    =====================
    masked_data     : list
        Flagged data from CPARAM column to be plotted.
    masked_data_err : list
        Flagged data from the PARAMERR column to be plotted
    doplot: str
        Either 'ap' or 'ri'
    corr: int
        Correlation to plot (0,1 e.t.c)

    Outputs
    -------
    (y1_data_array, y1_error_data_array, y2_data_array, y2_error_data_array): tuple
        Tuple with arrays of the different data

    """

    if doplot == 'ap':
        y1 = np.abs(masked_data)[0, :, corr]
        y1_err = np.abs(masked_data_err)[0, :, corr]
        y2 = np.array(np.angle(masked_data[0, :, corr]))
        y2 = np.rad2deg(np.unwrap(y2))
        y2_err = np.array(np.angle(masked_data_err[0, :, corr]))
        y2_err = np.rad2deg(np.unwrap(y2_err))
    else:
        y1 = np.real(masked_data)[0, :, corr]
        y1_err = np.abs(masked_data_err)[0, :, corr]
        y2 = np.imag(masked_data)[0, :, corr]
        y2_err = None

    return y1, y1_err, y2, y2_err


def data_prep_K(masked_data, masked_data_err, corr):
    """Preparing the data for plotting. Doplot must be 'ap'.

    Inputs
    ------
    masked_data     : list
        Flagged data from CPARAM column to be plotted.
    masked_data_err : list
        Flagged data from the PARAMERR column to be plotted
    corr: int
        Correlation to plot (0,1 e.t.c)

    Outputs
    -------
    (y1_data_array, y1_error_data_array, y2_data_array, y2_error_data_array): tuple
        Tuple with arrays of the different data

    """
    y1 = masked_data[:, 0, corr]
    y1 = np.array(y1)
    y1_err = masked_data_err
    y2 = masked_data[:, 0, int(not corr)]
    y2 = np.array(y2)
    y2_err = masked_data_err

    return y1, y1_err, y2, y2_err


def get_argparser():
    """Get argument parser"""
    parser = OptionParser(usage='%prog [options] tablename')
    parser.add_option('-f', '--field', dest='field',
                      help='Field ID to plot (default = 0)', default=0)
    parser.add_option('-d', '--doplot', dest='doplot',
                      help='Plot complex values as amp and phase (ap)'
                      'or real and imag (ri) (default = ap)', default='ap')
    parser.add_option('-a', '--ant', dest='plotants',
                      help='Plot only this antenna, or comma-separated list of antennas',
                      default=[-1])
    parser.add_option('-c', '--corr', dest='corr',
                      help='Correlation index to plot (usually just 0 or 1, default = 0)',
                      default=0)
    parser.add_option('--t0', dest='t0',
                      help='Minimum time to plot (default = full range)', default=-1)
    parser.add_option('--t1', dest='t1',
                      help='Maximum time to plot (default = full range)', default=-1)
    parser.add_option('--yu0', dest='yu0',
                      help='Minimum y-value to plot for upper panel (default=full range)',
                      default=-1)
    parser.add_option('--yu1', dest='yu1',
                      help='Maximum y-value to plot for upper panel (default=full range)',
                      default=-1)
    parser.add_option('--yl0', dest='yl0',
                      help='Minimum y-value to plot for lower panel (default=full range)',
                      default=-1)
    parser.add_option('--yl1', dest='yl1',
                      help='Maximum y-value to plot for lower panel (default=full range)',
                      default=-1)
    parser.add_option('--cmap', dest='mycmap',
                      help='Matplotlib colour map to use for antennas (default=coolwarm)',
                      default='coolwarm')
    parser.add_option('--ms', dest='myms',
                      help='Measurement Set to consult for proper antenna names',
                      default='')
    parser.add_option('-p', '--plotname', dest='pngname',
                      help='Output PNG name(default = something sensible)', default='')

    return parser


def main():
    """Main function"""
    parser = get_argparser()
    (options, args) = parser.parse_args()

    field = int(options.field)
    doplot = options.doplot
    plotants = options.plotants
    corr = int(options.corr)
    t0 = float(options.t0)
    t1 = float(options.t1)
    yu0 = float(options.yu0)
    yu1 = float(options.yu1)
    yl0 = float(options.yl0)
    yl1 = float(options.yl1)
    mycmap = options.mycmap
    myms = options.myms
    pngname = options.pngname


    #uncomment next line for inline notebok output
    #output_notebook()


    if len(args) != 1:
        print 'Please specify a gain table to plot.'
        sys.exit(-1)
    else:
        #getting the name of the gain table specified
        mytab = args[0].rstrip("/")
        
    if pngname == '':
        pngname = 'plot_' + mytab + '_corr' + str(corr) + '_' + doplot + '_field' + str(field)
        output_file(pngname + ".html")
        
    #by default is ap: amplitude and phase
    if doplot not in ['ap','ri']:
        print "Plot selection must be either ap (amp and phase) or ri (real and imag)"
        sys.exit(-1)


    #configuring the plot dimensions
    PLOT_WIDTH = 700
    PLOT_HEIGHT = 600


    tt = table(mytab,ack=False)
    ants = np.unique(tt.getcol('ANTENNA1'))
    fields = np.unique(tt.getcol('FIELD_ID'))
    flags = tt.getcol('FLAG')


    #setting up colors for the antenna plots
    cNorm = colors.Normalize(vmin=0, vmax=len(ants)-1)
    mymap = cm = pylab.get_cmap(mycmap)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=mymap)


    if int(field) not in fields.tolist():
        print 'Field ID '+ str(field) + ' not found'
        sys.exit(-1)

    if plotants[0] != -1:
        #creating a list for the antennas to be plotted
        plotants = plotants.split(',')

        for ant in plotants:
            if int(ant) not in ants:
                plotants.remove(ant)
                print 'Requested antenna ID '+ str(ant) + ' not found'
        if len(plotants) == 0:
            print 'No valid antennas have been requested'
            sys.exit(-1)
        else:
            plotants = np.array(plotants, dtype=int)
    else:
        plotants = ants

    if myms != '':
        anttab = table(myms.rstrip('/') + '/ANTENNA')
        antnames = anttab.getcol('NAME')
        anttab.done()
    else:
        antnames = ''


    #creating bokeh figures for plots   
    #linking plots ax1 and ax2 via the x_axes because fo similarities in range
    TOOLS = dict(tools='box_select, box_zoom, reset, pan, save, wheel_zoom, lasso_select')
    ax1 = figure(sizing_mode='scale_both', **TOOLS)
    ax2 = figure(sizing_mode='scale_both', x_range=ax1.x_range, **TOOLS)

    hover = HoverTool(tooltips=[("(time,y1)", "($x,$y)")], mode='mouse')
    hover.point_policy = 'snap_to_data'
    hover2 = HoverTool(tooltips=[("(time,y2)", "($x,$y)")], mode='mouse')
    hover2.point_policy = 'snap_to_data'


    #forming Legend object items for data and errors
    legend_items_ax1 = []
    legend_items_ax2 = []
    legend_items_err_ax1 = []
    legend_items_err_ax2 = []


    #setting default maximum and minimum values for the different axes
    xmin = 1e20
    xmax = -1e20
    ylmin = 1e20
    ylmax = -1e20
    yumin = 1e20
    yumax = -1e20



    #for each antenna
    for ant in plotants:
        #creating legend labels
        legend     = "A"+str(ant)
        legend_err = "E"+str(ant)

        #creating colors for maps
        y1col = scalarMap.to_rgba(float(ant))
        y2col = scalarMap.to_rgba(float(ant))

        #denormalizing the color array
        y1col = color_denormalize(y1col)
        y2col = color_denormalize(y2col)

        
        mytaql = 'ANTENNA1=='+str(ant)
        mytaql += '&&FIELD_ID=='+str(field)

        # querying the table for the 2 columns
        # getting data from the antennas, cparam contains the correlated data,
        # time is the time stamps
        
        subtab = tt.query(query=mytaql)
        #Selecting values from the table for antenna ants
        times = subtab.getcol('TIME')
        #Referencing time wrt the initial time
        times = times - times[0]
        
        flagcol = subtab.getcol('FLAG')
        
        paramerr = subtab.getcol('PARAMERR')



        if doplot == 'ap':
            if ".G" in determine_table(mytab):
                cparam = subtab.getcol('CPARAM')
                
                # creating a masked array to prevent invalid values from being
                # computed. IF mask is true, then the element is masked, and thus
                # won't be used in the calculation
                #removing flagged data from cparams
                masked_data = np.ma.masked_array(data=cparam, mask=flagcol)
                masked_data_err = np.ma.masked_array(data=paramerr, mask=flagcol)

                y1, y1_err, y2, y2_err =  data_prep_G(masked_data, masked_data_err, doplot, corr)
                #setting up glyph data source
                source = ColumnDataSource(data=dict(x=times, y1=y1, y2=y2 ))
                ax1.xaxis.axis_label = ax1_xlabel = 'Time [s]'
                ax2.xaxis.axis_label = ax2_xlabel = 'Time [s]'

            elif ".B" in determine_table(mytab):
                cparam = subtab.getcol('CPARAM')
                nchan = cparam.shape[1]
                chans = np.arange(0,nchan,dtype='int')
                masked_data = np.ma.masked_array(data=cparam,mask=flagcol)
                masked_data_err= np.ma.masked_array(data=paramerr, mask=flagcol)

                y1, y1_err, y2, y2_err =  data_prep_B(masked_data, masked_data_err, doplot, corr)
                source = ColumnDataSource(data=dict(x=chans,y1=y1,y2=y2))
                ax1.xaxis.axis_label = ax1_xlabel = 'Channel'
                ax2.xaxis.axis_label = ax2_xlabel = 'Channel'

            elif ".K" in determine_table(mytab):
                antenna=subtab.getcol('ANTENNA1')
                fparam = subtab.getcol('FPARAM')
                masked_data = np.ma.masked_array(data=fparam,mask=flagcol)
                masked_data_err = np.ma.masked_array(data=paramerr,mask=flagcol)

                y1, y1_err, y2, y2_err =  data_prep_K(masked_data, masked_data_err, corr)
                source = ColumnDataSource(data=dict(x=antenna,y1=y1,y2=y2))
                ax1.xaxis.axis_label = ax1_xlabel = 'Antenna'
                ax2.xaxis.axis_label = ax2_xlabel = 'Antenna'

            elif determine_table(mytab) == -1:
                print "Invalid table"
                sys.exit(-1)
            
            p1, p1_err, p2, p2_err = make_plots(source=source, color=y1col, ax1=ax1, ax2=ax2, y1_err=y1_err)

            ax1.yaxis.axis_label = ax1_ylabel = 'Amplitude'
            ax2.yaxis.axis_label = ax2_ylabel = 'Phase [Deg]'

        elif doplot == 'ri':
            if ".G" in determine_table(mytab):
                cparam = subtab.getcol('CPARAM')
                times = subtab.getcol('TIME')
                times = times - times[0]

                masked_data = np.ma.masked_array(data=cparam, mask=flagcol)
                masked_data_err = np.ma.masked_array(data=paramerr, mask=flagcol)

                y1, y1_err, y2, y2_err =  data_prep_G(masked_data, masked_data_err, doplot, corr)
                #setting up glyph data source
                source = ColumnDataSource(data=dict(x=times, y1=y1, y2=y2 ))
                ax1.xaxis.axis_label = ax1_xlabel = 'Time [s]'
                ax2.xaxis.axis_label = ax2_xlabel = 'Time [s]'

            elif ".B" in determine_table(mytab):
                cparam = subtab.getcol('CPARAM')
                nchan = cparam.shape[1]
                chans = np.arange(0,nchan,dtype='int')
                masked_data = np.ma.masked_array(data=cparam,mask=flagcol)
                masked_data_err= np.ma.masked_array(data=paramerr, mask=flagcol)

                y1, y1_err, y2, y2_err =  data_prep_B(masked_data, masked_data_err, doplot, corr)
                source = ColumnDataSource(data=dict(x=chans, y1=y1, y2=y2))
                ax1.xaxis.axis_label = ax1_xlabel = 'Channel'
                ax2.xaxis.axis_label = ax2_xlabel = 'Channel'

            elif ".K" in determine_table(mytab):
                print "No complex values to plot"
                sys.exit()

            elif determine_table(mytab) == -1:
                print "Invalid table"
                sys.exit(-1)

            p1, p1_err, p2, p2_err = make_plots(source=source, color=y1col, ax1=ax1, ax2=ax2, y1_err=y1_err)

            ax1.yaxis.axis_label = ax1_ylabel = 'Real'
            ax2.yaxis.axis_label = ax2_ylabel = 'Imaginary'

        #hide all the other plots until legend is clicked
        if ant>0:
            p1.visible = p2.visible = False
            

        #forming legend object items
        legend_items_ax1.append( (legend, [p1]) )
        legend_items_ax2.append( (legend, [p2]) )
        #for the errors
        legend_items_err_ax1.append( (legend_err, [p1_err]) )
        legend_items_err_ax2.append( (legend_err, [p2_err]) )
        

        subtab.close()

        #dx = 1.0/float(len(ants)-1)
        if antnames == '':
            antlabel = str(ant)
        else:
            antlabel = antnames[ant]

        if np.min(times) < xmin:
            xmin = np.min(times)
        if np.max(times) > xmax:
            xmax = np.max(times)
        if np.min(y1) < yumin:
            yumin = np.min(y1)
        if np.max(y1) > yumax:
            yumax = np.max(y1)
        if np.min(y2) < ylmin:
            ylmin = np.min(y2)
        if np.max(y2) > ylmax:
            ylmax = np.max(y2)


    #reorienting the min and max vales for x and y axes
    xmin = xmin - 400
    xmax = xmax + 400


    #setting the axis limits for scaliing
    if yumin < 0.0:
        yumin = -1*(1.1*np.abs(yumin))
    else:
        yumin = yumin*0.9
    yumax = yumax*1.1
    if ylmin < 0.0:
        ylmin = -1*(1.1*np.abs(ylmin))
    else:
        ylmin = ylmin*0.9
    ylmax = ylmax*1.1

    if t0 != -1:
        xmin = float(t0)
    if t1 != -1:
        xmax = float(t1)
    if yl0 != -1:
        ylmin = yl0
    if yl1 != -1:
        ylmax = yl1
    if yu0 != -1:
        yumin = yu0
    if yu1 != -1:
        yumax = yu1



    ax1.y_range = Range1d(yumin,yumax)
    ax2.y_range = Range1d(ylmin,ylmax)


    tt.close()

    #configuring titles for the plots
    ax1_title = Title(text=ax1_ylabel + ' vs ' + ax1_xlabel, align='center', text_font_size='25px')
    ax2_title = Title(text =ax2_ylabel + ' vs ' + ax2_xlabel, align='center', text_font_size='25px')

    #LEGEND CONFIGURATIONS
    BATCH_SIZE = 16
    # determining the number of legend objects required to be created
    # for each plot
    num_legend_objs =  int(np.ceil(len(plotants) / float(BATCH_SIZE)))


    # Automating creating batches of 16 each unless otherwise
    # Looks like
    # batch_0 : legend_items_ax1[:16]
    # equivalent to
    # batch_0 = legend_items_ax1[:16]
    batches_ax1, batches_ax1_err, batches_ax2, batches_ax2_err = [],[], [], []

    j = 0
    for i in range(num_legend_objs):
        # incase the number is not a multiple of 16
        if i == num_legend_objs:
            batches_ax1.extend([legend_items_ax1[j:]])
            batches_ax2.extend([legend_items_ax2[j:]])
            batches_ax1_err.extend([legend_items_err_ax1[j:]])
            batches_ax2_err.extend([legend_items_err_ax2[j:]])
        else:
            batches_ax1.extend([legend_items_ax1[j:j+BATCH_SIZE]])
            batches_ax2.extend([legend_items_ax2[j:j+BATCH_SIZE]])
            batches_ax1_err.extend([legend_items_err_ax1[j:j+BATCH_SIZE]])
            batches_ax2_err.extend([legend_items_err_ax2[j:j+BATCH_SIZE]])

        j += BATCH_SIZE


    # creating legend objects using items from the previous batches dictionary
    # Legend objects allow their positioning outside the main plot
    # resulting ordered dictionary looks like; 
    # leg_0 : Legend(items=batch_0, location='top_right', click_policy='hide')
    # equivalent to
    # leg_0 = Legend(items=batch_0, location='top_right', click_policy='hide')

    legend_objs_ax1, legend_objs_ax1_err, legend_objs_ax2, legend_objs_ax2_err = {}, {}, {}, {}

    for i in range(num_legend_objs):
        legend_objs_ax1['leg_%s'%str(i)] = Legend(items=batches_ax1[i], location='top_right', click_policy='hide')
        legend_objs_ax2['leg_%s'%str(i)] = Legend(items=batches_ax2[i], location='top_right', click_policy='hide')
        legend_objs_ax1_err['leg_%s'%str(i)] = Legend(items=batches_ax1_err[i], location='top_right', click_policy='hide', visible=False)
        legend_objs_ax2_err['leg_%s'%str(i)] = Legend(items=batches_ax2_err[i], location='top_right', click_policy='hide', visible = False)

    #adding legend objects to the layouts
    for i in range(num_legend_objs):
        ax1.add_layout(legend_objs_ax1['leg_%s'%str(i)], 'right')
        ax2.add_layout(legend_objs_ax2['leg_%s'%str(i)], 'right')

        ax1.add_layout(legend_objs_ax1_err['leg_%s'%str(i)], 'left')
        ax2.add_layout(legend_objs_ax2_err['leg_%s'%str(i)], 'left')


    #adding plot titles
    ax2.add_layout(ax2_title, 'above')
    ax1.add_layout(ax1_title, 'above')


    ax1.add_tools(hover)
    ax2.add_tools(hover2)


    # creating and configuring Antenna selection buttons
    ant_select = Toggle(label='Select All Antennas', button_type='success', width=200)

    #configuring toggle button for showing all the errors
    toggle_err = Toggle(label='Show All Error bars', button_type='warning', width=200)

    # Creating and configuring checkboxes
    # Autogenerating checkbox labels
    ant_labs = []
    s= 0
    e= BATCH_SIZE-1
    for i in range(num_legend_objs):
        ant_labs.append("A%s - A%s"%(s,e))
        s = s + BATCH_SIZE
        e = e + BATCH_SIZE

    batch_select = CheckboxGroup(labels=ant_labs, active=[])

    # Dropdown to hide and show legends
    legend_toggle = Select(title="Showing Legends: ", value="alo",
                    options = [("all","All"), ("alo","Antennas"), ("elo","Errors"),("non","None")])

    ant_select.callback = CustomJS(args=dict(glyph1=legend_items_ax1, glyph2=legend_items_ax2, batchsel=batch_select), code=
        '''
            var i;
             //if toggle button active
            if (this.active==false)
                {
                    this.label='Select all Antennas';
                    
                    
                    for(i=0; i<glyph1.length; i++){
                        glyph1[i][1][0].visible = false;
                        glyph2[i][1][0].visible = false;
                    }

                    batchsel.active = []
                }
            else{
                    this.label='Deselect all Antennas';
                    for(i=0; i<glyph1.length; i++){
                        glyph1[i][1][0].visible = true;
                        glyph2[i][1][0].visible = true;
              
                    }

                    batchsel.active = [0,1,2,3]
                }
        '''
         )



    toggle_err.callback = CustomJS(args=dict(err1=legend_items_err_ax1, err2=legend_items_err_ax2), code='''
            var i;
             //if toggle button active
            if (this.active==false)
                {
                    this.label='Show All Error bars';
                    
                    
                    for(i=0; i<err1.length; i++){
                        err1[i][1][0].visible = false;
                        //checking for error on phase and imaginary planes as these tend to go off
                        if (err2[i][1][0]){
                            err2[i][1][0].visible = false;
                        }

                   
                        
                    }
                }
            else{
                    this.label='Hide All Error bars';
                    for(i=0; i<err1.length; i++){
                        err1[i][1][0].visible = true;
                        if (err2[i][1][0]){
                            err2[i][1][0].visible = true;
                        }
                    }
                }
               
        ''')


    #BATCH SELECTION

    batch_select.callback = CustomJS.from_coffeescript(args=dict(bax1=batches_ax1, bax1_err=batches_ax1_err, bax2=batches_ax2, bax2_err = batches_ax2_err, antsel=ant_select), code="""
        
        #bax = [ [batch1], [batch2], [batch3] ]

        #j is batch number
        #i is glyph number
        j=0
        i=0

        if 0 in this.active
            i=0
            while i < bax1[j].length
                bax1[0][i][1][0].visible = true
                bax2[0][i][1][0].visible = true
                i++
        else
            i=0
            while i < bax1[0].length
                bax1[0][i][1][0].visible = false
                bax2[0][i][1][0].visible = false
                i++

        if 1 in this.active
            i=0
            while i < bax1[j].length
                bax1[1][i][1][0].visible = true
                bax2[1][i][1][0].visible = true
                i++
        else
            i=0
            while i < bax1[0].length
                bax1[1][i][1][0].visible = false
                bax2[1][i][1][0].visible = false
                i++
        
        if 2 in this.active
            i=0
            while i < bax1[j].length
                bax1[2][i][1][0].visible = true
                bax2[2][i][1][0].visible = true
                i++
        else
            i=0
            while i < bax1[0].length
                bax1[2][i][1][0].visible = false
                bax2[2][i][1][0].visible = false
                i++
        
        if 3 in this.active
            i=0
            while i < bax1[j].length
                bax1[3][i][1][0].visible = true
                bax2[3][i][1][0].visible = true
                i++
        else
            i=0
            while i < bax1[0].length
                bax1[3][i][1][0].visible = false
                bax2[3][i][1][0].visible = false
                i++



        if this.active.length == 4
            antsel.active = true
            antsel.label =  "Deselect all Antennas"
        else if this.active.length == 0
            antsel.active = false
            antsel.label = "Select all Antennas"
        """ )


    legend_toggle.callback = CustomJS(args=dict(loax1=legend_objs_ax1.values(), loax1_err=legend_objs_ax1_err.values(), loax2 = legend_objs_ax2.values(), loax2_err=legend_objs_ax2_err.values()), code = """

        var len = loax1.length;
        var i ;
        if (this.value == "alo"){
            for(i=0; i<len; i++){
                loax1[i].visible = true;
                loax2[i].visible = true;
                
            }
        }

        else{
            for(i=0; i<len; i++){
                loax1[i].visible = false;
                loax2[i].visible = false;
                
            }
        }

        

        if (this.value == "elo"){
            for(i=0; i<len; i++){
                loax1_err[i].visible = true;
                loax2_err[i].visible = true;
                
            }
        }

        else{
            for(i=0; i<len; i++){
                loax1_err[i].visible = false;
                loax2_err[i].visible = false;
                
            }
        }   

        if (this.value == "all"){
            for(i=0; i<len; i++){
                loax1[i].visible = true;
                loax2[i].visible = true;
                loax1_err[i].visible = true;
                loax2_err[i].visible = true;
                
            }
        }

        if (this.value == "non"){
            for(i=0; i<len; i++){
                loax1[i].visible = false;
                loax2[i].visible = false;
                loax1_err[i].visible = false;
                loax2_err[i].visible = false;
                
            }
        }   

        """)


    plot_widgets = widgetbox([ant_select, batch_select, toggle_err, legend_toggle])
    #figures   = column(ax1,ant_select, toggle_err)
    #figures_b = column(ax2)

    layout = gridplot([[plot_widgets, ax1, ax2]], plot_width=700, plot_height=600)
    
    #uncomment next line to automatically plot on web browser
    #show(layout)

        
    if pngname:
        for i in range(len(legend_items_ax1)):
            legend_items_ax1[i][1][0].visible = True
            legend_items_ax2[i][1][0].visible = True
            #p2.visible = True
        save_svg_image(pngname, ax1, ax2)

    
    print 'Rendered: '+pngname


main()
