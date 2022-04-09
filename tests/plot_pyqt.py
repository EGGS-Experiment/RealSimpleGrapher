# test plotting window in pyqtgraph
from pyqtgraph import PlotWidget

from np import linspace
from random import random
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication


class Graph(QWidget):

    def __init__(self, parent=None):
        super(Graph, self).__init__(parent)
        self.initUI()

    def initUI(self):
        x = linspace(0, 100, 100)
        y = [random() for k in x]
        y2 = [random() for k in x]
        self.pw = PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.pw)
        self.setLayout(layout)
        # self.pw = pg.plot([],[])
        self.legend = self.pw.addLegend()
        self.pw.setXRange(1, 503)
        self.pw.setYRange(-2, 2)
        p1 = self.pw.plot(x, y, pen='r', name='plot1')
        p2 = self.pw.plot(x, y2, pen='g', name='plot2')
        self.pw.removeItem(p2)
        self.legend.removeItem('plot2')


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main = Graph()
    main.show()
    sys.exit(app.exec_())
