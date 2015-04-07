#!/usr/bin/env python
import sys

from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import *
from PyQt5 import QtGui

import zarafa
from MAPI.Util import *
from MAPI.Util.Generators import *
import MAPI.Util.AddressBook
import MAPI.Tags
import _MAPICore

# FIXME: move to seperate file
class FolderTree(QTreeWidget):
    def __init__(self, parent = None, user = None):
        super(FolderTree, self).__init__(parent)

        self.header().setHidden(True)
        self.folders = user.store.folders()

        rootnode = QTreeWidgetItem(self, [user.name])
        rootnode.setData(0, Qt.UserRole, user.store.root)
        self.parent = rootnode
        self.expandItem(rootnode)

        # Draw folder hierachy
        folders = {}
        for folder in user.store.folders(system=True, recurse=True): # XXX: configureable?
            # FIXME: performance / cleaner method without temp dict
            if folder.depth != 0:
                parentid = folder.parent.entryid
                if folders[parentid]:
                    parent = folders[parentid]
            else:
                parent = self.parent

            item = QTreeWidgetItem(parent, [folder.name])
            item.setData(0, Qt.UserRole, folder)
            folders[folder.entryid] = item

# FIXME: move to seperate file
class LoginDialog(QDialog):
    def __init__(self, parent = None):
        super(LoginDialog, self).__init__(parent)

        self.textName = QLineEdit(self)
        self.textPass = QLineEdit(self)
        self.textServer = QLineEdit(self)
        self.buttonLogin = QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)

        form = QFormLayout()
        form.addRow(QLabel('Login' , self), self.textName)
        form.addRow(QLabel('Password' , self), self.textPass)
        form.addRow(QLabel('Server' , self), self.textServer)

        form.addRow(self.buttonLogin)
        self.setLayout(form)

        self.setWindowTitle("Login")
        self.show()

    def handleLogin(self):
        try:
            self.zarafa_server = zarafa.Server(auth_user=self.textName.text(), auth_pass=self.textPass.text(), server_socket=self.textServer.text())
            self.accept()
        except MAPI.Struct.MAPIErrorLogonFailed: # TODO: handle invalid Server
            QMessageBox.warning(self, 'Error', 'Bad user or password or wrong server')

    @property
    def server(self):
        return self.zarafa_server


class ZarafaInspector(QMainWindow):
    def __init__(self, server):
        super(ZarafaInspector, self).__init__()
        self.server = server # Zarafa server object
        self.initUI()

    def initUI(self):
        close_action = QAction('Close', self)
        close_action.setShortcut('Ctrl+Q')
        close_action.setStatusTip('Close Zarafa Inspector')
        close_action.triggered.connect(self.close)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&file')
        file_menu.addAction(close_action)

        # QtabWidget
        # TAB1: GAB => show user details and maybe GAB?
        # TAB2: FolderTree | QListView | QTableWidget

        # FIXME in seperate widget?
        self.tabwidget = QTabWidget()
        self.setCentralWidget(self.tabwidget)
        self.tab1 = QWidget()

        # User Store
        self.tab2 = QWidget()
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(FolderTree(user = server.user(server.options.auth_user)))
        self.tab2.setLayout(vbox_layout)
        self.tabwidget.addTab(self.tab1, "GAB")
        self.tabwidget.addTab(self.tab2, "User Store")

        # FIXME: If not SYSTEM
        self.tabwidget.setCurrentIndex(1)

        self.resize(1024, 768)
        self.setWindowTitle('Zarafa Inspector')
        self.show()

if __name__ == '__main__':
    options, args = zarafa.parser().parse_args()
    #server = zarafa.Server()

    # Start the app up
    app = QApplication(sys.argv)

    if options.auth_user and options.auth_pass: # TODO: SYSTEM user?
        server = zarafa.Server(options) # Throw exception if it fails
        inspector = ZarafaInspector(server) # Refactor in one if?
    else:
        logindialog = LoginDialog()
        if logindialog.exec_() == QDialog.Accepted:
            server = logindialog.server

            # Load GUI
            inspector = ZarafaInspector(server)

        else: # Login failed
            sys.exit(1)
    sys.exit(app.exec_())

