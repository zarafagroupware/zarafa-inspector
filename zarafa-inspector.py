#!/usr/bin/env python
import sys

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import *
from PyQt5 import QtGui

import zarafa
from MAPI.Util import *
from MAPI.Util.Generators import *
import MAPI.Util.AddressBook
import MAPI.Tags
import _MAPICore

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

if __name__ == '__main__':
    options, args = zarafa.parser().parse_args()
    #server = zarafa.Server()

    # Start the app up
    app = QApplication(sys.argv)

    if options.auth_user and options.auth_pass:
        server = zarafa.Server(options) # Throw exception if it fails
    else:
        logindialog = LoginDialog()
        if logindialog.exec_() == QDialog.Accepted:
            server = logindialog.server
            # Load GUI
        else: # Login failed
            sys.exit(1)

