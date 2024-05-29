import argparse
import logging
from enum import Enum
from os import getenv
from os.path import splitext
from build import build
from certified_secure import download_certified_secure
from certified_secure_json import download_certified_secure_json, format_json_file
from download import download, download_action
from status import wait_for_status_complete
from upload import upload
from utils import (validate_response, log_and_exit, add_common_args, init_common_args, validate_output_path,
                   init_overrides)

class Platform(Enum):
    UNKNOWN = 0
    ANDROID = 1
    IOS = 2


def parse_arguments():
    parser = argparse.ArgumentParser(description='Runs Appdome API commands for SDK')
    upload_group = parser.add_mutually_exclusive_group(required=True)
    upload_group.add_argument('-a', '--app', metavar='application_file', help='Upload app file input path')
    upload_group.add_argument('--app_id', metavar='app_id_value', help='App id of previously uploaded app')

    add_common_args(parser)

    parser.add_argument('-fs', '--fusion_set_id', metavar='fusion_set_id_value',
                        help='Appdome Fusion Set id. '
                             'Default for Android is environment variable APPDOME_ANDROID_FS_ID. '
                             'Default for iOS is environment variable APPDOME_IOS_FS_ID')
    parser.add_argument('-bv', '--build_overrides', metavar='overrides_json_file',
                        help='Path to json file with build overrides')
    parser.add_argument('-bl', '--diagnostic_logs', action='store_true',
                        help="Build the app with Appdome's Diagnostic Logs (if licensed)")

    # Output parameters
    parser.add_argument('-o', '--output', metavar='output_app_file',
                        help='Output file for fused and signed app after Appdome')
    parser.add_argument('-co', '--certificate_output', metavar='certificate_output_file',
                        help='Output file for Certified Secure pdf')
    parser.add_argument('-cj', '--certificate_json', metavar='certificate_json_output_file',
                        help='Output file for Certified Secure json')
    return parser.parse_args()


def validate_args(args):
    fusion_set_id = args.fusion_set_id
    platform = Platform.UNKNOWN
    init_common_args(args)
    if args.app:
        app_path_ext = splitext(args.app)[-1].lower()
        if not app_path_ext == ".aar":
            platform = Platform.IOS
            log_and_exit(f"SDK extension [{app_path_ext}] must be .aar")
        else:
            platform = Platform.ANDROID

    if not fusion_set_id:
        fusion_set_id = getenv('APPDOME_IOS_FS_ID' if platform == Platform.IOS else 'APPDOME_ANDROID_FS_ID')
        if not fusion_set_id:
            log_and_exit("fusion_set_id must be specified or set though the correct platform environment variable")

    validate_output_path(args.output)
    validate_output_path(args.certificate_output)
    validate_output_path(args.certificate_json)
    return platform, fusion_set_id


def _upload(api_key, team_id, app_path):
    upload_response = upload(api_key, team_id, app_path)
    validate_response(upload_response)
    logging.info(f"Upload done. App-id: {upload_response.json()['id']}")
    return upload_response.json()['id']


def _build(api_key, team_id, app_id, fusion_set_id, build_overrides, use_diagnostic_logs):
    build_overrides_json = init_overrides(build_overrides)
    build_response = build(api_key, team_id, app_id, fusion_set_id, build_overrides_json, use_diagnostic_logs)
    validate_response(build_response)
    logging.info(f"Build request started. Response: {build_response.json()}")
    task_id = build_response.json()['task_id']
    wait_for_status_complete(api_key, team_id, task_id)
    logging.info(f"Build request finished.")
    return task_id


def _download_file(api_key, team_id, task_id, output_path, download_func):
    download_response = download_func(api_key, team_id, task_id)
    validate_response(download_response)
    with open(output_path, 'wb') as f:
        f.write(download_response.content)
    logging.info(f"File written to {output_path}")


def main():
    args = parse_arguments()
    platform, fusion_set_id = validate_args(args)
    app_id = _upload(args.api_key, args.team_id, args.app) if args.app else args.app_id
    task_id = _build(args.api_key, args.team_id, app_id, fusion_set_id, args.build_overrides, args.diagnostic_logs)

    if args.output:
        _download_file(args.api_key, args.team_id, task_id, args.output, download)
    if args.certificate_output:
        _download_file(args.api_key, args.team_id, task_id, args.certificate_output, download_certified_secure)
    if args.certificate_json:
        _download_file(args.api_key, args.team_id, task_id, args.certificate_json, download_certified_secure_json)
        format_json_file(args.certificate_json)


if __name__ == '__main__':
    main()
