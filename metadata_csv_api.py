import argparse
import json
import logging
import os
import pprint
import requests
# import shutil

import pandas as pd

API_URL = 'https://earthexplorer.usgs.gov/inventory/json/v/1.4.0/'


def main(username, password, wrs2_tile_list, years, csv_ws=os.getcwd(),
         months=''):
    """Download filtered Landsat Collection 1 metadata CSV files

    Parameters
    ----------
    username : str
        USGS Earth Explorer username.
    password : str
        USGS Earth Explorer password.
    wrs2_tile_list : list
        Landsat path/rows to process. Example: ['p043r032', 'p043r033']
    years : str
        Comma separated values or ranges of years to download.
        Example: '1984,2000-2015'
    csv_ws : str, optional
        Output workspace (the default is the current working directory).
    months : str, optional
        Comma separated values or ranges of months to keep.
        Example: '1, 2, 3-5'.
        Default is '' which will keep images for all months.

    Notes
    -----
    The following filtering will be applied:
    Remove extreme latitude images (remove row < 100 or row > 9)

    """
    logging.info('\nDownloading Filtered Landsat Metadata CSV files')

    # Search result fields (renamed to better match XML metadata field names)
    acq_date_col = 'ACQUISITION_DATE'
    browse_url_col = 'BROWSE_REFLECTIVE_PATH'
    col_category_col = 'COLLECTION_CATEGORY'
    col_number_col = 'COLLECTION_NUMBER'
    product_id_col = 'LANDSAT_PRODUCT_ID'
    scene_id_col = 'LANDSAT_SCENE_ID'
    data_type_col = 'DATA_TYPE_L1'
    wrs2_path_col = 'WRS_PATH'
    wrs2_row_col = 'WRS_ROW'

    # Derived field
    wrs2_tile_col = 'WRS2_TILE'

    # Fields missing from API search results (could get from metadata)
    # sensor_col = 'SENSOR'
    # cloud_col = 'CLOUD_COVER_LAND'

    # Keep the following search result fields (but rename)
    result_fields = ['entityId', 'displayId', 'acquisitionDate', 'browseUrl']

    # Output file names (to match bulk metadata file names)
    csv_names = {
        'LANDSAT_8_C1': 'LANDSAT_8_C1.csv',
        'LANDSAT_ETM_C1': 'LANDSAT_ETM_C1.csv',
        'LANDSAT_TM_C1': 'LANDSAT_TM_C1.csv',
    }

    # Limit year ranges
    landsat_years = {
        'LANDSAT_8_C1': range(2013, 2018 + 1),
        'LANDSAT_ETM_C1': range(1999, 2018 + 1),
        'LANDSAT_TM_C1': range(1984, 2011 + 1),
    }

    # Convert/parse the input year and month strings to lists
    year_list = sorted(list(parse_int_set(years)))
    month_list = sorted(list(parse_int_set(months)))

    # Login to get API key
    api_key = api_login(username, password)

    for landsat, csv_file in csv_names.items():
        logging.info('\n{}'.format(landsat))

        output_path = os.path.join(csv_ws, csv_file)
        logging.debug('  CSV: {}'.format(csv_file))

        # Filter year list by Landsat type
        landsat_year_list = sorted(list(
            set(year_list) & set(landsat_years[landsat])))
        if not landsat_year_list:
            logging.debug('  Skipping year')
            continue
        logging.debug('  Years: {}'.format(landsat_year_list))

        # Field IDs
        fields = get_field_ids(landsat, api_key)

        output_list = []

        for year in landsat_year_list:
            logging.info('\nYear: {}'.format(year))

            for wrs2_tile in wrs2_tile_list:
                logging.info('  WRS2 tile: {}'.format(wrs2_tile))

                path = str(int(wrs2_tile[1:4]))
                row = str(int(wrs2_tile[5:8]))
                logging.debug('  WRS2 Path: {}'.format(path))
                logging.debug('  WRS2 Row:  {}'.format(row))

                payload = {
                    "datasetName": landsat,
                    "temporalFilter": {
                        "startDate": "{}-01-01".format(year),
                        "endDate": "{}-12-31".format(year)
                    },
                    "additionalCriteria": {
                        "filterType": "and",
                        "childFilters": [
                            {"filterType": "value",
                             "fieldId": fields['WRS Path'],
                             "value": path,
                             "operand": "=",
                            },
                            {"filterType": "value",
                             "fieldId": fields['WRS Row'],
                             "value": row,
                             "operand": "="
                            }
                        ]
                    },
                    "maxResults": 100,
                    "startingNumber": 1,
                    "sortOrder": "ASC",
                    "apiKey": api_key
                }
                if months:
                    payload["months"] = month_list

                payload = {'jsonRequest': json.dumps(payload)}
                logging.debug(payload)

                r = requests.post(API_URL + 'search', data=payload)
                data = r.json()['data']
                if not data['results']:
                    logging.info('  No images, skipping')
                    continue
                # logging.debug(data['results'][0])

                # Only keep a subset of the search results
                results = [
                    {k: v for k, v in r.items() if k in result_fields}
                    for r in data['results']]
                # pprint.pprint(results)
                logging.debug(pprint.pformat([r['displayId'] for r in results]))

                output_list.extend(results)
                # input('ENTER')

        # Save results to CSV by Landsat type (to match bulk files)
        if output_list:
            output_df = pd.DataFrame.from_records(output_list)
            output_df.rename(
                columns={
                    'displayId': product_id_col,
                    'entityId': scene_id_col,
                    'browseUrl': browse_url_col,
                    'acquisitionDate': acq_date_col,
                },
                inplace=True)
            # output_df[sensor_col] = output_df[product_col].str.slice(0, 4)
            output_df[data_type_col] = output_df[product_id_col].str.slice(5, 9)
            output_df[wrs2_path_col] = output_df[product_id_col]\
                .str.slice(10, 13).astype(int)
            output_df[wrs2_row_col] = output_df[product_id_col]\
                .str.slice(13, 16).astype(int)
            output_df[col_number_col] = output_df[product_id_col]\
                .str.slice(35, 37).astype(int)
            output_df[col_category_col] = output_df[product_id_col]\
                .str.slice(38, 40)
            output_df[wrs2_tile_col] = output_df[[wrs2_path_col, wrs2_row_col]]\
                .apply(lambda x: 'p{:03d}r{:03d}'.format(x[0], x[1]), axis=1)

            # Apply basic high latitude filtering based on path
            output_df = output_df[output_df[wrs2_row_col] < 100]
            output_df = output_df[output_df[wrs2_row_col] > 9]

            if not output_df.empty:
                logging.debug('\nSaving CSV')
                output_df.sort_index(axis=1, inplace=True)
                output_df.to_csv(output_path, index=None)


def api_login(username, password):
    logging.debug('\nRetrieving API key')
    payload = json.dumps({"username": username, "password": password})
    r = requests.post(API_URL + 'login', data={"jsonRequest": payload})
    api_key = r.json()['data']
    logging.debug('  {}'.format(api_key))
    return api_key


def get_field_ids(landsat, api_key):
    logging.debug('\nRetrieving dataset field list')
    payload = {"datasetName": landsat, "apiKey": api_key}
    r = requests.post(
        API_URL + 'datasetfields',
        data={'jsonRequest': json.dumps(payload)})
    fields = r.json()['data']
    fields = {f['name']: f['fieldId'] for f in fields}
    logging.debug('Fields:')
    logging.debug(pprint.pformat(fields))
    return fields


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
        description='Download filtered Landsat Collection 1 metadata CSV files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('username', help='USGS Earth Explorer Username')
    parser.add_argument('password', help='USGS Earth Explorer Password')
    parser.add_argument(
        '--csv', type=lambda x: is_valid_folder(parser, x),
        default=os.getcwd(), help='Landsat metadata CSV folder')
    parser.add_argument(
        '-pr', '--pathrows', nargs='+', required=True, metavar='pXXXrYYY',
        help='Space separated string of Landsat path/rows to keep '
             '(i.e. -pr p043r032 p043r033)')
    parser.add_argument(
        '-y', '--years', required=True, type=str,
        help='Comma separated list or range of years to download'
             '(i.e. "--years 1984,2000-2015")')
    parser.add_argument(
        '-m', '--months', default='1-12', type=str,
        help='Comma separated list or range of months to download'
             '(i.e. "--months 1,2,3-5")')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    if args.csv and os.path.isdir(os.path.abspath(args.csv)):
        args.csv = os.path.abspath(args.csv)
    # else:
    #     args.csv = get_csv_path(os.getcwd())

    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')

    main(username=args.username, password=args.password, csv_ws=args.csv,
         wrs2_tile_list=args.pathrows, years=args.years, months=args.months)
