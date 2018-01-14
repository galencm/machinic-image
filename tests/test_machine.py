# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import os
import sys
sys.path.insert(0, "../")
sys.path.insert(0, ".")
import local_tools

def test_machine_scheduled_running(machine_yaml):

    # pytest may be run insides tests directory
    # or main directory of project
    if not os.path.isfile(machine_yaml):
        if os.path.isfile("../"+machine_yaml):
            machine_yaml = "../"+machine_yaml
    
    assert os.path.isfile(machine_yaml)

    machine_scheduled_components = local_tools.lookup_machine(machine_yaml,ignored_services=[])
    
    for k,v in machine_scheduled_components.items():
        assert (k != "") and (v == "running")
    
    assert(set(list(machine_scheduled_components.values()))) == set(list(["running"]))
