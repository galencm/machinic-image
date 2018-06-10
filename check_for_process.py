# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

#import psutil
import argparse
import subprocess
import sys
import fnmatch
import time

def watch_loop(check_interval, proc_pattern, terminate_found=False):
    while True:
        match_procs(proc_pattern, terminate_found)
        time.sleep(check_interval)

def match_procs(proc_pattern, terminate_found):
    found_procs = []
    procs = subprocess.check_output(["ps", "-e"]).decode()
    proc_pattern = '*'.join(proc_pattern)
    proc_pattern = "*" + proc_pattern + "*"
    matches = fnmatch.filter( procs.split("\n"), proc_pattern)
    for match in matches:
        pid = match.strip().split(" ", 1)[0]
        proc = match.strip().rsplit(" ", 1)[-1]
        if terminate_found:
            try:
                print(subprocess.check_output(['kill', '-9', pid]).decode())
            except Exception as ex:
                pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--name-includes", nargs="+", help="substrings to match in process names")
    parser.add_argument("--check-interval", type=int, default=10, help="seconds between checks")
    parser.add_argument("--terminate-found", action='store_true', help="terminate process if found")
    args = parser.parse_known_args()[0]

    watch_loop(args.check_interval, args.name_includes, args.terminate_found)
