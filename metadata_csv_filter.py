import argparse
import logging
import os
import pprint
import re
import sys

import pandas as pd


def main(csv_folder, wrs2_tiles=None, years=None, months=None,
         landsat=[5, 7, 8], conus_flag=False):
    """Filter Landsat Collection 1 bulk metadata CSV files

    Parameters
    ----------
    csv_folder : str
        Folder path of the Landsat bulk metadata CSV files.
    wrs2_tiles : list, optional
        Landsat WRS2 tiles (path/rows) to include.
        The default is None which will keep entries for all tiles.
        Example: ['p043r032', 'p043r033']
    years : list, optional
        Comma separated values or ranges of years to include.
        The default is None which will keep entries for all years.
        Example: ['1984', '2000-2015']
    months : list, optional
        Comma separated values or ranges of months to include.
        The default is None which will keep entries for all months.
        Example: ['1', '2', '3-5']
    landsat : list, optional
        CSV files will only be downloaded for the specified Landsat missions.
        The default is to attempt to process Landsat(s) 5, 7, and 8, but this
        is also dependent on the "years" parameter.
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

    if wrs2_tiles is not None:
        wrs2_tiles = sorted([
            x.strip() for w in wrs2_tiles for x in w.split(',') if x.strip()])
    else:
        wrs2_tiles = []

    if years is not None:
        years = sorted([x for y in years for x in parse_int_set(y)])
    else:
        years = []

    if months is not None:
        months = sorted([x for m in months for x in parse_int_set(m)])
    else:
        months = []

    if conus_flag:
        paths = list(range(10, 49))
        rows = list(range(25, 44))
    else:
        paths = []
        rows = []

    csv_names = {
        8: 'LANDSAT_8_C1.csv',
        7: 'LANDSAT_ETM_C1.csv',
        5: 'LANDSAT_TM_C1.csv',
    }
    csv_years = {
        8: set(range(2013, 2099)),
        7: set(range(1999, 2099)),
        5: set(range(1984, 2012)),
    }

    # Input fields (default values in bulk metadata CSV file)
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

    # Output fieldnames (matches metadata_csv_api.py and newer style formatting)
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

    # Field rename mapping
    use_cols = [
        [acq_date_col, acq_date_col_out],
        [browse_url_col, browse_url_col_out],
        [cloud_col, cloud_col_out],
        [col_category_col, col_category_col_out],
        [col_number_col, col_number_col_out],
        [data_type_col, data_type_col_out],
        [product_id_col, product_id_col_out],
        [scene_id_col, scene_id_col_out],
        [sensor_col, sensor_col_out],
        [time_col, time_col_out],
        [wrs2_path_col, wrs2_path_col_out],
        [wrs2_row_col, wrs2_row_col_out],
    ]

    # Setup and validate the path/row lists
    wrs2_tiles, paths, rows = check_wrs2_tiles(wrs2_tiles, paths, rows)

    # Process each CSV
    for landsat_index, csv_name in csv_names.items():
        csv_path = os.path.join(csv_folder, csv_name)
        logging.info('{}'.format(csv_name))
        logging.debug('  {}'.format(os.path.join(csv_folder, csv_name)))

        if landsat_index not in landsat:
            logging.info('  Skipping Landsat {}'.format(landsat_index))
            # logging.info('  Removing Landsat {} csv'.format(landsat_index))
            # os.remove(csv_path)
            continue
        elif years and not csv_years[landsat_index].intersection(set(years)):
            logging.info('  No data for target year(s), skipping file')
            # logging.info('  No data for target year(s), removing file')
            # os.remove(csv_path)
            continue
        elif not os.path.isfile(csv_path):
            logging.info('  The CSV file does not exist, skipping')

        # Process the CSVs in chunks to limit the memory usage
        logging.info('  Filtering by chunk')
        temp_path = csv_path.replace('.csv', '_filter.csv')
        append_flag = False
        for input_df in pd.read_csv(csv_path, chunksize=1 << 16):
            logging.debug('\n  Scene count: {}'.format(len(input_df)))

            # Rename fields before filtering
            for input_col, output_col in use_cols:
                if input_col in input_df.columns:
                    input_df.rename(columns={input_col: output_col},
                                    inplace=True)

            # Manually convert date string to datetime
            # Can't use parse_dates in read_csv() since we are not sure which
            #   field is present.
            if acq_date_col in input_df.columns:
                input_df[acq_date_col] = pd.to_datetime(
                    input_df[acq_date_col], infer_datetime_format=True)
            if acq_date_col_out in input_df.columns:
                input_df[acq_date_col_out] = pd.to_datetime(
                    input_df[acq_date_col_out], infer_datetime_format=True)

            # Remove high latitude rows
            if wrs2_row_col_out in input_df.columns:
                input_df = input_df[input_df[wrs2_row_col_out] < 100]
                input_df = input_df[input_df[wrs2_row_col_out] > 9]
                logging.debug('  Scene count: {}'.format(len(input_df)))

            # Filter by path and row separately
            if paths and wrs2_path_col_out in input_df.columns:
                logging.debug('  Filtering by path')
                input_df = input_df[input_df[wrs2_path_col_out] <= max(paths)]
                input_df = input_df[input_df[wrs2_path_col_out] >= min(paths)]
                input_df = input_df[input_df[wrs2_path_col_out].isin(paths)]
            if rows and wrs2_row_col_out in input_df.columns:
                logging.debug('  Filtering by row')
                input_df = input_df[input_df[wrs2_row_col_out] <= max(rows)]
                input_df = input_df[input_df[wrs2_row_col_out] >= min(rows)]
                input_df = input_df[input_df[wrs2_row_col_out].isin(rows)]

            # Filter by WRS2 tile list (apply call raises exception on empty df)
            if input_df.empty:
                logging.debug('  Empty dataframe, skipping chunk')
                continue
            if (wrs2_tiles and
                    wrs2_path_col_out in input_df.columns and
                    wrs2_row_col_out in input_df.columns):
                logging.debug('  Computing WRS2 tile')
                try:
                    input_df[wrs2_tile_col] = input_df[[wrs2_path_col_out,
                                                        wrs2_row_col_out]]\
                        .apply(lambda x: 'p{:03d}r{:03d}'.format(x[0], x[1]),
                               axis=1)
                except ValueError:
                    logging.info('  Possible empty DataFrame, skipping file')
                    continue

                logging.debug('  Filtering by path/row')
                input_df = input_df[input_df[wrs2_tile_col].isin(wrs2_tiles)]
                # input_df.drop(wrs2_tile_col, axis=1, inplace=True)

            # Filter by year
            if years and acq_date_col_out in input_df.columns:
                input_df = input_df[
                    input_df[acq_date_col_out].dt.year.isin(years)]

            # Skip early/late months
            if months and acq_date_col_out in input_df.columns:
                logging.debug('  Filtering by month')
                input_df = input_df[
                    input_df[acq_date_col_out].dt.month.isin(months)]

            # Subset and order columns to match metadata_csv_api.py
            input_df = input_df[[x[1] for x in use_cols] + [wrs2_tile_col]]
            if input_df.empty:
                logging.debug('  Empty dataframe, skipping chunk')
                continue

            # Write dataframe to csv
            logging.debug('  Saving')
            if append_flag:
                input_df.to_csv(temp_path, mode='a', index=False, header=False)
            else:
                input_df.to_csv(temp_path, mode='w', index=False, header=True)
                append_flag = True

        # Overwrite metadata csv with filter csv
        if os.path.isfile(temp_path):
            input_df = pd.read_csv(temp_path)
            input_df.sort_values(by=[wrs2_tile_col, acq_date_col_out],
                                 inplace=True)
            input_df.to_csv(csv_path, index=False)
            del input_df
            os.remove(temp_path)

            # shutil.move(temp_path, csv_path)


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
    if not os.path.isdir(os.path.abspath(arg)):
        parser.error('The folder {} does not exist!'.format(arg))
    else:
        return arg


def parse_int_set(nputstr=""):
    """Return list of numbers given a string of ranges

    http://thoughtsbyclayg.blogspot.com/2008/10/parsing-list-of-numbers-in-python.html
    """
    selection = set()
    invalid = set()
    # tokens are comma separated values
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
                    # we have items separated by a dash
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
        '--csv', default=os.getcwd(), metavar='FOLDER',
        type=lambda x: is_valid_folder(parser, x),
        help='Landsat bulk metadata CSV folder')
    parser.add_argument(
        '-pr', '--wrs2', default=None, nargs='+', metavar='pXXXrYYY',
        help='Space/comma separated list of Landsat WRS2 tiles to keep '
             '(i.e. --wrs2 p043r032 p043r033)')
    parser.add_argument(
        '-y', '--years', default=None, nargs='+',
        help='Space/comma separated list of years or year ranges to keep '
             '(i.e. "--years 1984 2000-2015")')
    parser.add_argument(
        '-m', '--months', default=None, nargs='+',
        help='Space/comma separated list of months or month ranges to keep '
             '(i.e. "--months 1 2 3-5")')
    parser.add_argument(
        '-l', '--landsat', default=[5, 7, 8], choices=[5, 7, 8], nargs='+',
        type=int, help='Space separated list of Landsat(s) files to filter')
    parser.add_argument(
        '--conus', default=False, action='store_true',
        help='Filter CSV files to only CONUS Landsat images/tiles')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    # Convert relative paths to absolute paths
    if args.csv and os.path.isdir(os.path.abspath(args.csv)):
        args.csv = os.path.abspath(args.csv)

    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')

    main(csv_folder=args.csv, wrs2_tiles=args.wrs2, years=args.years,
         months=args.months, landsat=args.landsat, conus_flag=args.conus)
