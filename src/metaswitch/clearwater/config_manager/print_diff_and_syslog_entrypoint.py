"""Wrapper script to use `print_diff_and_syslog` on the command line."""
import argparse
from metaswitch.clearwater.config_manager.config_access import print_diff_and_syslog


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_type', type=str)
    parser.add_argument('--config_1_path', type=str)
    parser.add_argument('--config_2_path', type=str)
    args = parser.parse_args()

    with open(args.config_1_path, 'r') as config_1_file:
        config_1 = config_1_file.read()

    with open(args.config_2_path, 'r') as config_2_file:
        config_2 = config_2_file.read()

    print_diff_and_syslog(args.config_type, config_1, config_2)


if __name__ == '__main__':
    main()