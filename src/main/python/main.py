"""Main RIMSEval graphical user interface."""

import itertools
from pathlib import Path
import sys
from typing import Union

try:
    from fbs_runtime.application_context.PyQt6 import ApplicationContext
    import fbs_runtime.platform as fbsrt_platform
except ImportError:
    ApplicationContext = None
    fbsrt_platform = None

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
from pyqtconfig import ConfigDialog, ConfigManager
import qdarktheme
import rimseval
from rimseval.utilities import ini

from data_models import (
    IntegralsModel,
    IntegralBackgroundDefinitionModel,
    OpenFilesModel,
    NormIsosModel,
)
from data_views import IntegralsDisplay, OpenFilesListView
from dialogs import (
    AboutDialog,
    BackgroundEditDialog,
    IntegralEditDialog,
    MassCalDialog,
    NormIsosDialog,
)
from elements import PeriodicTable
from info_window import FileInfoWindow
from plot_window import PlotWindow
from statusindicator import StatusIndicator
import widgets


class MainRimsEvalGui(QtWidgets.QMainWindow):
    """Main GUI for the RIMSEval program."""

    def __init__(self, appctxt, is_windows: bool = False):
        """Initialize the main window.

        :param appctxt: Application context, fbs or none fbs.
        :param is_windows: Are we on Windows?
        """
        super().__init__()

        # fbs related stuff
        self.appctxt = appctxt
        self.is_windows = is_windows

        # local profile
        self.config = None
        self._user_folder = None
        self.app_local_path = None  # home path for the application configs, etc.
        self.init_local_profile()
        self.init_config_manager()

        # window titles and geometry
        self.version = f"v{rimseval.__version__}"
        self.setWindowTitle(f"RIMS Evaluation {self.version}")
        self.setGeometry(QtCore.QRect(310, 100, 700, 100))

        # crd related stuff
        self.crd_files = None

        # views to access
        self.file_names_view = OpenFilesListView(self)
        self.file_names_model = OpenFilesModel(
            tick=self.appctxt.get_resource("icons/tick.png")
        )  # empty model
        self.integrals_model = IntegralsModel()
        self.user_macro = None  # file path to user macro, if loaded

        # menu bar
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("&File")
        self.mass_cal_menu = menu_bar.addMenu("&Mass Cal")
        self.integrals_menu = menu_bar.addMenu("&Integrals")
        self.calculate_menu = menu_bar.addMenu("Calculate")
        self.lst_menu = menu_bar.addMenu("&LST Files")
        self.export_menu = menu_bar.addMenu("&Export")
        self.special_menu = menu_bar.addMenu("&Special")
        self.view_menu = menu_bar.addMenu("&View")
        self.settings_menu = menu_bar.addMenu("Settings")

        # actions
        self.load_cal_action = None
        self.load_lioneval_cal_action = None
        self.save_cal_action = None
        self.save_cal_as_action = None
        self.mass_cal_def_action = None
        self.mass_cal_optimize_action = None
        self.mass_cal_apply_action = None
        self.mass_cal_show_action = None
        self.integrals_set_edit_action = None
        self.integrals_draw_action = None
        self.integrals_fitting_action = None
        self.integrals_copy_action = None
        self.integrals_copy_w_names_action = None
        self.integrals_copy_all_w_fnames_action = None
        self.integrals_copy_pkg_action = None
        self.integrals_copy_pkg_w_names_action = None
        self.backgrounds_draw_action = None
        self.backgrounds_set_edit_action = None
        self.calculate_single_action = None
        self.calculate_batch_action = None
        self.export_mass_spectrum_action = None
        self.export_tof_spectrum_action = None
        self.special_integrals_per_pkg_action = None
        self.special_hist_dt_ions_action = None
        self.special_hist_ions_shot_action = None
        self.window_elements_action = None
        self.window_info_action = None
        self.window_plot_action = None

        # crd file controls
        self.control_spectrum_part = [QtWidgets.QCheckBox(), QtWidgets.QLineEdit()]
        self.control_max_ions_per_shot = [QtWidgets.QCheckBox(), QtWidgets.QSpinBox()]
        self.control_max_ions_per_time = [
            QtWidgets.QCheckBox(),
            QtWidgets.QSpinBox(),
            QtWidgets.QDoubleSpinBox(),
        ]
        self.control_max_ions_per_tof_window = [
            QtWidgets.QCheckBox(),
            QtWidgets.QSpinBox(),
            QtWidgets.QDoubleSpinBox(),
            QtWidgets.QDoubleSpinBox(),
        ]
        self.control_packages = [QtWidgets.QCheckBox(), QtWidgets.QSpinBox()]
        self.control_max_ions_per_pkg = [QtWidgets.QCheckBox(), QtWidgets.QSpinBox()]
        self.control_dead_time_correction = [
            QtWidgets.QCheckBox(),
            QtWidgets.QSpinBox(),
        ]
        self.control_macro = [
            QtWidgets.QCheckBox(),
            QtWidgets.QPushButton(),
            QtWidgets.QLabel(),
        ]
        self.control_bg_correction = QtWidgets.QCheckBox()

        # other windows
        self.elements_window = PeriodicTable(self)
        self.info_window = FileInfoWindow(self)
        self.plot_window = PlotWindow(self)
        self.tmp_window = None  # container in self for plot windows from package

        # bars and layouts of program
        self.main_widget = QtWidgets.QWidget()
        self.status_bar = QtWidgets.QStatusBar()
        self.status_widget = StatusIndicator(size=20, margin=0)

        # variables to be defined
        self.status_bar_time = 5000  # status bar time in msec

        # add stuff to widget
        self.setCentralWidget(self.main_widget)
        self.setStatusBar(self.status_bar)

        # initialize the UI
        self.init_menu_toolbar()
        self.init_main_widget()
        self.init_status_bar()

        self.setStyleSheet(qdarktheme.load_stylesheet(self.config.get("Theme")))

        # welcome the user
        self.status_bar.showMessage(
            f"Welcome to RIMSEval v{rimseval.__version__}", msecs=self.status_bar_time
        )

        # update actions
        self.update_action_status()

    def init_local_profile(self):
        """Initialize a user's local profile, platform dependent."""
        if self.is_windows:
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

        # FILE CONTROL #

        # create lists to connect to status indicator when changed
        all_control_toggles = []
        all_control_text_edits = []
        all_control_value_edits = []

        control_layout = QtWidgets.QVBoxLayout()

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_spectrum_part[0].setText("Cut Shot Range")
        self.control_spectrum_part[0].setToolTip("Cut out part of the shot range.")
        tmphbox.addWidget(self.control_spectrum_part[0])
        tmphbox.addStretch()
        self.control_spectrum_part[1].setToolTip(
            "Set regions to cut comma separated.\n"
            "The first shots starts at 1.\n"
            "You can set more than 1 region."
        )
        tmphbox.addWidget(self.control_spectrum_part[1])
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_spectrum_part[0])
        all_control_text_edits.append(self.control_spectrum_part[1])

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_max_ions_per_shot[0].setText("Max ions / shot")
        self.control_max_ions_per_shot[0].setToolTip(
            "Filter for maximum number of ions per shot."
        )
        tmphbox.addWidget(self.control_max_ions_per_shot[0])
        tmphbox.addStretch()
        self.control_max_ions_per_shot[1].setRange(1, 99999)
        self.control_max_ions_per_shot[1].setToolTip("Maximum number of ions")
        tmphbox.addWidget(self.control_max_ions_per_shot[1])
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_max_ions_per_shot[0])
        all_control_value_edits.append(self.control_max_ions_per_shot[1])

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_max_ions_per_time[0].setText("Max ions / time")
        self.control_max_ions_per_time[0].setToolTip(
            "Filter maximum number of ions allowed per time (us)."
        )
        tmphbox.addWidget(self.control_max_ions_per_time[0])
        tmphbox.addStretch()
        self.control_max_ions_per_time[1].setRange(1, 99999)
        self.control_max_ions_per_time[1].setToolTip("Maximum number of ions")
        tmphbox.addWidget(self.control_max_ions_per_time[1])
        self.control_max_ions_per_time[2].setRange(0, 999)
        self.control_max_ions_per_time[2].setDecimals(3)
        self.control_max_ions_per_time[2].setToolTip("Time in us")
        tmphbox.addWidget(self.control_max_ions_per_time[2])
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_max_ions_per_time[0])
        all_control_value_edits.append(self.control_max_ions_per_time[1])
        all_control_value_edits.append(self.control_max_ions_per_time[2])

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_max_ions_per_tof_window[0].setText("Max ions / ToF Window")
        self.control_max_ions_per_tof_window[0].setToolTip(
            "Filter maximum number of ions allowed in ToF window."
        )
        tmphbox.addWidget(self.control_max_ions_per_tof_window[0])
        tmphbox.addStretch()
        self.control_max_ions_per_tof_window[1].setRange(0, 99999)
        self.control_max_ions_per_tof_window[1].setToolTip("Maximum number of ions")
        tmphbox.addWidget(self.control_max_ions_per_tof_window[1])
        self.control_max_ions_per_tof_window[2].setRange(0, 999)
        self.control_max_ions_per_tof_window[2].setDecimals(3)
        self.control_max_ions_per_tof_window[2].setToolTip("Window start ToF (us)")
        tmphbox.addWidget(self.control_max_ions_per_tof_window[2])
        self.control_max_ions_per_tof_window[3].setRange(0, 999)
        self.control_max_ions_per_tof_window[3].setDecimals(3)
        self.control_max_ions_per_tof_window[3].setToolTip("Window end ToF (us)")
        tmphbox.addWidget(self.control_max_ions_per_tof_window[3])
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_max_ions_per_tof_window[0])
        all_control_value_edits.append(self.control_max_ions_per_tof_window[1])
        all_control_value_edits.append(self.control_max_ions_per_tof_window[2])
        all_control_value_edits.append(self.control_max_ions_per_tof_window[3])

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_packages[0].setText("Packages")
        self.control_packages[0].setToolTip(
            "Create packages with given number of shots per package."
        )
        tmphbox.addWidget(self.control_packages[0])
        tmphbox.addStretch()
        self.control_packages[1].setRange(1, 99999)
        self.control_packages[1].setToolTip("Number of shots per package")
        tmphbox.addWidget(self.control_packages[1])
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_packages[0])
        all_control_value_edits.append(self.control_packages[1])

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_max_ions_per_pkg[0].setText("Max ions / package")
        self.control_max_ions_per_pkg[0].setToolTip(
            "Filter the maximum number of ions per package."
        )
        tmphbox.addWidget(self.control_max_ions_per_pkg[0])
        tmphbox.addStretch()
        self.control_max_ions_per_pkg[1].setRange(1, 99999)
        self.control_max_ions_per_pkg[1].setToolTip("Maximum number of ions")
        tmphbox.addWidget(self.control_max_ions_per_pkg[1])
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_max_ions_per_pkg[0])
        all_control_value_edits.append(self.control_max_ions_per_pkg[1])

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_macro[0].setText("Run Macro")
        self.control_macro[0].setToolTip(
            "Runs your own macro after all other active filters and\n"
            "right before dead time correction (if active)."
        )
        tmphbox.addWidget(self.control_macro[0])
        self.control_macro[1].setText("Load")
        self.control_macro[1].setToolTip("Load your python macro.")
        self.control_macro[1].clicked.connect(self.load_macro)
        tmphbox.addWidget(self.control_macro[1])
        tmphbox.addStretch()
        tmphbox.addWidget(self.control_macro[2])
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_macro[0])

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_dead_time_correction[0].setText("Dead time correction")
        self.control_dead_time_correction[0].setToolTip(
            "Correct spectrum for dead time effects"
        )
        tmphbox.addWidget(self.control_dead_time_correction[0])
        tmphbox.addStretch()
        self.control_dead_time_correction[1].setRange(1, 99999)
        self.control_dead_time_correction[1].setToolTip(
            "Enter number of bins that are dead after ion arrival"
        )
        tmphbox.addWidget(self.control_dead_time_correction[1])
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_dead_time_correction[0])
        all_control_value_edits.append(self.control_dead_time_correction[1])

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
        )
        control_layout.addWidget(separator)

        tmphbox = QtWidgets.QHBoxLayout()
        self.control_bg_correction.setText("Integral Background Correction")
        self.control_bg_correction.setToolTip(
            "Toggle background correction for integrals, if set."
        )
        tmphbox.addWidget(self.control_bg_correction)
        tmphbox.addStretch()
        control_layout.addLayout(tmphbox)
        all_control_toggles.append(self.control_bg_correction)

        # end of control layout
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # connect control toggles and edits to status indicator
        for tog in all_control_toggles:
            tog.stateChanged.connect(lambda: self.status_widget.set_status("outdated"))
        for ed in all_control_text_edits:
            ed.textChanged.connect(lambda: self.status_widget.set_status("outdated"))
        for val in all_control_value_edits:
            val.valueChanged.connect(lambda: self.status_widget.set_status("outdated"))

        # INTEGRALS VIEW #
        integral_display = IntegralsDisplay(self)
        integral_display.setModel(self.integrals_model)
        layout.addWidget(integral_display)

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
            "Open CRD(s)",
            self,
        )
        open_crd_action.setStatusTip("Open CRD file(s)")
        open_crd_action.setShortcut(QtGui.QKeySequence("Ctrl+o"))
        open_crd_action.triggered.connect(self.open_crd)
        self.file_menu.addAction(open_crd_action)
        tool_bar.addAction(open_crd_action)

        open_additional_crd_action = QtGui.QAction(
            QtGui.QIcon(None), "Open additional CRD(s)", self
        )
        open_additional_crd_action.setStatusTip(
            "Add additional CRD files to the already open ones."
        )
        open_additional_crd_action.triggered.connect(self.open_additional_crd)
        self.file_menu.addAction(open_additional_crd_action)

        unload_crd_action = QtGui.QAction(
            QtGui.QIcon(None), "Unload selected CRD(s)", self
        )
        unload_crd_action.setStatusTip(
            "Unload selected CRD files. Currently active file cannot be unloaded."
        )
        unload_crd_action.triggered.connect(self.unload_selected_crd)
        self.file_menu.addAction(unload_crd_action)

        load_cal_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Load calibration",
            self,
        )
        load_cal_action.setStatusTip("Load calibration file")
        load_cal_action.triggered.connect(lambda: self.load_calibration(fname=None))
        self.file_menu.addSeparator()
        self.file_menu.addAction(load_cal_action)
        self.load_cal_action = load_cal_action

        load_lioneval_cal_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Load LIONEval calibration",
            self,
        )
        load_lioneval_cal_action.setStatusTip("Load old LIONEval calibration file")
        load_lioneval_cal_action.triggered.connect(
            lambda: self.load_lion_eval_calibration(fname=None)
        )
        self.file_menu.addAction(load_lioneval_cal_action)
        self.load_lioneval_cal_action = load_lioneval_cal_action

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
        self.save_cal_as_action = save_cal_as_action

        unload_macro_action = QtGui.QAction(QtGui.QIcon(None), "Unload Macro", self)
        unload_macro_action.setStatusTip("Unload a set macro and deactivate function.")
        unload_macro_action.triggered.connect(self.unload_macro)
        self.file_menu.addSeparator()
        self.file_menu.addAction(unload_macro_action)

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
            "Create Mass Calibration",
            self,
        )
        mass_cal_def_action.setStatusTip("Create a mass calibration")
        mass_cal_def_action.triggered.connect(self.create_mass_calibration)
        self.mass_cal_menu.addAction(mass_cal_def_action)
        tool_bar.addSeparator()
        tool_bar.addAction(mass_cal_def_action)
        self.mass_cal_def_action = mass_cal_def_action

        mass_cal_optimize_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Optimize mass calibration",
            self,
        )
        mass_cal_optimize_action.setStatusTip(
            "Optimize the mass calibration by re-fitting all defined peaks."
        )
        mass_cal_optimize_action.triggered.connect(self.optimize_mass_calibration)
        self.mass_cal_menu.addAction(mass_cal_optimize_action)
        self.mass_cal_optimize_action = mass_cal_optimize_action

        mass_cal_apply_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Apply mass calibration",
            self,
        )
        mass_cal_apply_action.setStatusTip("Apply the created mass calibration.")
        mass_cal_apply_action.triggered.connect(self.apply_mass_calibration)
        self.mass_cal_menu.addAction(mass_cal_apply_action)
        self.mass_cal_apply_action = mass_cal_apply_action

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
            QtGui.QIcon(self.appctxt.get_resource("icons/system-monitor.png")),
            "Set / Edit Integrals",
            self,
        )
        integrals_set_edit_action.setStatusTip("Set new or edit existing integrals.")
        integrals_set_edit_action.triggered.connect(self.integrals_set_edit)
        self.integrals_menu.addAction(integrals_set_edit_action)
        tool_bar.addAction(integrals_set_edit_action)
        self.integrals_set_edit_action = integrals_set_edit_action

        integrals_draw_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Draw Integrals",
            self,
        )
        integrals_draw_action.setStatusTip("Define integrals by drawing them")
        integrals_draw_action.triggered.connect(self.integrals_draw)
        self.integrals_menu.addAction(integrals_draw_action)
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
        # todo second version
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

        integrals_copy_w_names_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Copy Integrals w/ header",
            self,
        )
        integrals_copy_w_names_action.setStatusTip(
            "Copy all peak names and integrals to the clipboard"
        )
        integrals_copy_w_names_action.triggered.connect(
            lambda: self.integrals_copy_to_clipboard(get_names=True)
        )
        self.integrals_menu.addAction(integrals_copy_w_names_action)
        self.integrals_copy_w_names_action = integrals_copy_w_names_action

        integrals_copy_all_w_fnames_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Copy All Integrals",
            self,
        )
        integrals_copy_all_w_fnames_action.setStatusTip(
            "Copy all integrals of all open files to the clipboard"
        )
        integrals_copy_all_w_fnames_action.setShortcut(
            QtGui.QKeySequence("Ctrl+Shift+c")
        )
        integrals_copy_all_w_fnames_action.triggered.connect(
            self.integrals_copy_all_to_clipboard
        )
        self.integrals_menu.addAction(integrals_copy_all_w_fnames_action)
        self.integrals_copy_all_w_fnames_action = integrals_copy_all_w_fnames_action

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

        integrals_copy_pkg_w_names_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Copy Integrals Packages w/ header",
            self,
        )
        integrals_copy_pkg_w_names_action.setStatusTip(
            "Copy peak names and integrals of all packages to the clipboard"
        )
        integrals_copy_pkg_w_names_action.triggered.connect(
            lambda: self.integrals_pkg_copy_to_clipboard(get_names=True)
        )
        self.integrals_menu.addAction(integrals_copy_pkg_w_names_action)
        self.integrals_copy_pkg_w_names_action = integrals_copy_pkg_w_names_action

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
        calculate_batch_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+r"))
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

        lst_convert_tagged_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Convert Tagged LST to CRD",
            self,
        )
        lst_convert_tagged_action.setStatusTip("Convert Tagged LST to CRD file(s)")
        lst_convert_tagged_action.triggered.connect(
            lambda: self.convert_lst_to_crd(True)
        )
        self.lst_menu.addAction(lst_convert_tagged_action)

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

        # SPECIAL ACTIONS #

        special_integrals_per_pkg_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Plot integrals per package",
            self,
        )
        special_integrals_per_pkg_action.setStatusTip(
            "Show a plot of all integrals per package."
        )
        special_integrals_per_pkg_action.triggered.connect(self.plot_integrals_per_pkg)
        self.special_menu.addAction(special_integrals_per_pkg_action)
        self.special_integrals_per_pkg_action = special_integrals_per_pkg_action

        special_hist_ions_shot_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Histogram Ions/Shot",
            self,
        )
        special_hist_ions_shot_action.setStatusTip("Show a histogram of ions per shot.")
        special_hist_ions_shot_action.triggered.connect(self.histogram_ions_per_shot)
        self.special_menu.addAction(special_hist_ions_shot_action)
        self.special_hist_ions_shot_action = special_hist_ions_shot_action

        special_hist_dt_ions_action = QtGui.QAction(
            QtGui.QIcon(None),
            "Histogram dt ions",
            self,
        )
        special_hist_dt_ions_action.setStatusTip(
            "Show a histogram for multi-ion shots with time differences between ions."
        )
        special_hist_dt_ions_action.triggered.connect(self.histogram_dt_ions)
        self.special_menu.addAction(special_hist_dt_ions_action)
        self.special_hist_dt_ions_action = special_hist_dt_ions_action

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

        norm_isos_action = QtGui.QAction(
            QtGui.QIcon(None), "Normalizing Isotopes", self
        )
        norm_isos_action.setStatusTip("Set / edit normalization isotopes per element")
        norm_isos_action.triggered.connect(self.normalizing_isotopes_dialog)
        self.settings_menu.addAction(norm_isos_action)

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

        about_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/question.png")),
            "About",
            self,
        )
        about_action.triggered.connect(self.about_dialog)
        self.settings_menu.addAction(about_action)

        # exit button
        tool_bar.addSeparator()
        tool_bar.addAction(file_exit_action)

        # add toolbar to self
        self.addToolBar(tool_bar)

    def init_status_bar(self):
        """Initialize the status bar."""
        self.status_widget.setToolTip(
            "Status of calculation:\n"
            "Green:\tCalculation up to date\n"
            "Red:\tCalculation outdated\n"
            "Black:\tError\n"
            "Gray:\tNo Files loaded"
        )
        self.status_bar.addPermanentWidget(self.status_widget, stretch=1)

    def init_config_manager(self):
        """Initialize the configuration manager and load the default configuration."""
        default_values = {
            "Plot with log y-axis": True,
            "Calculate on open": True,
            "Optimize Mass Calibration": True,
            "Auto sort integrals": True,
            "Signal Channel": 1,
            "Tag Channel": 2,
            "Peak FWHM (us)": 0.02,
            "Copy integrals w/ unc.": True,
            "Copy timestamp with integrals": False,
            "Bins for spectra export": 10,
            "Max. time dt ions histogram (ns)": 120,
            "Theme": "light",
            "User folder": str(Path.home()),
            "Norm isos": {},
        }

        default_settings_metadata = {
            "Peak FWHM (us)": {"preferred_handler": widgets.PreciseQDoubleSpinBox},
            "Max. time dt ions histogram (ns)": {
                "preferred_handler": widgets.LargeQSpinBox
            },
            "Theme": {
                "preferred_handler": QtWidgets.QComboBox,
                "preferred_map_dict": {"Dark Colors": "dark", "Light Colors": "light"},
            },
            "User folder": {"prefer_hidden": True},
            "Norm isos": {"prefer_hidden": True},
        }

        self.config = ConfigManager(
            default_values, filename=self.app_local_path.joinpath("config.json")
        )
        self.config.set_many_metadata(default_settings_metadata)
        self.user_folder = Path(self.config.get("User folder"))
        ini.norm_isos = self.config.get("Norm isos")

    # PROPERTIES #

    @property
    def current_crd_file(self) -> rimseval.CRDFileProcessor:
        """Return currently active CRD file."""
        if self.crd_files is not None:
            return self.crd_files.files[self.file_names_model.currently_active]

    @property
    def user_folder(self) -> Path:
        """Set / get user folder (absolute path).

        :return: User folder as Path (absolute)
        """
        return self._user_folder.absolute()

    @user_folder.setter
    def user_folder(self, value: Union[Path, str]):
        if isinstance(value, str):
            value = Path(value)
        self._user_folder = value.absolute()
        self.config.set("User folder", str(value.absolute()))
        self.config.save()

    # FILE MENU FUNCTIONS #

    def open_crd(self):
        """Open CRD File(s)."""
        file_names = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open CRD File(s)",
            str(self.user_folder),
            "CRD Files (*.crd)",
        )[0]

        try:
            if len(file_names) > 0:
                file_names.sort()

                self.status_widget.set_status("outdated")
                # close files and remove from memory if they exist
                if self.crd_files:
                    self.crd_files.close_files()

                self.integrals_model.clear_data()
                self.plot_window.clear_plot()

                file_paths = [Path(file_name) for file_name in file_names]

                # set user path to this folder
                self.user_folder = file_paths[0].parent

                self.crd_files = rimseval.MultiFileProcessor(file_paths)
                self.crd_files.signal_processed.connect(
                    lambda x: self.update_status_bar_processed(x)
                )
                self.crd_files.open_files()  # open, but no read
                self.crd_files.peak_fwhm = self.config.get("Peak FWHM (us)")

                self.crd_files.load_calibrations(
                    secondary_cal=self.app_local_path.joinpath("calibration.json")
                )

                self.file_names_model.set_new_list(file_paths)

                self.set_controls_from_filters()

                if self.config.get("Calculate on open"):
                    self.crd_files.read_files()
                    if self.config.get("Optimize Mass Calibration"):
                        self.optimize_mass_calibration()
                    self.calculate_single()
                else:
                    self.update_action_status()

                self.update_info_window(update_all=True)
        except Exception as err:
            QtWidgets.QMessageBox.warning(
                self, "Error occurred when opening files", err.args[0]
            )
            self.status_widget.set_status("error")

    def open_additional_crd(self) -> None:
        """Open additional CRD files."""
        if not self.crd_files:  # No files are open
            self.open_crd()
            return

        file_names = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open CRD File(s)",
            str(self.user_folder),
            "CRD Files (*.crd)",
        )[0]

        try:
            if len(file_names) > 0:
                file_paths = [Path(file_name) for file_name in file_names]

                read_files = self.config.get("Calculate on open")
                secondary_cal = self.app_local_path.joinpath("calibration.json")
                self.crd_files.open_additional_files(
                    file_paths, read_files=read_files, secondary_cal=secondary_cal
                )

                self.file_names_model.add_to_list(file_paths)

        except Exception as err:
            QtWidgets.QMessageBox.warning(
                self, "Error occurred when opening additional files", err.args[0]
            )
            self.status_widget.set_status("error")

    def unload_selected_crd(self):
        """Close selected CRD files."""
        selected_models = self.file_names_view.selectedIndexes()
        selected_indexes = [it.row() for it in selected_models]
        main_id = self.file_names_model.currently_active

        if main_id in selected_indexes:
            QtWidgets.QMessageBox.warning(
                self, "Unloading failed", "Cannot unload currently active file."
            )
            return

        selected_indexes.sort(reverse=True)
        new_main_id = self.crd_files.close_selected_files(
            selected_indexes, main_id=main_id
        )
        # now unload from file list
        self.file_names_model.remove_from_list(selected_indexes, new_main_id)

    def load_calibration(self, fname: Path = None):
        """Load a specific calibration file.

        :param fname: If None, then bring up a dialog to query for the file.
        """
        if fname is None:
            query = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open Calibration File",
                str(self.user_folder),
                "JSON Files (*.json)",
            )[0]
            if query == "":
                return
            fname = Path(query)

        rimseval.interfacer.load_cal_file(self.current_crd_file, fname)

        self.status_widget.set_status("outdated")
        self.set_controls_from_filters()

        if self.config.get("Calculate on open"):
            self.calculate_single()

    def load_lion_eval_calibration(self, fname: Path = None):
        """Load an old LIONEval calibration file.

        :param fname: Name of calaibration file. If none, bring up a dialog to query.
        """
        if fname is None:
            query = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open LIONEval Calibration File",
                str(self.user_folder),
                "Cal Files (*.cal)",
            )[0]
            if query == "":
                return
            fname = Path(query)

        rimseval.interfacer.read_lion_eval_calfile(self.current_crd_file, fname)

        self.status_widget.set_status("outdated")
        self.set_controls_from_filters()

        if self.config.get("Calculate on open"):
            self.calculate_single()

    def save_calibration(self, save_as: bool = False):
        """Save Calibration.

        :param save_as: If True, brings up a dialog to save calibration to given file.
        """
        crd = self.current_crd_file
        if save_as:
            query = QtWidgets.QFileDialog.getSaveFileName(
                self,
                caption="Save calibration file as",
                directory=str(self.user_folder),
                filter="JSON Files (*.json)",
            )
            if query[0]:
                fname = Path(query[0]).with_suffix(".json")
        else:
            fname = None
        rimseval.interfacer.save_cal_file(crd, fname=fname)

        # save as program default:
        rimseval.interfacer.save_cal_file(
            crd,
            fname=self.app_local_path.joinpath("calibration.json"),
        )

    # MASS CALIBRATION FUNCTIONS #
    def apply_mass_calibration(self):
        """Apply an already defined / imported mass calibration."""
        crd = self.current_crd_file
        if crd is not None:
            if crd.def_mcal is not None:
                if crd.tof is None:
                    crd.spectrum_full()
                crd.mass_calibration()
                self.update_all()
                self.status_widget.set_status("outdated")

    def create_mass_calibration(self):
        """Enable user to create a mass calibration."""
        logy = self.config.get("Plot with log y-axis")
        theme = self.config.get("Theme")

        crd = self.current_crd_file

        if crd.tof is None:
            crd.spectrum_full()

        self.tmp_window = rimseval.guis.mcal.CreateMassCalibration(
            crd, logy=logy, theme=theme
        )
        self.tmp_window.signal_calibration_applied.connect(self.update_all)
        self.tmp_window.show()
        self.status_widget.set_status("outdated")

    def optimize_mass_calibration(self):
        """Optimize a given mass calibration by re-fitting all the peaks."""
        crd = self.current_crd_file
        if crd is not None:
            if crd.def_mcal is not None:
                if crd.mass is None:
                    self.apply_mass_calibration()
                try:
                    self.current_crd_file.optimize_mcal()
                except Exception as err:
                    QtWidgets.QMessageBox.warning(
                        self, "Mass calibratiaon optimization failed", err.args[0]
                    )
                self.update_all()
                self.status_widget.set_status("outdated")

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
        self.tmp_window = rimseval.guis.integrals.DefineIntegrals(
            self.current_crd_file, logy=logy, theme=theme
        )
        self.tmp_window.signal_integrals_defined.connect(self.update_all)
        self.tmp_window.show()
        self.status_widget.set_status("outdated")

    def integrals_set_edit(self):
        """Enable user to set integrals with a table widget."""
        model = IntegralBackgroundDefinitionModel(self.current_crd_file.def_integrals)
        dialog = IntegralEditDialog(model, parent=self)
        if dialog.exec():
            self.current_crd_file.def_integrals = model.return_data()
            if self.config.get("Auto sort integrals"):
                self.current_crd_file.sort_integrals(sort_vals=False)
            self.update_all()

            self.status_widget.set_status("outdated")

    def integrals_fitting(self):
        """Define integrals by fitting them."""
        # todo in second version
        self.status_widget.set_status("outdated")
        raise NotImplementedError

    def integrals_copy_to_clipboard(self, get_names: bool = False):
        """Copy the integrals to the clipboard for pasting into, e.g., Excel.

        :param get_names: Copy names of peaks as well?
        """
        get_unc = self.config.get("Copy integrals w/ unc.")
        cp_timestamp = self.config.get("Copy timestamp with integrals")

        ret_str = ""

        crd = self.current_crd_file
        if (integrals := crd.integrals) is not None:
            # header
            if get_names:
                ret_str += "File Name\tNum of Shots\t"
                if cp_timestamp:
                    ret_str += "Time\t"
                for it, name in enumerate(crd.def_integrals[0]):
                    ret_str += f"{name}"
                    if get_unc:
                        ret_str += f"\t{name}_1sig"
                    if it < len(crd.def_integrals[0]) - 1:
                        ret_str += "\t"
                ret_str += "\n"

            # integrals
            ret_str += f"{crd.fname.with_suffix('').name}\t"
            ret_str += f"{crd.nof_shots}\t"
            if cp_timestamp:
                ret_str += f"{crd.timestamp}\t"
            for col, val in enumerate(integrals):
                ret_str += f"{val[0]}\t{val[1]}" if get_unc else f"{val[0]}"
                if col < len(integrals) - 1:
                    ret_str += "\t"
            ret_str += "\n"

        QtWidgets.QApplication.clipboard().setText(ret_str)

    def integrals_copy_all_to_clipboard(self):
        """Copy all integrals with the filename to the clipboard."""
        get_unc = self.config.get("Copy integrals w/ unc.")
        cp_timestamp = self.config.get("Copy timestamp with integrals")

        ret_str = ""

        for crd in self.crd_files.files:
            if (integrals := crd.integrals) is not None:
                ret_str += f"{crd.fname.with_suffix('').name}\t"
                ret_str += f"{crd.nof_shots}\t"
                if cp_timestamp:
                    ret_str += f"{crd.timestamp}\t"
                for col, val in enumerate(integrals):
                    ret_str += f"{val[0]}\t{val[1]}" if get_unc else f"{val[0]}"
                    if col < len(integrals) - 1:
                        ret_str += "\t"
                ret_str += "\n"

        QtWidgets.QApplication.clipboard().setText(ret_str)

    def integrals_pkg_copy_to_clipboard(self, get_names: bool = False):
        """Copy the integrals to the clipboard for pasting into, e.g., Excel.

        :param get_names: Copy names of peaks as well?
        """
        crd = self.current_crd_file
        data = crd.integrals_pkg
        if data is None:
            QtWidgets.QMessageBox.warning(
                self, "No data", "No package data is available"
            )
            return

        get_unc = self.config.get("Copy integrals w/ unc.")
        cp_timestamp = self.config.get("Copy timestamp with integrals")
        ret_str = ""

        if get_names:
            names = crd.def_integrals[0]
            ret_str += "File Name\tNum of Shots\t"
            if cp_timestamp:
                ret_str += "Time\t"
            for col, name in enumerate(names):
                ret_str += f"{name}\t{name}_1sig" if get_unc else f"{name}"
                if col < len(names) - 1:
                    ret_str += "\t"
            ret_str += "\n"

        for it, row in enumerate(data):
            ret_str += f"{crd.fname.with_suffix('').name}\t"
            ret_str += f"{crd.nof_shots_pkg[it]}\t"
            if cp_timestamp:
                ret_str += f"{crd.timestamp}\t"
            for col, val in enumerate(row):
                ret_str += f"{val[0]}\t{val[1]}" if get_unc else f"{val[0]}"
                if col < len(row) - 1:
                    ret_str += "\t"
            ret_str += "\n"
        QtWidgets.QApplication.clipboard().setText(ret_str)

    def backgrounds_draw(self):
        """Open GUI for user to draw backgrounds."""
        logy = self.config.get("Plot with log y-axis")
        theme = self.config.get("Theme")
        self.tmp_window = rimseval.guis.integrals.DefineBackgrounds(
            self.current_crd_file, logy=logy, theme=theme
        )
        self.tmp_window.signal_backgrounds_defined.connect(self.update_all)
        self.tmp_window.show()

        if self.control_bg_correction.isChecked():
            self.status_widget.set_status("outdated")

    def backgrounds_set_edit(self):
        """Open GUI for user to set / edit backgrounds by hand."""
        model = IntegralBackgroundDefinitionModel(self.current_crd_file.def_backgrounds)
        dialog = BackgroundEditDialog(
            model, self.current_crd_file.def_integrals[0], parent=self
        )
        if dialog.exec():
            self.current_crd_file.def_backgrounds = model.return_data()
            self.update_all()

            if self.control_bg_correction.isChecked():
                self.status_widget.set_status("outdated")

    # CALCULATE FUNCTIONS #

    def calculate_single(self):
        """Applies the currently displayed settings to the displayed CRD file."""
        crd = self.current_crd_file

        # if file has never been read, run a full spectrum
        if crd.tof is None:
            crd.spectrum_full()

        # run mass calibration if necessary
        if crd.def_mcal is not None and crd.mass is None:
            crd.mass_calibration()
            if self.config.get("Optimize Mass Calibrataion"):
                self.optimize_mass_calibration()

        # calculate file
        if not self.set_filters_from_controls():
            return

        try:
            self.current_crd_file.calculate_applied_filters()
        except Exception as err:
            QtWidgets.QMessageBox.warning(self, "Error in calculation", err.args[0])
            self.status_widget.set_status("error")
            return

        # integrals
        if self.current_crd_file.def_integrals is not None:
            bg_corr = (
                self.control_bg_correction.isChecked()
                and self.current_crd_file.def_backgrounds is not None
            )
            self.current_crd_file.integrals_calc(bg_corr=bg_corr)
            self.current_crd_file.integrals_calc_delta()

            # update integral model
            self.integrals_model.update_data(
                data=self.current_crd_file.integrals,
                names=self.current_crd_file.def_integrals[0],
                deltas=self.current_crd_file.integrals_delta,
            )

        # save calibration file
        self.save_calibration()

        # update stuff
        self.update_action_status()
        self.update_info_window(update_all=False)
        self.update_plot_window()
        self.update_status_bar_processed(str(crd.fname.name))

        self.status_widget.set_status("current")

    def calculate_batch(self):
        """Applies the currently configured settings to all open CRD files."""
        if not self.set_filters_from_controls():
            return

        main_id = self.file_names_model.currently_active
        opt_mcal = self.config.get("Optimize Mass Calibration")
        bg_corr = self.control_bg_correction.isChecked()
        self.crd_files.apply_to_all(main_id, opt_mcal=opt_mcal, bg_corr=bg_corr)

        # update stuff
        self.update_action_status()
        self.update_info_window(update_all=False)
        self.update_plot_window()
        self.update_integral_view()

        self.status_widget.set_status("current")

    # LST FILE FUNCTIONS #

    def convert_lst_to_crd(self, tagged=False):
        """Convert LST to CRD File(s).

        :param tagged: Split tagged data?
        """
        query = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open LST File(s)",
            directory=str(self.user_folder),
            filter="LST Files (*.lst)",
        )[0]

        if len(query) > 0:
            fnames = [Path(it) for it in query]
            channel = self.config.get("Signal Channel")
            if tagged:
                tag = self.config.get("Tag Channel")
            else:
                tag = None
            for it, fname in enumerate(fnames):
                try:
                    lst = rimseval.data_io.lst_to_crd.LST2CRD(
                        file_name=fname, channel_data=channel, channel_tag=tag
                    )
                    lst.read_list_file()
                    lst.write_crd()

                    self.status_bar.showMessage(
                        f"{fname.name} converted, {it+1}/{len(fnames)} done.",
                        msecs=self.status_bar_time,
                    )
                    QtWidgets.QApplication.processEvents()

                except OSError as err:
                    QtWidgets.QMessageBox.warning(self, "LST File error", err.args[0])

            # set user path to this folder
            self.user_folder = fname.parent

    # EXPORT FUNCTIONS #

    def export_spectrum_as_csv(self, tof: bool = False) -> None:
        """Export a spectrum to a csv file.

        :param tof: If true, export ToF spectrum, otherwise tof and mass spectrum.
        """
        bins = self.config.get("Bins for spectra export")

        fname = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save spectrum as CSV File",
            str(self.user_folder),
            "CSV Files (*.csv)",
        )[0]

        if len(fname) > 0:
            if tof:
                rimseval.data_io.export.tof_spectrum(
                    self.current_crd_file, Path(fname), bins=bins
                )
            else:
                rimseval.data_io.export.mass_spectrum(
                    self.current_crd_file, Path(fname), bins=bins
                )

    # SPECIAL FUNCTIONS #

    def histogram_ions_per_shot(self):
        """Plot a histogram of ions per shot."""
        theme = self.config.get("Theme")
        self.tmp_window = rimseval.guis.plots.IonsPerShot(
            self.current_crd_file, theme=theme
        )
        self.tmp_window.show()

    def histogram_dt_ions(self):
        """Plot a histogram of time delta between arriving ions.

        Only done for shots with more than 2 ions.
        """
        theme = self.config.get("Theme")
        max_ns = self.config.get("Max. time dt ions histogram (ns)")

        self.tmp_window = rimseval.guis.plots.DtIons(
            self.current_crd_file, theme=theme, max_ns=max_ns
        )
        self.tmp_window.show()

    def plot_integrals_per_pkg(self):
        """Plot all integrals per pkg versus the package number."""
        theme = self.config.get("Theme")

        self.tmp_window = rimseval.guis.plots.IntegralsPerPackage(
            self.current_crd_file, theme=theme
        )
        self.tmp_window.show()

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

    def normalizing_isotopes_dialog(self):
        """Bring up dialog to set / edit normalizing isotopes with ini."""
        model = NormIsosModel(ini.norm_isos)
        dialog = NormIsosDialog(model, parent=self)
        if dialog.exec():
            ini.reset_norm_isos()
            norm_isos = model.return_data()
            ini.norm_isos = norm_isos
            self.config.set("Norm isos", norm_isos)
            self.config.save()
            self.status_widget.set_status("outdated")

    def window_settings(self):
        """Settings Dialog."""
        config_dialog = ConfigDialog(self.config, self, cols=1)
        config_dialog.setWindowTitle("Settings")
        config_dialog.accepted.connect(
            lambda: self.update_settings(config_dialog.config)
        )
        config_dialog.exec()

    def about_dialog(self):
        """Open an about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    # ACTIONS ON CHANGED MODEL VIEWS #

    def current_file_changed(self, ind: QtCore.QModelIndex) -> None:
        """Reacts to a different file that is currently selected."""
        self.file_names_model.update_current(ind.row())
        self.integrals_model.clear_data()

        self.set_controls_from_filters()

        self.status_widget.set_status("outdated")

        if self.config.get("Calculate on open"):
            self.calculate_single()
        else:
            self.update_action_status()
            self.update_info_window(update_all=True)
            self.update_integral_view()
            self.update_plot_window()

    def load_macro(self):
        """Queries the user for a macro and sets it to the load macro state."""
        query = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Macro File",
            str(self.user_folder),
            "Python Files (*.py)",
        )[0]
        if query == "":
            return
        fname = Path(query)
        self.user_macro = fname.absolute()
        self.control_macro[2].setText(fname.name)

        self.status_widget.set_status("outdated")

    def unload_macro(self):
        """Unloads the user macro."""
        self.user_macro = None
        self.control_macro[0].setChecked(False)
        self.control_macro[2].setText("")

    def set_controls_from_filters(self):
        """Set the UI controls from the current CRD filters."""
        filters = self.current_crd_file.applied_filters

        key = "spectrum_part"
        if key in filters:
            self.control_spectrum_part[0].setChecked(filters[key][0])
            if filters[key][0]:
                flat_list = list(itertools.chain(*filters[key][1]))
                txt = ", ".join(map(str, flat_list))
                self.control_spectrum_part[1].setText(txt)

        key = "max_ions_per_shot"
        if key in filters:
            self.control_max_ions_per_shot[0].setChecked(filters[key][0])
            self.control_max_ions_per_shot[1].setValue(filters[key][1])

        key = "max_ions_per_time"
        if key in filters:
            self.control_max_ions_per_time[0].setChecked(filters[key][0])
            self.control_max_ions_per_time[1].setValue(filters[key][1])
            self.control_max_ions_per_time[2].setValue(filters[key][2])

        key = "max_ions_per_tof_window"
        if key in filters:
            self.control_max_ions_per_tof_window[0].setChecked(filters[key][0])
            self.control_max_ions_per_tof_window[1].setValue(filters[key][1])
            self.control_max_ions_per_tof_window[2].setValue(filters[key][2][0])
            self.control_max_ions_per_tof_window[3].setValue(filters[key][2][1])

        key = "packages"
        if key in filters:
            self.control_packages[0].setChecked(filters[key][0])
            self.control_packages[1].setValue(filters[key][1])

        key = "max_ions_per_pkg"
        if key in filters:
            self.control_max_ions_per_pkg[0].setChecked(filters[key][0])
            self.control_max_ions_per_pkg[1].setValue(filters[key][1])

        key = "macro"
        if key in filters:
            self.control_macro[0].setChecked(filters[key][0])
            macro_name = Path(filters[key][1])
            self.user_macro = macro_name.absolute()
            self.control_macro[2].setText(macro_name.name)

        key = "dead_time_corr"
        if key in filters:
            self.control_dead_time_correction[0].setChecked(filters[key][0])
            self.control_dead_time_correction[1].setValue(filters[key][1])

    def set_filters_from_controls(self) -> bool:
        """Set the CRD file applied filters from the given controls.

        :return: False if it failed, otherwise True
        """
        filters = {}

        if self.control_spectrum_part[0].isChecked():
            vals = self.control_spectrum_part[1].text().replace(" ", "").split(",")
            if len(vals) % 2 != 0 or len(vals) == 0:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Spectrum Cut invalid",
                    "Please enter a valid range to cut the spectrum.",
                )
                return False
            try:
                vals_list = (
                    np.array(vals, dtype=int).reshape((len(vals) // 2, 2)).tolist()
                )
            except Exception as err:
                QtWidgets.QMessageBox.warning(
                    self, "Spectrum cut parameters invalid", err.args[0]
                )
                return False

            filters["spectrum_part"] = [
                self.control_spectrum_part[0].isChecked(),
                vals_list,
            ]
        else:
            filters["spectrum_part"] = [False, []]

        filters["max_ions_per_shot"] = [
            self.control_max_ions_per_shot[0].isChecked(),
            int(self.control_max_ions_per_shot[1].value()),
        ]

        filters["max_ions_per_time"] = [
            self.control_max_ions_per_time[0].isChecked(),
            int(self.control_max_ions_per_time[1].value()),
            float(self.control_max_ions_per_time[2].value()),
        ]

        filters["max_ions_per_tof_window"] = [
            self.control_max_ions_per_tof_window[0].isChecked(),
            int(self.control_max_ions_per_tof_window[1].value()),
            [
                float(self.control_max_ions_per_tof_window[2].value()),
                float(self.control_max_ions_per_tof_window[3].value()),
            ],
        ]

        if (
            self.control_max_ions_per_pkg[0].isChecked()
            and not self.control_packages[0].isChecked()
        ):
            QtWidgets.QMessageBox.warning(
                self,
                "Package filters invalid",
                "Please activate packaging if you want to filter by packages.",
            )
            return False

        filters["packages"] = [
            self.control_packages[0].isChecked(),
            int(self.control_packages[1].value()),
        ]

        filters["max_ions_per_pkg"] = [
            self.control_max_ions_per_pkg[0].isChecked(),
            int(self.control_max_ions_per_pkg[1].value()),
        ]

        if self.user_macro is not None:
            filters["macro"] = [self.control_macro[0].isChecked(), str(self.user_macro)]

        filters["dead_time_corr"] = [
            self.control_dead_time_correction[0].isChecked(),
            int(self.control_dead_time_correction[1].value()),
        ]

        self.current_crd_file.applied_filters = filters

        return True  # all worked :)

    def update_all(self):
        """Update Actions, Info, and Plot."""
        self.update_info_window()
        self.update_plot_window()
        self.update_action_status()

    def update_action_status(self):
        """Sets the status of actions based on what the CRD file is capable of."""
        crd = self.current_crd_file
        # turn all off
        all_actions = [
            self.load_cal_action,
            self.load_lioneval_cal_action,
            self.save_cal_action,
            self.save_cal_as_action,
            self.mass_cal_def_action,
            self.mass_cal_apply_action,
            self.mass_cal_optimize_action,
            self.mass_cal_show_action,
            self.integrals_set_edit_action,
            self.integrals_draw_action,
            self.integrals_fitting_action,
            self.integrals_copy_action,
            self.integrals_copy_w_names_action,
            self.integrals_copy_all_w_fnames_action,
            self.integrals_copy_pkg_action,
            self.integrals_copy_pkg_w_names_action,
            self.backgrounds_draw_action,
            self.backgrounds_set_edit_action,
            self.calculate_single_action,
            self.calculate_batch_action,
            self.export_mass_spectrum_action,
            self.export_tof_spectrum_action,
            self.special_integrals_per_pkg_action,
            self.special_hist_dt_ions_action,
            self.special_hist_ions_shot_action,
        ]
        for action in all_actions:
            action.setDisabled(True)

        if crd is None:
            return

        crd_loaded_actions = [
            self.load_cal_action,
            self.load_lioneval_cal_action,
            self.save_cal_action,
            self.save_cal_as_action,
            self.mass_cal_def_action,
            self.calculate_single_action,
            self.calculate_batch_action,
            self.special_hist_dt_ions_action,
            self.special_hist_ions_shot_action,
        ]
        if crd is not None:  # so we have a file!
            for action in crd_loaded_actions:
                action.setEnabled(True)

        tof_exists_actions = [
            self.export_tof_spectrum_action,
        ]
        if crd.tof is not None:
            for action in tof_exists_actions:
                action.setEnabled(True)

        mass_cal_exists_actions = [
            self.mass_cal_apply_action,
            self.mass_cal_optimize_action,
            self.mass_cal_show_action,
        ]
        if crd.def_mcal is not None:
            for action in mass_cal_exists_actions:
                action.setEnabled(True)

        mass_cal_applied_actions = [
            self.integrals_set_edit_action,
            self.integrals_draw_action,
            # todo self.integrals_fitting_action,
            self.export_mass_spectrum_action,
        ]
        if crd.mass is not None:
            for action in mass_cal_applied_actions:
                action.setEnabled(True)

        integrals_available_actions = [
            self.integrals_copy_action,
            self.integrals_copy_w_names_action,
            self.integrals_copy_all_w_fnames_action,
        ]
        if crd.integrals is not None:
            for action in integrals_available_actions:
                action.setEnabled(True)

        integrals_pkg_actions = [
            self.special_integrals_per_pkg_action,
            self.integrals_copy_pkg_action,
            self.integrals_copy_pkg_w_names_action,
        ]
        if crd.integrals_pkg is not None:
            for action in integrals_pkg_actions:
                action.setEnabled(True)

        backgrounds_actions = [
            self.backgrounds_draw_action,
            self.backgrounds_set_edit_action,
        ]
        if crd.def_integrals is not None and crd.mass is not None:
            for action in backgrounds_actions:
                action.setEnabled(True)

    def update_info_window(self, update_all: bool = False) -> None:
        """Update the Info window.

        :param update_all: If True, header information is updated as well.
        """
        crd_file = self.current_crd_file
        self.info_window.update_current(crd_file)
        if update_all:
            self.info_window.update_header(crd_file)

    def update_integral_view(self) -> None:
        """Update the integral view when necessary."""
        if self.current_crd_file.integrals is not None:
            self.integrals_model.update_data(
                self.current_crd_file.integrals,
                self.current_crd_file.def_integrals[0],
                self.current_crd_file.integrals_delta,
            )

    def update_plot_window(self) -> None:
        """Update the plot window."""
        self.plot_window.update_data(self.current_crd_file)

    def update_status_bar_processed(self, name) -> None:
        """Print message to status bar that a given file has been processed.

        :param name: Name of the file that has been processed
        """
        self.status_bar.showMessage(
            f"{name} has been processed", msecs=self.status_bar_time
        )
        QtWidgets.QApplication.processEvents()


if __name__ == "__main__":
    if ApplicationContext is not None:
        appctxt = ApplicationContext()  # 1. Instantiate ApplicationContext
        window = MainRimsEvalGui(appctxt, is_windows=fbsrt_platform.is_windows())
        window.show()
        exit_code = appctxt.app.exec()  # 2. Invoke appctxt.app.exec()
        sys.exit(exit_code)
