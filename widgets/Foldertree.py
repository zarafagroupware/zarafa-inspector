from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QWidget, QAction, QInputDialog

'''
- Rename folder
- export MBOX
- import MBOX
- export Maildir
- import Maildir
- import eml
- show hidden items
- show folder property's
'''

# FIXME: move to seperate file
class FolderTree(QTreeWidget): # QTreeView?
    def __init__(self, parent = None, user = None):
        super(FolderTree, self).__init__(parent)

        self.header().setHidden(True)
        self.folders = user.store.folders()
        self.store = user.store

        rootnode = QTreeWidgetItem(self, [user.name])
        rootnode.setData(0, Qt.UserRole, user.store.root)
        self.parent = rootnode
        self.expandItem(rootnode)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onCustomContextMenu)

        # Draw folder hierachy
        folders = {}
        for folder in user.store.folders(system=True, recurse=True): # XXX: configureable?
            # FIXME: performance / cleaner method without temp dict?
            if folder.depth != 0:
                parentid = folder.parent.entryid
                if folders[parentid]:
                    parent = folders[parentid]
            else:
                parent = self.parent

            item = QTreeWidgetItem(parent, [folder.name])
            item.setData(0, Qt.UserRole, folder)
            folders[folder.entryid] = item

    def onCustomContextMenu(self, point):
        menu = QMenu("Menu", self)
        menu.addAction("Delete folder", self.deleteFolder)
        menu.addAction("Create folder", self.createFolder)

        menu.exec_(self.mapToGlobal(point))

    def deleteFolder(self):
        current = self.currentItem()
        parent = current.parent()
        folder = current.data(0, Qt.UserRole)
        folder.parent.delete(folder)
        parent.removeChild(current)
        current = None

    def createFolder(self):
        current = self.currentItem()
        folder = current.data(0, Qt.UserRole)
        foldername, ok = QInputDialog.getText(self, 'Create folder Dialog', 'New folder name:')
        if ok and foldername:
            newfolder = folder.create_folder(str(foldername)) # TODO: cast to str really needed?
            item = QTreeWidgetItem(current, [foldername])
            item.setData(0, Qt.UserRole, newfolder)
            self.insertTopLevelItem(0, item)


