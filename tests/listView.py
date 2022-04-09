from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QListView

import sys
from random import randint

if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = QStandardItemModel()

    for n in range(10):
        item = QStandardItem('Item %s' % randint(1, 100))
        check = Qt.Checked if randint(0, 1) == 1 else Qt.Unchecked
        item.setCheckState(check)
        item.setCheckable(True)
        model.appendRow(item)

    view = QListView()
    view.setModel(model)
    view.show()
    app.exec_()
