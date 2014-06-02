#!/usr/bin/env python
from zinspectorlib import *

# PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import sys

import zarafa
from zarafa import Folder, Item
from MAPI.Util import *

app = QApplication(sys.argv)
MainWindow = QMainWindow()
ui = Ui_MainWindow()

def openTree(item):
    folder = item.data(0, Qt.UserRole).toPyObject()
    recordlist = ui.recordlistWidget
    recordlist.clear()
    ui.propertytableWidget.clear()
    for record in folder.items():
        listItem = QListWidgetItem()
        if record.subject is None:
            listItem.setText("<empty subject>")
        else:
            listItem.setText(record.subject)
        listItem.setData(Qt.UserRole, record)
        recordlist.addItem(listItem)

    # Add click event for 
    recordlist.itemClicked.connect(openRecord)

    # Show MAPI properties of folder
    drawTable(folder.properties())

def openRecord(item):
    record = item.data(Qt.UserRole).toPyObject()
    drawTable(record.properties())

def drawTable(properties):
    names, values, types, horHeaders = [], [], [], []
    mystruct = { 'Property' : names, 'Type' : types, 'Value' : values }
    propertytable = ui.propertytableWidget

    for rec in properties:
        names.append(rec.name)
        value = rec.value
        if PROP_TYPE(rec.proptag) == PT_BINARY:
            value = bin2hex(rec.value)
        values.append(value)

        types.append(rec.proptype)

    propertytable.setColumnCount(len(mystruct))
    propertytable.setRowCount(len(names))

    for n, key in enumerate(mystruct):
        horHeaders.append(key)
        for m, value in enumerate(mystruct[key]):
            newitem = QTableWidgetItem(str(value))
            newitem.setFlags(Qt.ItemIsEnabled)
            propertytable.setItem(m, n, newitem)

    propertytable.resizeColumnsToContents()
    propertytable.setHorizontalHeaderLabels(horHeaders)
    propertytable.show()

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
        item = Item(folder, rfc822)
        listItem = QListWidgetItem()
        if record.subject is None:
            listItem.setText("<empty subject>")
        else:
            listItem.setText(record.subject)
        listItem.setData(Qt.UserRole, record)
        ui.recordlistWidget.addItem(listItem)

def deleteItem():
    # select current item
    recordlist = ui.recordlistWidget
    current = recordlist.currentItem()
    record = current.data(Qt.UserRole).toPyObject()

    # Fetch selected folder, since I folder can delete an Item and the Item doesn't need to have Item.folder or Item.store
    currentfolder = ui.foldertreeWidget.currentItem()
    folder = currentfolder.data(0,Qt.UserRole).toPyObject()
    folder.delete([record])

    item = recordlist.takeItem(recordlist.row(current))
    item = None

def saveEML():
    current = ui.recordlistWidget.currentItem()
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
    current = ui.recordlistWidget.currentItem()
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
        for m, prop in enumerate(attachment.properties()):
            if PROP_TYPE(prop.proptag) == PT_BINARY:
                newitem = QTableWidgetItem(bin2hex(prop.value))
            else:
                newitem = QTableWidgetItem(str(prop.value))
            newitem.setFlags(Qt.ItemIsEnabled)
            newitem.setData(Qt.UserRole, attachment)
            attTable.setItem(n, m, newitem)
            if n == 0:
                horHeaders.append(prop.name)

    attTable.setHorizontalHeaderLabels(horHeaders)
    attTable.resizeColumnsToContents()
    attTable.show()

def onRecordContext(point):
    menu = QMenu("Menu",ui.recordlistWidget)
    item = ui.recordlistWidget.itemAt(point)
    record = item.data(Qt.UserRole).toPyObject()

    if record.property(PR_MESSAGE_CLASS).get_value().startswith('IPM.Note'):
        menu.addAction("Save as EML",saveEML)

    menu.addAction("Delete Item",deleteItem)

    if record.attachments():
        menu.addAction("Show attachments",showAttachments)

    # Show the context menu.
    menu.exec_(ui.recordlistWidget.mapToGlobal(point))

def onFolderContext(point):
    menu = QMenu("Menu",ui.foldertreeWidget)
    menu.addAction("Export as MBOX",saveMBOX)
    menu.addAction("Create new folder",createFolder)
    menu.addAction("Import EML",importEML)
    item = ui.foldertreeWidget.itemAt(point)
    record = item.data(0,Qt.UserRole).toPyObject()

    menu.exec_(ui.foldertreeWidget.mapToGlobal(point))

def openUserStore(tablewidgetitem):
    user = tablewidgetitem.data(Qt.UserRole).toPyObject()
    foldertree = ui.foldertreeWidget
    foldertree.clear()
    foldertree.itemClicked.connect(openTree)
    foldertree.parent = QTreeWidgetItem(foldertree, ["Inbox"])
    foldertree.setItemExpanded(foldertree.parent, True)

    folders = []
    for depth, folder in enumerate(user.store.folders(system=True,recurse=True)):
        # If folder.depth is not null, we must find the parent
        parent = foldertree.parent
        if folder.depth != 0:
            parentid = HrGetOneProp(folder.mapifolder, PR_PARENT_ENTRYID).Value
            for treewidget in folders:
                treewidgetfolder = treewidget.data(0, Qt.UserRole).toPyObject()
                if treewidgetfolder.entryid == parentid:
                    parent = treewidget
                    break

        item = QTreeWidgetItem(parent, [folder.name])
        item.setData(0, Qt.UserRole, folder)
        folders.append(item)

    # Setup contextmenu's
    recordlist = ui.recordlistWidget
    recordlist.setContextMenuPolicy(Qt.CustomContextMenu)
    foldertree.setContextMenuPolicy(Qt.CustomContextMenu)
    recordlist.connect(ui.recordlistWidget, SIGNAL("customContextMenuRequested(QPoint)"),onRecordContext)
    foldertree.connect(foldertree, SIGNAL("customContextMenuRequested(QPoint)"),onFolderContext)

    # Speed up recordlistwidget 
    recordlist.setLayoutMode(QListWidget.Batched)
    recordlist.updatesEnabled = False
    recordlist.setUniformItemSizes(True)

def drawGAB(server, remoteusers=False):
    # GAB
    horHeaders = ["Name","Email","Local","Home Server"]
    gabwidget = ui.gabwidget
    gabwidget.setRowCount(len(list(server.users(remote=remoteusers))))
    gabwidget.setColumnCount(len(horHeaders))

    # TODO: Refactor and seperate function
    for n, user in enumerate(list(server.users(remote=remoteusers))):
        for m in range(0,4):
            if m == 0:
                newitem = QTableWidgetItem(user.name)
            elif m == 1:
                newitem = QTableWidgetItem(user.email)
            elif m == 2:
                newitem = QTableWidgetItem(str(user.local))
            elif m == 3:
                newitem = QTableWidgetItem(user.home_server)

            newitem.setFlags(Qt.ItemIsEnabled)
            newitem.setData(Qt.UserRole, user)
            gabwidget.setItem(n, m, newitem)

    gabwidget.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred))
    gabwidget.setHorizontalHeaderLabels(horHeaders)
    gabwidget.resizeColumnsToContents()
    gabwidget.show()
    gabwidget.itemClicked.connect(openUserStore)

    # hide recordtableWidget by default
    ui.recordtableWidget.hide()

if __name__ == "__main__":
    ui.setupUi(MainWindow)

    # connect to server
    server = zarafa.Server()

    drawGAB(server)

    MainWindow.show()
    sys.exit(app.exec_())
