"""File to show my own PyQtDialogs."""

from PyQt6 import QtGui, QtWidgets
import numpy as np


class MassCalDialog(QtWidgets.QDialog):
    """Mass Calibration Dialog to show current values."""

    def __init__(self, mcal: np.ndarray, parent=None) -> None:
        """Initialize the mass calibration dialog

        :param mcal: Mass calibration, directly from crd file.
        :param parent: Parent widget
        """
        super().__init__(parent)

        self.mcal = mcal

        self.setWindowTitle("Current Mass Cal.")

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        button_box.accepted.connect(self.close)

        self.layout = QtWidgets.QVBoxLayout()
        self.fill_mcal_data()  # add the data
        self.layout.addWidget(button_box)  # add button
        self.setLayout(self.layout)

    def fill_mcal_data(self):
        """Fill the layout with some data from the mass calibration."""
        hdr_font = QtGui.QFont()
        hdr_font.setBold(True)

        tmp_hbox = QtWidgets.QHBoxLayout()
        tmp_hbox.addWidget(QtWidgets.QLabel("ToF (us)"))
        tmp_hbox.addWidget(QtWidgets.QLabel("Mass (amu)"))
        self.layout.addLayout(tmp_hbox)

        for tm, ms in self.mcal:
            tmp_hbox = QtWidgets.QHBoxLayout()
            tmp_hbox.addWidget(QtWidgets.QLabel(f"{tm:.3f}"))
            tmp_hbox.addWidget(QtWidgets.QLabel(f"{ms:.3f}"))
            self.layout.addLayout(tmp_hbox)
