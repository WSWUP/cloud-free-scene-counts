# Landsat Cloud Free Scene Count Tools

The purpose of these tools is to identify the approximate number of cloud free Landsat images by month and generate lists of Landsat scene IDs that are "cloudy" and "clear".

The general steps are:
+ Download the Landsat bulk metadata CSV files using the "metadata_csv_download.py" script
+ Filter the Landsat bulk metadata CSV files using the "metadata_csv_filter.py" script
+ Download the Landsat quicklook images by path/row and year using the "metadata_csv_image_download.py" script.
+ Manually sort/move the "cloudy" images into a separate "cloudy" folder for each year.
+ Generate scene counts and scene ID lists using the "make_quicklook_lists.py" script.

## Python Dependencies

You will need Python and the [Pandas](http://pandas.pydata.org) module in order to run the scripts.

For information on installing Python and Pandas or details on how to run the Python scripts, please see the [Python README](PYTHON.md).

## Download Landsat Bulk Metadata CSV files

The starting point for generating monthly cloud free scene counts is to obtain the Landsat bulk metadata CSV files.  These files are updated each day (Landsat 7 and 8), but for generating historical scene counts it is generally only necessary to download them once.  The  CSV files can be downloaded by running the provided python script "metadata_csv_download.py" or manually from the [Landsat Bulk Metadata Site](https://landsat.usgs.gov/download-entire-collection-metadata).

```
python metadata_csv_download.py
```

## Filter/reduce Landsat Bulk Metadata CSV files

The CSV files can then be filtered and reduced using the provided python script "metadata_csv_filter.py" or manually filtered using a text editor or spread sheet program.  If the "--filter_conus" command line argument is used (see below), all non-CONUS Landsat path/rows will be removed from the metadata.  Additional filtering can also be manually added to this script.

```
python metadata_csv_filter.py --filter_conus
```

## Download Landsat Quicklooks

The Landsat quicklook images can be downloaded using the provided script "metadata_csv_image_download.py".  The script will download the quicklooks into separate folders by path/row and year.  Any images that are not L1T (fully georectified) will be automatically moved into a "cloudy" folder within that year.

From the command prompt, change directory into the quicklooks folder, then enter the following command, where FOLDER is the path to the folder containing the bulk metadata CSV files.  If "--csv" is not set, the script will attempt to use the current working directory.
```
python metadata_quicklook_download.py --csv FOLDER
```

If you double click the download script, it should prompt open a GUI prompting you to select the folder containing the CSV files.

The download script can be manually modified to limit the path, rows, or path/rows that are processed.

## Sort Cloudy Landsat Quicklooks

After downloading the quicklook images, they need to be manually sorted to identify the "cloudy" images.  Within each path/row/year folder, manually move each "cloudy" (or image with bad data, snow, etc.) to the "cloudy" folder.

## Generate Scene Counts and Clear/Cloudy Scene Lists

The clear and cloudy scene ID lists can be generated either from the command prompt or by double clicking the "make_quicklook_lists.py" script.

From the command prompt, enter the following command:
```
python make_quicklook_lists.py
```
