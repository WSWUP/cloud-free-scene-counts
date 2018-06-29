import argparse
import logging
import os
import pprint
import re
import shutil
import sys

import pandas as pd


def main(csv_folder, wrs2_tile_list=[], years='', months='', conus_flag=False):
    """Filter Landsat Collection 1 bulk metadata CSV files

    Parameters
    ----------
    csv_folder : str
        Folder path of the Landsat bulk metadata CSV files.
    wrs2_tile_list : list, optional
        Landsat path/rows to process
        Example: ['p043r032', 'p043r033']
        Default is []
    years : str, optional
        Comma separated values or ranges of years to download.
        Example: '1984,2000-2015'
        Default is '' which will download images for all years.
    months : str, optional
        Comma separated values or ranges of months to keep.
        Example: '1, 2, 3-5'
        Default is '' which will keep images for all months.
    conus_flag : bool, optional
        If True, remove all non-CONUS entries.
        Remove path < 10, path > 48, row < 25 or row > 43.

    Notes
    -----
    The following filtering will be applied:
        Remove extreme latitude images (remove row < 100 or row > 9)
        Additional filtering can be manually specified in the script

    """
    logging.info('\nFilter/reducing Landsat Metadata CSV files')

    # Additional/custom path/row filtering can be hardcoded
    # wrs2_tile_list = []
    path_list = []
    row_list = []
    year_list = sorted(list(parse_int_set(years)))
    month_list = sorted(list(parse_int_set(months)))

    if conus_flag:
        path_list = list(range(10, 49))
        row_list = list(range(25, 44))

    csv_file_list = [
        'LANDSAT_8_C1.csv',
        'LANDSAT_ETM_C1.csv',
        'LANDSAT_TM_C1.csv',
    ]

    # Input fields
    acq_date_col = 'acquisitionDate'
    browse_url_col = 'browseURL'
    cloud_col = 'CLOUD_COVER_LAND'
    col_number_col = 'COLLECTION_NUMBER'
    col_category_col = 'COLLECTION_CATEGORY'
    product_id_col = 'LANDSAT_PRODUCT_ID'
    scene_id_col = 'sceneID'
    sensor_col = 'sensor'
    time_col = 'sceneStartTime'
    data_type_col = 'DATA_TYPE_L1'
    wrs2_path_col = 'path'
    wrs2_row_col = 'row'
    # browse_col = 'browseAvailable'
    # available_col = 'L1_AVAILABLE'
    # utm_zone = 'UTM_ZONE'  # Not in L8 file
    # azimuth_col = 'sunAzimuth'
    # elevation_col = 'sunElevation'

    # Output fieldnames: matches metadata_csv_api.py and newer style formatting
    acq_date_col_out = 'ACQUISITION_DATE'
    browse_url_col_out = 'BROWSE_REFLECTIVE_PATH'
    cloud_col_out = 'CLOUD_COVER_LAND'
    col_number_col_out = 'COLLECTION_NUMBER'
    col_category_col_out = 'COLLECTION_CATEGORY'
    product_id_col_out = 'LANDSAT_PRODUCT_ID'
    scene_id_col_out = 'LANDSAT_SCENE_ID'
    sensor_col_out = 'SENSOR'
    time_col_out = 'SCENE_START_TIME'
    data_type_col_out = 'DATA_TYPE_L1'
    wrs2_path_col_out = 'WRS_PATH'
    wrs2_row_col_out = 'WRS_ROW'

    # Generated fields
    wrs2_tile_col = 'WRS2_TILE'

    # data_types = ['L1TP']
    # categories = ['T1', 'RT']

    # Only load the following columns from the CSV
    use_cols = [
        acq_date_col, browse_url_col, cloud_col,
        col_category_col, col_number_col, data_type_col,
        product_id_col, scene_id_col, sensor_col, time_col,
        wrs2_path_col, wrs2_row_col]

    out_cols = [
        acq_date_col_out, browse_url_col_out, cloud_col_out,
        col_category_col_out, col_number_col_out, data_type_col_out,
        product_id_col_out, scene_id_col_out, sensor_col_out, time_col_out,
        wrs2_path_col_out, wrs2_row_col_out, wrs2_tile_col]

    dtype_cols = {
        acq_date_col: object,
        browse_url_col: object,
        col_number_col: object,
        col_category_col: object,
        cloud_col: float,
        data_type_col: object,
        product_id_col: object,
        scene_id_col: object,
        sensor_col: object,
        time_col: object,
        wrs2_path_col: int,
        wrs2_row_col: int}
        # elevation_col: float,
        # azimuth_col: float,
        # browse_col: object,
        # scene_id_col: object,

    # Remap download station strings in Landsat 7 file to just the code
    stations = {
        'AGS - Poker Flats, Alaska, USA': 'AGS',
        'ASA - Alice Springs, Austrailia': 'ASA',   # Spelling
        # 'ASA - Alice Springs, Australia': 'ASA',
        'ASN - Alice Springs, Australia': 'ASN',
        'BJC - Beijing, China': 'BJC',
        'BKT - Bangkok, Thailand': 'BKT',
        'COA - Cordoba, Argentina': 'COA',
        'CUB - Cuiaba, Brazil': 'CUB',
        'DKI - Parepare, Indonesia': 'DKI',
        'EDC Sioux Falls, South Dakota, USA (aka LGS)': 'EDC',
        'EDC - Sioux Falls, South Dakota, USA (aka LGS)': 'EDC',
        'FUI - Fucino, Italy': 'FUI',
        'GNC -  Gatineau, Canada': 'GNC',       # Extra space
        'GNC - Gatineau, Canada': 'GNC',
        'HAJ - Hatoyama, Japan': 'HAJ',
        'HIJ - Hiroshima, Japan': 'HIJ',
        'HOA - Hobart, Australia': 'HOA',
        'JSA': 'JSA',
        'KIS - Kiruna, Sweden': 'KIS',
        'LBG': 'LBG',
        'MPS - Maspalomas, Spain': 'MPS',
        'MTI - Matera, Italy': 'MTI',
        'NSG - Neustreliz, Germany': 'NSG',
        'NPA - North Pole, Alaska': 'NPA',
        'PAC - Prince Albert, Canada': 'PAC',
        'PFS - Poker Flats, Alaska': 'PFS',
        'SGS - Svalbard, Norway': 'SGS',
        'SGI - Shadnagar, India': 'SGI',
        'SG1': 'SGI',                           # Should this be SGI or SG1?
        'UPR - Mayaguez, Puerto Rico': 'UPR',
    }

    # product_re = re.compile(
    #     '(LT05|LE07|LC08)_\w{4}_\d{6}_\d{8}_\d{8}_\d{2}_\w{2}')
    # # The download station SGI is listed as SG1 in a couple of scenes
    # scene_re = re.compile('(LT5|LE7|LC8)\d{13}\D{2}\w\d{2}')

    # Setup and validate the path/row lists
    wrs2_tile_list, path_list, row_list = check_wrs2_tiles(
        wrs2_tile_list, path_list, row_list)

    # Process each CSV
    for csv_name in csv_file_list:
        logging.info('{}'.format(csv_name))
        csv_path = os.path.join(csv_folder, csv_name)

        # Process the CSVs in chunks to limit the memory usage
        logging.info('  Filtering by chunk')
        temp_path = csv_path.replace('.csv', '_filter.csv')
        for i, input_df in enumerate(pd.read_csv(
                csv_path, parse_dates=[acq_date_col], chunksize=1 << 16,
                usecols=use_cols)):
                # usecols=list(dtype_cols.keys()), dtype=dtype_cols)):
            logging.debug('\n  Scene count: {}'.format(len(input_df)))

            # Remove high latitute rows
            if wrs2_row_col in use_cols:
                input_df = input_df[input_df[wrs2_row_col] < 100]
                input_df = input_df[input_df[wrs2_row_col] > 9]
                logging.debug('  Scene count: {}'.format(len(input_df)))

            # Filter by path and row
            if path_list and wrs2_path_col in use_cols:
                logging.debug('  Filtering by path')
                input_df = input_df[input_df[wrs2_path_col] <= max(path_list)]
                input_df = input_df[input_df[wrs2_path_col] >= min(path_list)]
                input_df = input_df[input_df[wrs2_path_col].isin(path_list)]
            if row_list and wrs2_row_col in use_cols:
                logging.debug('  Filtering by row')
                input_df = input_df[input_df[wrs2_row_col] <= max(row_list)]
                input_df = input_df[input_df[wrs2_row_col] >= min(row_list)]
                input_df = input_df[input_df[wrs2_row_col].isin(row_list)]
            if wrs2_tile_list and wrs2_path_col in use_cols and\
                    wrs2_row_col in use_cols:
                logging.debug('  Filtering by path/row')
                try:
                    input_df[wrs2_tile_col] = input_df[[wrs2_path_col,
                                                        wrs2_row_col]]\
                        .apply(lambda x: 'p{:03d}r{:03d}'.format(x[0], x[1]),
                               axis=1)
                except ValueError:
                    logging.info('  Possible empty DataFrame, skipping file')
                    continue
                input_df = input_df[input_df[wrs2_tile_col].isin(wrs2_tile_list)]
                # input_df.drop(wrs2_tile_col, axis=1, inplace=True)

            # Filter by year
            if year_list and acq_date_col in use_cols:
                input_df = input_df[input_df[acq_date_col].dt.year.isin(year_list)]

            # Skip early/late months
            if month_list and acq_date_col in use_cols:
                logging.debug('  Filtering by month')
                input_df = input_df[input_df[acq_date_col].dt.month.isin(month_list)]

            # # Remove nighttime images
            # # (this could be a larger value to remove high latitute images)
            # if elevation_col in use_cols:
            #     input_df = input_df[input_df[elevation_col] > 0]
            # logging.debug('  Scene count: {}'.format(len(input_df)))

            input_df.sort_index(axis=1, inplace=True)

            # Reorder and rename columns to match metadata_csv_api.py
            # newer style name format
            input_df = input_df[use_cols + [wrs2_tile_col]]
            input_df.columns = out_cols

            # write dataframe to csv
            if i == 0:
                input_df.to_csv(temp_path, mode='w', index=False, header=True)
            else:
                input_df.to_csv(temp_path, mode='a', index=False, header=False)
        # overwrite metadata csv with filter csv
        if os.path.isfile(temp_path):
            shutil.move(temp_path, csv_path)


def check_wrs2_tiles(wrs2_tile_list=[], path_list=[], row_list=[]):
    """Setup path/row lists

    Populate the separate path and row lists from wrs2_tile_list
    Filtering by path and row lists separately seems to be faster than
        creating a new path/row field and filtering directly
    """
    wrs2_tile_fmt = 'p{:03d}r{:03d}'
    wrs2_tile_re = re.compile('p(?P<PATH>\d{1,3})r(?P<ROW>\d{1,3})')

    # Force path/row list to zero padded three digit numbers
    if wrs2_tile_list:
        wrs2_tile_list = sorted([
            wrs2_tile_fmt.format(int(m.group('PATH')), int(m.group('ROW')))
            for pr in wrs2_tile_list
            for m in [wrs2_tile_re.match(pr)] if m])

    # If path_list and row_list were specified, force to integer type
    # Declare variable as an empty list if it does not exist
    try:
        path_list = list(sorted(map(int, path_list)))
    except ValueError:
        logging.error(
            '\nERROR: The path list could not be converted to integers, '
            'exiting\n  {}'.format(path_list))
        sys.exit()
    try:
        row_list = list(sorted(map(int, row_list)))
    except ValueError:
        logging.error(
            '\nERROR: The row list could not be converted to integers, '
            'exiting\n  {}'.format(row_list))
        sys.exit()

    # Convert wrs2_tile_list to path_list and row_list if not set
    # Pre-filtering on path and row separately is faster than building wrs2_tile
    # This is a pretty messy way of doing this...
    if wrs2_tile_list and not path_list:
        path_list = sorted(list(set([
            int(wrs2_tile_re.match(pr).group('PATH'))
            for pr in wrs2_tile_list if wrs2_tile_re.match(pr)])))
    if wrs2_tile_list and not row_list:
        row_list = sorted(list(set([
            int(wrs2_tile_re.match(pr).group('ROW'))
            for pr in wrs2_tile_list if wrs2_tile_re.match(pr)])))
    if path_list:
        logging.debug('  Paths: {}'.format(
            ' '.join(list(map(str, path_list)))))
    if row_list:
        logging.debug('  Rows: {}'.format(' '.join(list(map(str, row_list)))))
    if wrs2_tile_list:
        logging.debug('  WRS2 Tiles: {}'.format(
            ' '.join(list(map(str, wrs2_tile_list)))))

    return wrs2_tile_list, path_list, row_list


def is_valid_folder(parser, arg):
    if not os.path.isdir(arg):
        parser.error('The folder {} does not exist!'.format(arg))
    else:
        return arg


def parse_int_set(nputstr=""):
    """Return list of numbers given a string of ranges

    http://thoughtsbyclayg.blogspot.com/2008/10/parsing-list-of-numbers-in-python.html
    """
    selection = set()
    invalid = set()
    # tokens are comma seperated values
    tokens = [x.strip() for x in nputstr.split(',')]
    for i in tokens:
        try:
            # typically tokens are plain old integers
            selection.add(int(i))
        except:
            # if not, then it might be a range
            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    # we have items seperated by a dash
                    # try to build a valid range
                    first = token[0]
                    last = token[len(token) - 1]
                    for x in range(first, last + 1):
                        selection.add(x)
            except:
                # not an int and not a range...
                invalid.add(i)
    # Report invalid tokens before returning valid selection
    # print "Invalid set: " + str(invalid)
    return selection


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Filter Landsat Collection 1 bulk metadata CSV files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--csv', type=lambda x: is_valid_folder(parser, x), metavar='FOLDER',
        default=os.getcwd(), help='Landsat bulk metadata CSV folder')
    parser.add_argument(
        '-pr', '--pathrows', nargs='+', default=None, metavar='pXXXrYYY',
        help='Space separated string of Landsat path/rows to keep '
             '(i.e. -pr p043r032 p043r033)')
    parser.add_argument(
        '-y', '--years', default='1984-2017', type=str,
        help='Comma separated list or range of years to download'
             '(i.e. "--years 1984,2000-2015")')
    parser.add_argument(
        '-m', '--months', default='1-12', type=str,
        help='Comma separated list or range of months to download'
             '(i.e. "--months 1,2,3-5")')
    parser.add_argument(
        '--conus', default=False, action='store_true',
        help='Filter CSV files to only CONUS Landsat images')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    if args.csv and os.path.isdir(os.path.abspath(args.csv)):
        args.csv = os.path.abspath(args.csv)

    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')

    main(csv_folder=args.csv, wrs2_tile_list=args.pathrows,
         years=args.years, months=args.months, conus_flag=args.conus)
