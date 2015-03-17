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
from MAPI.Tags import *

class ItemListView(QListView):
    '''
    ItemListView class

    Used to draw a QListView with MAPI objects and provides a number of operations
    on a MAPI object.
    '''

    def __init__(self, parent=None):
        super(ItemListView, self).__init__(parent)
        self.parent = self.parent()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.onRecordContext)

    def onRecordContext(self, point):
        index = self.indexAt(point)
        record = self.model().data(index, Qt.ItemDataRole)

        menu = QMenu("Menu",self)

        if record.prop(PR_MESSAGE_CLASS).get_value().startswith('IPM.Note'):
            menu.addAction("Save as EML", self.saveEML)
        if record.prop(PR_MESSAGE_CLASS).get_value().startswith('IPM.Contact'):
            menu.addAction("Save as vcard", self.saveVCF)
        # FIXME: Add export to ics item?

        menu.addAction("Delete Item", self.deleteItem)

        if record.attachments():
            menu.addAction("View attachments", self.showAttachments)

        menu.addAction("View recipients", self.showRecipients)

        # Show the context menu.
        menu.exec_(self.mapToGlobal(point))

    def showAttachments(self):
        # TODO: probably nicer to split this widget in a seperate class?
        current = self.currentIndex()
        record = self.model().data(current, Qt.ItemDataRole)

        attTable = self.parent.recordtableWidget
        attTable.clear()

        attTable.setContextMenuPolicy(Qt.CustomContextMenu)
        attTable.connect(attTable, SIGNAL("customContextMenuRequested(QPoint)"), self.onAttTableRow)

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

    def showRecipients(self):
        current = self.currentIndex()
        record = self.model().data(current, Qt.ItemDataRole)

        props = ['email','addrtype','name','entryid']
        data = [(getattr(recipient,prop) for prop in props) for recipient in record.recipients()]
        self.parent.drawTableWidget(self.parent.recordtableWidget, props, data)

    def deleteItem(self): # TODO: provide multi-select and removal
        current = self.currentIndex()
        record = self.model().data(current, Qt.ItemDataRole)

        # Fetch selected folder, since I folder can delete an Item and the Item doesn't need to have Item.folder or Item.store
        # TODO: record.folder?
        currentfolder = self.parent.foldertreeWidget.currentItem()
        folder = currentfolder.data(0, Qt.UserRole).toPyObject()
        folder.delete([record])

        self.model().removeItems([self.currentIndex().row()])

    def saveVCF(self):
        current = self.currentIndex()
        record = self.model().data(current, Qt.ItemDataRole)
        filename = QFileDialog.getSaveFileName(self.parent, 'Save vcard', '.', "Vcard (*.vcf,*.vcard)")

        if filename != '':
            fname = open(filename, 'w')
            fname.write(record.vcf())
            fname.close()


    def saveEML(self):
        current = self.currentIndex()
        record = self.model().data(current, Qt.ItemDataRole)
        filename = QFileDialog.getSaveFileName(self.parent, 'Save EML', '.', "Emails (*.eml)")

        if filename != '':
            rfc882 = record.eml()
            fname = open(filename, 'w')
            fname.write(rfc882)
            fname.close()

    def saveAttachment(self):
        current = self.parent.recordtableWidget.currentItem()
        record = current.data(Qt.UserRole).toPyObject()

        filename = QFileDialog.getSaveFileName(self.parent, 'Save Attachment', '.')
        if filename != '':
            fname = open(filename, 'w')
            fname.write(record.data)
            fname.close()

    def onAttTableRow(self, point):
        menu = QMenu("Menu", self.parent.recordtableWidget)
        menu.addAction("Save attachment", self.saveAttachment)
        menu.exec_(self.parent.recordtableWidget.mapToGlobal(point))

class ItemListModel(QtCore.QAbstractListModel):
    '''
    class ItemListModel

    Model which contains MAPI Objects from a MAPI Folder used by the ItemListView
    '''

    def __init__(self, parent=None):
        super(ItemListModel, self).__init__(parent)

        # Total items in the folder
        self.totalItems = 0
        # Total items which are displayed
        self.itemCount = 0
        # Items to be removed
        self.removalList = []
        # Items which are displayed
        self.itemList = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.itemCount

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() < 0:
            return None

        # If requisted row is bigger then we have and in range of total items, fetch it from the generator
        if index.row() >= len(self.itemList) and index.row() <= self.totalItems:
            try:
                tmp = self.itemGenerator.next()
            except StopIteration: # reached end of generator
                return None

            for remove_item in self.removalList:
                if tmp.sourcekey == remove_item.sourcekey:
                    self.removalList.remove(remove_item)
                    break
            self.itemList.append(tmp)

        if role == Qt.DisplayRole:
            item = self.itemList[index.row()]
            if not item.subject:
                return 'Empty Subject'
            else:
                return item.subject

        if role == Qt.ItemDataRole:
            return self.itemList[index.row()]

        return None

    def canFetchMore(self, index):
        return self.itemCount < self.totalItems

    def fetchMore(self, index):
        remainder = self.totalItems - self.itemCount
        itemsToFetch = min(20, remainder)

        self.beginInsertRows(QtCore.QModelIndex(), self.itemCount, self.itemCount + itemsToFetch)
        self.itemCount += itemsToFetch
        self.endInsertRows()

    def addData(self, items, total):
        self.itemGenerator = items # The generator Folder.items()
        self.totalItems = total

        self.itemList = [self.itemGenerator.next() for _ in xrange(0, min(20, total))]

        self.itemCount = 0
        self.reset()

    def addItems(self, items):
        self.beginInsertRows(QtCore.QModelIndex(), 0, len(items))
        [self.itemList.insert(0, item) for item in items]
        self.endInsertRows()
        self.itemCount = self.itemCount + len(items)
        self.totalItems = self.totalItems + len(items)

    def removeItemObjects(self, items):
        for item in items:
            for index, listitem in enumerate(self.itemList):
                if item.sourcekey == listitem.sourcekey:
                    self.beginRemoveRows(QtCore.QModelIndex(), index, index)
                    del self.itemList[index]
                    self.itemCount = self.itemCount - 1
                    self.totalItems = self.totalItems - 1
                    self.endRemoveRows()
                    break

    def removeItems(self, items):
        for index in items:
            self.beginRemoveRows(QtCore.QModelIndex(), index, index)
            del self.itemList[index]
            self.itemCount = self.itemCount - 1
            self.totalItems = self.totalItems - 1
            self.endRemoveRows()

class MyMainWindow(QMainWindow, Ui_MainWindow):
    '''
    class MyMainWindow

    Main GUI component which renders the whole Zarafa-Inspector

    '''

    def __init__(self, server):
        QMainWindow.__init__(self)

        # set up User Interface (widgets, layout...)
        self.setupUi(self)

        self.server = server

        # Stats tab. FIXME: Not possible with usersession
        self.actionUsers.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_USERS))
        self.actionSystem.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_SYSTEM))
        self.actionServers.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_SERVERS))
        self.actionSessions.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_SESSIONS))
        self.actionCompany.triggered.connect(lambda: self.drawStatsTable(PR_EC_STATSTABLE_COMPANY))

        # Recordlist
        self.recordlist = ItemListView(self)
        # TODO: check if sizePolicy can be cleaner
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.recordlist.sizePolicy().hasHeightForWidth())
        self.recordlist.setSizePolicy(sizePolicy)
        self.horizontalLayout.insertWidget(1, self.recordlist)
        QObject.connect(self.recordlist, SIGNAL("clicked(QModelIndex)"), self.openRecord)

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
                newitem = QTableWidgetItem()
                if column is None: # FIXME: named properties should be shown
                    column = str(column)
                newitem.setData(Qt.EditRole, column)
                newitem.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
                table.setItem(n, m, newitem)

        table.setHorizontalHeaderLabels(header)
        table.resizeColumnsToContents()
        table.setSortingEnabled(True)
        table.show()

    def drawGAB(self):
        headers = ["name", "fullname", "email", "active", "home_server"]
        # user session
        if self.server.options.auth_user and self.server.options.auth_pass:
            users = [self.server.user(self.server.options.auth_user)]
        else:
            users = self.server.users()
        data = [([getattr(user,prop) for prop in headers]) for user in users]
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

        rootnode = QTreeWidgetItem(foldertree, [user.name])
        rootnode.setData(0, Qt.UserRole, user.store.root)
        foldertree.parent = rootnode
        foldertree.setItemExpanded(foldertree.parent, True)

        folders = {} # Use hashmap instead of list for faster access
        for depth, folder in enumerate(user.store.folders(system=True,recurse=True)):
            # If folder.depth is not null, we must find the parent
            parent = foldertree.parent
            if folder.depth != 0:
                parentid = folder.parent.entryid
                if folders[parentid]:
                    parent = folders[parentid]

            item = QTreeWidgetItem(parent, [folder.name])
            item.setData(0, Qt.UserRole, folder)
            if folder.name == 'IPM_SUBTREE':
                foldertree.setItemExpanded(item, True)

            folders[folder.entryid] = item

        foldertree.setContextMenuPolicy(Qt.CustomContextMenu)
        foldertree.connect(foldertree, SIGNAL("customContextMenuRequested(QPoint)"), self.onFolderContext)

    # ICS update
    def update(self, item, flags):
        self.recordlist.model().addItems([item])

    # ICS delete, not implemented
    def delete(self, item, flags):
        listitem = [listitem for listitem in self.recordlist.model().itemList if listitem.sourcekey == item.sourcekey]
        if listitem:
            self.recordlist.model().removeItemObjects(listitem)
        else:
            # Item does not exists or is still in the generator
            self.recordlist.model().removalList.append(item)


    def updateFolder(self):
        # Sync with ICS
        folder_state = self.folder_state
        new_state = self.folder.sync(self, folder_state) # from last known state
        if new_state != folder_state:
            self.folder_state = new_state

    def openFolder(self, folder, associated = False):
        self.recordtableWidget.hide()
        self.propertytableWidget.clear()
        folder = folder.data(0, Qt.UserRole).toPyObject()
        if associated:
            folder = folder.associated

        model = ItemListModel(self)
        model.addData(folder.items(), folder.count)
        self.recordlist.setModel(model)

        # hooking ICS for new items
        self.folder = folder
        self.folder_state = folder.state

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateFolder)
        self.timer.start(1000) # 5 seconds
         
        # Show MAPI properties of folder
        self.drawTable(folder.props())

    def onFolderContext(self, point):
        menu = QMenu("Menu", self.foldertreeWidget)
        menu.addAction("Export as MBOX", self.saveMBOX)
        menu.addAction("Export as Maildir", self.saveMaildir)
        menu.addAction("Create new folder", self.createFolder)
        menu.addAction("Import EML", self.importEML) # TODO: enable once fixed
        menu.addAction("Hidden items", self.showHiddenItems)
        item = self.foldertreeWidget.itemAt(point)
        record = item.data(0, Qt.UserRole).toPyObject()

        menu.exec_(self.foldertreeWidget.mapToGlobal(point))

    def openRecord(self, index):
        item = index.model().data(index, role=Qt.ItemDataRole)
        self.recordtableWidget.hide()
        self.drawTable(item.props())

    def drawTable(self, properties):
        headers = ["Property", "Type", "Value"]
        propertytable = self.propertytableWidget
        # Convert list of properties to [[prop, type, value]]
        data = [(prop.idname or '',prop.typename,prop.strval()) for prop in properties]

        self.drawTableWidget(propertytable, headers, data)

    def saveMBOX(self):
        current = self.foldertreeWidget.currentItem()
        folder = current.data(0, Qt.UserRole).toPyObject()
        filename = QFileDialog.getSaveFileName(self, 'Save to MBOX', '.')

        if filename:
            # cast to string else mbox module breaks, since QString doesn't have endswith
            folder.mbox(str(filename))

    def saveMaildir(self):
        current = self.foldertreeWidget.currentItem()
        folder = current.data(0, Qt.UserRole).toPyObject()
        path = QFileDialog.getExistingDirectory(self, 'Specify folder to save Maildir', '.', QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

        if path != '':
            # cast to string else maildir module breaks, since QString doesn't have endswith
            folder.maildir(str(path))

    def createFolder(self):
        current = self.foldertreeWidget.currentItem()
        folder = current.data(0, Qt.UserRole).toPyObject()
        foldername, ok = QInputDialog.getText(self, 'Create folder Dialog', 'New folder name:')
        if ok and foldername != '':
            newfolder = folder.create_folder(str(foldername)) # TODO: cast to str really needed?
            item = QTreeWidgetItem(current, [foldername])
            item.setData(0, Qt.UserRole, newfolder)
            self.foldertreeWidget.insertTopLevelItem(0, item)

    def importEML(self):
        # TODO: update to new functionality
        current = self.foldertreeWidget.currentItem()
        folder = current.data(0, Qt.UserRole).toPyObject()
        filename = QFileDialog.getOpenFileName(self, 'Open EML', '.', "Emails (*.eml)")
        if filename:
            fname = open(filename, 'r')
            rfc822 = fname.read()
            fname.close()
            item = folder.create_item(eml=rfc822)
            self.recordlist.model().addItems([item])

    def showHiddenItems(self):
        current = self.foldertreeWidget.currentItem()
        self.openFolder(current, True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = zarafa.Server()
    window = MyMainWindow(server)
    window.show()
    sys.exit(app.exec_())
