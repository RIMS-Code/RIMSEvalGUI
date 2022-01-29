"""Models for connecting opened data with views."""

from pathlib import Path
from typing import Any, List

from PyQt6 import QtCore, QtGui, QtWidgets


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

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            _, text = self.open_files[index.row()]
            return text

        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            status, _ = self.open_files[index.row()]
            if status:
                return self.tick

    def rowCount(self, index) -> int:
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
        for it, name in enumerate(names):
            status = True if it == self._currently_active else False
            self.open_files.append([status, name.with_suffix("").name])
        self.layoutChanged.emit()
