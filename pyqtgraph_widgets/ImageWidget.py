import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QGridLayout


class ImageWidget(QWidget):
    """
    An image widget.
    Used to display images.
    """

    def __init__(self, reactor, config, cxn=None, parent=None, root=None):
        super(ImageWidget, self).__init__(parent)
        self.reactor = reactor
        self.artists = {}
        self.should_stop = False
        self.name = config.name
        self.image_list = []
        self.image_index = 0
        # start UI
        self.initUI()

    def initUI(self):
        """
        todo: document
        """
        # create and configure plotItem
        self.plt = plt = pg.PlotItem()
        plt.showAxis('top')
        plt.hideAxis('bottom')
        plt.setAspectLocked(True)
        # add lines to plotItem
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        plt.addItem(self.vLine, ignoreBounds=True)
        plt.addItem(self.hLine, ignoreBounds=True)

        # create other widgets
        self.title = QLabel(self.name)
        self.next_button = QPushButton('>')
        self.prev_button = QPushButton('<')
        self.imv = pg.ImageView(view=self.plt)

        # lay out
        layout = QGridLayout(self)
        layout.addWidget(self.title,                0, 0)
        layout.addWidget(self.prev_button,          1, 0)
        layout.addWidget(self.next_button,          1, 1)
        layout.addWidget(self.imv,                  2, 0, 20, 2)

        # connect signals to slots
        self.next_button.clicked.connect(self.on_next)
        self.prev_button.clicked.connect(self.on_prev)
        self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)

    def update_image(self, data, image_size, name):
        """
        todo: document
        """
        image = data.reshape(image_size[0], image_size[1])
        if len(self.image_list) == 0:
            self.imv.setImage(image)
        else:
            self.imv.setImage(image, autoRange=False, autoLevels=False, autoHistogramRange=False)
        self.image_list.append([image, self.name + ' ' + name])
        self.image_index = len(self.image_list) - 1
        if len(self.image_list) > 100:
            del self.image_list[0]
        self.title.setText(self.name + ' ' + name)

    def on_next(self):
        """
        todo: document
        """
        try:
            if self.image_index < len(self.image_list) - 1:
                self.image_index += 1
                self.imv.setImage(self.image_list[self.image_index][0], autoRange=False, autoLevels=False,
                                  autoHistogramRange=False)
                self.title.setText(self.image_list[self.image_index][1])
        except Exception as e:
            print('Could not access index: ' + str(self.image_index))

    def on_prev(self):
        """
        todo: document
        """
        try:
            if self.image_index > 0:
                self.image_index -= 1
                self.imv.setImage(self.image_list[self.image_index][0], autoRange=False, autoLevels=False,
                                  autoHistogramRange=False)
                self.title.setText(self.image_list[self.image_index][1])
        except Exception as e:
            print('Could not access index: ' + str(self.image_index))

    def mouse_clicked(self, event):
        """
        Draws the cross at the position of a double click.
        """
        pos = event.pos()
        if self.plt.sceneBoundingRect().contains(pos) and event.double():
            # only on double clicks within bounds
            mousePoint = self.plt.vb.mapToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())


if __name__ == '__main__':
    from EGGS_labrad.clients import runClient
    import labrad
    cxn = labrad.connect()
    from RealSimpleGrapher.GUIConfig import graphConfig
    runClient(ImageWidget, graphConfig('example', isImages=True), cxn=cxn)
