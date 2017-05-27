import argparse
import calendar
from collections import defaultdict
import datetime as dt
import logging
import os
import re
import sys


def main(quicklook_folder, output_folder, path_row_list=[],
         skip_list_path=None):
    """Generate Landsat scene ID skip and keep lists from quicklooks

    Args:
        quicklook_folder (str): folder path
        output_folder (str): folder path to save skip list
        path_row_list (list): list of Landsat path/rows to process
            Example: ['p043r032', 'p043r033']
            Default is []
        skip_list_path (str): file path of Landsat skip list
    """
    logging.info('\nMake skip & keep lists from quicklook images')

    output_keep_name = 'clear_scenes.txt'
    output_skip_name = 'cloudy_scenes.txt'
    summary_name = 'clear_scene_counts.txt'
    summary_flag = True

    output_keep_path = os.path.join(output_folder, output_keep_name)
    output_skip_path = os.path.join(output_folder, output_skip_name)
    summary_path = os.path.join(output_folder, summary_name)

    cloud_folder = 'cloudy'

    year_list = list(range(1984, dt.datetime.now().year + 1))
    # year_list = [2015]

    # Additional/custom path/row filtering can be hardcoded
    # path_row_list = []
    path_list = []
    row_list = []

    quicklook_re = re.compile(
        '(?P<year>\d{4})_(?P<doy>\d{3})_(?P<landsat>\w{3}).jpg')
    path_row_fmt = 'p{:03d}r{:03d}'
    # path_row_re = re.compile('p(?P<PATH>\d{1,3})r(?P<ROW>\d{1,3})')

    # Setup and validate the path/row lists
    path_row_list, path_list, row_list = check_path_rows(
        path_row_list, path_list, row_list)

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

    output_keep_list = []
    output_skip_list = []
    for root, dirs, files in os.walk(quicklook_folder):
        # DEADBEEF: Need better cross platform solution
        if os.name == 'nt':
            pr_match = re.search(
                'p(\d{3})r(\d{3})\\\(\d{4})(\\\%s)?' % cloud_folder, root)
        elif os.name == 'posix':
            pr_match = re.search(
                'p(\d{3})r(\d{3})/(\d{4})(/%s)?' % cloud_folder, root)
        if not pr_match:
            continue

        path, row, year = map(int, pr_match.groups()[:3])
        path_row = path_row_fmt.format(path, row)

        # Skip scenes first by path/row
        if path_row_list and path_row not in path_row_list:
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
                year, doy, landsat = quicklook_re.match(name).groups()
            except:
                continue
            scene_id = '{}{:03d}{:03d}{:04d}{:03d}'.format(
                landsat, path, row, int(year), int(doy))
            if input_skip_list and scene_id in input_skip_list:
                logging.debug('  {} - skip list, skipping'.format(
                    scene_id))
                continue

            if pr_match.groups()[3]:
                logging.debug('  {} - skip'.format(scene_id))
                output_skip_list.append([year, doy, scene_id])
            else:
                logging.debug('  {} - keep'.format(scene_id))
                output_keep_list.append([year, doy, scene_id])

    if output_keep_list:
        with open(output_keep_path, 'w') as output_f:
            for year, doy, scene in sorted(output_keep_list):
                output_f.write('{}\n'.format(scene))
    if output_skip_list:
        with open(output_skip_path, 'w') as output_f:
            for year, doy, scene in sorted(output_skip_list):
                output_f.write('{}\n'.format(scene))

    if summary_flag and output_keep_list:
        # This would probably be easier to do with pandas
        # def nested_dict():
        #     return defaultdict(nested_dict)
        # counts = nested_dict()
        counts = defaultdict(dict)

        for year, doy, scene in sorted(output_keep_list):
            path_row = 'p{}r{}'.format(scene[4:6], scene[7:9])
            output_dt = dt.datetime.strptime(
                '{}_{:03d}'.format(year, int(doy)), '%Y_%j')
            try:
                counts[path_row][year][output_dt.month] += 1
            except Exception as e:
                counts[path_row][year] = {m: 0 for m in range(1, 13)}

        with open(summary_path, 'w') as output_f:
            output_f.write('{},{},{}\n'.format(
                'PATH_ROW', 'YEAR', ','.join([
                    calendar.month_abbr[m].upper() for m in range(1, 13)])))
            for path_row, year_counts in sorted(counts.items()):
                for year, month_counts in sorted(year_counts.items()):
                    output_f.write('{},{},{}\n'.format(
                        path_row, year, ','.join([
                            str(c) for m, c in sorted(month_counts.items())])))


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


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description=(
            'Make skip list from quicklook images in "cloudy" folders\n' +
            'Beware that many values are hardcoded!'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-q', '--quicklook', metavar='FOLDER', default=os.getcwd(),
        help='Input folder with Landsat quicklook images')
    parser.add_argument(
        '--output', default=os.getcwd(), help='Output folder')
    parser.add_argument(
        '-pr', '--pathrows', nargs='+', default=None, metavar='pXXXrYYY',
        help=('Space separated string of Landsat path/rows to keep '
              '(i.e. -pr p043r032 p043r033)'))
    parser.add_argument(
        '--skiplist', default=None, help='Skips files in skip list')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    if args.quicklook and os.path.isfile(os.path.abspath(args.quicklook)):
        args.quicklook = os.path.abspath(args.quicklook)
    if args.output and os.path.isdir(os.path.abspath(args.output)):
        args.output = os.path.abspath(args.output)
    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{}'.format('#' * 80))
    logging.info('{:<20s} {}'.format(
        'Run Time Stamp:', dt.datetime.now().isoformat(' ')))
    logging.info('{:<20s} {}'.format('Current Directory:', os.getcwd()))
    logging.info('{:<20s} {}'.format(
        'Script:', os.path.basename(sys.argv[0])))

    main(quicklook_folder=args.quicklook, output_folder=args.output,
         path_row_list=args.pathrows, skip_list_path=args.skiplist)
