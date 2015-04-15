from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView


# FIXME: move to seperate file
class FolderTree(QTreeWidget): # QTreeView?
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
