from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex

class ItemListModel(QAbstractListModel):
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

    def rowCount(self, parent=QModelIndex()):
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

        self.beginInsertRows(QModelIndex(), self.itemCount, self.itemCount + itemsToFetch)
        self.itemCount += itemsToFetch
        self.endInsertRows()

    def addData(self, items, total):
        self.itemGenerator = items # The generator Folder.items()
        self.totalItems = total

        self.itemList = [self.itemGenerator.next() for _ in xrange(0, min(20, total))]

        self.itemCount = 0
        #self.reset() FIXME: still needed?

    def addItems(self, items):
        self.beginInsertRows(QModelIndex(), 0, len(items))
        [self.itemList.insert(0, item) for item in items]
        self.endInsertRows()
        self.itemCount = self.itemCount + len(items)
        self.totalItems = self.totalItems + len(items)

    def removeItemObjects(self, items):
        for item in items:
            for index, listitem in enumerate(self.itemList):
                if item.sourcekey == listitem.sourcekey:
                    self.beginRemoveRows(QModelIndex(), index, index)
                    del self.itemList[index]
                    self.itemCount = self.itemCount - 1
                    self.totalItems = self.totalItems - 1
                    self.endRemoveRows()
                    break

    def removeItems(self, items):
        for index in items:
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.itemList[index]
            self.itemCount = self.itemCount - 1
            self.totalItems = self.totalItems - 1
            self.endRemoveRows()
