"""Data views for opened CRD files."""


from typing import Any, List

from PyQt6 import QtCore, QtGui, QtWidgets


class OpenFilesListView(QtWidgets.QListView):
    """List view for opened CRD files."""

    def __init__(self, parent):
        """Initialize open files list view.

        :param parent: Parent widget.
        """
        super().__init__(parent)
        self.setMinimumWidth(400)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)


class IntegralBackgroundTableView(QtWidgets.QTableView):
    """Editable table view for managing models."""

    def __init__(self, parent=None):
        """Initialize widget.

        :param parent: Parent widget.
        """
        super().__init__(parent)
        self.setFixedHeight(350)  # to not have to scroll too frequently
        self.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow
        )
        self.resizeColumnsToContents()


class IntegralsDisplay(QtWidgets.QTableView):
    """Widget for integrals."""

    def __init__(self, parent=None):
        """Initialize the widget.

        :param parent: Parent widget.
        """
        super().__init__(parent)
        self.setMinimumWidth(530)
        self.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.resizeColumnsToContents()
