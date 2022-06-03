"""Utility functions for the GUI."""

from typing import Tuple

import requests


def check_update_status(curr_version) -> Tuple[str, int]:
    """Check online for the latest version and return version code and status.

    Possible query statuses:
        0: Updates available
        1: Up to date
        2: Connection error
        3: Current / local version is unknown.

    :param curr_version: Current version of GUI.

    :return: Version, query status (see above).
    """

    api_url_release = (
        "https://api.github.com/repos/RIMS-Code/RIMSEvalGUI/releases/latest"
    )

    try:
        resp = requests.get(api_url_release)
        latest_version = resp.json()["tag_name"]
    except:
        return "Unknown", 2

    # unknown current version
    if curr_version == "Unknown":
        return latest_version, 3

    if curr_version == latest_version:
        return latest_version, 1
    elif curr_version != latest_version:
        return latest_version, 0
