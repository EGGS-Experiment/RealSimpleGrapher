from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from RealSimpleGrapher.pyqtgraph_widgets import Graph_PyQtGraph


class ScrollingGraph_PyQtGraph(Graph_PyQtGraph):
    """
    todo: document
    """

    def __init__(self, reactor, name, parent=None, ylim=[0, 1], cxn=None, root=None):
        super().__init__(reactor, name, parent=parent, cxn=cxn, root=root)
        self.set_xlimits([0, 100])
        self.pointsToKeep = 100

    def update_figure(self, _input=None):
        for ident, params in self.artists.items():
            if params.shown:
                try:
                    index = params.index
                    x = params.dataset.data[:, 0]
                    y = params.dataset.data[:, index + 1]
                    params.artist.setData(x, y)
                except Exception as e:
                    pass

        try:
            mousepressed = QApplication.instance().MouseButton
            # a.mouseButtons()
            if mousepressed == (Qt.LeftButton or Qt.RightButton):
                return
                # see if we need to redraw
            xmin_cur, xmax_cur = self.current_limits
            x_cur = x[-1]  # current largest x value
            window_width = xmax_cur - xmin_cur
            # scroll if we've reached 75% of the window
            if x_cur > (xmin_cur + 0.75 * window_width) and (x_cur < xmax_cur):
                shift = (xmax_cur - xmin_cur) / 2.0
                xmin = xmin_cur + shift
                xmax = xmax_cur + shift
                self.set_xlimits([xmin, xmax])
        except Exception as e:
            pass


if __name__ == '__main__':
    from EGGS_labrad.clients import runClient
    import labrad
    cxn = labrad.connect()
    from RealSimpleGrapher.GUIConfig import graphConfig
    runClient(ScrollingGraph_PyQtGraph, graphConfig('example', isScrolling=True), cxn=cxn)
