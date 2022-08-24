"""
A normal graph widget. The "base unit" of the RSG.
"""
import pyqtgraph as pg
from itertools import cycle
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QSplitter, QHBoxLayout, QVBoxLayout, QFrame, QPushButton

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue

from RealSimpleGrapher.TraceListWidget import TraceList
from RealSimpleGrapher.DataVaultListWidget import DataVaultList
from RealSimpleGrapher.pyqtgraph_widgets.artists import artistParameters, colorList

from sys import settrace
settrace(None)


class Graph_PyQtGraph(QWidget):
    """
    A normal graph widget. The "base unit" of the RSG.
    Contains a PlotWidget for plotting data, a TraceListWidget for managing
    displayed datasets, and a DataVaultListWidget for selecting datasets.
    """

    # SETUP
    def __init__(self, reactor, config, cxn=None, parent=None, root=None):
        super().__init__(parent)
        self.root = root
        from labrad.units import WithUnit as U
        self.U = U
        self.cxn = cxn
        self.pv = self.cxn.parametervault
        self.reactor = reactor
        self.artists = {}
        self.should_stop = False
        # get properties from config
        self.name = config.name
        self.show_points = config.show_points
        self.grid_on = config.grid_on
        self.scatter_plot = config.scatter_plot
        # set lines from config
        self.vline_name, self.vline_param = (config.vline, config.vline_param)
        self.hline_name, self.hline_param = (config.hline, config.hline_param)
        # set background color
        self.setStyleSheet("background-color:black; color:white; border: 1px solid white")
        # datasets is used to store datasets and active traces
        self.datasets = {}
        # live_update_loop continuously calls _update_figure,
        # which is where points are received from the dataset objects
        # and pushed onto the plotwidget
        self.live_update_loop = LoopingCall(self._update_figure)
        self.live_update_loop.start(0.25)
        # colors
        self.colorList = colorList
        self.colorChooser = cycle(colorList)
        # autoranging
        self.autoRangeEnable = True
        # startup
        self.initUI()

    @inlineCallbacks
    def initUI(self):
        """
        Create the GUI.
        """
        layout = QHBoxLayout(self)
        splitter_widget = QSplitter()
        layout.addWidget(splitter_widget)

        # LHS displays datasets and active traces
        self.tracelist = TraceList(self, root=self.root)
        self.dv = DataVaultList(self.name, cxn=self.cxn, root=self.root)
        lhs_widget = QSplitter()
        lhs_widget.setOrientation(Qt.Vertical)
        lhs_widget.addWidget(QLabel('Dataset Traces:'))
        lhs_widget.addWidget(self.tracelist)
        lhs_widget.addWidget(self.dv)


        # RHS displays plots and related data
        self.pw = pg.PlotWidget()
        rhs_widget = QFrame()
        # create bottom buttons
        pwButtons = QWidget()
        pwButtons_layout = QHBoxLayout(pwButtons)
        self.coords = QLabel('')
        self.autorangebutton = QPushButton('Autorange Off')
        self.autorangebutton.setCheckable(True)
        pwButtons_layout.addWidget(self.coords)
        pwButtons_layout.addWidget(self.autorangebutton)

        rhs_widget_layout = QVBoxLayout(rhs_widget)
        rhs_widget_layout.addWidget(QLabel(self.name))
        rhs_widget_layout.addWidget(self.pw)
        rhs_widget_layout.addWidget(pwButtons)

        # add widgets to layout
        splitter_widget.addWidget(lhs_widget)
        splitter_widget.addWidget(rhs_widget)

        # set up viewbox
        self.pw.plot([], [])
        vb = self.pw.plotItem.vb
        self.img = pg.ImageItem()
        vb.addItem(self.img)

        # configure lines
        if self.vline_name:
            self.inf = pg.InfiniteLine(movable=True, angle=90,
                                       label=self.vline_name + '{value:0.0f}',
                                       labelOpts={'position': 0.9,
                                                  'color': (200, 200, 100),
                                                  'fill': (200, 200, 200, 50),
                                                  'movable': True})
            init_value = yield self.get_init_vline()
            self.inf.setValue(init_value)
            self.inf.setPen(width=5.0)
            vb.addItem(self.inf)
            self.inf.sigPositionChangeFinished.connect(self.vline_changed)
        if self.hline_name:
            self.inf = pg.InfiniteLine(movable=True, angle=0,
                                       label=self.hline_name + '{value:0.0f}',
                                       labelOpts={'position': 0.9,
                                                  'color': (200, 200, 100),
                                                  'fill': (200, 200, 200, 50),
                                                  'movable': True})
            init_value = yield self.get_init_hline()
            self.inf.setValue(init_value)
            self.inf.setPen(width=5.0)
            vb.addItem(self.inf)
            self.inf.sigPositionChangeFinished.connect(self.hline_changed)

        # connect signals to slots
        self.autorangebutton.toggled.connect(lambda status: self.toggleAutoRange(status))
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        self.pw.scene().sigMouseMoved.connect(self.mouseMoved)
        self.pw.sigRangeChanged.connect(self.rangeChanged)
        # self.pw.scene().sigMouseClicked.connect(self.mouseClicked)


    # DATASETS/TRACE MANAGEMENT
    @inlineCallbacks
    def add_dataset(self, dataset):
        """
        Adds a dataset.
        Arguments:
            dataset (Dataset): the dataset to add.
        """
        dataset_ident = self._makeDatasetIdent(dataset.dataset_location)
        dataset_trace_names = yield dataset.getLabels()
        existing_trace_names = set()
        # get index corresponding to each trace within the dataset
        index_dict = {}
        for i, trace_name in enumerate(dataset_trace_names):
            index_dict[trace_name] = i
        # use old dataset if dataset already exists
        if dataset_ident in self.datasets.keys():
            print('Error in graphwidget.add_dataset: Dataset already exists.')
            print('\tAdding any missing traces.')
            # update existing values
            existing_trace_names = self.datasets[dataset_ident]['trace_names']
            self.datasets[dataset_ident]['trace_names'] = set(dataset_trace_names)
            # get old dataset
            dataset = self.datasets[dataset_ident]['dataset']
        # otherwise add new dataset to self.datasets
        else:
            self.datasets[dataset_ident] = {
                'dataset': dataset,
                'trace_names': set(dataset_trace_names)
            }
            self.tracelist.addDataset(dataset_ident)
        # get different traces and add each trace to artists
        diff_trace_names = list(set(dataset_trace_names) - existing_trace_names)
        for trace_name in diff_trace_names:
            index = index_dict[trace_name]
            artist_ident = (*dataset_ident, trace_name)
            self.add_artist(artist_ident, dataset, index)
        # enable autorange
        self.toggleAutoRange(True)

    def remove_dataset(self, dataset_ident):
        """
        Removes all the traces of a dataset from the holding dictionary self.artists
        Arguments:
            dataset_ident   (dataset_location, dataset_name):  a unique identifier for a dataset.
        """
        try:
            # get all traces currently in use
            existing_trace_names = self.datasets[dataset_ident]['trace_names']
            # remove traces
            for trace_name in tuple(existing_trace_names):
                artist_ident = (*dataset_ident, trace_name)
                self.remove_artist(artist_ident)
            # no need to call traceList.removeDataset or otherwise interact since
            # it is all handled in self.remove_artist
        except Exception as e:
            print("Error in graphwidget.remove_dataset:", e)

    def add_artist(self, artist_ident, dataset, index, no_points=False):
        """
        Adds an artist/trace from a dataset.
        Called only by add_dataset to add the traces within a dataset.
        Arguments:
            artist_ident    (dataset_location, dataset_name, trace_name): a unique identifier for an artist.
            no_points       (bool)  : an override parameter to the global show_points setting,
                                    allowing data fits to be plotted without points.
        """
        if artist_ident not in self.artists.keys():
            new_color = next(self.colorChooser)
            trace_name = artist_ident[2]
            if self.show_points and (not no_points):
                line = self.pw.plot([], [],
                                    symbol=None, symbolBrush=new_color, pen=new_color,
                                    name=trace_name, connect=self.scatter_plot,
                                    SkipFiniteCheck=True)
            else:
                line = self.pw.plot([], [],
                                    symbol=None, pen=new_color, name=trace_name)
            if self.grid_on:
                self.pw.showGrid(x=True, y=True)
            # add artist to holding dictionary and tracelist
            self.artists[artist_ident] = artistParameters(line, dataset, index, True)
            self.tracelist.addTrace(artist_ident, new_color)
        else:
            print('Error in graphwidget.add_artist: Trace already added.')

    def remove_artist(self, artist_ident):
        """
        Removes an artist (i.e. trace) from the PlotWidget.
        Called by remove_dataset when dataset_queue is full and when we manually
        remove it via the TraceListWidget.
        Arguments:
            artist_ident    (dataset_location, dataset_name, trace_name): a unique identifier for an artist.
        """
        try:
            artist = self.artists[artist_ident].artist
            # remove references to the artist
            self.pw.removeItem(artist)
            # remove the artist from dataset holder
            dataset_location, dataset_name, trace_name = artist_ident
            dataset_ident = (dataset_location, dataset_name)
            trace_names = self.datasets[dataset_ident]['trace_names']
            trace_names.remove(trace_name)
            # delete the artist
            del self.artists[artist_ident]
            # if dataset has no active traces, remove the dataset
            if len(trace_names) == 0:
                del self.datasets[dataset_ident]
        except KeyError:
            print("Error in graphwidget.remove_artist: artist already deleted.")
            print("\tident:", artist_ident)
        except Exception as e:
            print("Error in graphwidget.remove_artist: remove failed:", e)


    # CONFIGURE PLOTWIDGET
    def set_xlimits(self, limits):
        self.pw.setXRange(*limits)
        self.current_limits = limits

    def set_ylimits(self, limits):
        self.pw.setYRange(*limits)

    @inlineCallbacks
    def get_init_vline(self):
        init_vline = yield self.pv.get_parameter(*self.vline_param)
        returnValue(init_vline)

    @inlineCallbacks
    def get_init_hline(self):
        init_hline = yield self.pv.get_parameter(*self.hline_param)
        returnValue(init_hline)


    # SLOTS
    def checkboxChanged(self):
        for ident, artist in self.tracelist.trace_dict.items():
            try:
                if artist.checkState(0) and (not self.artists[ident].shown):
                    self._display(ident, True)
                if (not artist.checkState(0)) and self.artists[ident].shown:
                    self._display(ident, False)
            # this means the artist has been deleted.
            except KeyError:
                pass

    def rangeChanged(self):
        lims = self.pw.viewRange()
        self.pointsToKeep = lims[0][1] - lims[0][0]
        self.current_limits = [lims[0][0], lims[0][1]]

    def mouseMoved(self, pos):
        pnt = self.img.mapFromScene(pos)
        string = "({:.4g},\t{:.4g})".format(pnt.x(), pnt.y())
        self.coords.setText(string)

    def toggleAutoRange(self, autorangeEnable):
        if autorangeEnable:
            # todo: try to move stylesheets to once during init for both states
            self.pw.enableAutoRange()
            self.autorangebutton.setText('Autorange On')
            self.autorangebutton.setStyleSheet("background-color:#272323; border-style:inset; border-width: 3px; border-color: grey")
        else:
            self.pw.disableAutoRange()
            self.autorangebutton.setText('Autorange Off')
            self.autorangebutton.setStyleSheet("background-color:black; border-style:outset; border-width: 3px; border-color: grey")

    @inlineCallbacks
    def vline_changed(self, sig):
        val = self.inf.value()
        param = yield self.pv.get_parameter(self.vline_param[0], self.vline_param[1])
        units = param.units
        val = self.U(val, units)
        yield self.pv.set_parameter(self.vline_param[0], self.vline_param[1], val)

    @inlineCallbacks
    def hline_changed(self, sig):
        val = self.inf.value()
        param = yield self.pv.get_parameter(self.hline_param[0], self.hline_param[1])
        units = param.units
        val = self.U(val, units)
        yield self.pv.set_parameter(self.hline_param[0], self.hline_param[1], val)
    
    
    # HELPER
    def _display(self, ident, shown):
        """
        Displays/removes a trace from the PlotWidget.
        Called only by checkboxChanged.
        Arguments:
            ident   ([str], str): the unique identifier for the trace.
            shown   (bool)      : whether the trace corresponding to ident is shown.
        """
        try:
            artist = self.artists[ident].artist
            self.artists[ident].shown = shown
            if shown:
                self.pw.addItem(artist)
            else:
                self.pw.removeItem(artist)
        except KeyError:
            raise Exception('Error in graphwidget._display: Artist not found')

    def _update_figure(self):
        """
        The main update loop which updates the artists
        with data from the Datasets.
        """
        for artist_params in self.artists.values():
            if artist_params.shown:
                try:
                    ds = artist_params.dataset
                    current_update = ds.updateCounter
                    if artist_params.last_update < current_update:
                        x = ds.data[:, 0]
                        y = ds.data[:, artist_params.index + 1]
                        artist_params.last_update = current_update
                        artist_params.artist.setData(x, y)
                except Exception as e:
                    print('Error in graphwidget._update_figure:', e)

    def _makeDatasetIdent(self, dataset_ident):
        """
        Creates an identifier unique to each dataset.
        """
        directory_list, dataset_name = dataset_ident
        dataset_location = '\\'.join(directory_list)
        return (dataset_location, dataset_name)


if __name__ == '__main__':
    from EGGS_labrad.clients import runClient
    from RealSimpleGrapher.GUIConfig import graphConfig
    import labrad
    cxn = labrad.connect()
    runClient(Graph_PyQtGraph, graphConfig('example'), cxn=cxn)
