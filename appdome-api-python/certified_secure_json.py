import argparse
import logging
from json import load, dump
from os.path import exists
from shutil import move
from utils import (validate_response, add_common_args, init_common_args, validate_output_path, task_output_command)


def download_certified_secure_json(api_key, team_id, task_id):
    return task_output_command(api_key, team_id, task_id, 'certificate-json')


def format_json_file(file_path):
    temp_write_file_path = file_path + '-tmp'
    if not file_path or not exists(file_path) or exists(temp_write_file_path):
        return
    try:
        with open(file_path) as f:
            obj = load(f)
        with open(temp_write_file_path, 'w') as f:
            dump(obj, f, indent=2, separators=(',', ': '))
        move(temp_write_file_path, file_path)
        logging.debug(f"Formatted {file_path}")
    except Exception:
        pass


def parse_arguments():
    parser = argparse.ArgumentParser(description='Download Certified Secure json file')
    add_common_args(parser, add_task_id=True)
    parser.add_argument('-cj', '--certificate_json', required=True, metavar='certificate_json_output_file', help='Output file for Certified Secure json')
    return parser.parse_args()


def main():
    args = parse_arguments()
    init_common_args(args)
    validate_output_path(args.certificate_json)
    r = download_certified_secure_json(args.api_key, args.team_id, args.task_id)
    validate_response(r)
    with open(args.certificate_json, 'wb') as f:
        f.write(r.content)
    logging.info(f"Downloaded file to {args.certificate_json}")
    format_json_file(args.certificate_json)


if __name__ == '__main__':
    main()
