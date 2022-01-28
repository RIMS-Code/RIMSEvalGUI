"""PyQt Main window to display mass spectrometer."""

from PyQt6 import QtCore, QtGui, QtWidgets


class PlotWindow(QtWidgets.QMainWindow):
    """Display header information of the selected CRD file."""

    def __init__(self, parent):
        """Initialize the window."""
        super().__init__(parent)

        self.parent = parent

        self.setGeometry(QtCore.QRect(1000, 600, 100, 100))

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """Close event also untoggles the respective button in parent class."""
        self.parent.window_plot_action.setChecked(False)
        super().closeEvent(a0)
