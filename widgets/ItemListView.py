from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListView, QFileDialog, QMenu

class ItemListView(QListView):
    '''
    ItemListView class
    Used to draw a QListView with MAPI objects and provides a number of operations
    on a MAPI object.
    '''

    def __init__(self, parent=None):
        super(ItemListView, self).__init__(parent)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onCustomContextMenu)

    def onCustomContextMenu(self, point):
        index = self.indexAt(point)
        record = self.model().data(index, Qt.ItemDataRole)

        menu = QMenu("Menu", self)

        if record.message_class.startswith('IPM.Note'):
            menu.addAction("Save as EML", self.saveEML)

        menu.addAction("Delete Item", self.deleteItem)

        '''
        if record.attachments():
            menu.addAction("View attachments", self.showAttachments)

        menu.addAction("View recipients", self.showRecipients)
        '''

        # Show the context menu.
        menu.exec_(self.mapToGlobal(point))

    def saveEML(self):
        current = self.currentIndex()
        record = self.model().data(current, Qt.ItemDataRole)
        filename = QFileDialog.getSaveFileName(caption='Save EML', filter='Emails (*.eml)')

        if filename[0]: # TODO: fix test for set entry?
            rfc882 = record.eml()
            fname = open(filename[0], 'w') # Check for .eml else append it
            fname.write(rfc882)
            fname.close()

    def deleteItem(self):
        current = self.currentIndex()
        record = self.model().data(current, Qt.ItemDataRole)
        record.folder.delete([record])
        self.model().removeItems([self.currentIndex().row()])
