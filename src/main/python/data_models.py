"""Models for connecting opened data with views."""

from pathlib import Path
from typing import Any, List

from PyQt6 import QtCore, QtGui, QtWidgets
import numpy as np


class OpenFilesModel(QtCore.QAbstractListModel):
    """Model for the data that are in the open files view.

    The ``open_files`` variable is a list of filenames, as strings.
    """

    def __init__(self, *args, tick=None, **kwargs):
        """Initialize open files model.

        :param tick: File Path to the tick icon.
        """
        super().__init__(*args, **kwargs)
        self.tick = QtGui.QImage(tick)

        self.open_files = []
        self._currently_active = 0

    @property
    def currently_active(self) -> int:
        """Return index of currently active file."""
        return self._currently_active

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            _, text = self.open_files[index.row()]
            return text

        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            status, _ = self.open_files[index.row()]
            if status:
                return self.tick

    def rowCount(self, index) -> int:
        """Return the row count."""
        return len(self.open_files)

    def update_current(self, ind: int) -> None:
        """Update the currently active item to the new one."""
        self.open_files[self._currently_active][0] = False
        self._currently_active = ind
        self.open_files[ind][0] = True
        self.layoutChanged.emit()

    def set_new_list(self, names: List[Path]) -> None:
        """Clear the old model and set the new dataset."""
        self.open_files = []
        self._currently_active = 0
        for it, name in enumerate(names):
            status = True if it == self._currently_active else False
            self.open_files.append([status, name.with_suffix("").name])
        self.layoutChanged.emit()


class IntegralsModel(QtCore.QAbstractTableModel):
    """Data model for integrals."""

    def __init__(self, data=None, names=None):
        """Initialize the integral model.

        :param data: Integrals, from ``CRDProcessor.integrals``.
        """
        super().__init__()
        self._names = names
        self._header = ["Counts", "Uncertainty"]

        if data is None:
            self._data = np.empty((0, 0))

    def columnCount(self, index):
        """Return the number of columns."""
        return self._data.shape[1]

    def data(self, index, role):
        """Return the data."""
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            value = np.round(self._data[index.row()][index.column()], 2)
            return str(value)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._header[section])
            if orientation == QtCore.Qt.Orientation.Vertical:
                return str(self._names[section])

    def rowCount(self, index):
        """Return the number of rows."""
        return self._data.shape[0]

    def clear_data(self):
        """Clear data."""
        self._names = None
        self._data = np.empty((0, 0))
        self.layoutChanged.emit()

    def get_integrals_to_copy(self, names: bool = False, unc: bool = True) -> str:
        """Get string with the data to copy to clipboard.

        :param names: Copy the names of the peaks as well?
        :param unc: Copy uncertainties as well?
        """
        if self._names is None:
            return ""

        ret_str = ""
        if names:
            for it, name in enumerate(self._names):
                ret_str += f"{name}\t{name}_1sig" if unc else f"{name}"
                if it < len(self._names) - 1:
                    ret_str += "\t"
            ret_str += "\n"
        for it, val in enumerate(self._data):
            ret_str += f"{val[0]}\t{val[1]}" if unc else f"{val[0]}"
            if it < len(self._data) - 1:
                ret_str += "\t"
        return ret_str

    def update_data(self, data: np.ndarray, names: List[str]):
        """Update the model with new data.

        :param data: Data to set
        :param names: Names of the peaks
        """
        self._names = names
        self._data = data
        self.layoutChanged.emit()


class IntegralBackgroundDefinitionModel(QtCore.QAbstractTableModel):
    """Abstract table model for the integral definitions."""

    def __init__(self, data=None):
        """Initialize integrals definition model.

        :param data: Integrals definition, directly from CRDProcessor -> def_integrals
        """
        super().__init__()
        if data is None:
            self.init_empty()

        else:
            self._names = data[0]
            self._values = data[1]

        self._header = ["Peak", "Lower Lim.", "Upper Lim."]

    def columnCount(self, index):
        return self._values.shape[1] + 1

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                value = self._names[index.row()]
            else:
                value = np.round(self._values[index.row()][index.column() - 1], 5)
            return str(value)

    def flags(self, index):
        """Make all items editable."""
        return (
            QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsEditable
        )

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._header[section])

    def rowCount(self, index):
        return self._values.shape[0]

    def setData(self, index, value, role):
        """Make the data editable."""
        if not index.isValid():
            return False
        if role != QtCore.Qt.ItemDataRole.EditRole:
            return False

        row = index.row()
        if row < 0 or row >= self._values.shape[0]:
            return False

        column = index.column()
        if column < 0 or column >= self._values.shape[1] + 1:
            return False

        if column == 0:
            self._names[row] = value
            self.dataChanged.emit(index, index)
        else:
            try:
                self._values[row][column - 1] = value
            except ValueError:
                return False
        return True

    # PROPERTIES #
    @property
    def names(self):
        """Return all names in columns"""
        return self._names

    def add_row(self):
        """Add a row to the integral data."""
        self._names.append("")
        self._values = np.append(self._values, np.zeros((1, 2)), axis=0)
        self.layoutChanged.emit()

    def auto_fill(self, masses: List[float], lower: float, upper: float):
        """Automatically fill the values of all the peaks.

        :param masses: Masses for all non-empty names
        :param lower: Lower limit is mass - lower
        :param upper: Upper limit is mass + upper
        """

        # we have the masses, fill them
        for it, mass in enumerate(masses):
            self._values[it][0] = mass - lower
            self._values[it][1] = mass + upper
        self.layoutChanged.emit()

    def init_empty(self):
        """Initialize empty data."""
        num_of_lines = 10
        self._names = ["" for it in range(num_of_lines)]
        self._values = np.zeros((num_of_lines, 2))
        self.layoutChanged.emit()

    def remove_empties(self):
        """Delete empties from list."""
        # remove empties
        while "" in self._names:
            ind = self._names.index("")
            self._names.pop(ind)
            self._values = np.delete(self._values, ind, axis=0)
        self.layoutChanged.emit()

    def return_data(self):
        """Return data of the model."""
        self.remove_empties()
        if self._names:
            return self._names, self._values
