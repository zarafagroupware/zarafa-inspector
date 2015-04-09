from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListView

class ItemListView(QListView):
    '''
    ItemListView class
    Used to draw a QListView with MAPI objects and provides a number of operations
    on a MAPI object.
    '''

    def __init__(self, parent=None):
        super(ItemListView, self).__init__(parent)
        self.parent = self.parent()
