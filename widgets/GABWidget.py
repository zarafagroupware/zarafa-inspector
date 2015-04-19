from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QMenu, QAction, QInputDialog, QVBoxLayout

class GABWidget(QWidget):
    def __init__(self, parent = None, server = None):
        super(GABWidget, self).__init__(parent)
        self.user = server.user(server.options.auth_user or server.auth_user)

        self.propertywidget = QTableWidget()
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.propertywidget)
        self.setLayout(vbox_layout)
        self.drawTable()

    def drawTable(self):
        self.propertywidget.setSortingEnabled(False)
        self.propertywidget.clear()
        headers = ["Property", "Type", "Value"]
        data = [(prop.strid ,prop.typename, prop.strval) for prop in self.user.props()]
        self.propertywidget.setRowCount(len(data))
        self.propertywidget.setColumnCount(len(headers))

        for n, row in enumerate(data):
            for m, column in enumerate(row):
                newitem = QTableWidgetItem()
                newitem.setData(Qt.EditRole, column)
                newitem.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                self.propertywidget.setItem(n, m, newitem)

        self.propertywidget.setHorizontalHeaderLabels(headers)
        self.propertywidget.resizeColumnsToContents()
        self.propertywidget.setSortingEnabled(True)
