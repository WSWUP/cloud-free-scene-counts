# Landsat Cloud Free Scene Count - Example

For this example, please open up a command prompt or terminal window and navigate to the example folder in the cloud-free-scenes-counts project.  All of the example commands below will assume you are in the example folder, the scripts are in the parent folder, and you are using a Windows command prompt.

## Building the Example

The files provided in the example folder can be rebuilt using the following steps.

#### Download Landsat Bulk Metadata CSV files

The Landsat bulk metadata CSV files in the example folder were downloaded from the bulk metadata site on 2017-04-12 using the provided download script, and then filtered down to  Landsat images in 2000 and 2015 for path/row 43/30 (covering Central Oregon).

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
python ..\metadata_csv_filter.py -pr p043r030 -y 2000,2015
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
PATH_ROW,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC
p043r030,2000,2,3,4,3,3,2,3,4,4,4,2,3
p043r030,2015,2,3,3,3,4,4,4,4,2,3,2,3
```

## Sort Cloudy Landsat Quicklooks

Try moving the 2000_288_LT05 quicklook image from the "p043r030\2000" folder into the "p043r030\2000\cloudy" folder and rerun the make_quicklook_lists.py script.  Notice that the count for Oct., 2000 has gone from 4 to 3, and the product ID LT05_043030_20001014 has moved from clear_list.txt file to the skip_list.txt.

The scene count file should look identical to the following:
```
PATH_ROW,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC
p043r030,2000,2,3,4,3,3,2,3,4,4,3,2,3
p043r030,2015,2,3,3,3,4,4,4,4,2,3,2,3
```

## "Cloudy"

Determing the allowable amount and extent of clouds and snow in an image will depend on the application and the study are.  For estimating evapotranspiration (ET) over large basins using land surface temeprature, even small amounts of cloud, snow, shadows, and smoke can have major impacts on the final estimates.  For extracting time series of vegetation indices more moderate amounts of cloud cover may be acceptable.

Some other considerations when deciding whether to exclude an image is how close in time are the previous and next images, are the images Landsat 7 with missing data (due to the broken scan line corrector), are the images very early or late in the year when a measurement may not be needed or accurate.

##

The following is one possible interpretation of the clear scene counts and IDs, assuming that the goal is to compute ET using a remotely sensed surface energy balance and even minimal levels of cloud and snow cover are unwanted.  Some of the "non-cloudy" images are still questionable and might be removed in subsequent analysis/filtering (e.g. 2000-08-19, 2000-09-04, 2015-01-25, 2015-04-23)

Clear Scene Counts:
```
PATH_ROW,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC
p043r030,2000,0,0,0,2,2,2,3,3,3,2,0,0
p043r030,2015,0,2,1,2,2,2,2,2,2,1,0,0
```

Cloudy Scenes:
```
LE07_043030_20000108
LT05_043030_20000116
LE07_043030_20000124
LT05_043030_20000201
LE07_043030_20000209
LT05_043030_20000217
LE07_043030_20000225
LT05_043030_20000304
LE07_043030_20000312
LE07_043030_20000328
LE07_043030_20000413
LT05_043030_20000507
LT05_043030_20000523
LT05_043030_20000608
LE07_043030_20000803
LT05_043030_20000928
LT05_043030_20001014
LT05_043030_20001030
LE07_043030_20001107
LT05_043030_20001115
LE07_043030_20001123
LT05_043030_20001201
LE07_043030_20001209
LT05_043030_20001217
LE07_043030_20001225
LE07_043030_20150101
LC08_043030_20150109
LE07_043030_20150117
LE07_043030_20150202
LC08_043030_20150226
LC08_043030_20150314
LE07_043030_20150322
LC08_043030_20150330
LE07_043030_20150407
LC08_043030_20150517
LE07_043030_20150525
LC08_043030_20150602
LC08_043030_20150618
LC08_043030_20150704
LE07_043030_20150712
LC08_043030_20150805
LE07_043030_20150829
LE07_043030_20150914
LC08_043030_20151008
LC08_043030_20151024
LE07_043030_20151101
LC08_043030_20151109
LE07_043030_20151117
LC08_043030_20151125
LE07_043030_20151203
LC08_043030_20151211
LE07_043030_20151219
LC08_043030_20151227
```

Clear Scenes:
```
LT05_043030_20000320
LT05_043030_20000421
LE07_043030_20000429
LE07_043030_20000515
LE07_043030_20000531
LE07_043030_20000616
LT05_043030_20000624
LE07_043030_20000702
LE07_043030_20000718
LT05_043030_20000726
LT05_043030_20000811
LE07_043030_20000819
LT05_043030_20000827
LE07_043030_20000904
LT05_043030_20000912
LE07_043030_20000920
LE07_043030_20001006
LE07_043030_20001022
LC08_043030_20150125
LO08_043030_20150210
LE07_043030_20150218
LE07_043030_20150306
LC08_043030_20150415
LE07_043030_20150423
LC08_043030_20150501
LE07_043030_20150509
LE07_043030_20150610
LE07_043030_20150626
LC08_043030_20150720
LE07_043030_20150728
LE07_043030_20150813
LC08_043030_20150821
LC08_043030_20150906
LC08_043030_20150922
LE07_043030_20151016
```