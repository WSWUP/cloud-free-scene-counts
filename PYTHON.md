# Python

The cloud free scene count Python scripts have been tested using both Python 3.6 and Python 2.7.

The following module must be present to run some of the cloud free scene count scripts:
* [pandas](http://pandas.pydata.org)
* [requests](http://docs.python-requests.org)

## Anaconda

The easiest way of obtaining Python and all of the necessary external modules, is to install [Anaconda](https://www.continuum.io/downloads).

#### Installing/Updating Python Modules

The Requests and Pandas modules needed for these scripts are installed by default with Anaconda, but additional modules can be installed or updated using "conda".  For example to install the pandas and requests modules, enter the following in a command prompt or terminal window:

```
conda install pandas requests
```

To update the pandas and requests module to the latest version, enter the following in a command prompt or terminal window:

```
conda update pandas requests
```

## Running the Python Scripts

The python scripts can be run from the terminal (mac/linux) or command prompt (windows).

In some cases the scripts can also be run by double clicking directly on the script, but if you have multiple versions of Python installed (for example if you have ArcGIS and you install Anaconda), this may try to use a different different version of Python.

#### Windows Command Prompt

To open the Windows command prompt (on Windows 7), click the Start Menu -> All Programs -> Accessories -> Command Prompt, or press the Windows Key and the letter R, and then type "cmd" in the Run Tool dialog box.

To change to the D drive on your computer, you would type "D:" and press enter.
To change to the cloud free scene counts folder, assuming you installed it in your D:\Projects folder and you have already changed to the D drive if necessary, you would type: "cd D:\Projects\cloud-free-scene-counts" and then press enter.

#### Mac/Linux Terminal



## Command Line Arguments

The python scripts have additional arguments that can be set from the command line.  To view these options, run the script with the "-h" argument.

```
python metadata_quicklook_download.py -h

usage: quicklook_download.py [-h] [--csv FOLDER] [--output FOLDER]
                             [-pr pXXXrYYY [pXXXrYYY ...]]
                             [-y YEARS [YEARS ...]] [-m MONTHS [MONTHS ...]]
                             [--skiplist FILE] [-id {product,short}] [-o] [-d]

Download Landsat Collection 1 quicklook images

optional arguments:
  -h, --help            show this help message and exit
  --csv FOLDER          Landsat metadata CSV folder (default:
                        C:\Projects\cloud-free-scene-counts\example)
  --output FOLDER       Output folder (default: C:\Projects\cloud-free-scene-
                        counts\example)
  -pr pXXXrYYY [pXXXrYYY ...], --wrs2 pXXXrYYY [pXXXrYYY ...]
                        Space/comma separated list of Landsat WRS2 tiles to
                        download (i.e. -pr p043r032 p043r033) (default: None)
  -y YEARS [YEARS ...], --years YEARS [YEARS ...]
                        Space/comma separated list of years or year_ranges to
                        download (i.e. "--years 1984 2000-2015") (default:
                        None)
  -m MONTHS [MONTHS ...], --months MONTHS [MONTHS ...]
                        Space/comma separated list of months or month ranges
                        to download (i.e. "--months 1 2 3-5") (default: None)
  --skiplist FILE       File path of scene IDs that should be downloaded
                        directly to the "cloudy" scenes folder (default: None)
  -id {product,short}, --id_type {product,short}
                        Landsat ID type (default: product)
  -o, --overwrite       Overwite existing quicklooks (default: False)
  -d, --debug           Debug level logging (default: 20)
```

## Style Guide

All Python code should follow the [PEP8 Style Guide](https://www.python.org/dev/peps/pep-0008/).
