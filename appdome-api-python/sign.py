import argparse
import logging

from utils import (add_provisioning_profiles_entitlements, add_google_play_signing_fingerprint,
                   run_task_action, cleaned_fd_list, validate_response, add_common_args, init_common_args, init_overrides)

SIGN_ACTION = 'sign'


def sign_android(api_key, team_id, task_id,
                 keystore_path, keystore_pass, key_alias, key_pass,
                 google_play_signing_fingerprint=None, sign_overrides=None):
    overrides = {
        'signing_keystore_password':  keystore_pass,
        'signing_keystore_alias': key_alias,
        'signing_keystore_key_password': key_pass
    }
    
    add_google_play_signing_fingerprint(google_play_signing_fingerprint, overrides)

    if sign_overrides:
        overrides.update(sign_overrides)

    with open(keystore_path, 'rb') as f:
        files = {'signing_keystore': (keystore_path, f)}
        return run_task_action(api_key, team_id, SIGN_ACTION, task_id, overrides, files)


def sign_ios(api_key, team_id, task_id,
             keystore_p12_path, keystore_pass, provisioning_profiles_paths, entitlements_paths=None, sign_overrides=None):
    overrides = {'signing_p12_password':  keystore_pass}

    with cleaned_fd_list() as open_fd:
        f = open(keystore_p12_path, 'rb')
        open_fd.append(f)
        files_list = [('signing_p12_content', (keystore_p12_path, f))]
        add_provisioning_profiles_entitlements(provisioning_profiles_paths, entitlements_paths, files_list, overrides, open_fd)
        if sign_overrides:
            overrides.update(sign_overrides)
        return run_task_action(api_key, team_id, SIGN_ACTION, task_id, overrides, files_list)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Initialize signing on Appdome')
    add_common_args(parser, add_task_id=True)
    parser.add_argument('-k', '--keystore', required=True, metavar='keystore_file', help='Path to keystore file to use on Appdome iOS and Android signing.')
    parser.add_argument('-kp', '--keystore_pass', required=True, metavar='keystore_password', help='Password for keystore to use on Appdome iOS and Android signing..')
    parser.add_argument('-sv', '--sign_overrides', metavar='overrides_json_file', help='Path to json file with sign overrides')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-pr', '--provisioning_profiles', nargs='+', metavar='provisioning_profile_file', help='Path to iOS provisioning profiles files to use. Can be multiple profiles')
    group.add_argument('-ka', '--keystore_alias', metavar='key_alias', help='Key alias to use on Appdome Android signing.')
    parser.add_argument('-kyp', '--key_pass', metavar='key_password', help='Password for the key to use on Appdome Android signing.')
    parser.add_argument('--google_play_signing_fingerprint', metavar='signing_fingerprint', help='SHA-1 or SHA-256 Google Play App Signing certificate fingerprint.')
    parser.add_argument('-gp', '--google_play_signing', action='store_true', help='This Android application will be distributed via the Google Play App Signing program.')
    parser.add_argument('-entt', '--entitlements', nargs='+', metavar='entitlements_plist_path', help='Path to iOS entitlements plist to use. Can be multiple entitlements files')
    return parser.parse_args()


def main():
    args = parse_arguments()
    init_common_args(args)

    overrides = init_overrides(args.sign_overrides)

    if args.keystore_alias:
        r = sign_android(args.api_key, args.team_id, args.task_id, args.keystore, args.keystore_pass,
                         args.keystore_alias, args.key_pass, args.google_play_signing_fingerprint, overrides)
    else:
        r = sign_ios(args.api_key, args.team_id, args.task_id, args.keystore, args.keystore_pass,
                     args.provisioning_profiles, args.entitlements, overrides)

    validate_response(r)
    logging.info(f"On Appdome signing for Build id: {r.json()['task_id']} started")


if __name__ == '__main__':
    main()
