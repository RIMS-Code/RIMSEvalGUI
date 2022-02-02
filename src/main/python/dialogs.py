"""File to show my own PyQtDialogs."""

from typing import List

from PyQt6 import QtGui, QtWidgets
import numpy as np
from rimseval.utilities import ini

from data_models import IntegralBackgroundDefinitionModel
from data_views import IntegralBackgroundTableView


class BackgroundEditDialog(QtWidgets.QDialog):
    """Set / Edit backgrounds dialog."""

    def __init__(
        self, model: IntegralBackgroundDefinitionModel, peaks: List, parent=None
    ):
        """Initialize the dialog

        :param model: Model to set to ``EditableTableView``
        :param peaks: List of defined peak names
        :param parent: Parent widget
        """
        super().__init__(parent)

        self.peaks = peaks

        self.setWindowTitle("Add / Edit Backgrounds")

        self.table_edit = IntegralBackgroundTableView()
        self.model = model
        self.table_edit.setModel(self.model)

        self.init_ui()

    def init_ui(self):
        """Initialize the dialog."""
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.table_edit)

        clear_all_button = QtWidgets.QPushButton("Clear All")
        clear_all_button.clicked.connect(self.clear_all)
        add_row_button = QtWidgets.QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_row)
        tmp_layout = QtWidgets.QHBoxLayout()
        tmp_layout.addStretch()
        tmp_layout.addWidget(clear_all_button)
        tmp_layout.addWidget(add_row_button)
        layout.addLayout(tmp_layout)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def accept(self) -> None:
        """Ensure that the names are unique and accept."""
        peak_list_str = "\n".join(self.peaks)
        self.model.remove_empties()
        for name in self.model.names:
            if name not in self.peaks:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Undefined Peak",
                    f"The given names must be in the background list. However, "
                    f"{name} is not in the peak list. Valid peaks are:\n"
                    f"{peak_list_str}",
                )
        super().accept()

    def add_row(self):
        """Add a row to the data."""
        self.model.add_row()

    def clear_all(self):
        """Clear all data and add 10 empty rows."""
        self.model.init_empty()


class IntegralEditDialog(QtWidgets.QDialog):
    """Set / Edit integrals dialog."""

    def __init__(self, model: IntegralBackgroundDefinitionModel, parent=None):
        """Initialize the dialog

        :param model: Model to set to ``EditableTableView``
        :param parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Add / Edit Integrals")

        self.lower_limit_autofill = QtWidgets.QDoubleSpinBox()
        self.upper_limit_autofill = QtWidgets.QDoubleSpinBox()
        self.table_edit = IntegralBackgroundTableView()
        self.model = model
        self.table_edit.setModel(self.model)

        self.init_ui()

    def init_ui(self):
        """Initialize the dialog."""
        layout = QtWidgets.QVBoxLayout()

        self.lower_limit_autofill.setRange(0, 99)
        self.lower_limit_autofill.setSingleStep(0.1)
        self.lower_limit_autofill.setDecimals(5)
        self.upper_limit_autofill.setRange(0, 99)
        self.upper_limit_autofill.setSingleStep(0.1)
        self.upper_limit_autofill.setDecimals(5)
        auto_layout = QtWidgets.QHBoxLayout()
        auto_layout.addWidget(QtWidgets.QLabel("Limits"))
        auto_layout.addWidget(self.lower_limit_autofill)
        auto_layout.addWidget(self.upper_limit_autofill)
        auto_fill_button = QtWidgets.QPushButton("Auto fill")
        auto_fill_button.clicked.connect(self.auto_fill_values)
        auto_layout.addStretch()
        auto_layout.addWidget(auto_fill_button)

        layout.addLayout(auto_layout)

        layout.addWidget(self.table_edit)

        clear_all_button = QtWidgets.QPushButton("Clear All")
        clear_all_button.clicked.connect(self.clear_all)
        add_row_button = QtWidgets.QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_row)
        tmp_layout = QtWidgets.QHBoxLayout()
        tmp_layout.addStretch()
        tmp_layout.addWidget(clear_all_button)
        tmp_layout.addWidget(add_row_button)
        layout.addLayout(tmp_layout)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def add_row(self):
        """Add a row to the data."""
        self.model.add_row()

    def auto_fill_values(self):
        """Automatically fill the values for the integrals based on mass or isotope."""
        self.model.remove_empties()
        masses = []
        for item in self.model.names:
            try:
                masses.append(float(item))  # user gave a mass
            except ValueError:
                try:
                    masses.append(ini.iso[item].mass)  # user gave an isotope
                except IndexError:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Invalid mass",
                        f"Cannot determine a mass for entry {item}.",
                    )
                    return None
        self.model.auto_fill(
            masses, self.lower_limit_autofill.value(), self.upper_limit_autofill.value()
        )

    def clear_all(self):
        """Clear all data and add 10 empty rows."""
        self.model.init_empty()


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
