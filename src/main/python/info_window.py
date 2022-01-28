"""PyQt Main window to display information on the selected file."""

from PyQt6 import QtCore, QtGui, QtWidgets


class FileInfoWindow(QtWidgets.QMainWindow):
    """Display header information of the selected CRD file."""

    def __init__(self, parent):
        """Initialize the window."""
        super().__init__(parent)

        self.parent = parent

        self.setGeometry(QtCore.QRect(0, 150, 100, 100))

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """Close event also untoggles the respective button in parent class."""
        self.parent.window_info_action.setChecked(False)
        super().closeEvent(a0)
