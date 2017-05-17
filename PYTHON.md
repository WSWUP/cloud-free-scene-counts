# Python

The cloud free scene count Python scripts have been tested using both Python 3.6 and Python 2.7.

The following module must be present to run some of the cloud free scene count scripts:
* [pandas](http://pandas.pydata.org)

## Anaconda

The easiest way of obtaining Python and all of the necessary external modules, is to install [Anaconda](https://www.continuum.io/downloads).

#### Installing/Updating Python Modules

The Pandas module needed for these scripts is installed by default with Anaconda but additional modules can be installed or updated using "conda".  For example to install the pandas module, enter the following in a command prompt or terminal window:

```
conda install pandas
```

To update the pandas module to the latest version, enter the following in a command prompt or terminal window:

```
conda update pandas
```

## Running the Python Scripts

The python scripts can be run from the terminal (mac/linux) or command prompt (windows).

In some cases the scripts can also be run by double clicking directly on the script, but if you have multiple versions of Python installed (for example if you have ArcGIS and you install Anaconda), this may try to use a different different version of Python.

#### Windows Command Prompt

To open the Windows command prompt (on Windows 7), click the Start Menu -> All Programs -> Accessories -> Command Prompt, or press the Windows Key and the letter R, and then type "cmd" in the Run Tool dialog box.

To change to the D drive on your computer, you would type "D:" and press enter.
To change to the cloud free scene counts folder, assuming you installed it in your D:\Projects folder and you have already changed to the D drive if necessary, you would type: "cd D:\Projects\cloud-free-scene-counts" and then press enter.

#### Mac/Linux Terminal



#### Command Line Arguments

The python scripts have additional arguments that can be set from the command line.  To view these options, run the script with the "-h" argument.

```
python metadata_csv_image_download.py -h

usage: metadata_csv_image_download.py [-h] [--csv CSV] [--output OUTPUT]
                                      [--skiplist SKIPLIST] [-o] [-d]

Download Landsat Quicklook images Beware that many values are hardcoded!

optional arguments:
  -h, --help           show this help message and exit
  --csv CSV            Landsat bulk metadata CSV folder
                       (default: D:\Projects\cloud-free-scene-counts)
  --output OUTPUT      Output folder
                       (default: D:\Projects\Projects\cloud-free-scene-counts)
  --skiplist SKIPLIST  Skips files in skip list (default: None)
  -o, --overwrite      Include existing scenes in scene download list
                       (default: False)
  -d, --debug          Debug level logging (default: 20)


```

#### Style Guide
All Python code should follow the [PEP8 Style Guide](https://www.python.org/dev/peps/pep-0008/).
