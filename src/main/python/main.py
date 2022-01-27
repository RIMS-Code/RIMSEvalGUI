from fbs_runtime.application_context.PyQt6 import ApplicationContext
from PyQt6 import QtCore, QtGui, QtWidgets

import sys

import rimseval


class MainRimsEvalGui(QtWidgets.QMainWindow):
    """Main GUI for the RIMSEval program."""

    def __init__(self, appctxt):
        """Initialize the main window."""
        super().__init__()

        self.setWindowTitle(f"RIMS Evaluation v{rimseval.__version__}")

        # fbs related stuff
        self.appctxt = appctxt

        # menu bar
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("&File")
        self.mass_cal_menu = menu_bar.addMenu("&Mass Cal")
        self.integrals_menu = menu_bar.addMenu("&Integrals")
        self.lst_menu = menu_bar.addMenu("&LST Files")
        self.export_menu = menu_bar.addMenu("&Export")
        self.special_menu = menu_bar.addMenu("&Special")
        self.settings_menu = menu_bar.addMenu("Settings")

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
        self.init_menu_and_toolbar()

    def init_menu_and_toolbar(self):
        """Initialize the basics of the menu and tool bar, set the given categories."""
        tool_bar = QtWidgets.QToolBar("Main Toolbar")
        tool_bar.setIconSize(QtCore.QSize(24, 24))

        # ACTIONS #
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

        lst_convert_action = QtGui.QAction(
            QtGui.QIcon(self.appctxt.get_resource("icons/blue-folder-import.png")),
            "Convert LST to CRD",
            self,
        )
        lst_convert_action.setStatusTip("Convert LST to CRD file(s)")
        lst_convert_action.setShortcut(QtGui.QKeySequence("Ctrl+l"))
        lst_convert_action.triggered.connect(self.convert_lst_to_crd)
        self.lst_menu.addAction(lst_convert_action)
        tool_bar.addAction(lst_convert_action)

        self.addToolBar(tool_bar)

    def convert_lst_to_crd(self):
        """Convert LST to CRD File(s)."""
        pass

    def open_crd(self):
        """Open CRD File(s)."""
        pass

    def window_info(self):
        """Show / Hide information window."""
        pass

    def window_plot(self):
        """Show / Hide plot window."""
        pass

    def window_settings(self):
        """Settings Dialog."""
        pass


if __name__ == "__main__":
    appctxt = ApplicationContext()  # 1. Instantiate ApplicationContext
    window = MainRimsEvalGui(appctxt)
    window.show()
    exit_code = appctxt.app.exec()  # 2. Invoke appctxt.app.exec()
    sys.exit(exit_code)
