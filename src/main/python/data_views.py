"""Data views for opened CRD files."""


from typing import Any, List

from PyQt6 import QtCore, QtGui, QtWidgets


class OpenFilesListView(QtWidgets.QListView):
    """List view for opened CRD files."""

    def __init__(self, parent):
        """Initialize open files list view."""
        super().__init__(parent)

        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
