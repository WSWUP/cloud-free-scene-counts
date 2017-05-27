import argparse
import logging
import os
import re
import sys

import pandas as pd


def main(csv_ws, path_row_list=[], conus_flag=False, example_flag=False):
    """Filter Landsat Collection 1 bulk metadata CSV files

    The following filtering will be applied:
    Remove extreme latitute images (remove row < 100 or row > 9)
    Remove nighttime images (remove sun_elevation < 0)
    Additional filtering can be manually specified in the script

    Args:
        csv_ws (): workspace of the Landsat bulk metadata CSV files
        path_row_list (list): list of Landsat path/rows to process
            Example: ['p043r032', 'p043r033']
            Default is []
        conus_flag (bool): if True, remove all non-CONUS entries
            Remove path < 10, path > 48, row < 25 or row > 43
        example_flag (bool): if True, filter CSV files for example.
            Only keep images in path/row 43/30 for 2000 and 2015.
    """
    logging.info('\nFilter/reducing Landsat Metdata CSV files')

    # Additional/custom path/row filtering can be hardcoded
    # path_row_list = []
    path_list = []
    row_list = []
    year_list = []

    if conus_flag:
        path_list = list(range(10, 49))
        row_list = list(range(25, 44))
    if example_flag:
        path_row_list = ['p043r030']
        year_list = [2000, 2015]

    csv_file_list = [
        'LANDSAT_8_C1.csv',
        'LANDSAT_ETM_C1.csv',
        'LANDSAT_TM_C1.csv'
    ]

    # Input fields
    browse_col = 'browseAvailable'
    url_col = 'browseURL'
    scene_col = 'sceneID'
    date_col = 'acquisitionDate'
    cloud_cover_col = 'cloudCover'
    path_col = 'path'
    row_col = 'row'
    data_type_col = 'DATA_TYPE_L1'

    sensor_col = 'sensor'
    cloud_full_col = 'cloudCoverFull'
    # available_col = 'L1_AVAILABLE'

    # Generated fields
    path_row_col = 'PATH_ROW'

    # Only load the following columns from the CSV
    use_cols = [
        browse_col, url_col, scene_col, date_col, cloud_cover_col,
        path_col, row_col, data_type_col, sensor_col, cloud_full_col,
        'sceneStartTime', 'sunElevation', 'sunAzimuth']
        # 'UTM_ZONE', 'IMAGE_QUALITY', available_col, 'satelliteNumber']

    # Setup and validate the path/row lists
    path_row_list, path_list, row_list = check_path_rows(
        path_row_list, path_list, row_list)

    # Process each CSV
    for csv_name in csv_file_list:
        logging.info('{}'.format(csv_name))
        csv_path = os.path.join(csv_ws, csv_name)

        # Read in the CSV
        try:
            input_df = pd.read_csv(csv_path, parse_dates=[date_col])
        except Exception as e:
            logging.warning(
                '  CSV file could not be read or does not exist, skipping')
            logging.debug('  Exception: {}'.format(e))
            continue

        # parse_dates=[date_col]
        # logging.debug('  {}'.format(', '.join(input_df.columns.values)))
        # logging.debug(input_df.head())
        logging.debug('  Scene count: {}'.format(len(input_df)))

        # Keep target columns
        input_df = input_df[use_cols]

        # Remove high latitute rows
        input_df = input_df[input_df[row_col] < 100]
        input_df = input_df[input_df[row_col] > 9]
        logging.debug('  Scene count: {}'.format(len(input_df)))

        if path_list:
            logging.debug('  Filtering by path')
            input_df = input_df[input_df[path_col] <= max(path_list)]
            input_df = input_df[input_df[path_col] >= min(path_list)]
            input_df = input_df[input_df[path_col].isin(path_list)]
        if row_list:
            logging.debug('  Filtering by row')
            input_df = input_df[input_df[row_col] <= max(row_list)]
            input_df = input_df[input_df[row_col] >= min(row_list)]
            input_df = input_df[input_df[row_col].isin(row_list)]
        if path_row_list:
            logging.debug('  Filtering by path/row')
            try:
                input_df[path_row_col] = input_df[[path_col, row_col]].apply(
                    lambda x: 'p{:03d}r{:03d}'.format(x[0], x[1]), axis=1)
            except ValueError:
                logging.info('  Possible empty DataFrame, skipping file')
                continue
            input_df = input_df[input_df[path_row_col].isin(path_row_list)]
            input_df.drop(path_row_col, axis=1, inplace=True)

        if year_list:
            input_df = input_df[input_df[date_col].dt.year.isin(year_list)]

        input_df = input_df[input_df['sunElevation'] > 0]
        logging.debug('  Scene count: {}'.format(len(input_df)))

        # Drop fields
        # input_df.drop(browse_col, axis=1, inplace=True)

        # Save to CSV
        input_df.to_csv(csv_path, index=None)


def check_path_rows(path_row_list=[], path_list=[], row_list=[]):
    """Setup path/row lists"""
    path_row_fmt = 'p{:03d}r{:03d}'
    path_row_re = re.compile('p(?P<PATH>\d{1,3})r(?P<ROW>\d{1,3})')

    # Force path/row list to zero padded three digit numbers
    if path_row_list:
        path_row_list = sorted([
            path_row_fmt.format(int(m.group('PATH')), int(m.group('ROW')))
            for pr in path_row_list
            for m in [path_row_re.match(pr)] if m])

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

    # Convert path_row_list to path_list and row_list if not set
    # Pre-filtering on path and row separately is faster than building path_row
    # This is a pretty messy way of doing this...
    if path_row_list and not path_list:
        path_list = sorted(list(set([
            int(path_row_re.match(pr).group('PATH'))
            for pr in path_row_list if path_row_re.match(pr)])))
    if path_row_list and not row_list:
        row_list = sorted(list(set([
            int(path_row_re.match(pr).group('ROW'))
            for pr in path_row_list if path_row_re.match(pr)])))
    if path_list:
        logging.debug('  Paths: {}'.format(
            ' '.join(list(map(str, path_list)))))
    if row_list:
        logging.debug('  Rows: {}'.format(' '.join(list(map(str, row_list)))))
    if path_row_list:
        logging.debug('  Path/Rows: {}'.format(
            ' '.join(list(map(str, path_row_list)))))

    return path_row_list, path_list, row_list


def is_valid_folder(parser, arg):
    if not os.path.isdir(arg):
        parser.error('The folder {} does not exist!'.format(arg))
    else:
        return arg


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description=('Filter Landsat Collection 1 bulk metadata CSV files'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--csv', type=lambda x: is_valid_folder(parser, x),
        default=os.getcwd(), help='Landsat bulk metadata CSV folder')
    parser.add_argument(
        '-pr', '--pathrows', nargs='+', default=None, metavar='pXXXrYYY',
        help=('Space separated string of Landsat path/rows to keep '
              '(i.e. -pr p043r032 p043r033)'))
    parser.add_argument(
        '--conus', default=False, action='store_true',
        help='Filter CSV files to only CONUS Landsat images', )
    parser.add_argument(
        '--example', default=False, action='store_true',
        help='Filter CSV files for example')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    if args.csv and os.path.isfile(os.path.abspath(args.csv)):
        args.csv = os.path.abspath(args.csv)
    # else:
    #     args.csv = get_csv_path(os.getcwd())
    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')

    main(csv_ws=args.csv, path_row_list=args.pathrows,
         conus_flag=args.conus, example_flag=args.example)
