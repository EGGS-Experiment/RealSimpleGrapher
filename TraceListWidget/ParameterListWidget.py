from twisted.internet.defer import inlineCallbacks
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget


class ParameterList(QWidget):
    """
    A window for visualizing dataset parameters.
    """

    def __init__(self, dataset):
        super(ParameterList, self).__init__()
        #self.setStyleSheet("background-color:%s;" % self.config.background_color)
        self.dataset = dataset
        mainLayout = QVBoxLayout(self)
        self.parameterListWidget = QListWidget()
        mainLayout.addWidget(self.parameterListWidget)
        self.setWindowTitle(str(dataset.dataset_name))
        self.populate()
        self.show()

    @inlineCallbacks
    def populate(self):
        parameters = yield self.dataset.getParameters()
        self.parameterListWidget.clear()
        self.parameterListWidget.addItems([str(x) for x in sorted(parameters)])
