"""
A normal graph widget. The "base unit" of the RSG.
"""
import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue

from TraceListWidget import TraceList
from DataVaultListWidget.DataVaultListWidget import DataVaultList

from sys import settrace
from itertools import cycle
from queue import Queue, Full as QueueFull

settrace(None)


class artistParameters():
    def __init__(self, artist, dataset, index, shown):
        self.artist = artist
        self.dataset = dataset
        self.index = index
        self.shown = shown
        # update counter in the Dataset object, only
        # redraw if the dataset has a higher update count
        self.last_update = 0
        # keep track of log mode
        self.logModeX = False
        self.logModeY = False


class Graph_PyQtGraph(QtWidgets.QWidget):
    """
    A normal graph widget. The "base unit" of the RSG. Contains a
    PlotWidget for plotting data, a TraceListWidget for managing
    displayed datasets, and a DataVaultListWidget for selecting datasets.
    """

    def __init__(self, config, reactor, cxn=None, parent=None, root=None):
        super(Graph_PyQtGraph, self).__init__(parent)
        self.root = root
        from labrad.units import WithUnit as U
        self.U = U
        self.cxn = cxn
        self.pv = self.cxn.parameter_vault
        self.reactor = reactor
        self.artists = {}
        self.should_stop = False
        self.name = config.name
        # set lines from config
        self.vline_name = config.vline
        self.vline_param = config.vline_param
        self.hline_name = config.hline
        self.hline_param = config.hline_param
        self.show_points = config.show_points
        self.grid_on = config.grid_on
        self.scatter_plot = config.scatter_plot
        # set background color
        self.setStyleSheet("background-color:black; color:white; border: 1px solid white")
        # dataset queue is used to store datasets
        self.dataset_queue = Queue(config.max_datasets)
        # live_update_loop continuously calls update_figure,
        # which is where points are received from the dataset objects
        # and pushed onto the plotwidget
        self.live_update_loop = LoopingCall(self.update_figure)
        self.live_update_loop.start(0)
        # colors
        # todo: move this to GUIConfig
        self.colors = [QColor(Qt.red).lighter(130),
                  QColor(Qt.green),
                  QColor(Qt.yellow),
                  QColor(Qt.cyan),
                  QColor(Qt.magenta).lighter(120),
                  QColor(Qt.white)]
        self.colorChooser = cycle(self.colors)
        self.autoRangeEnable = True
        self.initUI()

    @inlineCallbacks
    def initUI(self):
        """
        Draws the UI.
        """
        # import constituent widgets
        self.tracelist = TraceList(self, root=self.root)
        self.dv = DataVaultList(self.name, cxn=self.cxn, root=self.root)
        self.pw = pg.PlotWidget()
        tracelistLabel = QtWidgets.QLabel('Dataset Traces:')
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
        # layout widgets
        lsplitter = QtWidgets.QSplitter()
        lsplitter.setOrientation(Qt.Vertical)
        lsplitter.addWidget(tracelistLabel)
        lsplitter.addWidget(self.tracelist)
        lsplitter.addWidget(self.dv)
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(lsplitter)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(splitter)
        # frame/vbox is everything on RHS
        frame = QtWidgets.QFrame()
        vbox = QtWidgets.QVBoxLayout()
        self.title = QtWidgets.QLabel(self.name)
        vbox.addWidget(self.title)
        vbox.addWidget(self.pw)
        frame.setLayout(vbox)
        splitter.addWidget(frame)
        # create bottom buttons
        pwButtons = QtWidgets.QWidget()
        pwButtons_layout = QtWidgets.QHBoxLayout()
        pwButtons.setLayout(pwButtons_layout)
        self.coords = QtWidgets.QLabel('')
        self.autorangebutton = QtWidgets.QPushButton('Autorange Off')
        self.autorangebutton.setCheckable(True)
        self.autorangebutton.toggled.connect(lambda: self.toggleAutoRange(self.autorangebutton.isChecked()))
        pwButtons_layout.addWidget(self.coords)
        pwButtons_layout.addWidget(self.autorangebutton)
        vbox.addWidget(pwButtons)
        # set layout
        self.setLayout(hbox)
        # self.legend = self.pw.addLegend()
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        self.pw.plot([], [])
        # setup viewbox
        vb = self.pw.plotItem.vb
        self.img = pg.ImageItem()
        vb.addItem(self.img)
        # connect signals to slots
        if self.vline_name:
            vb.addItem(self.inf)
            self.inf.sigPositionChangeFinished.connect(self.vline_changed)
        if self.hline_name:
            vb.addItem(self.inf)
            self.inf.sigPositionChangeFinished.connect(self.hline_changed)
        self.pw.scene().sigMouseMoved.connect(self.mouseMoved)
        self.pw.sigRangeChanged.connect(self.rangeChanged)
        # sigrangechanged and sigmouseclicked and return graphics scene
        # self.pw.scene().sigMouseClicked.connect(self.mouseClicked)

    def update_figure(self):
        for ident, params in self.artists.items():
            if params.shown:
                try:
                    ds = params.dataset
                    index = params.index
                    current_update = ds.updateCounter
                    if params.last_update < current_update:
                        x = ds.data[:, 0]
                        y = ds.data[:, index + 1]
                        params.last_update = current_update
                        params.artist.setData(x, y)
                        if x < 500:
                            params.artist.setData(symbol='o')
                except Exception as e:
                    pass

    def add_artist(self, ident, dataset, index, no_points=False):
        '''
        no_points is an override parameter to the global show_points setting.
        It is to allow data fits to be plotted without points
        '''
        if ident not in self.artists.keys():
            new_color = next(self.colorChooser)
            if self.show_points and not no_points:
                line = self.pw.plot([], [], symbol=None, symbolBrush=new_color,
                                    name=ident, pen=new_color, connect=self.scatter_plot,
                                    setSkipFiniteCheck=True)
            else:
                line = self.pw.plot([], [], symbol=None, pen=new_color, name=ident)
            if self.grid_on:
                self.pw.showGrid(x=True, y=True)
            self.artists[ident] = artistParameters(line, dataset, index, True)
            self.tracelist.addTrace(ident, new_color)
        else:
            print('Trace already added.')

    def remove_artist(self, ident):
        try:
            artist = self.artists[ident].artist
            self.pw.removeItem(artist)
            self.tracelist.removeTrace(ident)
            self.artists[ident].shown = False
            del self.artists[ident]
        except Exception as e:
            print("Remove failed")

    def display(self, ident, shown):
        try:
            artist = self.artists[ident].artist
            if shown:
                self.pw.addItem(artist)
                self.artists[ident].shown = True
            else:
                self.pw.removeItem(artist)
                self.artists[ident].shown = False
        except KeyError:
            raise Exception('404 Artist not found')

    def checkboxChanged(self):
        for ident, item in self.tracelist.trace_dict.items():
            try:
                if item.checkState() and not self.artists[ident].shown:
                    self.display(ident, True)
                if not item.checkState() and self.artists[ident].shown:
                    self.display(ident, False)
            # this means the artist has been deleted.
            except KeyError:
                pass

    @inlineCallbacks
    def add_dataset(self, dataset):
        try:
            self.dataset_queue.put(dataset, block=False)
        except QueueFull:
            #print('Dataset queue full. Removing previous dataset.')
            remove_ds = self.dataset_queue.get()
            self.remove_dataset(remove_ds)
            self.dataset_queue.put(dataset, block=False)
        labels = yield dataset.getLabels()
        for i, label in enumerate(labels):
            self.add_artist(label, dataset, i)

    @inlineCallbacks
    def remove_dataset(self, dataset):
        labels = yield dataset.getLabels()
        for label in labels:
            self.remove_artist(label)

    def set_xlimits(self, limits):
        self.pw.setXRange(limits[0], limits[1])
        self.current_limits = limits

    def set_ylimits(self, limits):
        self.pw.setYRange(limits[0], limits[1])


    # SLOTS
    def rangeChanged(self):
        lims = self.pw.viewRange()
        self.pointsToKeep = lims[0][1] - lims[0][0]
        self.current_limits = [lims[0][0], lims[0][1]]

    def mouseMoved(self, pos):
        # print("Image position:", self.img.mapFromScene(pos))
        pnt = self.img.mapFromScene(pos)
        string = '(' + str(pnt.x()) + ' , ' + str(pnt.y()) + ')'
        self.coords.setText(string)

    def toggleAutoRange(self, autorangeEnable):
        if autorangeEnable:
            self.pw.enableAutoRange()
            self.autorangebutton.setText('Autorange On')
        else:
            self.pw.disableAutoRange()
            self.autorangebutton.setText('Autorange Off')

    @inlineCallbacks
    def get_init_vline(self):
        init_vline = yield self.pv.get_parameter(self.vline_param[0],
                                                 self.vline_param[1])
        returnValue(init_vline)

    @inlineCallbacks
    def get_init_hline(self):
        init_hline = yield self.pv.get_parameter(self.hline_param[0],
                                                 self.hline_param[1])
        returnValue(init_hline)

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


if __name__ == '__main__':
    from EGGS_labrad.clients import runGUI
    runGUI(Graph_PyQtGraph, 'example')
    main = Graph_PyQtGraph('example', reactor)
