#!/usr/bin/python3
import redis
import argparse
import sys

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

redis_ip,redis_port = lookup('redis')
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)

DEVICE_NAME = "capture4"
DEVICE_DIR = ""
#keyname directory
def action(action,primitive):
    if primitive == "generic":
        primitive_type = "primitive_generic"
    elif primitive == "virtual_camera":
        primitive_type = "primitive_virtual_camera"

    if action == 'run':
        r.set("{}:{}".format(primitive_type,DEVICE_NAME),DEVICE_DIR)
        print("running")
    elif action == 'stop':
        r.delete("{}:{}".format(primitive_type,DEVICE_NAME))
        print("stopped")
    elif action == 'status':
        status = r.get("{}:{}".format(primitive_type,DEVICE_NAME))
        if status:
            print("running")
        else:
            print("stopped")

def main(argv):
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", help="stop|run|status", choices=['run','stop','status'])
    parser.add_argument("primitive", help="generic|virtual_camera", choices=['generic','virtual_camera'])

    args = parser.parse_args()
    action(args.action,args.primitive)

if __name__ == '__main__':
    main(sys.argv)

