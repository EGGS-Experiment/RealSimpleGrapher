# imports
# todo: requirements.txt
from os import _exit
from random import randrange
from socket import gethostname

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QApplication

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from GraphWindow import GraphWindow
from DataVaultListWidget import Dataset


class RSG_client(QMainWindow):
    """
    Client for the Real Simple Grapher.
    Doesn't require the RSG to be running at all.
    """

    name = gethostname() + " RSG Client"

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        # create random client ID
        self.ID = randrange(3e5, 1e6)
        self.cxn = cxn
        self.reactor = reactor
        self.setWindowTitle(self.name)
        self.servers = ['Data Vault', 'Parameter Vault']
        # initialization sequence
        d = self.connect()
        d.addCallback(self.initializeGUI)

    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad.
        """
        # create labrad connection
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            # set self name to rsg client + node name + number (if multiple)
            localname = gethostname() + ' ' + self.name
            self.cxn = yield connectAsync(LABRADHOST, name=localname)
        # try to get servers
        try:
            self.reg = self.cxn.registry
            self.pv = self.cxn.parameter_vault
            self.dv = self.cxn.data_vault
            #self.rsg = self.cxn.real_simple_grapher
        except Exception as e:
            print(e)
            raise
        # connect to signals
            # rsg signal
        # yield self.rsg.signal__plot_update(self.ID)
        # yield self.rsg.addListener(listener=self., source=None, ID=self.ID)
            # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)
        return self.cxn

    def initializeGUI(self, cxn):
        centralWidget = QWidget()
        layout = QHBoxLayout(centralWidget)

        # GUI creation needs to be here since the connection needs to be established
        self.gui = GraphWindow(self.reactor, cxn=self.cxn, root=self)
        self.gui.setWindowTitle('Real Simple Grapher - Client')
        self.gui.setWindowIcon(QIcon('rsg_icon.JPG'))
        layout.addWidget(self.gui)

        self.setCentralWidget(centralWidget)


    # SIGNALS
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            self.gui.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.gui.setEnabled(False)


    # PLOTTING
    def make_dataset(self, dataset_location):
        """
        Create and initialize a dataset object.
        Arguments:
            dataset_location    ([str]): the dataset directory location in the data vault.
        """
        cxt = self.cxn.context()
        ds = Dataset(self.dv, cxt, dataset_location, reactor)
        return ds

    def do_plot(self, dataset_location, graph, send_to_current):
        if (graph != 'current') and send_to_current:
            # add the plot to the Current tab as well as an additional
            # specified tab for later examination
            ds = self.make_dataset(dataset_location)
            # look in dict for existing
            # if same name but different loc, then add new
            self.gui.graphDict['current'].add_dataset(ds)
        ds = self.make_dataset(dataset_location)
        self.gui.graphDict[graph].add_dataset(ds)

    def plot_image(self, data, image_size, graph, name):
        self.gui.graphDict[graph].update_image(data, image_size, name)

    def plot_with_axis(self, c, dataset_location, graph, axis, send_to_current=True):
        minim, maxim = min(axis), max(axis)
        if (graph != 'current') and send_to_current:
            self.gui.graphDict['current'].set_xlimits([minim[minim.units], maxim[maxim.units]])
        self.gui.graphDict[graph].set_xlimits([minim[minim.units], maxim[maxim.units]])
        self.do_plot(dataset_location, graph, send_to_current)

    def close(self):
        _exit(0)


if __name__ == '__main__':
    # set up QApplication
    app = QApplication([])
    try:
        import qt5reactor
        qt5reactor.install()
    except Exception as e:
        print(e)
    # instantiate client with a reactor
    from twisted.internet import reactor
    client_tmp = RSG_client(reactor)
    # show gui
    client_tmp.showMaximized()
    # start reactor
    reactor.callWhenRunning(app.exec)
    reactor.addSystemEventTrigger('after', 'shutdown', client_tmp.close)
    reactor.runReturn()
    # close client on exit
    try:
        client_tmp.close()
    except Exception as e:
        print(e)
