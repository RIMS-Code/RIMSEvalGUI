"""PyQt Main window to display mass spectrometer."""

from typing import Union, List

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
import rimseval
from rimseval.guis.integrals import tableau_color
from rimseval.guis.mpl_canvas import MyMplNavigationToolbar


class PlotWindow(QtWidgets.QMainWindow):
    """Display header information of the selected CRD file."""

    def __init__(self, parent):
        """Initialize the window."""
        super().__init__(parent)

        self.parent = parent
        self.setWindowTitle("Spectrum")
        # self.setGeometry(QtCore.QRect(1000, 1000, 100, 100))
        self.move(1550, 200)

        self.theme = parent.config.get("Theme")
        if self.theme == "dark":
            matplotlib.style.use("dark_background")

        self.logy = parent.config.get("Plot with log y-axis")

        # buttons
        self.button_spectrum_type = QtWidgets.QPushButton("Mass")
        self.button_integrals = QtWidgets.QPushButton("Integrals")
        self.button_backgrounds = QtWidgets.QPushButton("Backgrounds")

        # set xrange stuff
        self.entry_xrange_start = QtWidgets.QLineEdit()
        self.entry_xrange_stop = QtWidgets.QLineEdit()
        self.button_set_xrange = QtWidgets.QPushButton("Set x limits")

        # settings for the program
        self._is_multi_plot = False
        self._plot_ms = True  # plot mass spectrum when mass available
        self._plot_integrals = True
        self._plot_backgrounds = True

        # shading references
        self._peak_shades_ref = None
        self._background_shades_ref = None

        # empty data
        self.file_name = None
        self.mass = None
        self.tof = None
        self.data = None
        self.integrals = None
        self.backgrounds = None
        self.tof_to_chan = 1

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
        ax_autoscale_button.clicked.connect(self.toggle_autoscale)
        self.button_bar.addWidget(ax_autoscale_button)
        self.ax_autoscale_button = ax_autoscale_button

        self.button_spectrum_type.setCheckable(True)
        self.button_spectrum_type.setChecked(self._plot_ms)
        self.button_spectrum_type.clicked.connect(self.toggle_spectrum_type)
        self.button_bar.addWidget(self.button_spectrum_type)

        self.button_integrals.setCheckable(True)
        self.button_integrals.setChecked(self._plot_integrals)
        self.button_integrals.clicked.connect(self.toggle_integrals)
        self.button_bar.addWidget(self.button_integrals)

        self.button_backgrounds.setCheckable(True)
        self.button_backgrounds.setChecked(self._plot_backgrounds)
        self.button_backgrounds.clicked.connect(self.toggle_backgrounds)
        self.button_bar.addWidget(self.button_backgrounds)

        # x range

        self.button_bar.addStretch()

        self.entry_xrange_start.setValidator(QtGui.QDoubleValidator(bottom=0, top=1000))
        self.entry_xrange_start.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.entry_xrange_start.editingFinished.connect(self.set_x_range)
        self.entry_xrange_start.setToolTip("Left x-axis range to set.")
        self.button_bar.addWidget(self.entry_xrange_start)

        self.entry_xrange_stop.setValidator(QtGui.QDoubleValidator(bottom=0, top=1000))
        self.entry_xrange_stop.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.entry_xrange_stop.editingFinished.connect(self.set_x_range)
        self.entry_xrange_stop.setToolTip("Right x-axis range to set.")
        self.button_bar.addWidget(self.entry_xrange_stop)

        self.button_set_xrange.clicked.connect(self.set_x_range)
        self.button_bar.addWidget(self.button_set_xrange)

        # close button

        close_button = QtWidgets.QPushButton("Close")
        close_button.setToolTip("Hide this window from view")
        close_button.clicked.connect(self.close)
        self.button_bar.addStretch()
        self.button_bar.addWidget(close_button)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """Close event also untoggles the respective button in parent class."""
        self.parent.window_plot_action.setChecked(False)
        super().closeEvent(a0)

    # MY METHODS #

    def clear_plot(self):
        """Clear figure."""
        self.ax_autoscale_button.setChecked(True)  # disable autoscale
        self.axes.clear()
        self.sc.draw()

    def clear_x_range(self):
        """Clear the x-range of all values."""
        self.entry_xrange_start.setText("")
        self.entry_xrange_stop.setText("")

    def format_coordinates(self, x: float, y: float) -> str:
        """Format the coordinates that should be displayed

        :param x: X coordinate of mouse
        :param y: Y coordinate of mouse

        :return: String to display on top
        """
        tof = self.tof[0] if self._is_multi_plot else self.tof
        mass = self.mass[0] if self._is_multi_plot and self.mass else self.mass

        ydisp = f"y={y:.1f}"
        if tof is None:
            return f"x={x:.2f}, {ydisp}"
        elif mass is None or not self._plot_ms:  # ToF display
            if self.tof_to_chan:
                chan = int(x * self.tof_to_chan)
                chan_disp = f"Channel={chan}, "
            else:
                chan_disp = ""
            if mass is not None:  # we have a mass but display tof
                mass_ind = np.argmin(np.abs(tof - x))
                mass = mass[mass_ind]
                return f"{chan_disp}ToF={x:.3f}us, Mass={mass:.2f}amu, {ydisp}"
            else:  # no mass calibration, display tof only
                return f"{chan_disp}ToF={x:.3f}us, {ydisp}"
        else:  # Mass display
            tof_ind = np.argmin(np.abs(mass - x))
            tof = tof[tof_ind]
            if self.tof_to_chan:
                chan = int(tof * self.tof_to_chan)
                chan_disp = f"Channel={chan}, "
            else:
                chan_disp = ""
            return f"{chan_disp}ToF={tof:.3f}us, Mass={x:.2f}amu, {ydisp}"

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

    def plot_multi(self) -> None:
        """Plot multiple spectra files on the canvas."""
        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        if self.logy:
            ylim = 0.7, ylim[1]

        self.axes.clear()

        self.axes.format_coord = self.format_coordinates

        # are masses / tofs available?
        masses_unavailable = any([it is None for it in self.mass])
        tofs_unavailable = any([it is None for it in self.tof])

        if masses_unavailable or not self._plot_ms:
            if tofs_unavailable:  # no data
                self.sc.draw()  # clear plot
                return
            xax = self.tof
            xlabel = "Time of Flight (us)"
        elif not tofs_unavailable:
            xax = self.mass
            xlabel = "Mass (amu)"
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Undefined data",
                "Tof and mass axes are undefined. "
                "Please process your CRD files first "
                "before trying to plot multiple spectra.",
            )
            self.sc.draw()
            return

        for it, xdat in enumerate(xax):
            self.axes.plot(
                xdat,
                self.data[it],
                color=tableau_color(it),
                label=self.file_name[it],
                linewidth=0.5,
            )

        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel("Counts")
        if self.logy:
            self.axes.set_yscale("log")
            self.axes.set_ylim(bottom=0.7)

        # set limits back if user wants it
        if not self.ax_autoscale_button.isChecked():
            self.axes.set_xlim(xlim)
            self.axes.set_ylim(ylim)

        self.axes.legend()

        self.sc.draw()

    def plot_single(self) -> None:
        """Plot the data of a single CRD file on the canvas."""

        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        if self.logy:
            ylim = 0.7, ylim[1]

        self.axes.clear()

        self.axes.format_coord = self.format_coordinates

        if self.mass is None or not self._plot_ms:
            if self.tof is None:  # no data...
                self.sc.draw()  # clear plot
                return
            xax = self.tof
            xlabel = "Time of Flight (us)"
        elif self.tof is not None:
            xax = self.mass
            xlabel = "Mass (amu)"
        else:
            self.sc.draw()
            return

        color = "w" if self.theme == "dark" else "k"

        self.axes.fill_between(xax, self.data, color=color, linewidth=0.3)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel("Counts")
        if self.logy:
            self.axes.set_yscale("log")
            self.axes.set_ylim(bottom=0.7)

        # set limits back if user wants it
        if not self.ax_autoscale_button.isChecked():
            self.axes.set_xlim(xlim)
            self.axes.set_ylim(ylim)

        # title
        self.axes.set_title(self.file_name)

        self.sc.draw()

        if self._plot_ms:  # only when in mass spectrum mode
            if self._plot_integrals:
                self.shade_peaks()
            if self._plot_backgrounds:
                self.shade_backgrounds()

    def set_x_range(self):
        """Set the x range according to user specs."""
        start = None
        stop = None

        if (st := self.entry_xrange_start.text()) != "":
            start = float(st)
        if (st := self.entry_xrange_stop.text()) != "":
            stop = float(st)

        if not start and not stop:
            return

        self.ax_autoscale_button.setChecked(False)

        if start:
            self.axes.set_xlim(left=start)
        if stop:
            self.axes.set_xlim(right=stop)

        self.sc.draw()

    def shade_backgrounds(self):
        """Go through background list and shade them."""
        if self.backgrounds is not None and self.integrals is not None:
            for it, peak_pos in enumerate(self.backgrounds[1]):
                int_name_index = self.integrals[0].index(self.backgrounds[0][it])
                col = tableau_color(int_name_index)

                self.axes.axvspan(
                    peak_pos[0], peak_pos[1], linewidth=0, color=col, alpha=0.25
                )

            self.sc.draw()

    def shade_peaks(self):
        """Shade the peaks with given integrals."""
        if self.integrals is not None:
            xax_lims = self.axes.get_xlim()
            yax_lims = self.axes.get_ylim()

            # shade peaks
            for it, peak_pos in enumerate(self.integrals[1]):
                indexes = np.where(
                    np.logical_and(self.mass > peak_pos[0], self.mass < peak_pos[1])
                )

                self.axes.fill_between(
                    self.mass[indexes],
                    self.data[indexes],
                    color=tableau_color(it),
                    linewidth=0.3,
                )

            self.axes.set_xlim(xax_lims)
            self.axes.set_ylim(yax_lims)

            self.sc.draw()

    def toggle_autoscale(self) -> None:
        """Run autoscale on current axis if autoscale is turned on by user."""
        if self.ax_autoscale_button.isChecked():
            # turn around if necessary
            curr_xlims = self.axes.get_xlim()
            if curr_xlims[0] > curr_xlims[1]:
                self.axes.set_xlim(curr_xlims[1], curr_xlims[0])

            self.axes.autoscale()

            self.clear_x_range()

            self.sc.draw()

    def toggle_integrals(self) -> None:
        """Toggle if integrals are being plotted."""
        self._plot_integrals = not self._plot_integrals
        self.button_integrals.setChecked(self._plot_integrals)
        self.plot_single()

    def toggle_backgrounds(self) -> None:
        """Toggle if backgrounds are being plotted."""
        self._plot_backgrounds = not self._plot_backgrounds
        self.button_backgrounds.setChecked(self._plot_backgrounds)
        self.plot_single()

    def toggle_spectrum_type(self) -> None:
        """Toggle the spectrum type that is being plotted."""
        self._plot_ms = not self._plot_ms
        self.button_spectrum_type.setChecked(self._plot_ms)

        self.ax_autoscale_button.setChecked(True)
        self.clear_x_range()

        if self._is_multi_plot:
            self.plot_multi()
        else:
            self.plot_single()

    def update_data(
        self, crd: Union[rimseval.CRDFileProcessor, List[rimseval.CRDFileProcessor]]
    ) -> None:
        """Update the data required for plotting.

        :param crd: CRD file(s) to plot. If single file, plot only one. If a list,
            use the "plot_multi" feature and deactivate some featuers like shadings.
        """
        if isinstance(crd, rimseval.CRDFileProcessor):  # plot single
            self.button_integrals.setEnabled(True)
            self.button_backgrounds.setEnabled(True)
            self.file_name = crd.fname.with_suffix("").name
            self.mass = crd.mass
            self.tof = crd.tof
            self.data = crd.data
            self.integrals = crd.def_integrals
            self.backgrounds = crd.def_backgrounds
            self.tof_to_chan = crd.us_to_chan
            self._is_multi_plot = False
            self.plot_single()
        else:
            self.button_integrals.setEnabled(False)
            self.button_backgrounds.setEnabled(False)
            self.file_name = [it.fname.with_suffix("").name for it in crd]
            self.mass = [it.mass for it in crd]
            self.tof = [it.tof for it in crd]
            self.data = [it.data for it in crd]
            self.tof_to_chan = None
            self._is_multi_plot = True
            self.plot_multi()
