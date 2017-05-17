import argparse
import logging
import os
import urllib
# import urllib2


def main(download_ws=os.getcwd(), overwrite_flag=False):
    """Download Landsat bulk metadata CSV files"""
    logging.info('\nDownloading Landsat Bulk Metadata CSV files')

    download_url = 'https://landsat.usgs.gov/landsat/metadata_service/bulk_metadata_files/'

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
        csv_path = os.path.join(download_ws, csv_name)
        if overwrite_flag or not os.path.isfile(csv_path):
            csv_url = '{}/{}'.format(download_url, csv_name)
            urllib.urlretrieve(csv_url, csv_path)


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description=('Download Landsat Bulk Metadata CSV files'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-o', '--overwrite', default=False, action='store_true',
        help='Force overwrite of existing files')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')

    main(overwrite_flag=args.overwrite)
