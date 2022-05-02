from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMenu, QFileDialog

from .FitWindowWidget import FitWindow
from .ParameterListWidget import ParameterList
from .PredictSpectrumWidget import PredictSpectrum

from RealSimpleGrapher.GUIConfig import traceListConfig

from os import getenv
from numpy import savetxt


class TraceList(QListWidget):
    """
    Manages the datasets that are being plotted.
    Basically the left-hand column of each GraphWidget.
    """

    def __init__(self, parent, root=None):
        super(TraceList, self).__init__()
        self.parent = parent
        self.root = root
        self.windows = []
        self.config = traceListConfig()
        self.setStyleSheet("background-color:%s;" % self.config.background_color)
        try:
            self.use_trace_color = self.config.use_trace_color
        except AttributeError:
            self.use_trace_color = False
        #self.name = 'pmt'
        self.initUI()

    def initUI(self):
        self.trace_dict = {}
        item = QListWidgetItem('Traces') # todo: check if these are necessary
        item.setCheckState(Qt.Checked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)

    def addTrace(self, ident, color):
        """
        Adds a trace to the TraceListWidget.
        """
        dataset_location, trace_name = ident
        item = QListWidgetItem(trace_name)
        # store ident within the QListWidgetItem
        item.setData(ident, Qt.UserRole)
        # set color of artist entry in tracelist
        if self.use_trace_color:
            item.setForeground(color)
        else:
            item.setForeground(QColor(255, 255, 255))
        item.setBackground(QColor(0, 0, 0))
        item.setCheckState(Qt.Checked)
        self.addItem(trace_name)
        self.trace_dict[ident] = item

    def removeTrace(self, ident):
        """
        Removes a trace from the TraceListWidget.
        """
        item = self.trace_dict[ident]
        row = self.row(item)
        self.takeItem(row)
        item = None

    def changeTraceListColor(self, ident, new_color):
        """
        Changes the color of a trace.
        """
        item = self.trace_dict[ident]
        item.setForeground(new_color)

    def popupMenu(self, pos):
        """
        Manages the pop-up menu that happens upon a right-click.
        """
        menu = QMenu()
        item = self.itemAt(pos)
        if item is None:
            spectrumaddAction = menu.addAction('Add Predicted Spectrum')
            removeallAction = menu.addAction('Remove All Traces')
            exportallAction = menu.addAction('Export All Traces')

            # process actions
            action = menu.exec_(self.mapToGlobal(pos))
            if action == spectrumaddAction:
                ps = PredictSpectrum(self)
                self.windows.append(ps)
                ps.show()
            elif action == removeallAction:
                # remove all artists/traces
                for index in reversed(range(self.count())):
                    ident = self.item(index).data(Qt.UserRole)
                    self.parent.remove_artist(ident)
            elif action == exportallAction:
                # get all datasets
                datasets_all = set()
                for index in range(self.count()):
                    ident = self.item(index).data(Qt.UserRole)
                    dataset_tmp = self.parent.artists[ident].dataset
                    datasets_all.add(dataset_tmp)
                # export all datasets
                for dataset in datasets_all:
                    try:
                        filename = QFileDialog.getSaveFileName(self, 'Save Dataset: ' + dataset.dataset_name,
                                                               getenv('HOME'), "CSV (*.csv)")
                        savetxt(filename[0], dataset.data, delimiter=',')
                    except Exception as e:
                        print("Error during exportAll:", e)
        else:
            ident = item.data(Qt.UserRole)
            # create list of user actions in menu
            removeallAction = menu.addAction('Remove All Traces')
            parametersAction = menu.addAction('Parameters')
            togglecolorsAction = menu.addAction('Toggle Colors')
            fitAction = menu.addAction('Fit')
            removeAction = menu.addAction('Remove')
            exportAction = menu.addAction('Export')
            # log mode
            logAction = menu.addMenu('Set Log Mode')
            logXaction = logAction.addAction('X-axis')
            logXaction.setCheckable(True)
            if self.parent.artists[ident].logModeX:
                logXaction.setChecked(True)
            logYaction = logAction.addAction('Y-axis')
            logYaction.setCheckable(True)
            if self.parent.artists[ident].logModeY:
                logYaction.setChecked(True)
            # color menu
            # todo: fix and clean up
            selectColorMenu = menu.addMenu("Select Color")
            colorActions = list(map(selectColorMenu.addAction,
                                    ["Red", "Green", "Yellow", "Cyan", "Magenta", "White"]))
            # process actions
            action = menu.exec_(self.mapToGlobal(pos))
            # remove all traces
            if action == removeallAction:
                try:
                    for index in reversed(range(self.count())):
                        ident = self.item(index).data(Qt.UserRole)
                        self.parent.remove_artist(ident)
                except Exception as e:
                    print('Error when doing Remove All:', e)
            # remove an individual trace
            elif action == removeAction:
                try:
                    self.parent.remove_artist(ident)
                except Exception as e:
                    print('Remove Error:', e)
            # toggle log-scaling for x-axis
            elif action == logXaction:
                if self.parent.artists[ident].logModeX:
                    self.parent.artists[ident].artist.setLogMode(False, None)
                    self.parent.artists[ident].logModeX = False
                else:
                    self.parent.artists[ident].artist.setLogMode(True, None)
                    self.parent.artists[ident].logModeX = True
            # toggle log-scaling for y-axis
            elif action == logYaction:
                if self.parent.artists[ident].logModeY:
                    self.parent.artists[ident].artist.setLogMode(None, False)
                    self.parent.artists[ident].logModeY = False
                else:
                    self.parent.artists[ident].artist.setLogMode(None, True)
                    self.parent.artists[ident].logModeY = True
            # show parameters in a separate window
            elif action == parametersAction:
                dataset = self.parent.artists[ident].dataset
                pl = ParameterList(dataset)
                self.windows.append(pl)
                pl.show()
            # toggle the color of the trace
            elif action == togglecolorsAction:
                new_color = next(self.parent.colorChooser)
                if self.use_trace_color:
                    self.changeTraceListColor(ident, new_color)
                if self.parent.show_points:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbolBrush=new_color, symbol=None)
                else:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbol=None)
            # change the color of the trace
            elif action in colorActions:
                # get color index
                color_ind = colorActions.index(action)
                new_color = self.parent.colors[color_ind]
                if self.use_trace_color:
                    self.changeTraceListColor(ident, new_color)
                if self.parent.show_points:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbolBrush=new_color, symbol=None)
                else:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbol=None)
            # fit the selected artist/trace
            elif action == fitAction:
                dataset = self.parent.artists[ident].dataset
                index = self.parent.artists[ident].index
                fw = FitWindow(dataset, index, self)
                self.windows.append(fw)
                fw.show()
            # export the trace
            elif action == exportAction:
                # get datasets and index
                dataset = self.parent.artists[ident].dataset.data
                index = self.parent.artists[ident].index
                # get trace from dataset
                trace = dataset[:, (0, index + 1)]
                # export trace
                try:
                    trace_name = ident[1]
                    filename = QFileDialog.getSaveFileName(self, 'Save Dataset: ' + trace_name, getenv('HOME'), "CSV (*.csv)")
                    savetxt(filename[0], trace, delimiter=',')
                except Exception as e:
                    pass
