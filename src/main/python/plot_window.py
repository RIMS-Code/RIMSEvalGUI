"""PyQt Main window to display mass spectrometer."""

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6 import QtCore, QtGui, QtWidgets
import rimseval
from rimseval.guis.mpl_canvas import MyMplNavigationToolbar


class PlotWindow(QtWidgets.QMainWindow):
    """Display header information of the selected CRD file."""

    def __init__(self, parent):
        """Initialize the window."""
        super().__init__(parent)

        self.parent = parent
        self.setWindowTitle("Spectrum")

        self.theme = parent.config.get("Theme")
        if self.theme == "dark":
            matplotlib.style.use("dark_background")

        self.logy = parent.config.get("Plot with log y-axis")

        self.fig = Figure(figsize=(9, 6), dpi=100)
        self.sc = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)

        self.button_bar = QtWidgets.QHBoxLayout()
        self.logy_button = None
        self.ax_autoscale_button = None
        self.init_button_bar()

        toolbar = MyMplNavigationToolbar(self.sc, self)

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
        logy_button = QtWidgets.QPushButton("Log Y")
        logy_button.setToolTip("Plot vertical axis logarithmically?")
        logy_button.setCheckable(True)
        logy_button.setChecked(self.logy)
        logy_button.toggled.connect(self.logy_toggle)
        self.button_bar.addWidget(logy_button)
        self.logy_button = logy_button

        ax_autoscale_button = QtWidgets.QPushButton("Auto Scale")
        ax_autoscale_button.setToolTip(
            "Automatically scale the x and y axis when re-plotting?"
        )
        ax_autoscale_button.setCheckable(True)
        ax_autoscale_button.setChecked(True)  # turn it on
        self.button_bar.addWidget(ax_autoscale_button)
        self.ax_autoscale_button = ax_autoscale_button

        close_button = QtWidgets.QPushButton("Close")
        close_button.setToolTip("Hide this window from view")
        close_button.clicked.connect(self.close)
        self.button_bar.addStretch()
        self.button_bar.addWidget(close_button)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """Close event also untoggles the respective button in parent class."""
        self.parent.window_plot_action.setChecked(False)
        super().closeEvent(a0)

    def clear_plot(self):
        """Clear figure."""
        self.axes.clear()
        self.sc.draw()

    def logy_toggle(self):
        """Toggle logy."""
        self.logy = not self.logy
        self.logy_button.setDown(self.logy)

        if self.logy:
            self.axes.set_yscale("log")
            self.axes.set_ylim(bottom=0.7)
        else:
            self.axes.set_yscale("linear")
            self.axes.set_ylim(bottom=0)

        self.sc.draw()

    def plot_single(self, crd: rimseval.CRDFileProcessor) -> None:
        """Plot the data of a single CRD file ont he canvas.

        :param crd: CRD File to plot from
        """
        if crd.mass is None:
            xax = crd.tof
            xlabel = "Time of Flight (us)"
        elif crd.tof is not None:
            xax = crd.mass
            xlabel = "Mass (amu)"
        else:
            return

        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()

        self.axes.clear()

        color = "w" if self.theme == "dark" else "k"

        self.axes.fill_between(xax, crd.data, color=color, linewidth=0.3)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel("Counts")
        if self.logy:
            self.axes.set_yscale("log")
            self.axes.set_ylim(bottom=0.7)

        # set limits back if user wants it
        if not self.ax_autoscale_button.isChecked():
            self.axes.set_xlim(xlim)
            self.axes.set_ylim(ylim)

        self.sc.draw()
