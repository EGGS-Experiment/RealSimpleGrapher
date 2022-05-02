"""
Contains helper objects used by the pyqtgraph widgets
to create and store traces.
"""
from itertools import cycle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class artistParameters:
    """
    todo: document
    Arguments:
        artist: the PlotLine object used to create traces on the pyqtgraph.
        dataset: the Dataset object which provides data for the artist.
        index: holds the dimension of data to receive from the dataset when the dataset has multiple artists.
        shown:
    """

    def __init__(self, artist, dataset, index, shown):
        self.artist = artist
        self.dataset = dataset
        self.index = index
        self.shown = shown
        # last_update: update counter in the Dataset object, only
        # redraws if the dataset has a higher update count
        self.last_update = 0
        # lodModeX/Y: keeps track of log mode
        self.logModeX = False
        self.logModeY = False


"""
Used to cycle through colors for the traces.
"""
colorList = [
    QColor(Qt.red).lighter(130),
    QColor(Qt.green),
    QColor(Qt.yellow),
    QColor(Qt.cyan),
    QColor(Qt.magenta).lighter(120),
    QColor(Qt.white)
]
