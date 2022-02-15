"""PyQt Main window to display information on the selected file."""

from PyQt6 import QtCore, QtGui, QtWidgets

import numpy as np
from rimseval import CRDFileProcessor


class FileInfoWindow(QtWidgets.QMainWindow):
    """Display header information of the selected CRD file."""

    def __init__(self, parent):
        """Initialize the window."""
        super().__init__(parent)

        self.parent = parent

        self.setGeometry(QtCore.QRect(0, 50, 300, 200))
        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)

        # labels to set dynamically
        self.nof_shots_used = QtWidgets.QLabel("")
        self.nof_packages = QtWidgets.QLabel("")
        self.nof_ions_used = QtWidgets.QLabel("")
        self.nof_ions_total = QtWidgets.QLabel("")
        self.hdr_file_id = QtWidgets.QLabel("")
        self.hdr_timestamp = QtWidgets.QLabel("")
        self.hdr_crd_version = QtWidgets.QLabel("")
        self.hdr_size_header = QtWidgets.QLabel("")
        self.hdr_shot_pattern = QtWidgets.QLabel("")
        self.hdr_tof_format = QtWidgets.QLabel("")
        self.hdr_polarity = QtWidgets.QLabel("")
        self.hdr_bin_length = QtWidgets.QLabel("")
        self.hdr_bin_start = QtWidgets.QLabel("")
        self.hdr_bin_end = QtWidgets.QLabel("")
        self.hdr_xdim = QtWidgets.QLabel("")
        self.hdr_ydim = QtWidgets.QLabel("")
        self.hdr_shots_per_px = QtWidgets.QLabel("")
        self.hdr_px_per_scan = QtWidgets.QLabel("")
        self.hdr_nof_scans = QtWidgets.QLabel("")
        self.hdr_nof_shots = QtWidgets.QLabel("")
        self.hdr_delta_t = QtWidgets.QLabel("")

        self.all_editable_labels = (
            self.nof_shots_used,
            self.nof_packages,
            self.nof_ions_used,
            self.nof_ions_total,
            self.hdr_file_id,
            self.hdr_timestamp,
            self.hdr_crd_version,
            self.hdr_size_header,
            self.hdr_shot_pattern,
            self.hdr_tof_format,
            self.hdr_polarity,
            self.hdr_bin_length,
            self.hdr_bin_start,
            self.hdr_bin_length,
            self.hdr_xdim,
            self.hdr_ydim,
            self.hdr_shots_per_px,
            self.hdr_px_per_scan,
            self.hdr_nof_scans,
            self.hdr_nof_shots,
            self.hdr_delta_t,
        )

        # init
        self.init_ui()

    def init_ui(self):
        """Initialize the standard style."""

        def add_two_to_layout(
            layout_in: QtWidgets.QVBoxLayout,
            name: str,
            widget: QtWidgets.QWidget,
        ):
            """Create HBoxLayout, add name and widget, then add it to the layout.

            :param layout_in: Layout to add the others to
            :param name: Name of entry
            :param widget: Widget to add for name
            """
            tmp_layout = QtWidgets.QHBoxLayout()
            tmp_layout.addWidget(QtWidgets.QLabel(name))
            tmp_layout.addStretch()
            tmp_layout.addWidget(widget)
            layout_in.addLayout(tmp_layout)

        # fonts
        font_bold = QtGui.QFont()
        font_bold.setBold(True)

        layout = QtWidgets.QVBoxLayout()

        hdr_current = QtWidgets.QLabel("Current File Specifications:")
        hdr_current.setFont(font_bold)
        layout.addWidget(hdr_current)

        layout_current = QtWidgets.QVBoxLayout()
        add_two_to_layout(layout_current, "Shots used:", self.nof_shots_used)
        add_two_to_layout(layout_current, "Shots total:", self.hdr_nof_shots)
        add_two_to_layout(layout_current, "Ions in spectrum:", self.nof_ions_used)
        add_two_to_layout(layout_current, "Ions total:", self.nof_ions_total)
        add_two_to_layout(layout_current, "Number of packages:", self.nof_packages)
        layout.addLayout(layout_current)

        layout.addWidget(QtWidgets.QLabel(""))  # add an empty spacer label

        hdr_header = QtWidgets.QLabel("CRD File Header:")
        hdr_header.setFont(font_bold)
        layout.addWidget(hdr_header)

        layout_hdr = QtWidgets.QVBoxLayout()
        add_two_to_layout(layout_hdr, "File ID:", self.hdr_file_id)
        add_two_to_layout(layout_hdr, "Timestamp:", self.hdr_timestamp)
        add_two_to_layout(layout_hdr, "CRD Version:", self.hdr_crd_version)
        add_two_to_layout(layout_hdr, "Size of Header:", self.hdr_size_header)
        add_two_to_layout(layout_hdr, "Shot Pattern:", self.hdr_shot_pattern)
        add_two_to_layout(layout_hdr, "ToF Format:", self.hdr_tof_format)
        add_two_to_layout(layout_hdr, "Polarity:", self.hdr_polarity)
        add_two_to_layout(layout_hdr, "Bin Length (ps):", self.hdr_bin_length)
        add_two_to_layout(layout_hdr, "Bin Start:", self.hdr_bin_start)
        add_two_to_layout(layout_hdr, "Bin End:", self.hdr_bin_end)
        add_two_to_layout(layout_hdr, "X Dimension:", self.hdr_xdim)
        add_two_to_layout(layout_hdr, "Y Dimension:", self.hdr_ydim)
        add_two_to_layout(layout_hdr, "Shots per pixel:", self.hdr_shots_per_px)
        add_two_to_layout(layout_hdr, "Pixels per Scan:", self.hdr_px_per_scan)
        add_two_to_layout(layout_hdr, "Number of Scans:", self.hdr_nof_scans)
        add_two_to_layout(layout_hdr, "Number of Shots:", self.hdr_nof_shots)
        add_two_to_layout(layout_hdr, "Delta T (s):", self.hdr_delta_t)
        layout.addLayout(layout_hdr)

        # align all editable labels right
        for lbl in self.all_editable_labels:
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.main_widget.setLayout(layout)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """Close event also untoggles the respective button in parent class."""
        self.parent.window_info_action.setChecked(False)
        super().closeEvent(a0)

    def update_current(self, crd: CRDFileProcessor) -> None:
        """Update current shot and package settings."""
        self.nof_shots_used.setText(str(crd.nof_shots))
        self.hdr_nof_shots.setText(str(crd.crd.header["nofShots"]))
        self.nof_ions_used.setText(str(int(np.sum(crd.data))))
        nof_packages = (
            len(crd.nof_shots_pkg) if crd.nof_shots_pkg is not None else "N/A"
        )
        self.nof_ions_total.setText(str(len(crd.crd.all_tofs)))
        self.nof_packages.setText(str(nof_packages))

    def update_header(self, crd: CRDFileProcessor) -> None:
        """Update header values and number of ions total."""

        header = crd.crd.header

        def add_header_info(entry: str, label: QtWidgets.QLabel) -> None:
            """Add a header entry, if it exists, to the widget.

            :param entry: Key in header dictionary.
            :param label: Set value to this label.
            """
            try:
                if isinstance(val := header[entry], bytes):
                    val = val.rstrip(b"\x00").decode("utf-8")
                label.setText(str(val))
            except KeyError:
                label.setText("N/A")

        add_header_info("fileID", self.hdr_file_id)
        add_header_info("startDateTime", self.hdr_timestamp)

        try:
            version = f"{header['majVer']}.{header['minVer']}"
        except KeyError:
            version = "N/A"
        finally:
            self.hdr_crd_version.setText(version)

        add_header_info("sizeOfHeaders", self.hdr_size_header)
        add_header_info("shotPattern", self.hdr_shot_pattern)
        add_header_info("tofFormat", self.hdr_tof_format)
        add_header_info("polarity", self.hdr_polarity)
        add_header_info("binLength", self.hdr_bin_length)
        add_header_info("binStart", self.hdr_bin_start)
        add_header_info("binEnd", self.hdr_bin_end)
        add_header_info("xDim", self.hdr_xdim)
        add_header_info("yDim", self.hdr_ydim)
        add_header_info("shotsPerPixel", self.hdr_shots_per_px)
        add_header_info("pixelPerScan", self.hdr_px_per_scan)
        add_header_info("nofScans", self.hdr_nof_scans)
        add_header_info("nofShots", self.hdr_nof_shots)
        add_header_info("deltaT", self.hdr_delta_t)
