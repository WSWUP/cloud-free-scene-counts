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

The Landsat bulk metadata CSV files can be filtered to match those provided in the example folder by running the "metadata_csv_filter.py" script with the the "--example" command line argument.

```
python ..\metadata_csv_filter.py --example
```

#### Download Landsat Quicklooks

The Landsat quicklooks provided in the example folder can be downloaded by running the "metadata_quicklook_download.py" script within the example folder.

```
python ..\metadata_quicklook_download.py
```


## Generate Scene Counts and Clear/Cloudy Scene Lists

Before identifying and sorting the cloudy quicklook images, generate an initial set of scene counts and scene ID lists using the following:

```
python ..\make_quicklook_lists.py
```

The file "clear_scene_counts.txt" should look identical to the following:
```
PATH_ROW,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC
p43r30,2000,1,3,4,3,3,2,3,4,4,4,2,3
p43r30,2015,2,3,3,3,4,4,4,4,2,3,2,3
```

## Sort Cloudy Landsat Quicklooks

Try moving the 2000_288_LT5 quicklook image from the "p043r030\2000" folder into the "p043r030\2000\cloudy" folder and rerun the make_quicklook_lists.py script.  Notice that the count for Oct., 2000 has gone from 4 to 3, and the scene ID LT50430302000288 has moved from clear_list.txt file to the skip_list.txt.

The scene count file should look identical to the following:
```
PATH_ROW,YEAR,JAN,FEB,MAR,APR,MAY,JUN,JUL,AUG,SEP,OCT,NOV,DEC
p43r30,2000,1,3,4,3,3,2,3,4,4,3,2,3
p43r30,2015,2,3,3,3,4,4,4,4,2,3,2,3
```
