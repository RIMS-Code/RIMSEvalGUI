"""Models for connecting opened data with views."""

from pathlib import Path
from typing import Any, List

from PyQt6 import QtCore, QtGui
import numpy as np
from rimseval.guis.integrals import tableau_color

from items import TreeItem


class EvaluatorFilesModel(QtCore.QAbstractItemModel):
    def __init__(
        self, experiment_name: str = "Experiment", data: dict = None, parent=None
    ):
        """Initialize the model.

        :param experiment_name: Name of the experiment.
        :param data: Data to be displayed in the tree.
        :param parent: Parent widget.
        """
        super().__init__(parent)

        data = {
            "a": ["a1", "a2", "a3"],
            "b": ["b1", "b2"],
            "c": ["c1", "c2", "c3", "c4"],
            "d": ["d1", "d2", "d3"],
            "e": ["e1", "e2", "e3", "e4", "e5"],
        }

        self.root_item = TreeItem(experiment_name)
        self.setup_model_data(data)

    def columnCount(self, parent: QtCore.QModelIndex = None) -> int:
        """Return the number of columns."""
        return self.root_item.column_count()

    def data(self, index: QtCore.QModelIndex, role: int = None):
        """Return the data at a given index."""
        if not index.isValid():
            return None

        if (
            role != QtCore.Qt.ItemDataRole.DisplayRole
            and role != QtCore.Qt.ItemDataRole.EditRole
        ):
            return None

        item: TreeItem = self.get_item(index)

        return item.data()

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """Return the flags for a given index."""
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags

        return QtCore.QAbstractItemModel.flags(self, index)

    def get_item(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) -> TreeItem:
        if index.isValid():
            item: TreeItem = index.internalPointer()
            if item:
                return item

        return self.root_item

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ):
        if (
            orientation == QtCore.Qt.Orientation.Horizontal
            and role == QtCore.Qt.ItemDataRole.DisplayRole
        ):
            return self.root_item.data()

        return None

    def index(
        self, row: int, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> QtCore.QModelIndex:
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()

        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return QtCore.QModelIndex()

        child_item: TreeItem = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QtCore.QModelIndex()

    def parent(
        self, index: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item: TreeItem = self.get_item(index)
        if child_item:
            parent_item: TreeItem = child_item.parent()
        else:
            parent_item = None

        if parent_item == self.root_item or not parent_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.child_number(), 0, parent_item)

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if parent.isValid() and parent.column() > 0:
            return 0

        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return 0
        return parent_item.child_count()

    def setup_model_data(self, data: dict):
        """Set up the model data from the given dictionary.

        :param data: Dictionary with the data to be displayed.
        """
        parent = self.root_item
        for key, values in data.items():
            parent.insert_children(parent.child_count(), 1)
            child = parent.last_child()
            child.set_data(key)

            for jt, val in enumerate(values):
                child.insert_children(child.child_count(), 1)
                child.last_child().set_data(val)
        return None

    def _repr_recursion(self, item: TreeItem, indent: int = 0) -> str:
        result = " " * indent + repr(item) + "\n"
        for child in item.child_items:
            result += self._repr_recursion(child, indent + 2)
        return result

    def __repr__(self) -> str:
        return self._repr_recursion(self.root_item)


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

    def add_to_list(self, names: List[Path]) -> None:
        """Add new items to the list at the end.

        :param names: List of new file names to append.
        """
        for name in names:
            self.open_files.append([False, name.with_suffix("").name])
        self.layoutChanged.emit()

    def remove_from_list(self, ids: List[int], main_id: int) -> None:
        """Remove selected ids from the list.

        :param ids: IDs to remove.
        :param main_id: ID of the currently active one (new ID).
        """
        self.open_files[self._currently_active][0] = False  # unset active one

        ids.sort(reverse=True)
        for id in ids:
            del self.open_files[id]

        self.open_files[main_id][0] = True  # set new active
        self._currently_active = main_id

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

    def __init__(self, data=None, names=None, deltas=None):
        """Initialize the integral model.

        :param data: Integrals, from ``CRDProcessor.integrals``.
        """
        super().__init__()
        self._names = names
        self._header = ["Peak", "Counts", "\u00B11\u03C3", "Delta", "\u00B11\u03C3"]

        if data is None:
            self._data = np.zeros((0, 0, 0, 0))
        else:
            if deltas is None:
                deltas = np.zeros_lie(self._data)
            self._data = np.stack([data, deltas], axis=1)
            self._data.reshape(self._data.shape[0], 4)

    def columnCount(self, index):
        """Return the number of columns."""
        if self._data.shape[1] == 0:
            return 0
        else:
            return self._data.shape[1] + 1  # add names

    def data(self, index, role):
        """Return the data."""
        row = index.row()
        col = index.column()

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if col == 0:
                try:
                    return str(self._names[row])
                except IndexError:
                    return "N/A"
            else:
                value = np.round(self._data[row][col - 1], 2)
                return str(value)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:  # column headers
                return str(self._header[section])
            if orientation == QtCore.Qt.Orientation.Vertical:  # row headers
                return "\u25CF"

        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            if orientation == QtCore.Qt.Orientation.Vertical:
                color = tableau_color(section)
                return QtGui.QBrush(QtGui.QColor(color))

    def rowCount(self, index):
        """Return the number of rows."""
        return self._data.shape[0]

    def clear_data(self):
        """Clear data."""
        self._names = None
        self._data = np.empty((0, 0, 0, 0))
        self.layoutChanged.emit()

    def update_data(self, data: np.ndarray, names: List[str], deltas: np.ndarray):
        """Update the model with new data.

        :param data: Data to set
        :param names: Names of the peaks
        :param deltas: Delta value to set.
        """
        self._names = names
        data = np.stack([data, deltas], axis=1)
        self._data = data.reshape(data.shape[0], 4)
        self.layoutChanged.emit()


class IntegralBackgroundDefinitionModel(QtCore.QAbstractTableModel):
    """Abstract table model for the integral and backgruond definitions."""

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

    def delete_selected(self, rows: List):
        """Remove names for selected entries and then call the remove empties method."""
        for ind in rows:
            self._names[ind] = ""
        self.remove_empties()
        if len(self._names) == 0:
            self.init_empty()

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

    def add_element(self, names, values):
        """Add isotopes with given values, overwrite doubles."""
        for it, name in enumerate(names):
            if name not in self._names:
                self._names.append(name)
                self._values = np.append(self._values, values[it].reshape(1, 2), axis=0)
            else:
                index = self._names.index(name)
                self._values[index] = values[it]
        self.remove_empties()
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


class NormIsosModel(QtCore.QAbstractTableModel):
    """Data model for normalization isotopes dictionary."""

    def __init__(self, data=None):
        """Initialize the normalization isotopes model.

        :param data: Dictionary with elements as keys and isotopes as values, e.g.:
            {"Ba": "Ba-136"}, or None
        """
        super().__init__()
        self._header = ["Element", "Isotope"]

        if data is None:
            self.init_empty()
        else:
            self._data = data
            self._keys = list(self._data.keys())

    def add_entry(self, ele: str, iso: str) -> None:
        """Add a new element / isotope combination and change the layout.

        :param ele: Element name.
        :param iso: Isotope name.
        """
        self._data[ele] = iso
        self._keys = list(self._data.keys())
        self.layoutChanged.emit()

    def columnCount(self, index):
        """Return the number of columns."""
        return 2

    def data(self, index, role):
        """Return the data."""
        row = index.row()
        col = index.column()
        key = self._keys[row]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return key
            else:
                return self._data[key]

    def delete_selected(self, rows: List):
        """Delete all entries that are selected."""
        for ind in rows:
            del self._data[self._keys[ind]]
        self._keys = list(self._data.keys())
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._header[section])

    def init_empty(self):
        """Initialize empty model."""
        self._data = {}
        self._keys = []
        self.layoutChanged.emit()

    def return_data(self) -> dict:
        """Return the dictionary with all data."""
        return self._data

    def rowCount(self, index):
        """Return the number of rows."""
        return len(self._keys)
