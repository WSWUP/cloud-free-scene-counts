import argparse
import logging
import os
import re
import sys

import pandas as pd
import requests


def main(csv_folder, output_folder, collection=2,
         wrs2_tiles=None, years=None, months=None,
         skip_list_path=None, overwrite_flag=False, id_type='product'):
    """Download Landsat quicklook images

    Parameters
    ----------
    csv_folder : str
        Folder path of the Landsat metadata CSV files.
    output_folder : str
        Folder path where the quicklook images will be saved.
    collection : int, str, optional
        Landsat Collection number (the default is 2).
    wrs2_tiles : list, optional
        Landsat WRS2 tiles (path/rows) to download images for.
        The default is None which will download images for all tiles.
        Example: ['p043r032', 'p043r033']
    years : list, optional
        Comma separated values or ranges of years to download.
        The default is None which will download images for all years.
        Example: ['1984', '2000-2015']
    months : list, optional
        Comma separated values or ranges of months to download.
        The default is None which will download images for all months.
        Example: ['1', '2', '3-5']
    skip_list_path : str, optional
        File path of an existing Landsat skip list (the default is None).
    overwrite_flag : bool, optional
        If True, overwrite existing files (the default is False).
    id_type : str, optional
        Landsat ID type (the default is 'product').

    Returns
    -------
    None

    Notes
    -----
    Additional filtering can be manually specified in the scripts

    """
    logging.info('\nDownload Landsat Collection 1 Quicklooks')
    cloud_folder_name = 'cloudy'

    if wrs2_tiles is not None:
        wrs2_tile_list = sorted([
            x.strip() for w in wrs2_tiles for x in w.split(',') if x.strip()])
    else:
        wrs2_tile_list = []

    if years is not None:
        year_list = sorted([x for y in years for x in parse_int_set(y)])
    else:
        year_list = []

    if months is not None:
        month_list = sorted([x for m in months for x in parse_int_set(m)])
    else:
        month_list = []

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

    wrs2_tile_fmt = 'p{:03d}r{:03d}'

    # Input fields
    acq_date_col = 'ACQUISITION_DATE'
    browse_url_col = 'BROWSE_REFLECTIVE_PATH'
    col_category_col = 'COLLECTION_CATEGORY'
    col_number_col = 'COLLECTION_NUMBER'
    product_id_col = 'LANDSAT_PRODUCT_ID'
    scene_id_col = 'LANDSAT_SCENE_ID'
    data_type_col = 'DATA_TYPE_L1'
    wrs2_path_col = 'WRS_PATH'
    wrs2_row_col = 'WRS_ROW'
    wrs2_tile_col = 'WRS2_TILE'

    # Only load the following columns from the CSV
    input_cols = [
        acq_date_col, browse_url_col, col_category_col, col_number_col,
        data_type_col, product_id_col, scene_id_col, wrs2_path_col,
        wrs2_row_col, wrs2_tile_col]

    # All other data types and categories will be written to cloudy folder
    # DEADBEEF Should OLI_L1TP (no TIRS) be included in clear images?
    data_types = ['OLI_TIRS_L1TP', 'OLI_L1TP', 'ETM_L1TP', 'TM_L1TP', 'L1TP']
    # data_types = ['OLI_TIRS_L1TP', 'ETM_L1TP', 'TM_L1TP', 'L1TP']

    # "A1" isn't documented but appear to be good Landsat 7 L1TP images
    categories = ['T1', 'RT', 'A1']

    if id_type.lower() == 'short':
        logging.info('\nUsing shortened Landsat ID')

    # Setup and validate the path/row lists
    wrs2_tile_list, path_list, row_list = check_wrs2_tiles(
        wrs2_tile_list, path_list, row_list)

    # Error checking
    if not os.path.isdir(csv_folder):
        logging.error('The CSV folder {} doesn\'t exists'.format(csv_folder))
        sys.exit()
    if skip_list_path and not os.path.isfile(skip_list_path):
        logging.error('The skip list file {} doesn\'t exists'.format(
            skip_list_path))
        sys.exit()

    # Read in skip list
    skip_list = []
    if skip_list_path:
        with open(skip_list_path, 'r') as skip_f:
            skip_list = skip_f.readlines()
            skip_list = [item.strip() for item in skip_list]

    logging.info('\nReading metadata CSV files')
    download_list = []
    for csv_name in csv_file_list:
        logging.info('{}'.format(csv_name))
        csv_path = os.path.join(csv_folder, csv_name)

        if year_list and not csv_years[csv_name].intersection(set(year_list)):
            logging.info('  No data for target year(s), skipping file')
            continue
        elif not os.path.isfile(csv_path):
            logging.info('  The CSV file does not exist, skipping')

        try:
            input_df = pd.read_csv(
                csv_path, usecols=input_cols, parse_dates=[acq_date_col])
        except Exception as e:
            logging.warning('  The CSV file could not be read, skipping')
            logging.debug('  Exception: {}'.format(e))
            continue
        if input_df.empty:
            logging.debug('  Empty DataFrame, skipping file')
            continue
        # logging.debug(input_df.head())
        logging.debug('  Fields: {}'.format(', '.join(input_df.columns.values)))
        logging.debug('  Initial scene count: {}'.format(len(input_df)))

        # Filter scenes first by path and row separately
        if path_list:
            logging.debug('  Filtering by path')
            input_df = input_df[input_df[wrs2_path_col] <= max(path_list)]
            input_df = input_df[input_df[wrs2_path_col] >= min(path_list)]
            input_df = input_df[input_df[wrs2_path_col].isin(path_list)]
        if row_list:
            logging.debug('  Filtering by row')
            input_df = input_df[input_df[wrs2_row_col] <= max(row_list)]
            input_df = input_df[input_df[wrs2_row_col] >= min(row_list)]
            input_df = input_df[input_df[wrs2_row_col].isin(row_list)]

        # Then filter by path/row combined
        # DEADBEEF - WRS2_TILE should already be in the file
        try:
            input_df[wrs2_tile_col] = input_df[[wrs2_path_col, wrs2_row_col]] \
                .apply(lambda x: wrs2_tile_fmt.format(x[0], x[1]), axis=1)
        except ValueError:
            logging.info('  Possible empty DataFrame, skipping file')
            continue
        if wrs2_tile_list:
            logging.debug('  Filtering by path/row')
            input_df = input_df[input_df[wrs2_tile_col].isin(wrs2_tile_list)]

        # Filter by year
        if year_list:
            logging.debug('  Filtering by year')
            input_df = input_df[input_df[acq_date_col].dt.year.isin(year_list)]

        # Skip early/late months
        if month_list:
            logging.debug('  Filtering by month')
            input_df = input_df[
                input_df[acq_date_col].dt.month.isin(month_list)]
        # if start_month:
        #     logging.debug('  Filtering by start month')
        #     input_df = input_df[input_df[date_col].dt.month >= start_month]
        # if end_month:
        #     logging.debug('  Filtering by end month')
        #     input_df = input_df[input_df[date_col].dt.month <= end_month]

        # # Skip scenes that don't have a browse image
        # if browse_url_col in input_df.columns.values:
        #     logging.debug('  Filtering images without a quicklook')
        #     input_df = input_df[input_df[browse_url_col] != 'N']

        logging.debug('  Final scene count: {}'.format(len(input_df)))
        if input_df.empty:
            logging.debug('  Empty DataFrame, skipping file')
            continue

        # Each item is a "row" of data
        for row_index, row_df in input_df.iterrows():
            # logging.debug(row_df)
            if id_type.lower() == 'short':
                product_id = row_df[product_id_col].split('_')
                product_id = '_'.join([
                    product_id[0], product_id[2], product_id[3]])
            else:
                product_id = str(row_df[product_id_col])
            # logging.debug('  {}'.format(product_id))
            image_dt = row_df[acq_date_col].to_pydatetime()

            # Quicklook image path
            image_folder = os.path.join(
                output_folder, row_df[wrs2_tile_col], str(image_dt.year))
            image_name = '{}_{}.jpg'.format(
                image_dt.strftime('%Y%m%d_%j'), product_id[:4].upper())
            image_path = os.path.join(image_folder, image_name)

            # "Cloudy" quicklooks are moved to a separate folder
            cloud_path = os.path.join(
                image_folder, cloud_folder_name, image_name)

            # Remove exist
            if overwrite_flag:
                if os.path.isfile(image_path):
                    # logging.debug('  {} - removing'.format(product_id))
                    os.remove(image_path)
                if os.path.isfile(cloud_path):
                    # logging.debug('  {} - removing'.format(product_id))
                    os.remove(cloud_path)
            # Skip if file is already classified as cloud
            elif os.path.isfile(cloud_path):
                if os.path.isfile(image_path):
                    os.remove(image_path)
                logging.debug(
                    '  {} - in cloudy folder, skipping'.format(product_id))
                continue

            # # Download fully cloudy scenes to cloud folder
            # if int(row_dict[cloud_cover_col]) >= 90:
            #    image_path = cloud_path[:]
            #    logging.info('  {} - cloud_cover >= 90, downloading to cloudy'.format(
            #         product_id))

            # Download non-L1T quicklooks to the cloud folder
            if (row_df[data_type_col].upper() not in data_types or
                    row_df[col_category_col].upper() not in categories):
                if os.path.isfile(image_path):
                    os.remove(image_path)
                image_path = cloud_path[:]
                logging.info('  {} - not T1/L1TP, downloading to cloudy'.format(
                    product_id))

            # Download scenes in skip list to cloudy folder
            if skip_list and product_id in skip_list:
                if os.path.isfile(image_path):
                    os.remove(image_path)
                image_path = cloud_path[:]
                logging.info('  {} - in skip list, downloading to cloudy'.format(
                    product_id))

            # Check if file exists last
            if os.path.isfile(image_path):
                logging.debug(
                    '  {} - image exists, skipping'.format(product_id))
                continue

            # Save download URL and save path
            logging.debug('  {}'.format(product_id))
            download_list.append([image_path, row_df[browse_url_col]])

    # Download Landsat Look Images
    logging.debug('')
    for image_path, image_url in sorted(download_list):
        logging.info('{}'.format(image_path))
        logging.debug('  {}'.format(image_url))
        image_folder = os.path.dirname(image_path)
        if not os.path.isdir(image_folder):
            os.makedirs(image_folder)

        # Make cloudy image folder also
        cloud_folder = os.path.join(image_folder, cloud_folder_name)
        if (os.path.basename(image_folder) != cloud_folder_name and
                not os.path.isdir(cloud_folder)):
            os.makedirs(cloud_folder)

        # Trying to catch errors when the bulk metadata site is down
        download_file(image_url, image_path)


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


def download_file(file_url, file_path):
    """"""
    logging.debug('  Downloading file')
    logging.debug('  {}'.format(file_url))
    try:
        r = requests.get(file_url)
        with open(file_path, 'wb') as output_f:
            for chunk in r.iter_content(chunk_size=128):
                output_f.write(chunk)
    except Exception as e:
        logging.info('  {}\n  Try manually checking the quicklook '
                     'URL\n'.format(e))
    # urlrequest.urlretrieve(file_url, file_path)


# def get_csv_path(workspace):
#     import Tkinter, tkFileDialog
#     root = Tkinter.Tk()
#     ini_path = tkFileDialog.askopenfilename(
#         initialdir=workspace, parent=root, filetypes=[('XML files', '.xml')],
#         title='Select the target XML file')
#     root.destroy()
#     return ini_path


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
        description='Download Landsat Collection 1 quicklook images',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--csv', default=os.getcwd(), metavar='FOLDER',
        type=lambda x: is_valid_folder(parser, x),
        help='Landsat metadata CSV folder')
    parser.add_argument(
        '--output', default=os.getcwd(), metavar='FOLDER',
        type=lambda x: is_valid_folder(parser, x),
        help='Output folder')
    parser.add_argument(
        '-coll', '--collection', default='2', choices=['1', '2'],
        help='Landsat Collection number')
    parser.add_argument(
        '-pr', '--wrs2', default=None, nargs='+', metavar='pXXXrYYY',
        help='Space/comma separated list of Landsat WRS2 tiles to download '
             '(i.e. --wrs2 p043r032 p043r033)')
    parser.add_argument(
        '-y', '--years', default=None, nargs='+',
        help='Space/comma separated list of years or year_ranges to download '
             '(i.e. "--years 1984 2000-2015")')
    parser.add_argument(
        '-m', '--months', default=None, nargs='+',
        help='Space/comma separated list of months or month ranges to download '
             '(i.e. "--months 1 2 3-5")')
    parser.add_argument(
        '--skiplist', default=None, metavar='FILE',
        type=lambda x: is_valid_file(parser, x),
        help='File path of scene IDs that should be downloaded directly to '
             'the "cloudy" scenes folder')
    parser.add_argument(
        '-id', '--id_type', default='product', choices=['product', 'short'],
        help='Landsat ID type')
    parser.add_argument(
        '--overwrite', default=False, action='store_true',
        help='Overwite existing quicklooks')
    parser.add_argument(
        '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    # Convert relative paths to absolute paths
    if args.csv and os.path.isdir(os.path.abspath(args.csv)):
        args.csv = os.path.abspath(args.csv)
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
        output_folder=args.output,
        collection=args.collection,
        wrs2_tiles=args.wrs2,
        years=args.years,
        months=args.months,
        skip_list_path=args.skiplist,
        id_type=args.id_type,
        overwrite_flag=args.overwrite
    )
