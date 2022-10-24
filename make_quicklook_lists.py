import argparse
import calendar
from collections import defaultdict
import datetime as dt
import logging
import os
import pprint
import re
import sys

import pandas as pd


def main(csv_folder, quicklook_folder, output_folder, collection=2,
         wrs2_tiles=None, years=None, skip_list_path=None,
         summary_flag=True, id_type='product',
         ):
    """Generate Landsat scene ID skip and keep lists from quicklooks

    Parameters
    ----------
    csv_folder : str
        Folder path of the Landsat metadata CSV files.
    quicklook_folder : str
        Folder path of the Landsat quicklook images.
    output_folder : str
        Folder path to save skip list.
    collection : int, str, optional
        Landsat Collection number (the default is 2).
    wrs2_tiles : list, optional
        Landsat WRS2 tiles (path/rows) to include in output files.
        The default is None which will include images for all tiles.
        Example: ['p043r032', 'p043r033']
    years : list, optional
        Comma separated values or ranges of years to include.
        The default is None which will keep entries for all years.
        Example: ['1984', '2000-2015']
    skip_list_path : str, optional
        File path of an existing Landsat skip list (the default is None).
    summary_flag : bool, optional
        Generate clear scene counts summary file (the default is True).
    id_type : str, optional
        Landsat ID type (the default is 'product').

    """
    logging.info('\nMake skip & keep lists from quicklook images')

    output_keep_name = 'clear_scenes.txt'
    output_skip_name = 'cloudy_scenes.txt'
    summary_name = 'clear_scene_counts.txt'

    output_keep_path = os.path.join(output_folder, output_keep_name)
    output_skip_path = os.path.join(output_folder, output_skip_name)
    summary_path = os.path.join(output_folder, summary_name)

    cloud_folder = 'cloudy'

    if years is not None:
        year_list = sorted([x for y in years for x in parse_int_set(y)])
    else:
        year_list = []
    # year_list = list(range(1984, dt.datetime.now().year + 1))

    if wrs2_tiles is not None:
        wrs2_tile_list = sorted([
            x.strip() for w in wrs2_tiles for x in w.split(',') if x.strip()])
    else:
        wrs2_tile_list = []

    path_list = []
    row_list = []

    if collection in [2, '2', 'c02', 'C02' 'c2', 'C2']:
        csv_file_list = [
            'LANDSAT_OT_C2_L1.csv',
            'LANDSAT_ETM_C2_L1.csv',
            'LANDSAT_TM_C2_L1.csv',
        ]
        csv_years = {
            'LANDSAT_OT_C2_L1.csv': set(range(2013, 2099)),
            'LANDSAT_ETM_C2_L1.csv': set(range(1999, 2099)),
            'LANDSAT_TM_C2_L1.csv': set(range(1984, 2012)),
        }
    elif collection in [1, '1', 'c01', 'C01' 'c1', 'C1']:
        csv_file_list = [
            'LANDSAT_8_C1.csv',
            'LANDSAT_ETM_C1.csv',
            'LANDSAT_TM_C1.csv',
        ]
        csv_years = {
            'LANDSAT_8_C1.csv': set(range(2013, 2099)),
            'LANDSAT_ETM_C1.csv': set(range(1999, 2099)),
            'LANDSAT_TM_C1.csv': set(range(1984, 2012)),
        }
    else:
        raise ValueError(f'unsupported collection: {collection}')

    product_id_col = 'LANDSAT_PRODUCT_ID'
    wrs2_path_col = 'WRS_PATH'
    wrs2_row_col = 'WRS_ROW'
    wrs2_tile_col = 'WRS2_TILE'

    quicklook_re = re.compile(
        '(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})_'
        '(?P<doy>\d{3})_(?P<landsat>\w{4}).jpg')
    wrs2_tile_fmt = 'p{:03d}r{:03d}'
    # wrs2_tile_re = re.compile('p(?P<PATH>\d{1,3})r(?P<ROW>\d{1,3})')

    if id_type.lower() == 'short':
        logging.info('\nUsing shortened Landsat ID')

    # Setup and validate the path/row lists
    wrs2_tile_list, path_list, row_list = check_wrs2_tiles(
        wrs2_tile_list, path_list, row_list)

    # Error checking
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    if skip_list_path and not os.path.isfile(skip_list_path):
        logging.error('The skip list file {} doesn\'t exists'.format(
            skip_list_path))
        sys.exit()

    # Read in skip list
    input_skip_list = []
    if skip_list_path:
        with open(skip_list_path, 'r') as skip_f:
            input_skip_list = skip_f.readlines()
            input_skip_list = [item.strip()[:16] for item in input_skip_list]

    # Read in metadata CSV files
    logging.info('\nReading metadata CSV files')
    quicklook_ids = defaultdict(dict)
    for csv_name in csv_file_list:
        csv_path = os.path.join(csv_folder, csv_name)
        logging.info('{}'.format(csv_name))

        if year_list and not csv_years[csv_name].intersection(set(year_list)):
            logging.info('  No data for target year(s), skipping file')
            continue
        elif not os.path.isfile(csv_path):
            logging.info('  The CSV file does not exist, skipping')

        try:
            input_df = pd.read_csv(csv_path)
        except Exception as e:
            logging.warning('  The CSV file could not be read, skipping')
            logging.debug('  Exception: {}'.format(e))
            continue
        if input_df.empty:
            logging.debug('  Empty DataFrame, skipping file')
            continue

        # Warn the user if the WRS path and row columns don't exist
        if (wrs2_path_col not in input_df.columns.values and
                'path' in input_df.columns.values):
            logging.error(
                '\nERROR: The {} field doesn\'t exist in the CSV'
                '\n  You may be attempting to run the script on the unfiltered '
                'metadata CSV file\n  Exiting script'.format(wrs2_path_col))
            return False
        elif (wrs2_row_col not in input_df.columns.values and
                'row' in input_df.columns.values):
            logging.error(
                '\nERROR: The {} field doesn\'t exist in the CSV'
                '\n  You may be attempting to run the script on the unfiltered '
                'metadata CSV file\n  Exiting script'.format(wrs2_path_col))
            return False

        # Compute WRS2 tile column if it doesn't exist
        if (wrs2_tile_col not in input_df.columns.values and
                wrs2_path_col in input_df.columns.values and
                wrs2_row_col in input_df.columns.values):
            logging.debug('  {} field doesn\'t exist, adding'.format(
                wrs2_tile_col))
            input_df[wrs2_tile_col] = input_df[[wrs2_path_col, wrs2_row_col]] \
                .apply(lambda x: 'p{:03d}r{:03d}'.format(x[0], x[1]),
                       axis=1)

        # Compute quicklook image name from PRODUCT_ID
        input_df['QUICKLOOK'] = input_df[[product_id_col]].apply(
            lambda x: '{}_{}.jpg'.format(
                dt.datetime.strptime(x[0][17:25], '%Y%m%d').strftime('%Y%m%d_%j'),
                x[0][:4]),
            axis=1)
        # print(input_df.head())
        input_df.set_index([wrs2_tile_col, 'QUICKLOOK'],
                           drop=True, inplace=True)

        if id_type.lower() == 'short':
            input_df['temp_id'] = input_df[[product_id_col]].apply(
                lambda x: '{}_{}_{}'.format(x[0][0:4], x[0][10:16], x[0][17:25]),
                axis=1)
            update_dict = input_df['temp_id'].to_dict()
        else:
            update_dict = input_df[product_id_col].to_dict()

        for [wrs2_tile, image_id], product_id in update_dict.items():
            quicklook_ids[wrs2_tile][image_id] = product_id

    logging.debug('\nQuicklook PRODUCT_ID lookup:')
    logging.debug(pprint.pformat(quicklook_ids))
    logging.info('')
    # input('ENTER')

    output_keep_list = []
    output_skip_list = []
    for root, dirs, files in os.walk(quicklook_folder):
        # This should only match path/row folders directly in quicklook folder
        # DEADBEEF: Need better cross platform solution
        if os.name == 'nt':
            pr_match = re.search(
                '{}\\\p(\d{{3}})r(\d{{3}})\\\(\d{{4}})(\\\{})?'.format(
                    os.path.basename(quicklook_folder), cloud_folder),
                root)
        elif os.name == 'posix':
            pr_match = re.search(
                '{}/p(\d{{3}})r(\d{{3}})/(\d{{4}})(/{})?'.format(
                    os.path.basename(quicklook_folder), cloud_folder),
                root)
        if not pr_match:
            continue

        path, row, year = list(map(int, pr_match.groups()[:3]))
        wrs2_tile = wrs2_tile_fmt.format(path, row)

        # Skip scenes first by path/row
        if wrs2_tile_list and wrs2_tile not in wrs2_tile_list:
            logging.info('{} - path/row, skipping'.format(root))
            continue
        elif path_list and path not in path_list:
            logging.info('{} - path, skipping'.format(root))
            continue
        elif row_list and row not in row_list:
            logging.info('{} - row, skipping'.format(root))
            continue
        elif year_list and year not in year_list:
            logging.info('{} - year, skipping'.format(root))
            continue
        else:
            logging.info('{}'.format(root))

        for name in files:
            try:
                y, m, d, doy, landsat = quicklook_re.match(name).groups()
            except Exception as e:
                logging.debug('  {} - quicklook_re exception, skipping'.format(
                    name))
                continue

            # Look up PRODUCT_ID/SCENE_ID using metadata CSV data
            try:
                product_id = quicklook_ids[wrs2_tile][name]
            except:
                logging.debug('  {} - quicklook_id exception, skipping'.format(
                    quicklook_ids))
                continue
            if input_skip_list and product_id in input_skip_list:
                logging.debug('  {} - skip list, skipping'.format(
                    product_id))
                continue

            if pr_match.groups()[3]:
                logging.debug('  {} - skip'.format(product_id))
                output_skip_list.append([year, doy, product_id])
            else:
                logging.debug('  {} - keep'.format(product_id))
                output_keep_list.append([year, doy, product_id])

    if output_keep_list:
        with open(output_keep_path, 'w') as output_f:
            for year, doy, product_id in sorted(output_keep_list):
                output_f.write('{}\n'.format(product_id))
    if output_skip_list:
        with open(output_skip_path, 'w') as output_f:
            for year, doy, product_id in sorted(output_skip_list):
                output_f.write('{}\n'.format(product_id))

    if summary_flag and output_keep_list:
        # This would probably be easier to do with pandas
        counts = defaultdict(dict)

        for year, doy, product_id in sorted(output_keep_list):
            if id_type.lower() == 'short':
                wrs2_tile = 'p{}r{}'.format(product_id[5:8], product_id[8:11])
            else:
                wrs2_tile = 'p{}r{}'.format(product_id[10:13], product_id[13:16])
            output_dt = dt.datetime.strptime(
                '{}_{:03d}'.format(year, int(doy)), '%Y_%j')
            try:
                counts[wrs2_tile][year][output_dt.month] += 1
            except Exception as e:
                counts[wrs2_tile][year] = {m: 0 for m in range(1, 13)}
                counts[wrs2_tile][year][output_dt.month] = 1

        with open(summary_path, 'w') as output_f:
            output_f.write('{},{},{}\n'.format(
                'WRS2_TILE', 'YEAR', ','.join([
                    calendar.month_abbr[m].upper() for m in range(1, 13)])))
            for wrs2_tile, year_counts in sorted(counts.items()):
                for year, month_counts in sorted(year_counts.items()):
                    output_f.write('{},{},{}\n'.format(
                        wrs2_tile, year, ','.join([
                            str(c) for m, c in sorted(month_counts.items())])))


def check_wrs2_tiles(wrs2_tile_list=[], path_list=[], row_list=[]):
    """Setup path/row lists"""
    wrs2_tile_fmt = 'p{:03d}r{:03d}'
    wrs2_tile_re = re.compile('p(?P<PATH>\d{1,3})r(?P<ROW>\d{1,3})')

    # Force path/row list to zero padded three digit numbers
    if wrs2_tile_list:
        wrs2_tile_list = sorted([
            wrs2_tile_fmt.format(int(m.group('PATH')), int(m.group('ROW')))
            for wrs2_tile in wrs2_tile_list
            for m in [wrs2_tile_re.match(wrs2_tile)] if m])

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
            int(wrs2_tile_re.match(wrs2_tile).group('PATH'))
            for wrs2_tile in wrs2_tile_list
            if wrs2_tile_re.match(wrs2_tile)])))
    if wrs2_tile_list and not row_list:
        row_list = sorted(list(set([
            int(wrs2_tile_re.match(wrs2_tile).group('ROW'))
            for wrs2_tile in wrs2_tile_list
            if wrs2_tile_re.match(wrs2_tile)])))
    if path_list:
        logging.debug('  Paths: {}'.format(
            ' '.join(list(map(str, path_list)))))
    if row_list:
        logging.debug('  Rows: {}'.format(' '.join(list(map(str, row_list)))))
    if wrs2_tile_list:
        logging.debug('  WRS2 Tiles: {}'.format(
            ' '.join(list(map(str, wrs2_tile_list)))))

    return wrs2_tile_list, path_list, row_list


def is_valid_file(parser, arg):
    if not os.path.isfile(os.path.abspath(arg)):
        parser.error('The file {} does not exist!'.format(arg))
    else:
        return arg


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
        description='Make keep and skip scene lists from quicklook images',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--csv', default=os.getcwd(), metavar='FOLDER',
        type=lambda x: is_valid_folder(parser, x),
        help='Landsat metadata CSV folder')
    parser.add_argument(
        '--quicklook', default=os.getcwd(), metavar='FOLDER',
        type=lambda x: is_valid_folder(parser, x),
        help='Landsat quicklook image folder')
    parser.add_argument(
        '--output', default=os.getcwd(), metavar='FOLDER',
        help='Output folder')
    parser.add_argument(
        '-coll', '--collection', default='2', choices=['1', '2'],
        help='Landsat Collection number')
    parser.add_argument(
        '-pr', '--wrs2', default=None, nargs='+', metavar='pXXXrYYY',
        help='Space/comma separated list of Landsat WRS2 tiles to keep '
             '(i.e. --wrs2 p043r032 p043r033)')
    parser.add_argument(
        '-y', '--years', default=None, nargs='+',
        help='Space/comma separated list of years or year ranges to keep '
             '(i.e. "--years 1984 2000-2015")')
    parser.add_argument(
        '--skiplist', default=None, metavar='FILE',
        type=lambda x: is_valid_file(parser, x),
        help='File path of scene IDs that should be written directly to the '
             'cloudy_scenes.txt file')
    parser.add_argument(
        '-id', '--id_type', default='product', choices=['product', 'short'],
        help='Landsat ID type')
    parser.add_argument(
        '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    # Convert relative paths to absolute paths
    if args.quicklook and os.path.isfile(os.path.abspath(args.quicklook)):
        args.quicklook = os.path.abspath(args.quicklook)
    if args.output and os.path.isdir(os.path.abspath(args.output)):
        args.output = os.path.abspath(args.output)
    if args.skiplist and os.path.isfile(os.path.abspath(args.skiplist)):
        args.skiplist = os.path.abspath(args.skiplist)

    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')

    main(
        csv_folder=args.csv,
        quicklook_folder=args.quicklook,
        output_folder=args.output,
        collection=args.collection,
        wrs2_tiles=args.wrs2,
        years=args.years,
        skip_list_path=args.skiplist,
        id_type=args.id_type,
    )
