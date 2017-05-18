import argparse
import logging
import os
import shutil
# Python 2/3 support
try:
    import urllib.request as urlrequest
except ImportError:
    import urllib as urlrequest


def main(csv_ws, overwrite_flag=False):
    """Download Landsat bulk metadata CSV files

    Main Landsat Bulk Metadata Site
    https://landsat.usgs.gov/download-entire-collection-metadata

    Example CSV download URL
    https://landsat.usgs.gov/landsat/metadata_service/bulk_metadata_files/LANDSAT_TM-1980-1989.csv

    Args:
        csv_ws (str): workspace of the Landsat bulk metadata CSV files
        overwrite_flag (bool): if True, overwrite existing CSV files
    """
    logging.info('\nDownloading Landsat Bulk Metadata CSV files')

    download_url = 'https://landsat.usgs.gov/landsat/metadata_service/bulk_metadata_files'

    csv_list = [
        'LANDSAT_8.csv',
        'LANDSAT_ETM.csv',
        'LANDSAT_ETM_SLC_OFF.csv',
        'LANDSAT_TM-1980-1989.csv',
        'LANDSAT_TM-1990-1999.csv',
        'LANDSAT_TM-2000-2009.csv',
        'LANDSAT_TM-2010-2012.csv'
    ]
    for csv_name in csv_list:
        logging.info('{}'.format(csv_name))
        csv_path = os.path.join(csv_ws, csv_name)
        if os.path.isfile(csv_path):
            if overwrite_flag:
                logging.debug('  CSV already exists, removing')
                os.remove(csv_path)
            else:
                logging.debug('  CSV already exists, skipping')
                continue
        csv_url = '{}/{}'.format(download_url, csv_name)
        logging.debug('  Downloading CSV')
        logging.debug('  {}'.format(csv_url))

        # Trying to catch errors when the bulk metadata site is down
        try:
            with urlrequest.urlopen(csv_url) as response:
                logging.debug('  Response')
                with open(csv_path, 'wb') as out_file:
                    logging.debug('  Open')
                    shutil.copyfileobj(response, out_file)
        except Exception as e:
            logging.info('  {}\n  Try manually checking the bulk metadata '
                         'site\n'.format(e))
            try:
                os.remove(csv_path)
            except:
                pass
        # urlrequest.urlretrieve(csv_url, csv_path)


def is_valid_folder(parser, arg):
    if not os.path.isdir(arg):
        parser.error('The folder {} does not exist!'.format(arg))
    else:
        return arg


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description=('Download Landsat Bulk Metadata CSV files'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--csv', type=lambda x: is_valid_folder(parser, x),
        default=os.getcwd(), help='Landsat bulk metadata CSV folder')
    parser.add_argument(
        '-o', '--overwrite', default=False, action='store_true',
        help='Force overwrite of existing files')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()

    if args.csv and os.path.isfile(os.path.abspath(args.csv)):
        args.csv = os.path.abspath(args.csv)
    # else:
    #     args.csv = get_csv_path(os.getcwd())
    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')

    main(csv_ws=args.csv, overwrite_flag=args.overwrite)
