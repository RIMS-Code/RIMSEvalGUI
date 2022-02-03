"""PyQt Main window to display mass spectrometer."""

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6 import QtCore, QtGui, QtWidgets
from rimseval.guis.mpl_canvas import MyMplNavigationToolbar


class PlotWindow(QtWidgets.QMainWindow):
    """Display header information of the selected CRD file."""

    def __init__(self, parent):
        """Initialize the window."""
        super().__init__(parent)

        self.parent = parent
        self.setWindowTitle("Spectrum")

        self.fig = Figure(figsize=(9, 6), dpi=100)
        sc = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.sc = sc

        toolbar = MyMplNavigationToolbar(sc, self)
        self.button_bar = QtWidgets.QHBoxLayout()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.sc)
        layout.addLayout(self.button_bar)

        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(layout)

        self.setCentralWidget(main_widget)

        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

    def init_button_bar(self):
        """Initialize the button bar at the bottom."""
        pass

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """Close event also untoggles the respective button in parent class."""
        self.parent.window_plot_action.setChecked(False)
        super().closeEvent(a0)

    def set_theme(self, theme: str):
        """Set the theme of the plot.

        :param theme: Theme to set.
        """
        # fixme
        if theme == "dark":
            matplotlib.style.use("dark_background")
        else:
            matplotlib.style.use("classic")
