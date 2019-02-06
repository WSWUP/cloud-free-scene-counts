import argparse
import gzip
import logging
import os

import requests


def main(csv_folder, years=None, overwrite_flag=False):
    """Download Landsat Collection 1 bulk metadata CSV GZ files and extract

    Parameters
    ----------
    csv_folder : str
        Folder path where the Landsat bulk metadata CSV files will be saved.
    years : list, optional
        Comma separated values or ranges of years to include.
        CSV files will only be downloaded if they include data for target years.
        The default is None which will download the Landsat 5, 7, & 8 CSV files.
        Example: ['1984', '2000-2015']
    overwrite_flag : bool, optional
        If True, overwrite existing CSV files (the default is False).

    Notes
    -----
    Main Landsat Bulk Metadata Site:
    https://landsat.usgs.gov/download-entire-collection-metadata

    Example CSV download URL:
    https://landsat.usgs.gov/landsat/metadata_service/bulk_metadata_files/
    LANDSAT_TM-1980-1989.csv

    """
    logging.info('\nDownloading Landsat Bulk Metadata CSV GZ files')

    download_url = 'https://landsat.usgs.gov/landsat/metadata_service/bulk_metadata_files'

    # The CSV GZ files are 15-20% of the full file size
    gz_file_list = [
        'LANDSAT_8_C1.csv.gz',
        'LANDSAT_ETM_C1.csv.gz',
        'LANDSAT_TM_C1.csv.gz',
    ]
    gz_years = {
        'LANDSAT_8_C1.csv.gz': set(range(2013, 2099)),
        'LANDSAT_ETM_C1.csv.gz': set(range(1999, 2099)),
        'LANDSAT_TM_C1.csv.gz': set(range(1984, 2012)),
    }

    if years is not None:
        user_years = set([x for y in years for x in parse_int_set(y)])
    else:
        user_years = set()

    for gz_name in gz_file_list:
        logging.info('{}'.format(gz_name))
        csv_name = gz_name.replace('.gz', '')
        gz_path = os.path.join(csv_folder, gz_name)
        csv_path = os.path.join(csv_folder, csv_name)
        file_url = '{}/{}'.format(download_url, gz_name)

        if user_years and not gz_years[gz_name].intersection(user_years):
            logging.info('  No data for target year(s), skipping file')
            continue

        # Don't redownload unless overwrite or both files don't exist
        if os.path.isfile(csv_path):
            if overwrite_flag:
                logging.debug('  CSV already exists, removing')
                os.remove(csv_path)
            else:
                logging.debug('  CSV already exists, skipping')
                continue
        elif os.path.isfile(gz_path):
            if overwrite_flag:
                logging.debug('  GZ already exists, removing')
                os.remove(gz_path)
            else:
                logging.debug('  GZ already exists')
                decompress_gz(gz_path, csv_path)
                continue

        # Trying to catch errors when the bulk metadata site is down
        download_file(file_url, gz_path)

        # Unpack the CSV gz file
        decompress_gz(gz_path, csv_path)


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
        logging.info('  {}\n  Try manually checking the bulk metadata '
                     'website\n'.format(e))


def decompress_gz(input_path, output_path, blocksize=1 << 14):
    """"""
    logging.debug('  Extracting CSV file')
    try:
        with gzip.open(input_path, 'rb') as input_f:
            with open(output_path, 'wb') as output_f:
                while True:
                    block = input_f.read(blocksize)
                    if block == '' or block == b'':
                        break
                    output_f.write(block)
            # with open(output_path, 'wb') as output_f:
            #     output_f.write(input_f.read())
    except Exception as e:
        logging.error('  Unhandled Exception: {}'.format(e))
        try:
            os.remove(output_path)
        except:
            pass


# def get_csv_path(workspace):
#     import Tkinter, tkFileDialog
#     root = Tkinter.Tk()
#     ini_path = tkFileDialog.askopenfilename(
#         initialdir=workspace, parent=root, filetypes=[('XML files', '.xml')],
#         title='Select the target XML file')
#     root.destroy()
#     return ini_path


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
        description='Download Landsat Collection 1 bulk metadata CSV files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--csv', default=os.getcwd(), metavar='FOLDER',
        type=lambda x: is_valid_folder(parser, x),
        help='Landsat bulk metadata CSV folder')
    parser.add_argument(
        '-y', '--years', default=None, nargs='+',
        help='Space/comma separated list of years or year ranges to keep '
             '(i.e. "--years 1984 2000-2015")')
    parser.add_argument(
        '-o', '--overwrite', default=False, action='store_true',
        help='Force overwrite of existing files')
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

    main(csv_folder=args.csv, years=args.years, overwrite_flag=args.overwrite)
