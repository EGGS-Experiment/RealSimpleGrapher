# imports
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

        self.name = 'pmt'
        self.initUI()

    def initUI(self):
        self.trace_dict = {}
        item = QListWidgetItem('Traces')
        item.setCheckState(Qt.Checked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)

    def addTrace(self, ident, color):
        item = QListWidgetItem(ident)

        if self.use_trace_color:
            foreground_color = self.parent.getItemColor(color)
            item.setForeground(foreground_color)
        else:
            item.setForeground(QColor(255, 255, 255))
        item.setBackground(QColor(0, 0, 0))

        item.setCheckState(Qt.Checked)
        self.addItem(item)
        self.trace_dict[ident] = item

    def removeTrace(self, ident):
        item = self.trace_dict[ident]
        row = self.row(item)
        self.takeItem(row)
        item = None

    def changeTraceListColor(self, ident, new_color):
        item = self.trace_dict[ident]
        color_dict = {"r": QColor(Qt.red).lighter(130),
                      "g": QColor(Qt.green),
                      "y": QColor(Qt.yellow),
                      "c": QColor(Qt.cyan),
                      "m": QColor(Qt.magenta).lighter(120),
                      "w": QColor(Qt.white)}
        item.setForeground(color_dict[new_color])

    def popupMenu(self, pos):
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
                for index in reversed(range(self.count())):
                    ident = str(self.item(index).text())
                    self.parent.remove_artist(ident)
            elif action == exportallAction:
                # get all datasets
                datasets_all = set()
                for index in range(self.count()):
                    ident = self.item(index).text()
                    dataset_tmp = self.parent.artists[ident].dataset
                    datasets_all.add(dataset_tmp)
                # export all datasets
                for dataset in datasets_all:
                    try:
                        filename = QFileDialog.getSaveFileName(self, 'Save Dataset: ' + dataset.dataset_name,
                                                               getenv('HOME'), "CSV (*.csv)")
                        savetxt(filename[0], dataset.data, delimiter=',')
                    except Exception as e:
                        pass
        else:
            ident = str(item.text())
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
            selectColorMenu = menu.addMenu("Select Color")
            colorActions = map(selectColorMenu.addAction, ["Red", "Green", "Yellow", "Cyan", "Magenta", "White"])
            colorCodes = ["r", "g", "y", "c", "m", "w"]
            colorActionDict = dict(zip(colorActions, colorCodes))

            # process actions
            action = menu.exec_(self.mapToGlobal(pos))
            if action == removeallAction:
                try:
                    for index in reversed(range(self.count())):
                        ident = str(self.item(index).text())
                        self.parent.remove_artist(ident)
                except Exception as e:
                    print('Remove All Error:', e)
            elif action == logXaction:
                if self.parent.artists[ident].logModeX:
                    self.parent.artists[ident].artist.setLogMode(False, None)
                    self.parent.artists[ident].logModeX = False
                else:
                    self.parent.artists[ident].artist.setLogMode(True, None)
                    self.parent.artists[ident].logModeX = True
            elif action == logYaction:
                if self.parent.artists[ident].logModeY:
                    self.parent.artists[ident].artist.setLogMode(None, False)
                    self.parent.artists[ident].logModeY = False
                else:
                    self.parent.artists[ident].artist.setLogMode(None, True)
                    self.parent.artists[ident].logModeY = True
            elif action == parametersAction:
                # option to show parameters in separate window
                dataset = self.parent.artists[ident].dataset
                pl = ParameterList(dataset)
                self.windows.append(pl)
                pl.show()
            elif action == togglecolorsAction:
                # option to change color of line
                new_color = next(self.parent.colorChooser)
                # self.parent.artists[ident].artist.setData(color=new_color, symbolBrush=new_color)
                self.parent.artists[ident].artist.setPen(new_color)
                if self.parent.show_points:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbolBrush=new_color, symbol=None)
                    self.changeTraceListColor(ident, new_color)
                else:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbol=None)
                    self.changeTraceListColor(ident, new_color)
            elif action == fitAction:
                dataset = self.parent.artists[ident].dataset
                index = self.parent.artists[ident].index
                fw = FitWindow(dataset, index, self)
                self.windows.append(fw)
                fw.show()
            elif action in colorActionDict.keys():
                new_color = colorActionDict[action]
                self.parent.artists[ident].artist.setPen(new_color)
                if self.parent.show_points:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbolBrush=new_color, symbol=None)
                    self.changeTraceListColor(ident, new_color)
                else:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbol=None)
                    self.changeTraceListColor(ident, new_color)
            elif action == removeAction:
                try:
                    self.parent.remove_artist(ident)
                except Exception as e:
                    print('Remove Error:', e)
            elif action == exportAction:
                # get datasets and index
                dataset = self.parent.artists[ident].dataset.data
                index = self.parent.artists[ident].index
                # get trace from dataset
                trace = dataset[:, (0, index + 1)]
                # export trace
                try:
                    filename = QFileDialog.getSaveFileName(self, 'Save Dataset: ' + ident, getenv('HOME'),
                                                           "CSV (*.csv)")
                    savetxt(filename[0], trace, delimiter=',')
                except Exception as e:
                    pass
