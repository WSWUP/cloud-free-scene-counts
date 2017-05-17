# Landsat Cloud Free Scene Count - Example

The Landsat bulk metadata CSV files were downloaded from the bulk metadata site using the provided download script and then filtered down to all Landsat images in path/row 43/30 (covering Central Oregon) for 1984-2016.

The Landsat quicklooks can be downloaded with the following command.  The --csv and --output command line arguments are being called assuming that you are running the script from within the example folder.
```
python ../metadata_csv_image_download.py --csv ./ --output ./
```
