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
