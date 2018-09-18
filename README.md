# Landsat Cloud Free Scene Count Tools

The purpose of these tools is to identify the approximate number of cloud free Landsat images by month and generate lists of Landsat collection 1 product identifiers that are "cloudy" and "clear".

The general steps are:
+ Download the Landsat bulk metadata CSV files using the "metadata_csv_download.py" script
+ Filter the Landsat bulk metadata CSV files using the "metadata_csv_filter.py" script
+ Download the Landsat quicklook images by path/row and year using the "quicklook_download.py" script.
+ Manually sort/move the "cloudy" images into a separate "cloudy" folder for each year.
+ Generate scene counts and product ID lists using the "make_quicklook_lists.py" script.

## Python Dependencies

The following module must be present to run some of the cloud free scene count scripts:
* [pandas](http://pandas.pydata.org)
* [requests](http://docs.python-requests.org)

For information on installing Python and Pandas or details on how to run the Python scripts, please see the [Python README](PYTHON.md).

## Download Landsat Bulk Metadata CSV files

The starting point for generating monthly cloud free scene counts is to obtain the full Landsat metadata CSV files.  These files are updated each day (Landsat 7 and 8), but for generating historical scene counts it is generally only necessary to download them once.  The CSV files can be downloaded by running the "metadata_csv_download.py" script or downloaded manually from the [Landsat Metadata Site](https://landsat.usgs.gov/download-entire-collection-metadata).

```
python metadata_csv_download.py
```

## Filter/reduce Landsat Bulk Metadata CSV files

The CSV files can be filtered and reduced using the "metadata_csv_filter.py" script or manually filtered using a text editor or spread sheet program.  WRS2 tile (path/row), year, and month filtering can be applied using the "--wrs2", "--years", and "--months" arguments.

```
python metadata_csv_filter.py --wrs2 p043r032 p043r33 --years 2010 2013-2015
```

## Download Landsat Quicklooks

The Landsat quicklook images can be downloaded using the "quicklook_download.py" script.  The script will download the quicklooks into separate folders by WRS2 tile (path/row) and year.  Any images that are not L1TP (fully georectified) will be automatically moved into a "cloudy" folder within that year.

```
python quicklook_download.py
```

Filtering by WRS2 tile, year, and month can also be applied to the quicklook download script using the same "--wrs2", "--years", and "--months" arguments.

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
python quicklook_download.py --id_type short
python make_quicklook_lists.py --id_type short
```
