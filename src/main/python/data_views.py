"""Views for the open data, implemented as models."""

from PyQt6 import QtCore, QtGui, QtWidgets


class OpenFilesView(QtWidgets.QListView):
    """QListView Model for displaying and selecting opened data."""

    def __ini__(self, parent):
        """Initialize the OpenFileView Widget."""
