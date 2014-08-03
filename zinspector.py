# zarafa-inspector: A GUI program which allows a user to examine MAPI properties in Zarafa and import and export data.
#
# Copyright 2014 Zarafa and contributors, license AGPLv3 (see LICENSE file for details)
#

#!/usr/bin/env python
from zinspectorlib import *

# PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import sys

import zarafa
from zarafa import Folder
from MAPI.Util import *
from MAPI.Tags import *

app = QApplication(sys.argv)
MainWindow = QMainWindow()
ui = Ui_MainWindow()

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

def openFolder(folder, associated = False):
    if associated:
        folder = folder.associated

    ui.recordtableWidget.hide()
    ui.propertytableWidget.clear()
    folder = folder.data(0, Qt.UserRole).toPyObject()
    recordlist = ui.recordlistView

    model = ItemListModel(MainWindow)
    model.addData(folder.items())
    recordlist.setModel(model)

    QObject.connect(recordlist,SIGNAL("clicked(QModelIndex)"), openRecord)    

    # Show MAPI properties of folder
    drawTable(folder.props())

def openRecord(index):
    item = index.model().data(index, role=Qt.ItemDataRole)
    ui.recordtableWidget.hide()

    drawTable(item.props())

def drawTable(properties):
    headers = ["Property", "Type", "Value"]
    propertytable = ui.propertytableWidget
    # Convert list of properties to [[prop, type, value]]
    data = []
    for prop in properties:
        data.append([prop.idname,prop.typename,prop.strval()])

    drawTableWidget(propertytable, headers, data)

def saveMBOX():
    current = ui.foldertreeWidget.currentItem()
    folder = current.data(0,Qt.UserRole).toPyObject()
    filename = QFileDialog.getSaveFileName(MainWindow, 'Save to MBOX', '.')

    if filename != '':
        # cast to string else mbox module breaks, since QString doesn't have endswith
        folder.mbox(str(filename))

def createFolder():
    current = ui.foldertreeWidget.currentItem()
    folder = current.data(0,Qt.UserRole).toPyObject()
    foldername, ok = QtGui.QInputDialog.getText(MainWindow, 'Create folder Dialog', 'New folder name:')
    if ok and foldername != '':
        mapifolder = folder.create_folder(str(foldername))
        newfolder = Folder(folder.store, mapifolder.GetProps([PR_ENTRYID], MAPI_UNICODE)[0].Value)
        item = QTreeWidgetItem(current, [foldername])
        item.setData(0, Qt.UserRole, newfolder)
        ui.foldertreeWidget.insertTopLevelItem(item,0)

def importEML():
    current = ui.foldertreeWidget.currentItem()
    folder = current.data(0,Qt.UserRole).toPyObject()
    filename = QFileDialog.getOpenFileName(MainWindow, 'Open EML', '.', "Emails (*.eml)")
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

def showHiddenItems():
    current = ui.foldertreeWidget.currentItem()
    openFolder(current, True)

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

def onFolderContext(point):
    menu = QMenu("Menu",ui.foldertreeWidget)
    menu.addAction("Export as MBOX",saveMBOX)
    menu.addAction("Create new folder",createFolder)
    menu.addAction("Import EML",importEML)
    menu.addAction("Hidden items",showHiddenItems)
    item = ui.foldertreeWidget.itemAt(point)
    record = item.data(0,Qt.UserRole).toPyObject()

    menu.exec_(ui.foldertreeWidget.mapToGlobal(point))

def openUserStore(tablewidgetitem):
    userEntry = ui.gabwidget.item(tablewidgetitem.row(), 0)
    user = server.user(userEntry.text())

    foldertree = ui.foldertreeWidget
    foldertree.clear()
    foldertree.itemClicked.connect(openFolder)

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

    # Setup contextmenu's
    """
    recordlist = ui.recordlistView
    recordlist.setContextMenuPolicy(Qt.CustomContextMenu)
    foldertree.setContextMenuPolicy(Qt.CustomContextMenu)
    recordlist.connect(ui.recordlistView, SIGNAL("customContextMenuRequested(QPoint)"),onRecordContext)
    foldertree.connect(foldertree, SIGNAL("customContextMenuRequested(QPoint)"),onFolderContext)
    """

    # Speed up recordlistwidget 
    #recordlist.setLayoutMode(QListWidget.Batched)
    #recordlist.updatesEnabled = False
    #recordlist.setUniformItemSizes(True)

def drawGAB(server, remoteusers=False):
    headers = ["name","fullname","email"]
    data = []
    for user in server.users(remote=remoteusers):
        data.append([getattr(user,prop) for prop in headers])
    drawTableWidget(ui.gabwidget,headers,data)

    ui.gabwidget.itemClicked.connect(openUserStore)
    # hide recordtableWidget by default
    ui.recordtableWidget.hide()

def drawTableWidget(table, header, data):
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

def drawStatsTable(statsTable):
    ui.tabWidget.setCurrentIndex(2)
    table = server.table(statsTable)
    drawTableWidget(ui.statstableWidget, table.header, table.data())

if __name__ == "__main__":
    ui.setupUi(MainWindow)

    # connect to server
    server = zarafa.Server()
    # Stats tab
    ui.actionUsers.triggered.connect(lambda: drawStatsTable(PR_EC_STATSTABLE_USERS))
    ui.actionSystem.triggered.connect(lambda: drawStatsTable(PR_EC_STATSTABLE_SYSTEM))
    ui.actionServers.triggered.connect(lambda: drawStatsTable(PR_EC_STATSTABLE_SERVERS))
    ui.actionSessions.triggered.connect(lambda: drawStatsTable(PR_EC_STATSTABLE_SESSIONS))
    ui.actionCompany.triggered.connect(lambda: drawStatsTable(PR_EC_STATSTABLE_COMPANY))
    drawGAB(server)
    MainWindow.show()
    sys.exit(app.exec_())
