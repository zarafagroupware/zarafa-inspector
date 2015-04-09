from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout

from widgets import Foldertree, ItemListView
from models import ItemListModel


class UserStore(QWidget):
    def __init__(self, parent = None, server = None):
        super(UserStore, self).__init__(parent)

        self.user = server.user(server.options.auth_user or server.auth_user)

        # Widgets
        self.foldertree = Foldertree.FolderTree(self, user=self.user)
        self.itemlist = ItemListView.ItemListView()

        # Signals
        self.foldertree.itemClicked.connect(self.openFolder) # Or in foldertree?

        # Layout
        vbox_layout = QHBoxLayout()
        vbox_layout.addWidget(self.foldertree)
        vbox_layout.addWidget(self.itemlist)
        parent.setLayout(vbox_layout)

    def openFolder(self, folder): # TODO: handle associated?
        folder = folder.data(0, Qt.UserRole)
        model = ItemListModel.ItemListModel(self)
        model.addData(folder.items(), folder.count)
        self.itemlist.setModel(model)
