# RIMSEvalGUI

This is the development branch for the GUI.
It uses [`fbs`](https://build-system.fman.io) for packaging
and you need an `fbs pro` license in order to package it.
All requirements are then handled by `fbs`.
If you want to manually install the requirements,
please check out the [`rimseval` repo](https://github.com/RIMS-Code/RIMSEval).
This project uses `PyQt6`.

ToDo: Run the GUI w/o having `fbs` installed.

## Requirements

Packaging requirements are in the respective `fbs` folder.
For installation of a virtual environments, 
install the requirements from `requirements.txt`, e.g.:

```bash
pip install -r requirements.txt
```

The `fbs` package is not listed in that file,
since you need to use the pro edition for packaging

## Attribution

### Icons

All icons are (C) 2013 [Yusuke Kamiyamane](https://p.yusukekamiyamane.com/).
These icons are licensed under a Creative Commons
Attribution 3.0 License.
<http://creativecommons.org/licenses/by/3.0/>