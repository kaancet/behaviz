# behaviz

A modular and flexible graphing library

![OS](https://img.shields.io/badge/OS-independent-green)
![Python](https://img.shields.io/badge/python-3.10-blue)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Behaviz tries to solve two main issues:

1. Consistent and reproducible plots for similar data
2. Modularity, flexibility and access to low-level plot properties through high-level function calls

It's built on `spec` dataclasses that hold the information about the plot in general. These can be created on the fly or called without modification during function calls.

It also enables overriding any plot property through overriding with kwargs inputs.

The idea behind this library is to be able to use building blocks of plots, like line, scatter, etc. to create any plot the user might need and having the ability to modify the properties of building blocks from the high-level call of the combined plot function call.

## To do

- Setting background in one plot can propagate to following plots
- Make overriding functions programmatically generate by existing functions in core
- Add other backends e.g. bokeh, seaborn...
