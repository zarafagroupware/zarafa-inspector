from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, QSizePolicy

from widgets import Foldertree, ItemListView
from models import ItemListModel


class UserStore(QWidget):
    def __init__(self, parent = None, server = None):
        super(UserStore, self).__init__(parent)

        self.user = server.user(server.options.auth_user or server.auth_user)

        # Widgets
        self.foldertree = Foldertree.FolderTree(self, user=self.user)
        self.itemlist = ItemListView.ItemListView()
        self.propertywidget = QTableWidget()

        # Signals
        self.foldertree.itemClicked.connect(self.openFolder) # Or in foldertree? Hidden items???
        self.itemlist.clicked.connect(self.openRecord)

        # Layout
        vbox_layout = QHBoxLayout()
        vbox_layout.addWidget(self.foldertree)
        vbox_layout.addWidget(self.itemlist)
        vbox_layout.addWidget(self.propertywidget)
        self.setLayout(vbox_layout)

    def openFolder(self, folder): # TODO: handle associated?
        folder = folder.data(0, Qt.UserRole)
        model = ItemListModel.ItemListModel(self)
        model.addData(folder.items(), folder.count)
        self.itemlist.setModel(model)

        # View properties of folder
        self.propertywidget.setSortingEnabled(False)
        self.propertywidget.clear()
        headers = ["Property", "Type", "Value"]
        data = [(prop.strid ,prop.typename, prop.strval) for prop in folder.props()]
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


    def openRecord(self, index):
        # Seperate widget class?
        self.propertywidget.setSortingEnabled(False)
        item = index.model().data(index, role=Qt.ItemDataRole)
        self.propertywidget.clear()
        headers = ["Property", "Type", "Value"]
        data = [(prop.strid ,prop.typename, prop.strval) for prop in item.props()]
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
