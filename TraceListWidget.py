# imports
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMenu

from FitWindowWidget import FitWindow
from ParameterListWidget import ParameterList
from DataVaultListWidget import DataVaultList
from PredictSpectrumWidget import PredictSpectrum

from GUIConfig import traceListConfig


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
        item.setForeground(self.parent.getItemColor(new_color))

    def popupMenu(self, pos):
        menu = QMenu()
        item = self.itemAt(pos)
        if item is None:
            dataaddAction = menu.addAction('Add Data Set')
            spectrumaddAction = menu.addAction('Add Predicted Spectrum')
            removeallAction = menu.addAction('Remove All Traces')
            exportallAction = menu.addAction('Export All Traces')

            # process actions
            action = menu.exec_(self.mapToGlobal(pos))
            if action == dataaddAction:
                dvlist = DataVaultList(self.parent.name, root=self.root)
                self.windows.append(dvlist)
                dvlist.show()
            elif action == spectrumaddAction:
                ps = PredictSpectrum(self)
                self.windows.append(ps)
                ps.show()
            elif action == removeallAction:
                for index in reversed(range(self.count())):
                    ident = str(self.item(index).text())
                    self.parent.remove_artist(ident)
            elif action == exportallAction:
                print('export all')
                #dataset = self.parent.artists[ident].dataset
                #da
        else:
            ident = str(item.text())
            parametersAction = menu.addAction('Parameters')
            togglecolorsAction = menu.addAction('Toggle colors')
            fitAction = menu.addAction('Fit')
            removeAction = menu.addAction('Remove')
            exportAction = menu.addAction('Export')
            # color menu
            selectColorMenu = menu.addMenu("Select color")
            redAction = selectColorMenu.addAction("Red")
            greenAction = selectColorMenu.addAction("Green")
            yellowAction = selectColorMenu.addAction("Yellow")
            cyanAction = selectColorMenu.addAction("Cyan")
            magentaAction = selectColorMenu.addAction("Magenta")
            whiteAction = selectColorMenu.addAction("White")
            colorActionDict = {redAction:"r", greenAction:"g", yellowAction:"y", cyanAction:"c", magentaAction:"m", whiteAction:"w"}

            # process actions
            action = menu.exec_(self.mapToGlobal(pos))
            if action == parametersAction:
                # option to show parameters in separate window
                dataset = self.parent.artists[ident].dataset
                pl = ParameterList(dataset)
                self.windows.append(pl)
                pl.show()
            elif action == togglecolorsAction:
                # option to change color of line
                new_color = self.parent.colorChooser.next()
                #self.parent.artists[ident].artist.setData(color=new_color, symbolBrush=new_color)
                self.parent.artists[ident].artist.setPen(new_color)
                if self.parent.show_points:
                    self.parent.artists[ident].artist.setData(pen=new_color, symbolBrush=new_color)
                    self.changeTraceListColor(ident, new_color)
                else:
                    self.parent.artists[ident].artist.setData(pen=new_color)
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
                    self.parent.artists[ident].artist.setData(pen=new_color, symbolBrush=new_color)
                    self.changeTraceListColor(ident, new_color)
                else:
                    self.parent.artists[ident].artist.setData(pen=new_color)
                    self.changeTraceListColor(ident, new_color)
            elif action == removeAction:
                self.parent.remove_artist(ident)
            elif action == exportAction:
                print('export')
                pass
