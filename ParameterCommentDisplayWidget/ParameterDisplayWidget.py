from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QFileDialog, QTreeWidget, QTreeWidgetItem

from .FitWindowWidget import FitWindow
from .ParameterListWidget import ParameterList
from .PredictSpectrumWidget import PredictSpectrum

from RealSimpleGrapher.GUIConfig import traceListConfig

from os import getenv
from numpy import savetxt
# todo: set symbol


class TraceList(QTreeWidget):
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
        self.setColumnCount(2)
        # todo: fix header label coloring problem
        self.setHeaderLabels(["Dataset Name", "Location"])
        try:
            self.use_trace_color = self.config.use_trace_color
        except AttributeError as e:
            self.use_trace_color = False
            print('Error in tracelist.__init__:', e)
        self.initUI()

    def initUI(self):
        self.dataset_dict = {}
        self.trace_dict = {}
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)

    def addDataset(self, dataset_ident):
        """
        Adds a dataset header.
        Arguments:
            dataset_ident   (dataset_location, dataset_name): a unique identifier for a dataset.
        """
        if dataset_ident in self.dataset_dict.keys():
            print('Error in tracelist.addDataset: Dataset already exists.')
            print('\tdataset_ident:', dataset_ident)
        else:
            # create dataset header
            ident_tmp = list(dataset_ident)
            dataset_item = QTreeWidgetItem(self, ident_tmp[::-1])
            dataset_item.setExpanded(True)
            # store dataset_ident within dataset_item
            dataset_item.setData(0, Qt.UserRole, dataset_ident)
            # store header in self.dataset_dict
            self.dataset_dict[dataset_ident] = dataset_item

    def removeDataset(self, dataset_ident):
        """
        Removes a dataset header and all child traces.
        Arguments:
            dataset_ident   (dataset_location, dataset_name): a unique identifier for a dataset.
        """
        if dataset_ident not in self.dataset_dict.keys():
            print("Error in tracelist.removeDataset: dataset doesn't exist.")
            print('\tdataset_ident:', dataset_ident)
        else:
            dataset_item = self.dataset_dict.pop(dataset_ident, None)
            dataset_item.takeChildren()
            # remove dataset item from QTreeWidget
            dataset_item_index = self.indexOfTopLevelItem(dataset_item)
            self.takeTopLevelItem(dataset_item_index)
            # remove from parent
            self.parent.remove_dataset(dataset_ident)

    def addTrace(self, artist_ident, color):
        """
        Adds a trace to the TraceListWidget.
        Arguments:
            artist_ident    (dataset_location, dataset_name, artist_name): a unique identifier for an artist.
            color           Qt.Color: the color to set the trace.
        """
        dataset_ident = artist_ident[:2]
        # get dataset
        try:
            dataset_item = self.dataset_dict[dataset_ident]
            # create artist_item
            artist_item = QTreeWidgetItem(dataset_item, [artist_ident[2]])
            artist_item.setData(0, Qt.UserRole, artist_ident)
            artist_item.setBackground(0, QColor(0, 0, 0))
            artist_item.setCheckState(0, Qt.Checked)
            artist_item.setFirstColumnSpanned(True)
            # set color of artist entry in tracelist
            if self.use_trace_color:
                artist_item.setForeground(0, color)
            else:
                artist_item.setForeground(0, QColor(255, 255, 255))
            # add artist_item to dataset_item and holding dictionary
            dataset_item.addChild(artist_item)
            self.trace_dict[artist_ident] = artist_item
            dataset_item.sortChildren(0, Qt.AscendingOrder)
        except KeyError:
            print("Error in tracelist.addTrace: parent dataset doesn't exist")
            print("\tdataset_ident:", dataset_ident)

    def removeTrace(self, artist_ident):
        """
        Removes a trace from the TraceListWidget.
        Arguments:
            artist_ident   (dataset_location, dataset_name, artist_name): a unique identifier for an artist.
        """
        # get objects
        dataset_ident = artist_ident[:2]
        dataset_item = self.dataset_dict[dataset_ident]
        artist_item = self.trace_dict[artist_ident]
        # remove child from dataset_item
        artist_index = dataset_item.indexOfChild(artist_item)
        dataset_item.takeChild(artist_index)
        # remove artist_item from parent graphwidget
        self.parent.remove_artist(artist_ident)
        # remove parent dataset if empty
        if dataset_item.childCount() == 0:
            self.removeDataset(dataset_ident)

    def changeTraceListColor(self, artist_ident, new_color):
        """
        Changes the color of a trace.
        """
        artist_item = self.trace_dict[artist_ident]
        artist_item.setForeground(0, new_color)

    def popupMenu(self, pos):
        """
        Manages the pop-up menu that happens upon a right-click.
        Arguments:
            pos: the position of the mouse click event.
        """
        # set up menu
        menu = QMenu()
        actionDict = {}
        item = self.itemAt(pos)

        # values
        dataset_ident, artist_ident, artist_params = None, None, None

        # permanent options
        actionDict['removeAllAction'] = menu.addAction('Remove All Traces')
        actionDict['exportAllAction'] = menu.addAction('Export All Traces')
        actionDict['spectrumAddAction'] = menu.addAction('Add Predicted Spectrum')

        # clicked on an item
        if item is not None:
            # dataset or trace actions
            actionDict['parametersAction'] = menu.addAction('Parameters')
            actionDict['toggleColorsAction'] = menu.addAction('Toggle Colors')
            actionDict['removeDatasetAction'] = menu.addAction('Remove Dataset')
            # clicked on artist_item
            if item.parent() is not None:
                artist_ident = item.data(0, Qt.UserRole)
                artist_params = self.parent.artists[artist_ident]
                dataset_ident = artist_ident[:2]

                # trace-specific functions
                actionDict['fitAction'] = menu.addAction('Fit')
                actionDict['removeAction'] = menu.addAction('Remove')
                actionDict['exportAction'] = menu.addAction('Export')
                selectColorMenu = menu.addMenu("Select Color")
                actionDict['selectColorMenu'] = selectColorMenu
                # log mode
                logAction = menu.addMenu('Set Log Mode')
                logXAction = logAction.addAction('X-axis')
                logYAction = logAction.addAction('Y-axis')
                # configure submenus
                actionDict['logXAction'] = logXAction
                logXAction.setCheckable(True)
                if artist_params.logModeX:
                    logXAction.setChecked(True)
                actionDict['logYAction'] = logYAction
                logYAction.setCheckable(True)
                if artist_params.logModeY:
                    logYAction.setChecked(True)
                # color menu
                actionDict['colorActions'] = list(map(selectColorMenu.addAction,
                                                      ["Red", "Green", "Yellow", "Cyan", "Magenta", "White"]))
            # clicked on a dataset
            else:
                dataset_ident = item.data(0, Qt.UserRole)

        # process actions
        action = menu.exec_(self.mapToGlobal(pos))
        try:
            if action == actionDict.get('spectrumAddAction'):
                ps = PredictSpectrum(self)
                self.windows.append(ps)
                ps.show()
            elif action == actionDict.get('removeAllAction'):
                # remove all artists/traces
                # todo: maybe should be reverse?
                for index in range(self.topLevelItemCount()):
                    dataset_item = self.topLevelItem(index)
                    ident = dataset_item.data(0, Qt.UserRole)
                    self.removeDataset(ident)
            elif action == actionDict.get('exportAllAction'):
                # get all datasets
                datasets_all = set()
                for index in range(self.topLevelItemCount()):
                    ident = self.topLevelItem(index).data(0, Qt.UserRole)
                    dataset_tmp = self.parent.artists[ident].dataset
                    datasets_all.add(dataset_tmp)
                # export all datasets
                for dataset in datasets_all:
                    try:
                        filename = QFileDialog.getSaveFileName(self, 'Save Dataset: ' + dataset.dataset_name,
                                                               getenv('HOME'), "CSV (*.csv)")
                        savetxt(filename[0], dataset.data, delimiter=',')
                    except Exception as e:
                        print("Error in tracelist.exportAllAction:", e)
            # remove an individual trace
            elif action == actionDict.get('removeAction'):
                self.removeTrace(artist_ident)
            # toggle log-scaling for x-axis
            elif action == actionDict.get('logXAction'):
                logx_state = not artist_params.logModeX
                artist_params.artist.setLogMode(logx_state, None)
            # toggle log-scaling for y-axis
            elif action == actionDict.get('logYAction'):
                logy_state = not artist_params.logModeY
                artist_params.artist.setLogMode(None, logy_state)
            # show parameters in a separate window
            elif action == actionDict.get('parametersAction'):
                dataset = artist_params.dataset
                pl = ParameterList(dataset)
                self.windows.append(pl)
                pl.show()
            # toggle the color of the trace
            elif action == actionDict.get('toggleColorsAction'):
                new_color = next(self.parent.colorChooser)
                if self.use_trace_color:
                    self.changeTraceListColor(artist_ident, new_color)
                if self.parent.show_points:
                    artist_params.artist.setData(pen=new_color, symbolBrush=new_color, symbol=None)
                else:
                    artist_params.artist.setData(pen=new_color, symbol=None)
            # change the color of the trace
            elif action in actionDict.get('colorActions', []):
                # get color index
                color_ind = actionDict.get('colorActions').index(action)
                new_color = self.parent.colorList[color_ind]
                if self.use_trace_color:
                    self.changeTraceListColor(artist_ident, new_color)
                if self.parent.show_points:
                    artist_params.artist.setData(pen=new_color, symbolBrush=new_color, symbol=None)
                else:
                    artist_params.artist.setData(pen=new_color, symbol=None)
            # fit the selected artist/trace
            elif action == actionDict.get('fitAction'):
                fw = FitWindow(artist_params.dataset, artist_params.index, self)
                self.windows.append(fw)
                fw.show()
            # export the trace
            elif action == actionDict.get('exportAction'):
                # get datasets and index
                index = artist_params.index
                trace = artist_params.dataset.data[:, (0, index + 1)]
                # export trace
                try:
                    trace_name = artist_ident[1]
                    filename = QFileDialog.getSaveFileName(self, 'Save Dataset: ' + trace_name, getenv('HOME'), "CSV (*.csv)")
                    savetxt(filename[0], trace, delimiter=',')
                except Exception as e:
                    print('Error during export:', e)
            # remove all traces within the dataset
            elif action == actionDict.get('removeDatasetAction'):
                # remove all child artists from the dataset
                try:
                    self.removeDataset(dataset_ident)
                except Exception as e:
                    print('Error in tracelist.removeDatasetAction:', e)
        except KeyError as e:
            pass
