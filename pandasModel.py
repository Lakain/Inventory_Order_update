import pandas as pd
from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor


class PandasModel(QAbstractTableModel):
    def __init__(self, data:pd.DataFrame):
        super(PandasModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        if role == Qt.BackgroundRole:
            if self._data.iloc[index.row(), index.column()] == 'Expedited':
                return QColor(128, 0, 0)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled

        return super().flags(index) | Qt.ItemIsEditable  # add editable flag.

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            # Set the value into the frame.
            self._data.iloc[index.row(), index.column()] = value
            return True

        return False