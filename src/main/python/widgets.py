"""My own implementations of PyQt widgets, small tweaking of existing ones."""

from PyQt6 import QtWidgets


class LargeQSpinBox(QtWidgets.QSpinBox):
    """Large QSpinBox with a max of 9999 instead of 99."""

    def __init__(self, parent=None):
        """Initialize the spin box with new settings."""
        super().__init__(parent)
        self.setMaximum(9999)


class PreciseQDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    """Create a more precise double spin box with 4 digits of precision instead of 2."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSingleStep(0.001)
        self.setDecimals(4)
