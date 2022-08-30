"""File to show my own PyQtDialogs."""

from typing import List

from iniabu.utilities import item_formatter
from PyQt6 import QtCore, QtGui, QtWidgets
import numpy as np
from rimseval import processor_utils as pu
from rimseval.utilities import ini

from data_models import IntegralBackgroundDefinitionModel, NormIsosModel
from data_views import IntegralBackgroundTableView


class AboutDialog(QtWidgets.QDialog):
    """Present an about dialog."""

    def __init__(self, parent=None):
        """Initialize the dialog.

        :param parent: Parent widget.
        """
        super().__init__(parent)

        self.setWindowTitle("About RIMSEval")
        self.version = parent.version
        self.theme = parent.config.get("Theme")
        self.about_text()

    def about_text(self):
        """Set the about text for the dialog."""
        layout = QtWidgets.QVBoxLayout()

        font_bold = QtGui.QFont()
        font_bold.setBold(True)

        title = QtWidgets.QLabel(f"RIMSEval {self.version}")
        title.setFont(font_bold)
        layout.addWidget(title)

        docs = QtWidgets.QLabel(
            f"Documentation can be found at:<br>"
            f"{html_url('https://rimseval.readthedocs.io', theme=self.theme)}"
        )
        docs.setOpenExternalLinks(True)
        layout.addWidget(docs)

        repo1 = QtWidgets.QLabel(
            f"GitHub repository for <code>rimseval</code> package<br>"
            f"{html_url('https://github.com/RIMS-Code/RIMSEval', theme=self.theme)}"
        )
        repo1.setOpenExternalLinks(True)
        layout.addWidget(repo1)

        repo2 = QtWidgets.QLabel(
            f"GitHub repository for the GUI<br>"
            f"{html_url('https://github.com/RIMS-Code/RIMSEvalGUI', theme=self.theme)}"
        )
        repo2.setOpenExternalLinks(True)
        layout.addWidget(repo2)

        issues = QtWidgets.QLabel(
            "If you encounter problems with this package, please<br>"
            "open a new issue on GitHub with a detailed description.<br>"
            "You can also include problematic files in your issue.<br>"
            "Issues can be posted in either repository."
        )
        layout.addWidget(issues)

        author = QtWidgets.QLabel("Reto Trappitsch, 2022")
        layout.addWidget(author)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)


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
        delete_selected_button = QtWidgets.QPushButton("Delete Selected")
        delete_selected_button.clicked.connect(self.delete_selected)
        add_row_button = QtWidgets.QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_row)
        tmp_layout = QtWidgets.QHBoxLayout()
        tmp_layout.addStretch()
        tmp_layout.addWidget(clear_all_button)
        tmp_layout.addWidget(delete_selected_button)
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
                return
        super().accept()

    def add_row(self):
        """Add a row to the data."""
        self.model.add_row()

    def clear_all(self):
        """Clear all data and add 10 empty rows."""
        self.model.init_empty()

    def delete_selected(self):
        """Delete selected rows."""
        selected_indexes = self.table_edit.selectedIndexes()
        rows = set()
        for ind in selected_indexes:
            rows.add(ind.row())

        if len(rows) > 0:
            self.model.delete_selected(list(rows))


class CheckForUpdatesDialog(QtWidgets.QDialog):
    """Dialog that displays if updates are available or not."""

    def __init__(
        self,
        parent=None,
        curr_version: str = None,
        latest_version: str = None,
        status: int = None,
    ):
        """Initialize the class.

        :param parent: Parent widget
        :param curr_version: Current version of the GUI
        :param latest_version: Latest version available on GitHub
        :param status: Status indicator.
            0: Updates available
            1: Up to date
            2: Connection error
            3: Local version unknown
        """
        super().__init__(parent)

        self.setWindowTitle("Check for updates...")
        self.theme = parent.config.get("Theme")

        self.curr_version = curr_version
        self.latest_version = latest_version
        self.status = status

        self.repo_url_release = (
            "https://github.com/RIMS-Code/RIMSEvalGUI/releases/latest"
        )

        self.version_text()

    def version_text(self):
        """Set the about text for the dialog."""
        layout = QtWidgets.QVBoxLayout()

        font_status = QtGui.QFont()
        font_status.setBold(True)
        tmp_point_size = font_status.pointSize()
        font_status.setPointSize(tmp_point_size + 4)

        curr_version_label = QtWidgets.QLabel(
            f"Current GUI version:\t{self.curr_version}"
        )
        layout.addWidget(curr_version_label)
        latest_version_label = QtWidgets.QLabel(
            f"Latest GUI version:\t{self.latest_version}"
        )
        layout.addWidget(latest_version_label)

        # determine final text with the conclusion
        disp_update_link = True
        if self.status == 3:
            conc_text = "Cannot determine current version of GUI."
        elif self.status == 2:
            conc_text = "Cannot connect to GitHub."
        elif self.status == 0:
            conc_text = "Updates available."
        elif self.status == 1:
            conc_text = "You are up to date."
            disp_update_link = False
        else:
            conc_text = "Unknown error occurred."

        layout.addStretch()

        conc_widget = QtWidgets.QLabel(conc_text)
        conc_widget.setFont(font_status)
        conc_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        conc_widget.setFixedHeight(50)
        layout.addWidget(conc_widget)

        if disp_update_link:
            layout.addStretch()
            latest_release_label = QtWidgets.QLabel(
                f"Latest releases can be found here<br>"
                f"{html_url(self.repo_url_release, theme=self.theme)}"
            )
            layout.addWidget(latest_release_label)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)


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
        self.element_entry = QtWidgets.QLineEdit()
        self.mass_offset = QtWidgets.QDoubleSpinBox()
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

        element_layout = QtWidgets.QHBoxLayout()
        self.element_entry.setToolTip(
            "Enter an element name to add within\nselect range and mass offset"
        )
        self.mass_offset.setRange(-99, 99)
        self.mass_offset.setDecimals(5)
        self.mass_offset.setSingleStep(0.1)
        self.mass_offset.setValue(0)
        self.mass_offset.setToolTip("Mass offset (amu)")
        element_button = QtWidgets.QPushButton("Add All Isotopes")
        element_button.clicked.connect(self.add_element)
        element_layout.addWidget(self.element_entry)
        element_layout.addWidget(self.mass_offset)
        element_layout.addWidget(element_button)
        layout.addLayout(element_layout)

        layout.addWidget(self.table_edit)

        clear_all_button = QtWidgets.QPushButton("Clear All")
        clear_all_button.clicked.connect(self.clear_all)
        delete_selected_button = QtWidgets.QPushButton("Delete Selected")
        delete_selected_button.clicked.connect(self.delete_selected)
        add_row_button = QtWidgets.QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_row)
        tmp_layout = QtWidgets.QHBoxLayout()
        tmp_layout.addStretch()
        tmp_layout.addWidget(clear_all_button)
        tmp_layout.addWidget(delete_selected_button)
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

    def accept(self):
        """Ensure peaks don't overlap, then accept the user input."""
        integral_vals = self.model.return_data()[1]
        if pu.check_peaks_overlap(integral_vals):
            QtWidgets.QMessageBox.warning(
                self, "Peak overlap", "Peaks overlap, please correct and try again."
            )
            return
        super().accept()

    def add_element(self):
        """Adds all isotopes of an element with set range and mass offset."""
        element = self.element_entry.text()
        try:
            isos = ini.iso[element]
        except IndexError:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid element",
                f"Cannot find isotopes for element {element}.",
            )
            return None

        names = isos.name
        masses = isos.mass

        lower_limit = float(self.lower_limit_autofill.value())
        upper_limit = float(self.upper_limit_autofill.value())
        offset = float(self.mass_offset.value())

        masses += offset

        values = np.zeros((len(names), 2))
        for it, mass in enumerate(masses):
            values[it][0] = masses[it] - lower_limit
            values[it][1] = masses[it] + upper_limit

        self.model.add_element(names, values)

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

    def delete_selected(self):
        """Delete selected rows."""
        selected_indexes = self.table_edit.selectedIndexes()
        rows = set()
        for ind in selected_indexes:
            rows.add(ind.row())

        if len(rows) > 0:
            self.model.delete_selected(list(rows))


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


class NormIsosDialog(QtWidgets.QDialog):
    """Set / Edit normalization isotopes dialog."""

    def __init__(self, model: NormIsosModel, data: dict = {}, parent=None):
        """Initialize the dialog

        :param model: Model to set to ``EditableTableView``
        :param data: List of existing elements.
        :param parent: Parent widget
        """
        super().__init__(parent)

        self.data = data

        self.setWindowTitle("Set / Edit Normalization Isotopes")

        self.add_ele = QtWidgets.QLineEdit()
        self.add_iso = QtWidgets.QLineEdit()

        self.table_edit = IntegralBackgroundTableView()
        self.model = model
        self.table_edit.setModel(self.model)

        self.init_ui()

    def init_ui(self):
        """Initialize the dialog."""
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.table_edit)

        self.add_ele.setFixedWidth(120)
        self.add_ele.setToolTip("Element name, e.g., 'Ba'.")
        self.add_iso.setFixedWidth(120)
        self.add_iso.setToolTip("Normalizing isotope name, e.g., 'Ba-136'")

        edit_hbox = QtWidgets.QHBoxLayout()
        edit_hbox.addWidget(self.add_ele)
        edit_hbox.addStretch()
        edit_hbox.addWidget(QtWidgets.QLabel(":"))
        edit_hbox.addStretch()
        edit_hbox.addWidget(self.add_iso)
        layout.addLayout(edit_hbox)
        add_button = QtWidgets.QPushButton("Add new entry")
        add_button.clicked.connect(self.add_new_entry)
        layout.addWidget(add_button)

        clear_all_button = QtWidgets.QPushButton("Clear All")
        clear_all_button.clicked.connect(self.clear_all)
        clear_selected_button = QtWidgets.QPushButton("Delete Selected")
        clear_selected_button.clicked.connect(self.delete_selected)
        tmp_layout = QtWidgets.QHBoxLayout()
        tmp_layout.addStretch()
        tmp_layout.addWidget(clear_all_button)
        tmp_layout.addWidget(clear_selected_button)
        layout.addLayout(tmp_layout)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Help
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        button_box.helpRequested.connect(self.help)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def add_new_entry(self):
        """Add a new entry to the model."""
        ele = self.add_ele.text()
        iso = self.add_iso.text()

        if ele == "" or iso == "":
            QtWidgets.QMessageBox.warning(
                self,
                "Add entries",
                "Please fill out the element and isotope fields above.",
            )
            return None

        try:
            ele = item_formatter(ele)
            iso = item_formatter(iso)
        except Exception as err:
            QtWidgets.QMessageBox.warning(
                self, "Error occurred when parsing element / isotope name", err.args[0]
            )

        if "-" in ele:
            QtWidgets.QMessageBox.warning(
                self,
                "Please select an element",
                "Please select an element for the parent (left entry), not an isotope.",
            )
            return None

        # try valid element
        try:
            _ = ini.ele[ele]
        except IndexError:
            QtWidgets.QMessageBox.warning(
                self,
                "Element invalid",
                "Please select a valid element in its short form, e.g., Ba.",
            )
            return None

        # try valid isotope
        try:
            _ = ini.iso[iso]
        except IndexError:
            QtWidgets.QMessageBox.warning(
                self,
                "Isotope invalid",
                "Please select a valid isotope in its short form, e.g., Ba-136.",
            )
            return None

        self.model.add_entry(ele, iso)
        self.add_ele.setText("")
        self.add_iso.setText("")

    def clear_all(self):
        """Clear all data and add 10 empty rows."""
        self.model.init_empty()

    def delete_selected(self):
        """Delete selected rows."""
        selected_indexes = self.table_edit.selectedIndexes()
        rows = set()
        for ind in selected_indexes:
            rows.add(ind.row())

        if len(rows) > 0:
            self.model.delete_selected(list(rows))

    def help(self):
        """Display a help / info dialog."""
        QtWidgets.QMessageBox.information(
            self,
            "Information",
            "Please select the element and requested normalizing isotope. If no "
            "normalizing isotope is selected, the program will automatically use "
            "the most abundant one as the normalizing isotope of a given element.",
        )


# METHODS #


def html_url(url: str, name: str = None, theme: str = "") -> str:
    """Create a HTML string for the URL and return it.

    :param url: URL to set
    :param name: Name of the URL, if None, use same as URL.
    :param theme: "dark" or other theme.

    :return: String with the correct formatting for URL
    """
    if theme == "dark":
        color = "#988fd4"
    else:
        color = "#1501a3"

    if name is None:
        name = url
    retval = f'<a href="{url}" style="color:{color}">{name}</a>'
    return retval
