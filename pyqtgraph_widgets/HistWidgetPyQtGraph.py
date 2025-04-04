from queue import Queue, Full as QueueFull

import pyqtgraph as pg
from itertools import cycle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QLabel, QFrame, QSplitter, QVBoxLayout, QHBoxLayout

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue

from RealSimpleGrapher.TraceListWidget import TraceList
from RealSimpleGrapher.pyqtgraph_widgets.artists import artistParameters, colorList
# todo: make an offshoot of graphwidgetpyqtgraph


class Hist_PyQtGraph(QWidget):
    """
    todo: document
    """

    def __init__(self, reactor, config, cxn=None, parent=None):
        super(Hist_PyQtGraph, self).__init__(parent)
        self.cxn = cxn
        # get parameter vault
        for server_name in self.cxn.servers.keys():
            if ("parameter" in server_name.lower()) and ("vault" in server_name.lower()):
                setattr(self, "pv", self.cxn.servers[server_name])
        self.reactor = reactor
        self.artists = {}
        self.should_stop = False
        self.name = config.name
        self.vline_name = config.vline
        self.vline_param = config.vline_param
        self.dataset_queue = Queue(config.max_datasets)
        self.live_update_loop = LoopingCall(self.update_figure)
        self.live_update_loop.start(0)
        self.colorChooser = cycle(colorList)
        self.initUI()

    @inlineCallbacks
    def initUI(self):
        self.tracelist = TraceList(self)
        self.pw = pg.PlotWidget()
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
        self.coords = QLabel('')
        self.title = QLabel(self.name)
        frame = QFrame()
        splitter = QSplitter()
        splitter.addWidget(self.tracelist)
        hbox = QHBoxLayout(self)
        vbox = QVBoxLayout(frame)
        vbox.addWidget(self.title)
        vbox.addWidget(self.pw)
        vbox.addWidget(self.coords)
        splitter.addWidget(frame)
        hbox.addWidget(splitter)
        # self.legend = self.pw.addLegend()
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        self.pw.plot([], [])
        vb = self.pw.plotItem.vb
        self.img = pg.ImageItem()
        vb.addItem(self.img)
        if self.vline_name:
            vb.addItem(self.inf)
            self.inf.sigPositionChangeFinished.connect(self.vline_changed)

        self.pw.scene().sigMouseMoved.connect(self.mouseMoved)
        self.pw.sigRangeChanged.connect(self.rangeChanged)

    def getItemColor(self, color):
        color_dict = {"r": QColor(Qt.red).lighter(130),
                      "g": QColor(Qt.green),
                      "y": QColor(Qt.yellow),
                      "c": QColor(Qt.cyan),
                      "m": QColor(Qt.magenta).lighter(120),
                      "w": QColor(Qt.white)}
        return color_dict[color]

    def update_figure(self):
        for ident, params in self.artists.items():
            if params.shown:
                try:
                    ds = params.dataset
                    index = params.index
                    current_update = ds.updateCounter
                    if params.last_update < current_update:
                        x = ds.data[:, 0]
                        x = list(x) + [x[-1] + 1]
                        y = ds.data[:, index + 1]
                        params.last_update = current_update
                        params.artist.setData(x, y)
                except:
                    pass

    def add_artist(self, ident, dataset, index, no_points=False):
        """
        no_points is an override parameter to the global show_points setting.
        It is to allow data fits to be plotted without points
        """
        new_color = self.colorChooser.next()
        hist = pg.PlotCurveItem([0, 1], [1], stepMode=True, fillLevel=0, brush=new_color, pen=None)
        self.artists[ident] = artistParameters(hist, dataset, index, True)
        self.pw.addItem(hist)
        self.tracelist.addTrace(ident, new_color)

    def remove_artist(self, ident):
        try:
            artist = self.artists[ident].artist
            self.pw.removeItem(artist)
            self.tracelist.removeTrace(ident)
            self.artists[ident].shown = False
            try:
                del self.artists[ident]
            except KeyError:
                pass
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
            except KeyError:  # this means the artist has been deleted.
                pass

    def rangeChanged(self):
        lims = self.pw.viewRange()
        self.pointsToKeep = lims[0][1] - lims[0][0]
        self.current_limits = [lims[0][0], lims[0][1]]

    @inlineCallbacks
    def add_dataset(self, dataset):
        try:
            self.dataset_queue.put(dataset, block=False)
        except QueueFull:
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

    def mouseMoved(self, pos):
        pnt = self.img.mapFromScene(pos)
        string = '(' + str(pnt.x()) + ' , ' + str(pnt.y()) + ')'
        self.coords.setText(string)

    @inlineCallbacks
    def get_init_vline(self):
        init_vline = yield self.pv.get_parameter(self.vline_param[0],
                                                 self.vline_param[1])
        print(init_vline)
        returnValue(init_vline)

    @inlineCallbacks
    def vline_changed(self, sig):
        val = self.inf.value()
        val = int(round(val))
        yield self.pv.set_parameter(self.vline_param[0],
                                    self.vline_param[1], val)


if __name__ == '__main__':
    from EGGS_labrad.clients import runClient
    import labrad
    cxn = labrad.connect()
    from RealSimpleGrapher.GUIConfig import graphConfig
    runClient(Hist_PyQtGraph, graphConfig('example', isHist=True), cxn=cxn)
