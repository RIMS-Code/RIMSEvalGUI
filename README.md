# RIMSEvalGUI

This is the repository for the GUI.

If you want to manually install the requirements,
please check out the [`rimseval` repo](https://github.com/RIMS-Code/RIMSEval).
This project uses `PyQt6`.

ToDo: Run the GUI w/o having `fbs` installed.

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

TBD

## Packaging

To package the program, we use [`fbs`](https://build-system.fman.io) 
and you need an `fbs pro` license in order to package it.
All requirements are then handled by `fbs`.

Instructions TBD

## Attribution

### Icons

All icons are (C) 2013 [Yusuke Kamiyamane](https://p.yusukekamiyamane.com/).
These icons are licensed under a Creative Commons
Attribution 3.0 License.
<http://creativecommons.org/licenses/by/3.0/>