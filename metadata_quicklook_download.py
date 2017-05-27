import argparse
import datetime as dt
import logging
import os
import re
import shutil
import sys
# Python 2/3 support
try:
    import urllib.request as urlrequest
except ImportError:
    import urllib as urlrequest

import pandas as pd


def main(csv_ws, output_folder, path_row_list=[], skip_list_path=None,
         example_flag=False, overwrite_flag=False):
    """Download Landsat Collection 1 quicklook images

    Additional filtering can be manually specified in the script

    Args:
        csv_ws (str): workspace of the Landsat bulk metadata CSV files
        output_folder (str): folder path
        path_row_list (list): list of Landsat path/rows to process
            Example: ['p043r032', 'p043r033']
            Default is []
        skip_list_path (str): file path of Landsat skip list
        example_flag (bool): if True, filter CSV files for example.
            Only keep images in path/row 43/30 for 2000 and 2015.
        overwrite_flag (bool): if True, overwrite existing files

    Returns:
        None
    """
    logging.info('\nDownload Landsat Collection 1 quicklooks')
    cloud_folder_name = 'cloudy'

    start_month = 1
    end_month = 12

    # Custom year filtering can be applied here
    year_list = list(range(1984, dt.datetime.now().year + 1))
    # year_list = []

    # Additional/custom path/row filtering can be hardcoded
    # path_row_list = []
    path_list = []
    row_list = []

    # Filter CSVs for example
    if example_flag:
        path_row_list = ['p043r030']
        year_list = [2000, 2015]

    csv_file_list = [
        'LANDSAT_8_C1.csv',
        'LANDSAT_ETM_C1.csv',
        'LANDSAT_TM_C1.csv'
    ]

    path_row_fmt = 'p{:03d}r{:03d}'

    # Input fields
    browse_col = 'browseAvailable'
    url_col = 'browseURL'
    scene_col = 'sceneID'
    # sensor_col = 'sensor'
    date_col = 'acquisitionDate'
    cloud_cover_col = 'cloudCover'
    # cloud_full_col = 'cloudCoverFull'
    path_col = 'path'
    row_col = 'row'
    data_type_col = 'DATA_TYPE_L1'
    # available_col = 'L1_AVAILABLE'

    # Only load the following columns from the CSV
    input_cols = [
        browse_col, url_col, scene_col, date_col, cloud_cover_col,
        path_col, row_col, data_type_col]

    # Generated fields
    path_row_col = 'PATH_ROW'

    # All other data types will be written to cloudy folder
    data_types = ['L1TP']
    # data_types = ['L1T', 'L1GT']

    # Setup and validate the path/row lists
    path_row_list, path_list, row_list = check_path_rows(
        path_row_list, path_list, row_list)

    # Error checking
    if not os.path.isdir(csv_ws):
        logging.error('The CSV folder {0} doesn\'t exists'.format(csv_ws))
        sys.exit()
    if skip_list_path and not os.path.isfile(skip_list_path):
        logging.error('The skip list file {0} doesn\'t exists'.format(
            skip_list_path))
        sys.exit()

    # Read in skip list
    skip_list = []
    if skip_list_path:
        with open(skip_list_path, 'r') as skip_f:
            skip_list = skip_f.readlines()
            skip_list = [item.strip()[:16] for item in skip_list]


    logging.info('\nReading metadata CSV files')
    download_list = []
    for csv_name in csv_file_list:
        logging.info('{}'.format(csv_name))
        csv_path = os.path.join(csv_ws, csv_name)

        # Read in the CSV, remove extra columns
        try:
            input_df = pd.read_csv(
                csv_path, usecols=input_cols, parse_dates=[date_col])
        except Exception as e:
            logging.warning(
                '  CSV file could not be read or does not exist, skipping')
            logging.debug('  Exception: {}'.format(e))
            continue
        logging.debug('  Fields: {}'.format(', '.join(input_df.columns.values)))
        # logging.debug(input_df.head())
        logging.debug('  Initial scene count: {}'.format(len(input_df)))
        if input_df.empty:
            logging.debug('  Empty DataFrame, skipping file')
            continue

        # Filter scenes first by path and row separately
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

        # Then filter by path/row combined
        try:
            input_df[path_row_col] = input_df[[path_col, row_col]].apply(
                lambda x: path_row_fmt.format(x[0], x[1]), axis=1)
        except ValueError:
            logging.info('  Possible empty DataFrame, skipping file')
            continue
        if path_row_list:
            logging.debug('  Filtering by path/row')
            input_df = input_df[input_df[path_row_col].isin(path_row_list)]

        # Filter by year
        if year_list:
            logging.debug('  Filtering by year')
            input_df = input_df[input_df[date_col].dt.year.isin(year_list)]

        # Skip early/late months
        if start_month:
            logging.debug('  Filtering by start month')
            input_df[input_df[date_col].dt.month >= start_month]
        if end_month:
            logging.debug('  Filtering by end month')
            input_df[input_df[date_col].dt.month <= end_month]

        # Skip scenes that don't have a browse image
        if browse_col in input_df.columns.values:
            logging.debug('  Filtering images without a quicklook')
            input_df = input_df[input_df[browse_col] != 'N']

        logging.debug('  Final scene count: {}'.format(len(input_df)))
        if input_df.empty:
            logging.debug('  Empty DataFrame, skipping file')
            continue

        # Each item is a "row" of data
        for row_index, row_df in input_df.iterrows():
            # logging.debug(row_df)
            scene_id = row_df[scene_col]
            logging.debug('  {}'.format(scene_id))
            image_dt = row_df[date_col].to_pydatetime()
            # sensor = row_dict[sensor_col].upper()
            # path = int(row_df[path_col])
            # row = int(row_df[row_col])
            # path_row = row_df[path_row_col]

            # Quicklook image path
            image_folder = os.path.join(
                output_folder, row_df[path_row_col], str(image_dt.year))
            image_name = '{0}_{1}.jpg'.format(
                image_dt.strftime('%Y_%j'), scene_id[:3])
            image_path = os.path.join(image_folder, image_name)

            # "Cloudy" quicklooks are moved to a separate folder
            cloud_path = os.path.join(
                image_folder, cloud_folder_name, image_name)

            # Remove exist
            if overwrite_flag:
                if os.path.isfile(image_path):
                    # logging.debug('  {} - removing'.format(scene_id))
                    os.remove(image_path)
                if os.path.isfile(cloud_path):
                    # logging.debug('  {} - removing'.format(scene_id))
                    os.remove(cloud_path)
            # Skip if file is already classified as cloud
            elif os.path.isfile(cloud_path):
                if os.path.isfile(image_path):
                    os.remove(image_path)
                logging.debug('  {} - cloudy, skipping'.format(scene_id))
                continue

            # # Try downloading fully cloudy scenes to cloud folder
            # if int(row_dict[cloud_cover_col]) >= 9:
            #    image_path = cloud_path[:]
            #    logging.info('  {} - cloud_cover >= 9, downloading to cloudy'.format(
            #         scene_id))

            # Try downloading non-L1T quicklooks to the cloud folder
            if row_df[data_type_col].upper() not in data_types:
                if os.path.isfile(image_path):
                    os.remove(image_path)
                image_path = cloud_path[:]
                logging.info('  {} - not L1TP, downloading to cloudy'.format(
                    scene_id))

            # Try downloading scenes in skip list to cloudy folder
            if skip_list and scene_id[:16] in skip_list:
                if os.path.isfile(image_path):
                    os.remove(image_path)
                image_path = cloud_path[:]
                logging.info('  {} - skip list, downloading to cloudy'.format(
                    scene_id))

            # Check if file exists last
            if os.path.isfile(image_path):
                logging.debug('  {} - image exists, skipping'.format(scene_id))
                continue

            # Save download URL and save path
            download_list.append([image_path, row_df[url_col]])

    # Download Landsat Look Images
    logging.debug('')
    for image_path, image_url in sorted(download_list):
        logging.info('{0}'.format(image_path))
        logging.debug('  {0}'.format(image_url))
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


def download_file(file_url, file_path):
    """"""
    logging.debug('  Downloading file')
    logging.debug('  {}'.format(file_url))
    # with urlrequest.urlopen(file_url) as response notation fails in Python 2
    try:
        response = urlrequest.urlopen(file_url)
        with open(file_path, 'wb') as output_f:
            shutil.copyfileobj(response, output_f)
    except Exception as e:
        logging.info('  {}\n  Try manually checking the bulk metadata '
                     'website\n'.format(e))
    # urlrequest.urlretrieve(file_url, file_path)


# def get_csv_path(workspace):
#     import Tkinter, tkFileDialog
#     root = Tkinter.Tk()
#     ini_path = tkFileDialog.askopenfilename(
#         initialdir=workspace, parent=root, filetypes=[('XML files', '.xml')],
#         title='Select the target XML file')
#     root.destroy()
#     return ini_path


def is_valid_folder(parser, arg):
    if not os.path.isdir(arg):
        parser.error('The folder {} does not exist!'.format(arg))
    else:
        return arg


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description=('Download Landsat Collection 1 quicklook images\n' +
                     'Beware that many script parameters are hardcoded.'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--csv', type=lambda x: is_valid_folder(parser, x),
        default=os.getcwd(), help='Landsat bulk metadata CSV folder')
    parser.add_argument(
        '--output', default=os.getcwd(), help='Output folder')
    #     '--output', default=sys.path[0], help='Output folder')
    parser.add_argument(
        '-pr', '--pathrows', nargs='+', default=None, metavar='pXXXrYYY',
        help=('Space separated string of Landsat path/rows to download '
              '(i.e. -pr p043r032 p043r033)'))
    parser.add_argument(
        '--skiplist', default=None, help='Skips files in skip list')
    parser.add_argument(
        '--example', default=False, action='store_true',
        help='Filter CSV files for example')
    parser.add_argument(
        '-o', '--overwrite', default=False, action='store_true',
        help='Include existing scenes in scene download list')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    if args.csv and os.path.isfile(os.path.abspath(args.csv)):
        args.csv = os.path.abspath(args.csv)
    # else:
    #     args.csv = get_csv_path(os.getcwd())
    if os.path.isdir(os.path.abspath(args.output)):
        args.output = os.path.abspath(args.output)
    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{0}'.format('#' * 80))
    logging.info('{0:<20s} {1}'.format(
        'Run Time Stamp:', dt.datetime.now().isoformat(' ')))
    logging.info('{0:<20s} {1}'.format('Current Directory:', os.getcwd()))
    logging.info('{0:<20s} {1}'.format(
        'Script:', os.path.basename(sys.argv[0])))

    main(csv_ws=args.csv, output_folder=args.output,
         path_row_list=args.pathrows, skip_list_path=args.skiplist,
         example_flag=args.example, overwrite_flag=args.overwrite)
