# Landsat Cloud Free Scene Count Tools

The purpose of these tools is to identify the approximate number of cloud free Landsat images by month and generate lists of Landsat collection 1 product identifiers that are "cloudy" and "clear".

The general steps are:
+ Download the Landsat bulk metadata CSV files using the "metadata_csv_download.py" script
+ Filter the Landsat bulk metadata CSV files using the "metadata_csv_filter.py" script
+ Download the Landsat quicklook images by path/row and year using the "metadata_csv_image_download.py" script.
+ Manually sort/move the "cloudy" images into a separate "cloudy" folder for each year.
+ Generate scene counts and product ID lists using the "make_quicklook_lists.py" script.

## Python Dependencies

The following module must be present to run some of the cloud free scene count scripts:
* [pandas](http://pandas.pydata.org)
* [requests](http://docs.python-requests.org)

For information on installing Python and Pandas or details on how to run the Python scripts, please see the [Python README](PYTHON.md).

## Download Landsat Bulk Metadata CSV files

The starting point for generating monthly cloud free scene counts is to obtain the Landsat bulk metadata CSV files.  These files are updated each day (Landsat 7 and 8), but for generating historical scene counts it is generally only necessary to download them once.  The CSV files can be downloaded by running the provided python script "metadata_csv_download.py" or manually from the [Landsat Bulk Metadata Site](https://landsat.usgs.gov/download-entire-collection-metadata).

```
python metadata_csv_download.py
```

## Filter/reduce Landsat Bulk Metadata CSV files

The CSV files can then be filtered and reduced using the provided python script "metadata_csv_filter.py" or manually filtered using a text editor or spread sheet program.  Path/row specific filtering can also be applied using the "-pr" or "--pathrows" argument.

```
python metadata_csv_filter.py -pr p043r032 p043r33
```

## Download Landsat Quicklooks

The Landsat quicklook images can be downloaded using the provided script "metadata_csv_image_download.py".  The script will download the quicklooks into separate folders by path/row and year.  Any images that are not L1TP (fully georectified) will be automatically moved into a "cloudy" folder within that year.

From the command prompt, change directory into the quicklooks folder, then enter the following command, where FOLDER is the path to the folder containing the bulk metadata CSV files.  If "--csv" is not set, the script will attempt to use the current working directory.
```
python metadata_quicklook_download.py --csv FOLDER
```

If you double click the download script, it should prompt open a GUI prompting you to select the folder containing the CSV files.

The download script can be manually modified to limit the path, rows, or path/rows that are processed.

## Sort Cloudy Landsat Quicklooks

After downloading the quicklook images, they need to be manually sorted to identify the "cloudy" images.  Within each path/row/year folder, manually move each "cloudy" (or image with bad data, snow, etc.) to the "cloudy" folder.

## Generate Scene Counts and Clear/Cloudy Scene Lists

The clear and cloudy product ID lists can be generated either from the command prompt or by double clicking the "make_quicklook_lists.py" script.

From the command prompt, enter the following command:
```
python make_quicklook_lists.py
```

## Example

For a detailed walk through of running the scripts and generating the scene list files, please see the provided [example](./example/EXAMPLE.md).

## Landsat Product Identifier

The scripts currently use the [Landsat Product Identifier](https://landsat.usgs.gov/landsat-collections#Prod%20IDs) as the unique identifier for each Landsat image.

The scripts originally (v0.1.X) used a "shortened" collection 1 product identifier to match the Earth Engine system index for the collection 1 images.  This ID is based on the Landsat product ID, but does not include the processing correction level, processing date, collection number, or collection category.  For example the Landsat product identifier LT05_L1TP_043030_20001014_20160922_01_T1 would have been saved in the output file as LT05_043030_20001014.  One assumption with this approach was that an image would be "cloudy" even if the processing date or correction level changes.

To enable backwards compatibility, the shortened IDs can be used in later versions of the scripts (v0.2+) by setting the "-id" or "--id_type" argument to "short".

```
python metadata_quicklook_download.py --id_type short
python make_quicklook_lists.py --id_type short
```
