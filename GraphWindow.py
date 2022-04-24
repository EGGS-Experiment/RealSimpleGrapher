"""
The main GUI which holds everything and puts everything together.
"""
import GUIConfig
from pyqtgraph_widgets import *
from PyQt5.QtWidgets import QWidget, QTabWidget, QGridLayout


class GridGraphWindow(QWidget):
    """
    Window containing a grid of graphs.
    Holds an individual RSG tab page.
    """

    def __init__(self, g_list, row_list, column_list, reactor, parent=None):
        super(GridGraphWindow, self).__init__(parent)
        self.reactor = reactor        
        self.initUI(g_list, row_list, column_list)
        self.show()

    def initUI(self, g_list, row_list, column_list):
        layout = QGridLayout()
        for k in range(len(g_list)):
            layout.addWidget(g_list[k], row_list[k], column_list[k])
        self.setLayout(layout)
        

class GraphWindow(QTabWidget):
    """
    The main RSG GUI which does nearly everything.
    Creates the RSG GUI from GUIConfig.py.
    Each tab is a GridGraphWindow object, which consists of _PyQtGraph objects.
    """

    def __init__(self, reactor, cxn=None, parent=None, root=None):
        """
        Initialize self variables and setup the GUI.
        """
        # initialize the PyQt object
        super(GraphWindow, self).__init__()
        # initialize self variables
        self.cxn = cxn
        self.parent = parent
        self.reactor = reactor
        self.root = root
        # initialize the UI
        self.initUI()
        # show the UI
        self.show()
        
    def initUI(self):
        reactor = self.reactor
        # create dictionaries to hold the graphs and tabs
        self.graphDict = {}
        self.tabDict = {}

        # create the individual tabs
        for gc in GUIConfig.tabs:
            # gcli = graph config list
            gcli = gc.config_list
            gli = []
            for config in gcli:
                name = config.name
                # max_ds = config.max_datasets
                if config.isScrolling:
                    graph_tmp = ScrollingGraph_PyQtGraph(config, reactor, cxn=self.cxn, root=self.root)
                elif config.isImages:
                    graph_tmp = ImageWidget(config, reactor)
                    self.graphDict[name] = graph_tmp
                    gli.append(graph_tmp)
                    continue
                elif config.isHist:
                    graph_tmp = Hist_PyQtGraph(config, reactor, cxn=self.cxn, root=self.root)
                    self.graphDict[name] = graph_tmp
                    gli.append(graph_tmp)
                    continue
                else:
                    graph_tmp = Graph_PyQtGraph(config, reactor, cxn=self.cxn, root=self.root)
                graph_tmp.set_ylimits(config.ylim)
                self.graphDict[name] = graph_tmp
                gli.append(graph_tmp)
            widget = GridGraphWindow(gli, gc.row_list, gc.column_list, reactor)
            self.tabDict[name] = widget
            self.addTab(widget, gc.tab)
            self.setMovable(True)

    def insert_tab(self, tab):
        graph_tmp = Graph_PyQtGraph(tab, self.reactor, cxn=self.cxn, root=self.root)
        self.graphDict[tab] = graph_tmp
        self.addTab(graph_tmp, tab)


if __name__ == '__main__':
    pass
    from EGGS_labrad.clients import runGUI
    #runGUI(GraphWindow)
