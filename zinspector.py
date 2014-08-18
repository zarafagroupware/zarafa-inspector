#!/usr/bin/env python
# zarafa-inspector: A GUI program which allows a user to examine MAPI properties in Zarafa and import and export data.
#
# Copyright 2014 Zarafa and contributors, license AGPLv3 (see LICENSE file for details)
#

from zinspectorlib import *

# PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import sys

import zarafa
from zarafa import Folder
from MAPI.Util import *
from MAPI.Tags import *

class ItemListView(QListView):
    def __init__(self, parent, *args):
        super(ItemListView, self).__init__(parent, args)


class ItemListModel(QtCore.QAbstractListModel):
    # TODO: make the class more intelligent and use a generator
    numberPopulated = pyqtSignal(int)

    def __init__(self, parent=None):
        super(ItemListModel, self).__init__(parent)

        self.itemCount = 0
        self.itemList = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.itemCount

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() >= len(self.itemList) or index.row() < 0:
            return None

        if role == Qt.DisplayRole:
            item = self.itemList[index.row()]
            if not item.subject: 
                return 'Empty Subject'
            else:
                return item.subject

        if role == Qt.BackgroundRole:
            batch = (index.row() // 20) % 2
            if batch == 0:
                return qApp.palette().base()

            return qApp.palette().alternateBase()

        if role == Qt.ItemDataRole:
            return self.itemList[index.row()]

        return None

    def canFetchMore(self, index):
        return self.itemCount < len(self.itemList)

    def fetchMore(self, index):
        remainder = len(self.itemList) - self.itemCount
        itemsToFetch = min(20, remainder)

        self.beginInsertRows(QtCore.QModelIndex(), self.itemCount,
                self.itemCount + itemsToFetch)

        self.itemCount += itemsToFetch

        self.endInsertRows()

        self.numberPopulated.emit(itemsToFetch)

    def addData(self, items):
        self.itemList = list(items)
        self.itemCount = 0
        self.reset()

"""




def deleteItem():
    # select current item
    # TODO: update to new functionality
    recordlist = ui.recordlistView
    current = recordlist.currentItem()
    record = current.data(Qt.UserRole).toPyObject()

    # Fetch selected folder, since I folder can delete an Item and the Item doesn't need to have Item.folder or Item.store
    currentfolder = ui.foldertreeWidget.currentItem()
    folder = currentfolder.data(0,Qt.UserRole).toPyObject()
    folder.delete([record])

    item = recordlist.takeItem(recordlist.row(current))
    item = None

def saveEML():
    # TODO: update to new functionality
    current = ui.recordlistView.currentItem()
    record = current.data(Qt.UserRole).toPyObject()
    filename = QFileDialog.getSaveFileName(MainWindow, 'Save EML', '.', "Emails (*.eml)")

    if filename != '':
        rfc882 = record.eml()
        fname = open(filename, 'w')
        fname.write(rfc882)
        fname.close()

def saveAttachment():
    current = ui.recordtableWidget.currentItem()
    record = current.data(Qt.UserRole).toPyObject()

    filename = QFileDialog.getSaveFileName(MainWindow, 'Save Attachment', '.')
    if filename != '':
        fname = open(filename, 'w')
        fname.write(record.data)
        fname.close()

def onAttTableRow(point):
    menu = QMenu("Menu", ui.recordtableWidget)
    menu.addAction("Save attachment",saveAttachment)
    menu.exec_(ui.recordtableWidget.mapToGlobal(point))

def showAttachments():
    # TODO: update to new functionality
    current = ui.recordlistView.currentItem()
    record = current.data(Qt.UserRole).toPyObject()
    attTable = ui.recordtableWidget
    attTable.clear()

    attTable.setContextMenuPolicy(Qt.CustomContextMenu)
    attTable.connect(attTable, SIGNAL("customContextMenuRequested(QPoint)"),onAttTableRow)

    # Draw table
    attTable.setColumnCount(20)
    attTable.setRowCount(len(record.attachments()))
    attTable.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred))
    horHeaders = []
    for n, attachment in enumerate(record.attachments()):
        for m, prop in enumerate(attachment.props()):
            newitem = QTableWidgetItem(prop.strval())
            newitem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            newitem.setData(Qt.UserRole, attachment)
            attTable.setItem(n, m, newitem)
            if n == 0:
                # setHorizontalHeaderLabels doesn't handle python None, so append 'None'
                if prop.idname is None:
                    horHeaders.append('None')
                else:
                    horHeaders.append(prop.idname)

    attTable.setHorizontalHeaderLabels(horHeaders)
    attTable.resizeColumnsToContents()
    attTable.show()

def showRecipients():
    # TODO: update to new functionality
    current = ui.recordlistView.currentItem()
    record = current.data(Qt.UserRole).toPyObject()

    props = ['email','addrtype','name','entryid']
    data = []
    for recipient in record.recipients():
        data.append([getattr(recipient,prop) for prop in props])
    drawTableWidget(ui.recordtableWidget, props, data)

def onRecordContext(point):
    # TODO: update to new functionality
    menu = QMenu("Menu",ui.recordlistView)
    item = ui.recordlistView.itemAt(point)
    record = item.data(Qt.UserRole).toPyObject()

    if record.prop(PR_MESSAGE_CLASS).get_value().startswith('IPM.Note'):
        menu.addAction("Save as EML",saveEML)

    menu.addAction("Delete Item",deleteItem)

    if record.attachments():
        menu.addAction("View attachments",showAttachments)

    menu.addAction("View recipients",showRecipients)

    # Show the context menu.
    menu.exec_(ui.recordlistView.mapToGlobal(point))

"""

class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # set up User Interface (widgets, layout...)
        self.setupUi(self)

        # TODO: add option to select server
        # TODO: what if connection fails?
        self.server = zarafa.Server()

        # Stats tab
        self.actionUsers.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_USERS))
        self.actionSystem.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_SYSTEM))
        self.actionServers.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_SERVERS))
        self.actionSessions.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_SESSIONS))
        self.actionCompany.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_COMPANY))

        self.drawGAB()

    def drawStatsTable(self, statsTable):
        self.tabWidget.setCurrentIndex(2)
        table = self.server.table(statsTable)
        self.drawTableWidget(self.statstableWidget, table.header, table.data())

    def drawTableWidget(self, table, header, data):
        table.setRowCount(len(data))
        table.setColumnCount(len(header))

        for n, row in enumerate(data):
            for m, column in enumerate(row):
                newitem = QTableWidgetItem(str(column))
                newitem.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
                table.setItem(n, m, newitem)

        table.setHorizontalHeaderLabels(header)
        table.resizeColumnsToContents()
        table.show()

    def drawGAB(self):
        headers = ["name","fullname","email"]
        data = []
        for user in self.server.users():
            data.append([getattr(user,prop) for prop in headers])
        self.drawTableWidget(self.gabwidget,headers,data)

        self.gabwidget.itemClicked.connect(self.openUserStore)
        # hide recordtableWidget by default
        self.recordtableWidget.hide()

    def openUserStore(self, tablewidgetitem):
        userEntry = self.gabwidget.item(tablewidgetitem.row(), 0)
        user = self.server.user(userEntry.text())

        foldertree = self.foldertreeWidget
        foldertree.clear()
        foldertree.itemClicked.connect(self.openFolder)

        # Root of the tree TODO: add this to python-zarafa as in user.store.root
        rootnode = QTreeWidgetItem(foldertree, [user.name])
        rootnode.setData(0, Qt.UserRole, Folder(user.store, None))
        foldertree.parent = rootnode
        foldertree.setItemExpanded(foldertree.parent, True)

        folders = []
        for depth, folder in enumerate(user.store.folders(system=True,recurse=True)):
            # If folder.depth is not null, we must find the parent
            parent = foldertree.parent
            if folder.depth != 0:
                parentid = bin2hex(folder.prop(PR_PARENT_ENTRYID).get_value())
                for treewidget in folders:
                    treewidgetfolder = treewidget.data(0, Qt.UserRole).toPyObject()
                    if treewidgetfolder.entryid == parentid:
                        parent = treewidget
                        break

            item = QTreeWidgetItem(parent, [folder.name])
            item.setData(0, Qt.UserRole, folder)
            if folder.name == "IPM_SUBTREE":
                foldertree.setItemExpanded(item, True)

            folders.append(item)

        foldertree.setContextMenuPolicy(Qt.CustomContextMenu)
        foldertree.connect(foldertree, SIGNAL("customContextMenuRequested(QPoint)"), self.onFolderContext)

    def openFolder(self, folder, associated = False):

        self.recordtableWidget.hide()
        self.propertytableWidget.clear()
        folder = folder.data(0, Qt.UserRole).toPyObject()
        if associated:
            folder = folder.associated

        model = ItemListModel(self)
        model.addData(folder.items())
        self.recordlistView.setModel(model)

        QObject.connect(self.recordlistView, SIGNAL("clicked(QModelIndex)"), self.openRecord)    

        # Show MAPI properties of folder
        self.drawTable(folder.props())

    def onFolderContext(self, point):
        menu = QMenu("Menu", self.foldertreeWidget)
        menu.addAction("Export as MBOX", self.saveMBOX)
        menu.addAction("Create new folder", self.createFolder)
        #menu.addAction("Import EML", self.importEML) # TODO: enable once fixed
        menu.addAction("Hidden items", self.showHiddenItems)
        item = self.foldertreeWidget.itemAt(point)
        record = item.data(0,Qt.UserRole).toPyObject()

        menu.exec_(self.foldertreeWidget.mapToGlobal(point))

    def openRecord(self, index):
        item = index.model().data(index, role=Qt.ItemDataRole)
        self.recordtableWidget.hide()
        self.drawTable(item.props())

    def drawTable(self, properties):
        headers = ["Property", "Type", "Value"]
        propertytable = self.propertytableWidget
        # Convert list of properties to [[prop, type, value]]
        data = []
        for prop in properties:
            data.append([prop.idname,prop.typename,prop.strval()])

        self.drawTableWidget(propertytable, headers, data)

    def saveMBOX(self):
        current = self.foldertreeWidget.currentItem()
        folder = current.data(0,Qt.UserRole).toPyObject()
        filename = QFileDialog.getSaveFileName(self, 'Save to MBOX', '.')

        if filename != '':
            # cast to string else mbox module breaks, since QString doesn't have endswith
            folder.mbox(str(filename))

    def createFolder(self):
        current = self.foldertreeWidget.currentItem()
        folder = current.data(0, Qt.UserRole).toPyObject()
        foldername, ok = QtGui.QInputDialog.getText(self, 'Create folder Dialog', 'New folder name:')
        if ok and foldername != '':
            newfolder = folder.create_folder(str(foldername)) # TODO: cast to str really needed?
            item = QTreeWidgetItem(current, [foldername])
            item.setData(0, Qt.UserRole, newfolder)
            self.foldertreeWidget.insertTopLevelItem(0, item)

    def importEML(self):
        # TODO: update to new functionality
        """"
        current = self.foldertreeWidget.currentItem()
        folder = current.data(0,Qt.UserRole).toPyObject()
        filename = QFileDialog.getOpenFileName(self, 'Open EML', '.', "Emails (*.eml)")
        if filename != "":
            fname = open(filename, 'r')
            rfc822 = fname.read()
            fname.close()
            item = folder.create_item(eml=rfc822)
            listItem = QListWidgetItem()
            if item.subject is None:
                listItem.setText("<empty subject>")
            else:
                listItem.setText(item.subject)
            listItem.setData(Qt.UserRole, item)
            # ui.recordlistView.addItem(listItem)
            """

    def showHiddenItems(self):
        current = self.foldertreeWidget.currentItem()
        self.openFolder(current, True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())
