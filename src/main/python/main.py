"""Main RIMSEval graphical user interface."""

from pathlib import Path
import sys

from fbs_runtime.application_context.PyQt6 import ApplicationContext
import fbs_runtime.platform as fbsrt_platform
from PyQt6 import QtCore, QtGui, QtWidgets
import rimseval

from data_models import OpenFilesModel
from data_views import OpenFilesListView
from elements import PeriodicTable
from info_window import FileInfoWindow
from plot_window import PlotWindow


class MainRimsEvalGui(QtWidgets.QMainWindow):
    """Main GUI for the RIMSEval program."""

    def __init__(self, appctxt):
        """Initialize the main window."""
        super().__init__()

        # crd related stuff
        self.crd_files = None

        # local profile
        # fixme change user path back to home only
        self.user_folder = Path.home().joinpath(
            "Documents/ztmp/test"
        )  # initialize, update as necessary
        self.app_local_path = None  # home path for the application configs, etc.
        self.init_local_profile()

        # fbs related stuff
        self.appctxt = appctxt

        # window titles and geometry
        self.setWindowTitle(f"RIMS Evaluation v{rimseval.__version__}")
        self.setGeometry(QtCore.QRect(300, 300, 600, 200))

        # views to access
        self.file_names_view = OpenFilesListView(self)
        self.file_names_model = OpenFilesModel(
            tick=self.appctxt.get_resource("icons/tick.png")
        )  # empty model

        # menu bar
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("&File")
        self.mass_cal_menu = menu_bar.addMenu("&Mass Cal")
        self.integrals_menu = menu_bar.addMenu("&Integrals")
        self.calculate_menu = menu_bar.addMenu("Calculate")
        self.lst_menu = menu_bar.addMenu("&LST Files")
        self.export_menu = menu_bar.addMenu("&Export")
        self.special_menu = menu_bar.addMenu("&Special")
        self.view_menu = menu_bar.addMenu(("&View"))
        self.settings_menu = menu_bar.addMenu("Settings")

        # actions
        self.save_cal_action = None
        self.save_cal_as_action = None
        self.mass_cal_def_action = None
        self.mass_cal_edit_action = None
        self.integrals_set_edit_action = None
        self.integrals_draw_action = None
        self.integrals_fitting_action = None
        self.integrals_copy_action = None
        self.backgrounds_draw_action = None
        self.backgrounds_set_edit_action = None
        self.calculate_single_action = None
        self.calculate_batch_action = None
        self.export_mass_spectrum_action = None
        self.export_tof_spectrum_action = None
        self.window_elements_action = None
        self.window_info_action = None
        self.window_plot_action = None

        # other windows
        self.elements_window = PeriodicTable(self)
        self.info_window = FileInfoWindow(self)
        self.plot_window = PlotWindow(self)

        # bars and layouts of program
        self.main_widget = QtWidgets.QWidget()
        self.status_bar = QtWidgets.QStatusBar()

        # variables to be defined
        self.status_bar_time = 5000  # status bar time in msec

        # add stuff to widget
        self.setCentralWidget(self.main_widget)
        self.setStatusBar(self.status_bar)

        # welcome the user
        self.status_bar.showMessage(
            f"Welcome to RIMSEval v{rimseval.__version__}", msecs=self.status_bar_time
        )

        # initialize the UI
        self.init_menu_toolbar()
        self.init_main_widget()

    def init_local_profile(self):
        """Initialize a user's local profile, platform dependent."""
        if fbsrt_platform.is_windows():
            app_local_path = Path.home().joinpath("AppData/Roaming/RIMSEval/")
        else:
            app_local_path = Path.home().joinpath(".config/RIMSEval/")
        app_local_path.mkdir(parents=True, exist_ok=True)
        self.app_local_path = app_local_path

    def init_main_widget(self):
        """Initialize the main widget."""
        layout = QtWidgets.QHBoxLayout()

        # OPEN FILE NAMES VIEW #
        self.file_names_view.setModel(self.file_names_model)
        self.file_names_view.activated.connect(
            lambda ind: self.current_file_changed(ind)
        )
        self.file_names_view.setToolTip(
            "Double click file to make current.\n"
            "Select multiple with Shift / Ctrl for batch processing."
        )

        layout.addWidget(self.file_names_view)
        self.main_widget.setLayout(layout)

    def init_menu_toolbar(self):
        """Initialize the basics of the menu and tool bar, set the given categories."""
        tool_bar = QtWidgets.QToolBar("Main Toolbar")
        tool_bar.setIconSize(QtCore.QSize(24, 24))

        #  FILE ACTIONS #

        open_crd_action = QtGui.QAction(
            QtGui.QIcon(
                self.appctxt.get_resource("icons/blue-folder-horizontal-open.png")
            ),
            "Open CRD",
            self,
        )
        open_crd_action.setStatusTip("Open CRD file(s)")
        open_crd_action.setShortcut(QtGui.QKeySequence("Ctrl+o"))
        open_crd_action.triggered.connect(self.open_crd)
        self.file_menu.addAction(open_crd_action)
        tool_bar.addAction(open_crd_action)

        save_cal_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/disk-black.png")),
            "Save Calibration",
            self,
        )
        save_cal_action.setStatusTip("Save calibration to default file")
        save_cal_action.setShortcut(QtGui.QKeySequence("Ctrl+s"))
        save_cal_action.triggered.connect(self.save_calibration)
        self.file_menu.addSeparator()
        self.file_menu.addAction(save_cal_action)
        tool_bar.addAction(save_cal_action)
        self.save_cal_action = save_cal_action

        save_cal_as_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Save Calibration As",
            self,
        )
        save_cal_as_action.setStatusTip("Save calibration to specified file")
        save_cal_as_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+s"))
        save_cal_as_action.triggered.connect(
            lambda: self.save_calibration(save_as=True)
        )
        self.file_menu.addAction(save_cal_as_action)
        self.save_cal_as_action = None

        # MASS CAL ACTIONS #

        mass_cal_def_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/target.png")),
            "Create",
            self,
        )
        mass_cal_def_action.setStatusTip("Create a mass calibration")
        mass_cal_def_action.triggered.connect(self.create_mass_calibration)
        self.mass_cal_menu.addAction(mass_cal_def_action)
        tool_bar.addSeparator()
        tool_bar.addAction(mass_cal_def_action)
        self.mass_cal_def_action = mass_cal_def_action

        mass_cal_edit_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Edit",
            self,
        )
        mass_cal_edit_action.setStatusTip("Edit the existing mass calibration")
        mass_cal_edit_action.triggered.connect(self.edit_mass_calibration)
        self.mass_cal_menu.addAction(mass_cal_edit_action)
        self.mass_cal_def_action = mass_cal_def_action

        # INTEGRALS ACTIONS #

        integrals_set_edit_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Set / Edit Integrals",
            self,
        )
        integrals_set_edit_action.setStatusTip("Set new or edit existing integrals.")
        integrals_set_edit_action.triggered.connect(self.integrals_set_edit)
        self.integrals_menu.addAction(integrals_set_edit_action)
        self.integrals_set_edit_action = integrals_set_edit_action

        integrals_draw_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/system-monitor.png")),
            "Draw Integrals",
            self,
        )
        integrals_draw_action.setStatusTip("Define integrals by drawing them")
        integrals_draw_action.triggered.connect(
            lambda val=False: self.save_calibration(val)
        )
        self.integrals_menu.addAction(integrals_draw_action)
        tool_bar.addAction(integrals_draw_action)
        self.integrals_draw_action = integrals_draw_action

        integrals_fitting_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Define integrals by fitting",
            self,
        )
        integrals_fitting_action.setStatusTip("Fit the peaks to define integrals")
        integrals_fitting_action.triggered.connect(self.integrals_fitting)
        self.integrals_menu.addAction(integrals_fitting_action)
        self.integrals_fitting_action = integrals_fitting_action
        # todo
        integrals_fitting_action.setDisabled(True)

        integrals_copy_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/table-export.png")),
            "Copy Integrals",
            self,
        )
        integrals_copy_action.setStatusTip("Copy all integrals to the clipboard")
        integrals_copy_action.setShortcut(QtGui.QKeySequence("Ctrl+c"))
        integrals_copy_action.triggered.connect(self.integrals_copy_to_clipboard)
        self.integrals_menu.addSeparator()
        self.integrals_menu.addAction(integrals_copy_action)
        tool_bar.addSeparator()
        tool_bar.addAction(integrals_copy_action)
        self.integrals_copy_action = None

        backgrounds_draw_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Draw Backgrounds",
            self,
        )
        backgrounds_draw_action.setStatusTip("Define backgrounds by drawing them.")
        backgrounds_draw_action.triggered.connect(self.backgrounds_draw)
        self.integrals_menu.addSeparator()
        self.integrals_menu.addAction(backgrounds_draw_action)
        self.backgrounds_draw_action = backgrounds_draw_action

        backgrounds_set_edit_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Set / Edit Backgrounds",
            self,
        )
        backgrounds_set_edit_action.setStatusTip("Set / edit backgrounds")
        backgrounds_set_edit_action.triggered.connect(self.backgrounds_set_edit)
        self.integrals_menu.addAction(backgrounds_set_edit_action)
        self.backgrounds_set_edit_action = backgrounds_set_edit_action

        # CALCULATE ACTIONS #

        calculate_single_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/wand.png")),
            "Calculate single",
            self,
        )
        calculate_single_action.setStatusTip(
            "Apply the specified configuration to displayed CRD file"
        )
        calculate_single_action.setShortcut(QtGui.QKeySequence("Ctrl+r"))
        calculate_single_action.triggered.connect(self.calculate_single)
        self.calculate_menu.addAction(calculate_single_action)
        tool_bar.addSeparator()
        tool_bar.addAction(calculate_single_action)
        self.calculate_single_action = calculate_single_action

        calculate_batch_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/wand-hat.png")),
            "Calculate batch",
            self,
        )
        calculate_batch_action.setStatusTip(
            "Apply the specified configuration to all open CRD files"
        )
        calculate_batch_action.triggered.connect(self.calculate_batch)
        self.calculate_menu.addAction(calculate_batch_action)
        tool_bar.addAction(calculate_batch_action)
        self.calculate_batch_action = calculate_batch_action

        # LST FILE ACTIONS #

        lst_convert_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/blue-folder-import.png")),
            "Convert LST to CRD",
            self,
        )
        lst_convert_action.setStatusTip("Convert LST to CRD file(s)")
        lst_convert_action.setShortcut(QtGui.QKeySequence("Ctrl+l"))
        lst_convert_action.triggered.connect(self.convert_lst_to_crd)
        self.lst_menu.addAction(lst_convert_action)
        tool_bar.addSeparator()
        tool_bar.addAction(lst_convert_action)

        # EXPORT ACTIONS #
        export_mass_spectrum_action = QtGui.QAction(
            QtGui.QIcon(),
            "Export Mass Spectrum",
            self,
        )
        export_mass_spectrum_action.setStatusTip("Export Mass Spectrum as csv file.")
        export_mass_spectrum_action.triggered.connect(self.export_spectrum_as_csv)
        self.export_menu.addAction(export_mass_spectrum_action)
        self.export_mass_spectrum_action = export_mass_spectrum_action
        # todo
        self.export_mass_spectrum_action.setDisabled(True)

        export_tof_spectrum_action = QtGui.QAction(
            QtGui.QIcon(),
            "Export ToF Spectrum",
            self,
        )
        export_tof_spectrum_action.setStatusTip(
            "Export Time of Flight Spectrum as csv file."
        )
        export_tof_spectrum_action.triggered.connect(
            lambda: self.export_spectrum_as_csv(tof=True)
        )
        self.export_menu.addAction(export_tof_spectrum_action)
        self.export_tof_spectrum_action = export_tof_spectrum_action
        # todo
        self.export_tof_spectrum_action.setDisabled(True)

        # VIEW ACIONS #

        window_info_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/information.png")),
            "CRD Information",
            self,
        )
        window_info_action.setStatusTip("Show / Hide CRD header information window")
        window_info_action.setShortcut(QtGui.QKeySequence("Ctrl+i"))
        window_info_action.triggered.connect(self.window_info)
        window_info_action.setCheckable(True)
        self.view_menu.addAction(window_info_action)
        tool_bar.addSeparator()
        tool_bar.addAction(window_info_action)
        self.window_info_action = window_info_action

        window_plot_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/image.png")),
            "Mass Spectrum",
            self,
        )
        window_plot_action.setStatusTip("Show / Hide mass spectrum")
        window_plot_action.setShortcut(QtGui.QKeySequence("Ctrl+m"))
        window_plot_action.triggered.connect(self.window_plot)
        window_plot_action.setCheckable(True)
        self.view_menu.addAction(window_plot_action)
        tool_bar.addAction(window_plot_action)
        self.window_plot_action = window_plot_action

        window_elements_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/color-swatch.png")),
            "Periodic Table",
            self,
        )
        window_elements_action.setStatusTip("Show / Hide periodic table")
        window_elements_action.setShortcut(QtGui.QKeySequence("Ctrl+t"))
        window_elements_action.triggered.connect(self.window_elements)
        window_elements_action.setCheckable(True)
        self.view_menu.addAction(window_elements_action)
        tool_bar.addSeparator()
        tool_bar.addAction(window_elements_action)
        self.window_elements_action = window_elements_action

        # SETTINGS ACTIONS #

        settings_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/gear.png")),
            "Settings",
            self,
        )
        settings_action.setStatusTip("Bring up settings dialog")
        settings_action.triggered.connect(self.window_plot)
        self.settings_menu.addAction(settings_action)
        tool_bar.addSeparator()
        tool_bar.addAction(settings_action)

        # add toolbar to self
        self.addToolBar(tool_bar)

    # PROPERTIES #

    @property
    def current_crd_file(self):
        """Return currently active CRD file."""
        if self.crd_files is not None:
            return self.crd_files.files[self.file_names_model.currently_active]

    # FILE MENU FUNCTIONS #

    def open_crd(self):
        """Open CRD File(s)."""
        file_names = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open CRD File(s)",
            str(self.user_folder.absolute()),
            "CRD Files (*.crd)",
        )[0]

        if len(file_names) > 0:
            # close files and remove from memory if they exist
            if self.crd_files:
                self.crd_files.close_files()

            file_paths = [Path(file_name) for file_name in file_names]

            # set user path to this folder
            self.user_folder = file_paths[0].parent

            self.crd_files = rimseval.MultiFileProcessor(file_paths)

            # fixme do not evaluate unless user wants...
            # self.crd_files.read_files()

            self.file_names_model.set_new_list(file_paths)

            self.update_info_window(update_all=True)

    def save_calibration(self, save_as: bool = False):
        """Save Calibration.

        :param save_as: If True, brings up a dialog to save calibration to given file.
        """
        print(save_as)

    # MASS CALIBRATION FUNCTIONS #
    def create_mass_calibration(self):
        """Enable user to create a mass calibration."""

    def edit_mass_calibration(self):
        """Edit the mass calibration."""

    # INTEGRAL DEFINITION FUNCTIONS #

    def integrals_draw(self):
        """Enable user to draw integrals."""
        pass

    def integrals_set_edit(self):
        """Enable user to set integrals with a table widget."""
        pass

    def integrals_fitting(self):
        """Define integrals by fitting them."""
        # todo in second version
        raise NotImplementedError

    def integrals_copy_to_clipboard(self):
        """Copy the integrals to the clipboard for pasting into, e.g., Excel."""
        pass

    def backgrounds_draw(self):
        """Open GUI for user to draw backgrounds."""
        pass

    def backgrounds_set_edit(self):
        """Open GUI for user to set / edit backgrounds by hand."""
        pass

    # CALCULATE FUNCTIONS #

    def calculate_single(self):
        """Applies the currently displayed settings to the displayed CRD file."""
        pass

    def calculate_batch(self):
        """Applies the currently congured settings to all open CRD files."""
        # get the currently selected files
        selected_models = self.file_names_view.selectedIndexes()
        selected_indexes = [it.row() for it in selected_models]
        print(selected_indexes)

    # LST FILE FUNCTIONS #

    def convert_lst_to_crd(self):
        """Convert LST to CRD File(s)."""
        pass

    # EXPORT FUNCTIONS #

    def export_spectrum_as_csv(self, tof: bool = False) -> None:
        """Export a spectrum to a csv file.

        :param tof: If true, export ToF spectrum, otherwise mass spectrum.
        """
        print(tof)

    # SPECIAL FUNCTIONS #

    # VIEW FUNCTIONS #

    def window_elements(self):
        """Show / Hide information window."""
        if self.window_elements_action.isChecked():
            self.elements_window.show()
        else:
            self.elements_window.close()

    def window_info(self):
        """Show / Hide information window."""
        if self.window_info_action.isChecked():
            self.info_window.show()
        else:
            self.info_window.close()

    def window_plot(self):
        """Show / Hide plot window."""
        if self.window_plot_action.isChecked():
            self.plot_window.show()
        else:
            self.plot_window.close()

    # SETTINGS FUNCTIONS #

    def window_settings(self):
        """Settings Dialog."""
        pass

    # ACTIONS ON CHANGED MODEL VIEWS #

    def current_file_changed(self, ind: QtCore.QModelIndex) -> None:
        """Reacts to a different file that is currently selected."""
        self.file_names_model.update_current(ind.row())

        # update windows
        self.update_info_window(update_all=True)

    def update_info_window(self, update_all: bool = False) -> None:
        """Update the Info window.

        :param update_all: If True, header information is updated as well.
        """
        crd_file = self.current_crd_file
        self.info_window.update_current(crd_file)
        if update_all:
            self.info_window.update_header(crd_file)


if __name__ == "__main__":
    appctxt = ApplicationContext()  # 1. Instantiate ApplicationContext
    window = MainRimsEvalGui(appctxt)
    window.show()
    exit_code = appctxt.app.exec()  # 2. Invoke appctxt.app.exec()
    sys.exit(exit_code)