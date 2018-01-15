# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import consul
import zerorpc

def lookup(service):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'],services[k]['Port']
                return service_ip,service_port
                break
    return None,None

def fuzzy_lookup(service):
    c = consul.Consul()
    matched_services = []
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if service in services[k]['Service']:
                sinfo = {
                'ip':services[k]['Address'],
                'port':services[k]['Port'],
                'service':services[k]['Service']
                }
                matched_services.append(sinfo)
    return matched_services

def rpc(func,*args):
    rip,rport = lookup('zerorpc-tools')
    zc = zerorpc.Client()
    zc.connect("tcp://{}:{}".format(rip,rport))
    result = zc(func,*args)
    return result

def parse_job_output(job_string):
    jobs = {}
    for line_num,line in enumerate(job_string.split("\n")):
        if line_num > 0 and line:
            # remove extra whitespace between columns
            job_name,job_type,job_priority,job_status,_ = " ".join(line.split()).split(" ",4)
            jobs[job_name] = job_status
    return jobs

def lookup_machine(machine_yaml_file,ignored_services=None):
    """
    return a dict {service_name:status}
    ignored_services are not included in dict
    """
    import subprocess
    from ruamel.yaml import YAML
    import pathlib
    # start.sh
    # --tags machine machine_core
    # but not in yaml?
    # get all with machine tag
    # parse yaml for includes, check...

    if ignored_services is None:
        ignored_services = []

    nomad_ip,nomad_port = lookup("nomad")

    nomad_jobs = subprocess.check_output(["nomad",
                                         "status",
                                         "-address=http://{}:{}".format(nomad_ip,nomad_port)
                                         ]).decode()

    nomad_jobs = parse_job_output(nomad_jobs)

    yaml=YAML(typ='safe')
    machine_outline = yaml.load(pathlib.Path(machine_yaml_file))
    #print(machine_outline)
    include_names = set()
    for includes in machine_outline['includes']:
        for include,include_properties in includes.items():
            # use name property if available, otherwise
            # name will be key
            service_prefix = ""
            # as-rpc services will be prefixed with zerorpc-
            # prefix name from yaml to correctly match service
            try:
                if include_properties['as-rpc'] is True:
                    service_prefix = "zerorpc-"
            except:
                pass

            try:
                include_names.add(service_prefix+include_properties['name'])
            except:
                # currently external file properties
                # are not available via yaml, 
                # so the name chop off .hcl and see
                # machine.py removes .py ending?
                #
                # replace underscores with dashes to reflect
                # replacement done to scheduled jobs
                if include.endswith(".hcl"):
                    include_names.add(service_prefix+include[:-4].replace("_","-"))
                elif include.endswith(".py"):
                    include_names.add(service_prefix+include[:-3].replace("_","-"))
                else:
                    include_names.add(service_prefix+include.replace("_","-"))

    #assert include_names.issubset(set(nomad_jobs.keys()))
    machine_scheduled_snapshot = {k:None for k in set(include_names)-set(ignored_services)}
    for k,v in nomad_jobs.items():
        if k in include_names and k not in ignored_services:
            #assert v == "running"
            print("{} {}".format(k,v))
            machine_scheduled_snapshot[k] = v

    return machine_scheduled_snapshot