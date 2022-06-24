"""Routines for data exports."""

from pathlib import Path
from typing import List

import numpy as np


def export_histogram(
    fname: Path, xdata: List, ydata: List, xtitle: str, names: List, dx: float
) -> None:
    """Export histogram for multiple data columns into a csv file.

    :param fname: File name to export to.
    :param xdata: X data array, that needs to be binned.
    :param ydata: Y data to export into histogram.
    :param xtitle: Title for the X data array in the csv file.
    :param names: Names for the ydata in the csv file header.
    :param dx: Bin width.
    """
    # determine the minimum and maximum x value
    xmin = xdata[0].min()
    xmax = xdata[0].max()
    for it in range(1, len(xdata)):
        xdat = xdata[it]
        if (mintmp := xdat.min()) < xmin:
            xmin = mintmp
        if (maxtmp := xdat.max()) > xmax:
            xmax = maxtmp

    # create the data arrays that need to be written into the csv file
    xarr = np.arange(xmin, xmax + dx, dx)
    yarr = np.zeros((len(ydata), len(xarr)))

    def hist_mapper(xval: float):
        """Map an x value to the index the counts will go into in the histogram.

        :param xval: Value of x.
        """
        slope = 1 / dx
        return int(slope * (xval - xmin))

    # fill the histograms
    for it, ydat in enumerate(ydata):
        for jt, xval in enumerate(xdata[it]):
            ind = hist_mapper(xval)
            yarr[it][ind] += ydat[jt]

    with fname.open("w") as fout:
        # write header
        fout.write(f"{xtitle},")
        fout.write(f"{','.join(names)}\n")
        # write out data
        for it in range(len(xarr)):
            fout.write(f"{xarr[it]},")
            fout.write(f"{','.join(map(str, yarr[:,it]))}\n")
