"""
Configuration settings for the RSG.
"""
import pyqtgraph as pg
from importlib.util import find_spec


"""
Set global configuration options.
"""
pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'y')
pg.setConfigOption('antialias', False)
if find_spec('OpenGL'):
    pg.setConfigOption('useOpenGL', True)
    pg.setConfigOption('enableExperimental', True)


"""
Configuration classes for the different graph widget types.
"""

class traceListConfig():
    """
    Config for the traceList widget. Mostly concerns its color.
    """

    def __init__(self, background_color='black', use_trace_color=True):
        self.background_color = background_color
        self.use_trace_color = use_trace_color


class graphConfig():
    """
    Config for an individual graph within a GridGraphWindow (i.e. a grapher unit).
    Sets graphing-related settings such as axes limits and horizontal/vertical lines.
    """

    def __init__(self, name, ylim=[0, 1], max_datasets=20,
                 isScrolling=False, isImages=False, isHist=False,
                 show_points=True, grid_on=False, scatter_plot='all',
                 line_param=None, vline=None, vline_param=None, hline=None, hline_param=None):
        self.name = name
        self.ylim = ylim
        self.isScrolling = isScrolling
        self.max_datasets = max_datasets
        self.graphs = 1
        self.show_points = show_points
        self.grid_on = grid_on
        self.scatter_plot = scatter_plot
        self.isImages = isImages
        self.isHist = isHist
        self.line_param = line_param
        self.vline = vline
        self.vline_param = vline_param
        self.hline = hline
        self.hline_param = hline_param


class gridGraphConfig():
    """
    Config for a GridGraphWindow (i.e. a tab).
    Sets the layout of the graphs on the tab.
    """
    def __init__(self, tab, config_list):
        self.tab = tab
        self.config_list = config_list[0::3]
        self.row_list = config_list[1::3]
        self.column_list = config_list[2::3]
        self.graphs = len(self.config_list)



"""
The actual config of the RSG is set here.

tabs holds the tabs on the RSG window.
Each tab must be a gridGraphConfig object, which can contain one or more graphConfig objects.
graphConfig objects correspond to a complete graphing unit (i.e. traceList and grapher).
If a gridGraphConfig object holds multiple graphConfig objects, their positions must be 
    specified in the format x_pos, y_pos.
"""

tabs = [
    # system monitor tab displays system essentials
    gridGraphConfig('System Monitor', [
        graphConfig('Lakeshore 336 Temperature', max_datasets=4),       0, 0,
        graphConfig('TwisTorr74 Pressure', max_datasets=1),             1, 0,
        graphConfig('NIOPS03 Pressure', max_datasets=1),                0, 1,
        graphConfig('RF Pickoff'),                                      1, 1
    ]),
    # laser monitor tab monitors laser frequencies via wavemeter
    gridGraphConfig('Laser Monitor', [
        graphConfig('397nm', max_datasets=1),                           0, 0,
        graphConfig('423nm', max_datasets=1),                           1, 0,
        graphConfig('854nm', max_datasets=1),                           0, 1,
        graphConfig('866nm', max_datasets=1),                           1, 1,
    ]),
    gridGraphConfig('RGA', [graphConfig('RGA Sweeps', max_datasets=5), 0, 0])
    # gridGraphConfig('SLS', [graphConfig('SLS Locking Output', max_datasets=5), 0, 0]),
    # gridGraphConfig('PMT', [graphConfig('pmt', ylim=[0, 30], isScrolling=True, max_datasets=1, show_points=False), 0, 0])
]
