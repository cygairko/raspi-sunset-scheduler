#!/usr/bin/env python3
import logging
import os, sys
import argparse
import shutil
from datetime import datetime, timedelta
from calc import Suncalc, EVENTS
from glob import glob
from skyfield import api, almanac
import pytz
from astral import LocationInfo
from astral.sun import sun

LOG_FORMAT="%(message)s"

logger = logging.getLogger(__name__)

def init():
    """
    Create settings module if it does not exist.
    """
    path = os.path.join(sys.path[0], 'settings.py')
    if os.path.isfile(path) == False:
        template = os.path.join(sys.path[0], 'sample_settings.py')
        shutil.copyfile(template, path)
        print("Created settings.py module from sample.")

def run_commands(args):
    """
    Output or execute commands as specified in settings.
    """
    init()
    from settings import LATITUDE, LONGITUDE
    from settings import commands, EVENT
    s = Suncalc(LATITUDE, LONGITUDE, EVENT)

    local_dt = datetime.now()
    value = s.local_value(local_dt)
    for c in commands(value):
        if args.execute:
            os.system(c)
        else:
            print(c)

def show_time(args):
    """
    Output fime for selected event.
    """
    init()
    from settings import LATITUDE, LONGITUDE
    s = Suncalc(LATITUDE, LONGITUDE, args.event)

    city = LocationInfo("Hamburg", "Germany", "Europe/Berlin", LATITUDE, LONGITUDE)
    print((
        f"Information for {city.name}/{city.region}\n"
        f"Timezone: {city.timezone}\n"
        f"Latitude: {city.latitude:.02f}; Longitude: {city.longitude:.02f}\n"
    ))

    local_dt = datetime.now(tz=city.tzinfo)
    thesun = sun(city.observer, date=local_dt, tzinfo=city.tzinfo)

    print((
    f'Dawn:    {thesun["dawn"]}\n'
    f'Sunrise: {thesun["sunrise"]}\n'
    f'Noon:    {thesun["noon"]}\n'
    f'Sunset:  {thesun["sunset"]}\n'
    f'Dusk:    {thesun["dusk"]}\n'
    ))


    value = s.local_value(local_dt)

    print("Local {} is at {}".format(args.event, value))

def collect_images(args):
    """
    Collect images with same index number to target directory.
    Order collected files by date created and create symbolic link
    for each file using numeric counter as filename.
    """
    from settings import TARGET_DIRECTORY as source_dir # sic!
    target_dir = args.target if os.path.isabs(args.target) else os.path.join(source_dir, args.target)
    if os.path.isdir(source_dir):
        if os.path.isdir(target_dir) == False:
            os.makedirs(target_dir)
        if args.purge:
            # Remove old files in target directory
            g = glob(os.path.join(target_dir, "*"))
            count = len(g)
            if count > 0:
                if args.silent == False:
                    print("All files in target directory {} will be deleted.".format(
                        target_dir))
                    print("Do you want to continue? (y/n)")
                    if input().lower() != 'y':
                        print("Operation cancelled.")
                        return
                for file in g:
                    os.remove(file)

        pattern = os.path.join(source_dir, args.subdir, "*{:+d}.jpg".format(args.offset))
        files = sorted(glob(pattern), key=os.path.getmtime)
        count = len(files)
        perform_operation = shutil.copyfile if args.copy else os.symlink
        if count > 0:
            for index, path in enumerate(files):
                target_path = os.path.join(target_dir, "{:d}.jpg".format(index))
                print(target_path)
                perform_operation(path, target_path)
            if args.copy:
                print("Successfully copied {} files to {}.".format(count, target_dir))
            else:
                print("Successfully created {} symlinks to {}.".format(count, target_dir))
        else:
            print("No files found to be processed.")

    else:
        print("Source directory defined in settings does not exist.".format(source_dir))

def main():
    parser = argparse.ArgumentParser("Sunset Calculator")
    subparsers = parser.add_subparsers(help="Action to perfom.")

    # Define parser for show-time action
    subparser = subparsers.add_parser("show-time",
        help="Show time for specific event.")
    subparser.add_argument('--event', required=True, type=str, choices=EVENTS,
        help="Defines event to be observed.")
    subparser.set_defaults(func=show_time)

    # Define parser for run-commands action
    subparser = subparsers.add_parser("run-commands",
        help="Run commands specified in settings.")
    subparser.set_defaults(func=run_commands)
    subparser.add_argument('--execute', action='store_true',
        default=False, help="If set to True, execute commands using os.system.")

    # Define parser for collect-images action
    subparser = subparsers.add_parser("collect-images",
        help="Collect images for creating time-lapse video.")
    subparser.set_defaults(func=collect_images)
    subparser.add_argument('--offset', type=int, required=True,
        help="Index of images to be collected.")
    subparser.add_argument('--target', type=str, required=True,
        help="Target path for images.")
    subparser.add_argument('--subdir', type=str, required=False, default='',
        help="Sub-directory to look for images.")
    subparser.add_argument('--purge', action='store_true',
        help="If set to True, remove old files before proceeding.")
    subparser.add_argument('--silent', default=False, action='store_true',
        help="If set to True, do not ask for confirmation.")
    subparser.add_argument('--copy', default=False, action='store_true',
        help="If set to True, copy files instead of creating symlink.")

    args = parser.parse_args()


    if hasattr(args, 'func') == False:
        parser.print_help()
        return
    try:
        args.func(args)
    except:
        e = sys.exc_info()
        logger.error("Operation failed: {0}".format(e[1]))


if __name__=='__main__':
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
    main()
