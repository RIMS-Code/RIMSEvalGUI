"""Main RIMSEval graphical user interface."""

from pathlib import Path
import sys

from fbs_runtime.application_context.PyQt6 import ApplicationContext
import fbs_runtime.platform as fbsrt_platform
from PyQt6 import QtCore, QtGui, QtWidgets
from pyqtconfig import ConfigDialog, ConfigManager
import qdarktheme
import rimseval

from data_models import IntegralBackgroundDefinitionModel, OpenFilesModel
from data_views import OpenFilesListView
from dialogs import BackgroundEditDialog, IntegralEditDialog, MassCalDialog
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
        self.user_folder = Path.home()
        self.app_local_path = None  # home path for the application configs, etc.
        self.init_local_profile()

        self.config = None

        # fbs related stuff
        self.appctxt = appctxt

        # window titles and geometry
        self.setWindowTitle(f"RIMS Evaluation v{rimseval.__version__}")
        self.setGeometry(QtCore.QRect(300, 300, 700, 400))

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
        self.load_cal_action = None
        self.save_cal_action = None
        self.save_cal_as_action = None
        self.mass_cal_def_action = None
        self.mass_cal_show_action = None
        self.integrals_set_edit_action = None
        self.integrals_draw_action = None
        self.integrals_fitting_action = None
        self.integrals_copy_action = None
        self.integrals_copy_pkg_action = None
        self.backgrounds_draw_action = None
        self.backgrounds_set_edit_action = None
        self.calculate_single_action = None
        self.calculate_batch_action = None
        self.export_mass_spectrum_action = None
        self.export_tof_spectrum_action = None
        self.special_hist_dt_ions_action = None
        self.special_hist_ions_shot_action = None
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
        self.init_config_manager()

        self.setStyleSheet(qdarktheme.load_stylesheet(self.config.get("Theme")))

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

        # FILE ACTIONS #

        # INTEGRALS VIEW #

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

        load_cal_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Load calibration",
            self,
        )
        load_cal_action.setStatusTip("Load calibration file")
        load_cal_action.triggered.connect(self.load_calibration)
        self.file_menu.addSeparator()
        self.file_menu.addAction(load_cal_action)
        self.load_cal_action = load_cal_action

        save_cal_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/disk-black.png")),
            "Save Calibration",
            self,
        )
        save_cal_action.setStatusTip("Save calibration to default file")
        save_cal_action.setShortcut(QtGui.QKeySequence("Ctrl+s"))
        save_cal_action.triggered.connect(self.save_calibration)
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

        file_exit_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/application-export.png")),
            "Exit",
            self,
        )
        file_exit_action.setStatusTip("Exit program")
        file_exit_action.setShortcut(QtGui.QKeySequence("Ctrl+q"))
        file_exit_action.triggered.connect(self.close)
        self.file_menu.addSeparator()
        self.file_menu.addAction(file_exit_action)

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

        mass_cal_show_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Show current calibration",
            self,
        )
        mass_cal_show_action.setStatusTip("Show the existing mass calibration")
        mass_cal_show_action.triggered.connect(self.show_mass_calibration)
        self.mass_cal_menu.addAction(mass_cal_show_action)
        self.mass_cal_show_action = mass_cal_show_action

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
        integrals_draw_action.triggered.connect(self.integrals_draw)
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
        self.integrals_copy_action = integrals_copy_action

        integrals_copy_pkg_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Copy Integrals Packages",
            self,
        )
        integrals_copy_pkg_action.setStatusTip(
            "Copy integrals of all packages to the clipboard"
        )
        integrals_copy_pkg_action.triggered.connect(
            self.integrals_pkg_copy_to_clipboard
        )
        self.integrals_menu.addAction(integrals_copy_pkg_action)
        self.integrals_copy_pkg_action = integrals_copy_pkg_action

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

        # SPECIAL ACTIONS #

        special_hist_ions_shot_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Histogram Ions/Shot",
            self,
        )
        special_hist_ions_shot_action.setStatusTip("Show a histogram of ions per shot.")
        special_hist_ions_shot_action.triggered.connect(self.histogram_ions_per_shot)
        self.special_menu.addAction(special_hist_ions_shot_action)
        self.special_hist_ions_shot_action = special_hist_ions_shot_action
        # todo
        self.special_hist_ions_shot_action.setDisabled(True)

        special_hist_dt_ions_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Histogram dt ions",
            self,
        )
        special_hist_dt_ions_action.setStatusTip(
            "Show a histogram for multi-ion shots with time differences between ions."
        )
        special_hist_dt_ions_action.triggered.connect(self.histogram_ions_per_shot)
        self.special_menu.addAction(special_hist_dt_ions_action)
        self.special_hist_dt_ions_action = special_hist_dt_ions_action
        # todo
        self.special_hist_dt_ions_action.setDisabled(True)

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
        settings_action.triggered.connect(self.window_settings)
        self.settings_menu.addAction(settings_action)
        tool_bar.addSeparator()
        tool_bar.addAction(settings_action)

        # exit button
        tool_bar.addSeparator()
        tool_bar.addAction(file_exit_action)

        # add toolbar to self
        self.addToolBar(tool_bar)

    def init_config_manager(self):
        """Initialize the configuration manager and load the default configuration."""
        default_values = {
            "Plot with log y-axis": True,
            "Calculate on open": True,
            "Signal Channel": 1,
            "Tag Channel": 2,
            "Peak FWHM (us)": 0.02,
            "Theme": "light",
        }

        default_settings_metadata = {
            "Theme": {
                "preferred_handler": QtWidgets.QComboBox,
                "preferred_map_dict": {"Dark Colors": "dark", "Light Colors": "light"},
            }
        }

        self.config = ConfigManager(
            default_values, filename=self.app_local_path.joinpath("config.json")
        )
        self.config.set_many_metadata(default_settings_metadata)

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
            self.crd_files.open_files()  # open, but no read

            # apply specifications if here:
            for crd in self.crd_files.files:
                if (calfile := crd.fname.with_suffix(".json")).is_file():
                    pass
                elif (
                    calfile := self.app_local_path.joinpath("calibration.json")
                ).is_file():
                    pass
                else:
                    calfile = None
                if calfile:
                    rimseval.interfacer.load_cal_file(crd, calfile)

            if self.config.get("Calculate on open"):

                self.crd_files.read_files()

                # mass calibration
                for crd in self.crd_files.files:
                    if crd.def_mcal is not None:
                        crd.mass_calibration()

            self.file_names_model.set_new_list(file_paths)

            self.update_info_window(update_all=True)

    def load_calibration(self, fname: Path = None):
        """Load a specific calibration file.

        :param fname: If None, then bring up a dialog to query for the file.
        """
        if fname is None:
            query = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open Calibration File",
                str(self.user_folder.absolute()),
                "JSON Files (*.json)",
            )[0]
            fname = Path(query)

        rimseval.interfacer.load_cal_file(self.current_crd_file, fname)

        if self.config.get("Calculate on open"):
            # todo: calculate on open
            pass

    def save_calibration(self, save_as: bool = False):
        """Save Calibration.

        :param save_as: If True, brings up a dialog to save calibration to given file.
        """
        if save_as:
            query = QtWidgets.QFileDialog.getSaveFileName(
                self,
                caption="Save calibration file as",
                directory=str(self.user_folder.absolute()),
                filter="JSON Files (*.json)",
            )
            if query[0]:
                fname = Path(query[0]).with_suffix(".json")
        else:
            fname = None
        rimseval.interfacer.save_cal_file(self.current_crd_file, fname=fname)

    # MASS CALIBRATION FUNCTIONS #
    def create_mass_calibration(self):
        """Enable user to create a mass calibration."""
        logy = self.config.get("Plot with log y-axis")
        theme = self.config.get("Theme")
        window = rimseval.guis.mcal.CreateMassCalibration(
            self.current_crd_file, logy=logy, theme=theme
        )
        window.show()

    def show_mass_calibration(self):
        """Show the current Mass calibration as a QDialog."""
        if (mcal := self.current_crd_file.def_mcal) is not None:
            dialog = MassCalDialog(mcal, parent=self)
            dialog.exec()

    # INTEGRAL DEFINITION FUNCTIONS #

    def integrals_draw(self):
        """Enable user to draw integrals."""
        logy = self.config.get("Plot with log y-axis")
        theme = self.config.get("Theme")
        window = rimseval.guis.integrals.DefineIntegrals(
            self.current_crd_file, logy=logy, theme=theme
        )
        window.show()

    def integrals_set_edit(self):
        """Enable user to set integrals with a table widget."""
        model = IntegralBackgroundDefinitionModel(self.current_crd_file.def_integrals)
        dialog = IntegralEditDialog(model, parent=self)
        if dialog.exec():
            self.current_crd_file.def_integrals = model.return_data()

    def integrals_fitting(self):
        """Define integrals by fitting them."""
        # todo in second version
        raise NotImplementedError

    def integrals_copy_to_clipboard(self):
        """Copy the integrals to the clipboard for pasting into, e.g., Excel."""
        pass

    def integrals_pkg_copy_to_clipboard(self):
        """Copy the integrals to the clipboard for pasting into, e.g., Excel."""
        pass

    def backgrounds_draw(self):
        """Open GUI for user to draw backgrounds."""
        logy = self.config.get("Plot with log y-axis")
        theme = self.config.get("Theme")
        window = rimseval.guis.integrals.DefineBackgrounds(
            self.current_crd_file, logy=logy, theme=theme
        )
        window.show()

    def backgrounds_set_edit(self):
        """Open GUI for user to set / edit backgrounds by hand."""
        model = IntegralBackgroundDefinitionModel(self.current_crd_file.def_backgrounds)
        dialog = BackgroundEditDialog(
            model, self.current_crd_file.def_integrals[0], parent=self
        )
        if dialog.exec():
            self.current_crd_file.def_backgrounds = model.return_data()

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

    def convert_lst_to_crd(self, tagged=False):
        """Convert LST to CRD File(s).

        :param tagged: Split tagged data?
        """
        query = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open LST File(s)",
            directory=str(self.user_folder.absolute()),
            filter="LST Files (*.lst)",
        )[0]

        if len(query) > 0:
            fnames = [Path(it) for it in query]
            channel = self.config.get("Signal Channel")
            if tagged:
                tag = self.config.get("Tag Channel")
            else:
                tag = None
            for fname in fnames:
                try:
                    lst = rimseval.data_io.lst_to_crd.LST2CRD(
                        file_name=fname, channel_data=channel, channel_tag=tag
                    )
                    lst.read_list_file()
                    lst.write_crd()
                except OSError as err:
                    QtWidgets.QMessageBox.warning(self, "LST File error", err.args[0])

    # EXPORT FUNCTIONS #

    def export_spectrum_as_csv(self, tof: bool = False) -> None:
        """Export a spectrum to a csv file.

        :param tof: If true, export ToF spectrum, otherwise mass spectrum.
        """
        print(tof)

    # SPECIAL FUNCTIONS #

    def histogram_ions_per_shot(self):
        """Plot a histogram of ions per shot."""
        pass

    def histogram_dt_ions(self):
        """Plot a histogram of time delta between arriving ions.

        Only done for shots with more than 2 ions.
        """
        pass

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

    def update_settings(self, update):
        self.config.set_many(update.as_dict())
        self.config.save()

        self.setStyleSheet(qdarktheme.load_stylesheet(self.config.get("Theme")))

    def window_settings(self):
        """Settings Dialog."""
        config_dialog = ConfigDialog(self.config, self, cols=1)
        config_dialog.setWindowTitle("Settings")
        config_dialog.accepted.connect(
            lambda: self.update_settings(config_dialog.config)
        )
        config_dialog.exec()

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
