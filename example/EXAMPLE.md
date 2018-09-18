# Landsat Cloud Free Scene Count - Example

For this example, please open up a command prompt or terminal window and navigate to the example folder in the cloud-free-scenes-counts project.  All of the example commands below will assume you are in the example folder, the scripts are in the parent folder, and you are using a Windows command prompt.

## Building the Example

The files provided in the example folder can be rebuilt using the following steps.

#### Download Landsat Bulk Metadata CSV files

The Landsat bulk metadata CSV files in the example folder were downloaded from the bulk metadata site on 2018-07-18 using the provided download script, and then filtered down to Landsat images in 2000 and 2015 for path/row 43/30 (covering Central Oregon).

If you would like to recreate the example CSV files, the metadata_csv_download.py script could be run from within the example folder with the following command.

In a Windows command prompt, the command would be:
```
python ..\metadata_csv_download.py --overwrite
```

In a Mac/Linux terminal windows, the same command would be (note the forward slashes instead of back slashes):
```
python ../metadata_csv_download.py --overwrite
```

The "..\" or "../" notation in the script call indicates that Python should look into the parent folder for the download script.  If a default output folder is not using the "--csv" command line argument, the script will attempt to use the current working directory, which in this case will be the example folder.  If the "--overwrite" command line argument is not set, the script will skip any CSV files that already exist in the output folder.

#### Filter CSV files

The Landsat bulk metadata CSV files can be filtered to match those provided in the example folder by running the "metadata_csv_filter.py" script with the command line arguments seen below.

```
python ..\metadata_csv_filter.py -pr p043r030 --years 2000 2015
```

#### Download Landsat Quicklooks

The Landsat quicklooks provided in the example folder can be downloaded by running the "metadata_quicklook_download.py" script within the example folder.

```
python ..\metadata_quicklook_download.py
```

## Generate Scene Counts and Clear/Cloudy Scene Lists

Before identifying and sorting the cloudy quicklook images, generate an initial set of scene counts and product ID lists using the following:

```
python ..\make_quicklook_lists.py
```

The file "clear_scene_counts.txt" should look identical to the following:
```
WRS2_TILE,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC
p043r030,2000,2,3,4,3,3,2,3,4,4,4,2,3
p043r030,2015,2,3,3,3,4,4,4,4,2,3,2,3
```

## Sort Cloudy Landsat Quicklooks

Try moving the 20001014_288_LT05 quicklook image from the "p043r030\2000" folder into the "p043r030\2000\cloudy" folder and rerun the make_quicklook_lists.py script.  Notice that the count for Oct., 2000 has gone from 4 to 3, and the product ID LT05_043030_20001014 has moved from clear_list.txt file to the cloudy_scenes.txt.

The updated scene count file should look identical to the following:
```
WRS2_TILE,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC
p043r030,2000,2,3,4,3,3,2,3,4,4,3,2,3
p043r030,2015,2,3,3,3,4,4,4,4,2,3,2,3
```

## "Cloudy"

Determining the allowable amount and extent of clouds and snow in an image will depend on the application and the study are.  For estimating evapotranspiration (ET) over large basins using land surface temperature, even small amounts of cloud, snow, shadows, and smoke can have major impacts on the final estimates.  For extracting time series of vegetation indices more moderate amounts of cloud cover may be acceptable.

Some other considerations when deciding whether to exclude an image is how close in time are the previous and next images, are the images Landsat 7 with missing data (due to the broken scan line corrector), are the images very early or late in the year when a measurement may not be needed or accurate.

## Final Scene ID lists

The following is one possible interpretation of the clear scene counts and IDs, assuming that the goal is to compute ET using a remotely sensed surface energy balance and even minimal levels of cloud and snow cover are unwanted.  Some of the "non-cloudy" images are still questionable and might be removed in subsequent analysis/filtering (e.g. 2000-08-19, 2000-09-04, 2015-01-25, 2015-04-23)

Clear Scene Counts:
```
WRS2_TILE,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC
p043r030,2000,0,0,1,2,2,2,3,3,3,2,0,0
p043r030,2015,0,2,1,2,2,2,2,2,2,1,0,0
```

Clear Scenes:
```
LT05_L1TP_043030_20000320_20160919_01_T1
LT05_L1TP_043030_20000421_20160918_01_T1
LE07_L1TP_043030_20000429_20161001_01_T1
LE07_L1TP_043030_20000515_20161001_01_T1
LE07_L1TP_043030_20000531_20161002_01_T1
LE07_L1TP_043030_20000616_20161001_01_T1
LT05_L1TP_043030_20000624_20160918_01_T1
LE07_L1TP_043030_20000702_20161001_01_T1
LE07_L1TP_043030_20000718_20161002_01_T1
LT05_L1TP_043030_20000726_20160918_01_T1
LT05_L1TP_043030_20000811_20160918_01_T1
LE07_L1TP_043030_20000819_20161002_01_T1
LT05_L1TP_043030_20000827_20160918_01_T1
LE07_L1TP_043030_20000904_20161001_01_T1
LT05_L1TP_043030_20000912_20160918_01_T1
LE07_L1TP_043030_20000920_20161001_01_T1
LE07_L1TP_043030_20001006_20161002_01_T1
LE07_L1TP_043030_20001022_20161002_01_T1
LO08_L1TP_043030_20150210_20170301_01_T1
LE07_L1TP_043030_20150218_20160902_01_T1
LE07_L1TP_043030_20150306_20160902_01_T1
LC08_L1TP_043030_20150415_20170227_01_T1
LE07_L1TP_043030_20150423_20160902_01_T1
LC08_L1TP_043030_20150501_20170301_01_T1
LE07_L1TP_043030_20150509_20160902_01_T1
LE07_L1TP_043030_20150610_20160905_01_T1
LE07_L1TP_043030_20150626_20160902_01_T1
LC08_L1TP_043030_20150720_20170226_01_T1
LE07_L1TP_043030_20150728_20160902_01_T1
LE07_L1TP_043030_20150813_20160903_01_T1
LC08_L1TP_043030_20150821_20170225_01_T1
LC08_L1TP_043030_20150906_20170225_01_T1
LC08_L1TP_043030_20150922_20170225_01_T1
LE07_L1TP_043030_20151016_20160903_01_T1
```

Cloudy Scenes:
```
LE07_L1TP_043030_20000108_20161002_01_T1
LT05_L1TP_043030_20000116_20160919_01_T1
LE07_L1GT_043030_20000124_20161002_01_T2
LT05_L1GS_043030_20000201_20160918_01_T2
LE07_L1TP_043030_20000209_20161003_01_T1
LT05_L1TP_043030_20000217_20160918_01_T1
LE07_L1TP_043030_20000225_20161002_01_T1
LT05_L1TP_043030_20000304_20160918_01_T1
LE07_L1TP_043030_20000312_20161002_01_T1
LE07_L1TP_043030_20000328_20161003_01_T1
LE07_L1TP_043030_20000413_20161001_01_T1
LT05_L1GS_043030_20000507_20160918_01_T2
LT05_L1TP_043030_20000523_20160918_01_T1
LT05_L1GS_043030_20000608_20160918_01_T2
LE07_L1TP_043030_20000803_20161002_01_T1
LT05_L1TP_043030_20000928_20160918_01_T1
LT05_L1TP_043030_20001014_20160922_01_T1
LT05_L1TP_043030_20001030_20160918_01_T1
LE07_L1TP_043030_20001107_20161001_01_T1
LT05_L1GS_043030_20001115_20160918_01_T2
LE07_L1TP_043030_20001123_20161002_01_T1
LT05_L1TP_043030_20001201_20160918_01_T1
LE07_L1GT_043030_20001209_20161002_01_T2
LT05_L1TP_043030_20001217_20160918_01_T1
LE07_L1TP_043030_20001225_20161001_01_T1
LE07_L1TP_043030_20150101_20160905_01_T1
LC08_L1TP_043030_20150109_20170302_01_T2
LE07_L1GT_043030_20150117_20160903_01_T2
LC08_L1TP_043030_20150125_20170302_01_T1
LE07_L1GT_043030_20150202_20160903_01_T2
LC08_L1TP_043030_20150226_20180201_01_T1
LC08_L1GT_043030_20150314_20170228_01_T2
LE07_L1TP_043030_20150322_20160906_01_T1
LC08_L1TP_043030_20150330_20170228_01_T1
LE07_L1TP_043030_20150407_20160904_01_T1
LC08_L1TP_043030_20150517_20170301_01_T1
LE07_L1TP_043030_20150525_20160902_01_T1
LC08_L1TP_043030_20150602_20170226_01_T1
LC08_L1TP_043030_20150618_20170226_01_T1
LC08_L1TP_043030_20150704_20170226_01_T1
LE07_L1TP_043030_20150712_20160904_01_T1
LC08_L1TP_043030_20150805_20170311_01_T1
LE07_L1TP_043030_20150829_20160905_01_T1
LE07_L1GT_043030_20150914_20160902_01_T2
LC08_L1TP_043030_20151008_20170225_01_T1
LC08_L1TP_043030_20151024_20170225_01_T1
LE07_L1TP_043030_20151101_20160903_01_T1
LC08_L1TP_043030_20151109_20170225_01_T1
LE07_L1GT_043030_20151117_20160903_01_T2
LC08_L1GT_043030_20151125_20170225_01_T2
LE07_L1TP_043030_20151203_20160903_01_T1
LC08_L1TP_043030_20151211_20170224_01_T1
LE07_L1GT_043030_20151219_20160902_01_T2
LC08_L1TP_043030_20151227_20180201_01_T2
```
