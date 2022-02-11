"""If ``fbs`` is not available, run this program from Python to start the GUI."""

from pathlib import Path
import os
import sys
import warnings

from PyQt6.QtWidgets import QApplication

THIS_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(str(THIS_PATH.joinpath("src/main/python").absolute()))

from main import MainRimsEvalGui


class AppContext:
    """Class to implement ``fbs`` routines that I need, but might not be available."""

    def __init__(self):
        """Initialize this class."""
        self.this_path = Path(os.path.dirname(os.path.realpath(__file__)))

    def get_resource(self, value: str) -> str:
        """Return the path to an object in the resources base directory."""
        resources = self.this_path.joinpath("src/main/resources/base/")
        return str(resources.joinpath(value))


if __name__ == "__main__":
    """This is executed when running from this script."""
    appctx = AppContext()

    # determine platform
    current_platform = sys.platform
    if current_platform == "win32" or current_platform == "cygwin":
        is_windows = True
    elif current_platform == "linux" or current_platform == "darwin":
        is_windows = False
    else:
        is_windows = False
        warnings.warn(
            f"Current platform {current_platform} is not recognized. "
            f"Assuming this is not windows."
        )

    # run the app
    app = QApplication(sys.argv)
    window = MainRimsEvalGui(appctx, is_windows=is_windows)
    window.show()

    app.exec()
