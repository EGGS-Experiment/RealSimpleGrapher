from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QFileDialog, QTreeWidget, QTreeWidgetItem

from .FitWindowWidget import FitWindow
from .ParameterListWidget import ParameterList
from .PredictSpectrumWidget import PredictSpectrum

from RealSimpleGrapher.GUIConfig import traceListConfig

from os import getenv
from numpy import savetxt


# todo: sort artists within a dataset
# todo: clicking on top item expands it
# todo: try setting background of qtreewidgetitem
# todo: ensureorder ok, otherwise traces won't get removed from graphwidget
# todo: missing traces not added
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
        #self.setStyleSheet("background-color:black; color:white;".format(self.config.background_color))
        #self.setStyleSheet("background-color:{:s};".format(self.config.background_color))
        # set up header
        header_labels = QTreeWidgetItem(None, ["Dataset Name", "Location"])
        header_labels.setForeground(0, QColor(0, 0, 0))
        header_labels.setForeground(1, QColor(0, 0, 0))
        header_labels.setBackground(0, QColor(0, 0, 0))
        header_labels.setBackground(1, QColor(0, 0, 0))
        #header_labels.setStyleSheet("background-color:white; color:black; border: 1px solid white;")
        self.setHeaderItem(header_labels)
        try:
            self.use_trace_color = self.config.use_trace_color
        except AttributeError as e:
            self.use_trace_color = False
            print('Error in init:', e)
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
            print('Error in tracelist.addDataset: dataset already added.')
            print('\tdataset_ident:', dataset_ident)
        else:
            ident_tmp = list(dataset_ident).reverse()
            dataset_item = QTreeWidgetItem(self, ident_tmp)
            dataset_item.setBackground(0, QColor(255, 255, 255))
            dataset_item.setForeground(0, QColor(0, 0, 0))
            dataset_item.setData(0, Qt.UserRole, dataset_ident)
            dataset_item.setExpanded(True)
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
            dataset_item = self.dataset_dict[dataset_ident]
            dataset_item.takeChildren()
            dataset_item = None

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
            artist_item = QTreeWidgetItem(dataset_item, [artist_ident[2]])
            artist_item.setData(0, Qt.UserRole, artist_ident)
            artist_item.setBackground(0, QColor(0, 0, 0))
            # set color of artist entry in tracelist
            if self.use_trace_color:
                artist_item.setForeground(0, color)
            else:
                artist_item.setForeground(0, QColor(255, 255, 255))
            artist_item.setCheckState(0, Qt.Checked)
            # add artist item
            dataset_item.addChild(artist_item)
            self.trace_dict[artist_ident] = artist_item
        except KeyError:
            print("Error in tracelist.addTrace: parent dataset doesn't exist")
            print("\tdataset_ident:", dataset_ident)
            # todo: create dataset item anyways

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
        # get artist_item (child) index from dataset_item (parent)
        artist_index = dataset_item.indexOfChild(artist_item)
        # remove child from parent
        dataset_item.takeChild(artist_index)

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
            pos     (todo): the position of the mouse click event.
        """
        menu = QMenu()
        item = self.itemAt(pos)
        # todo: remove artist before general
        # todo: make menu header
        # todo: add on later
        # clicked on nothing
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
                    ident = self.item(index).data(0, Qt.UserRole)
                    self.parent.remove_artist(ident)
            elif action == exportallAction:
                # get all datasets
                datasets_all = set()
                for index in range(self.count()):
                    ident = self.item(index).data(0, Qt.UserRole)
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
        # clicked on an item
        else:
            # clicked on artist_item
            if item.parent() is not None:
                artist_ident = item.data(0, Qt.UserRole)
                artist_params = self.parent.artists[artist_ident]
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
                if artist_params.logModeX:
                    logXaction.setChecked(True)
                logYaction = logAction.addAction('Y-axis')
                logYaction.setCheckable(True)
                if artist_params.logModeY:
                    logYaction.setChecked(True)
                # color menu
                selectColorMenu = menu.addMenu("Select Color")
                colorActions = list(map(selectColorMenu.addAction,
                                        ["Red", "Green", "Yellow", "Cyan", "Magenta", "White"]))
                # process actions
                action = menu.exec_(self.mapToGlobal(pos))
                # remove all traces
                if action == removeallAction:
                    # todo: implement
                    pass
                # remove an individual trace
                elif action == removeAction:
                    try:
                        self.parent.remove_artist(artist_ident)
                    except Exception as e:
                        print('Remove Error:', e)
                # toggle log-scaling for x-axis
                elif action == logXaction:
                    logx_state = not artist_params.logModeX
                    artist_params.artist.setLogMode(logx_state, None)
                # toggle log-scaling for y-axis
                elif action == logYaction:
                    logy_state = not artist_params.logModeY
                    artist_params.artist.setLogMode(None, logy_state)
                # show parameters in a separate window
                elif action == parametersAction:
                    dataset = artist_params.dataset
                    pl = ParameterList(dataset)
                    self.windows.append(pl)
                    pl.show()
                # toggle the color of the trace
                elif action == togglecolorsAction:
                    new_color = next(self.parent.colorChooser)
                    if self.use_trace_color:
                        self.changeTraceListColor(artist_ident, new_color)
                    if self.parent.show_points:
                        artist_params.artist.setData(pen=new_color, symbolBrush=new_color, symbol=None)
                    else:
                        artist_params.artist.setData(pen=new_color, symbol=None)
                # change the color of the trace
                elif action in colorActions:
                    # get color index
                    color_ind = colorActions.index(action)
                    new_color = self.parent.colors[color_ind]
                    if self.use_trace_color:
                        self.changeTraceListColor(artist_ident, new_color)
                    # todo: is this correct? parent has show_points? should it not be dataset_item?
                    if self.parent.show_points:
                        artist_params.artist.setData(pen=new_color, symbolBrush=new_color, symbol=None)
                    else:
                        artist_params.artist.setData(pen=new_color, symbol=None)
                # fit the selected artist/trace
                elif action == fitAction:
                    fw = FitWindow(artist_params.dataset, artist_params.index, self)
                    self.windows.append(fw)
                    fw.show()
                # export the trace
                elif action == exportAction:
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
            # clicked on dataset_item
            else:
                dataset_ident = item.data(0, Qt.UserRole)
                print('remove all: dataset ident:', dataset_ident)
                # create list of user actions in menu
                removeDatasetAction = menu.addAction('Remove Dataset')
                # process actions
                action = menu.exec_(self.mapToGlobal(pos))
                # remove all traces within the dataset
                if action == removeDatasetAction:
                    try:
                        self.parent.remove_dataset(dataset_ident)
                        # remove all child artists from the dataset
                        item.takeChildren()
                    except Exception as e:
                        print('Error when doing Remove Dataset:', e)
