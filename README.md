# RIMSEvalGUI

This is the repository for the GUI around the `rimseval` software.
Documentation here is only minimal!
For more detailed `rimseval` documentation, 
see [here](https://rimseval.readthedocs.io/en/latest/).


## Run the program within your python environment

Supported python versions are 3.8 and 3.9.
Running the program should work under Anaconda,
as long as you ensure that you use python 3.8 or python 3.9.

It is **highly** recommended to setup a virtual environment 
since the requirements are highly specific.
Please follow your python instructions on how to create one.

To install the requirements for the package in your virtual environment,
you can use `pip` and the given `requirements.txt` file as following:

```bash
pip install -r requirements.txt
```

Then you can simply run the `RIMSEvalGUI.py` file in the main directory,
e.g., from a terminal by typing:

```bash
python RIMSEvalGUI.py
```

## Run from executable

Download the latest release for your OS
from [GitHub](https://github.com/RIMS-Code/RIMSEvalGUI/releases).
Install and run.

## Packaging

To package the program, we use [`fbs`](https://build-system.fman.io) 
and you need an `fbs pro` license in order to package it.
Start a new virtual environment, enter the code folder, 
and install the requirements and fbs via:

```
pip install -r requirements.txt
pip install $FBS_DOWNLOAD_LINK
```

Here, `$FBS_DOWNLOAD_LINK` stands for the download link
that you received when purchasing fbs pro.
After all installations are complete and `fbs run` works, 
you can freeze and create an installer of the package via:

```
fbs freeze
fbs installer
```

*Note*: If you are on Windows,
further installations are necessary. 
If freezing fails, the error message
will provide you a link on where to download the Windows developer SDK.
If creating the installer fails,
you are likely missing [NSIS](https://nsis.sourceforge.io/Main_Page).
Install it and add its main folder to the system's `PATH` environment.

## Packaging and Release with GitHub Actions

Packaging and release of a new installer is also enabled
via GitHub Actions, see 
[here](https://github.com/trappitsch/fbs-release-github-actions).
Ensure that the `release_text.md` file is filled with the text
that you want to attach to the release.
When done, push your changes to GitHub.
Then create a tag to push as well. 
The tag should be the version you want to release, 
prepended by `v`, e.g., `v2.0.0`. 
Then push the tag to GitHub.
The release workflow will trigger when the tag is pushed.
It will package the software using `fbs pro`,
and create a new release with the installers as assets.

## Attribution

### Icons

All icons are (C) 2013 [Yusuke Kamiyamane](https://p.yusukekamiyamane.com/).
These icons are licensed under a Creative Commons
Attribution 3.0 License.
<http://creativecommons.org/licenses/by/3.0/>
