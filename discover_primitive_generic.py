import redis
import datetime
import local_tools

def discover_primitive_generic():

    r_ip,r_port = local_tools.lookup('redis')
    r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
    binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))

    discovery_method = "primitive_generic"
    camera_list = []
    errors = []
    matched = r.scan_iter("primitive_generic:*")

    for match in matched:
        name = match.split(":")[-1]
        source = r.get(match)
        now = str(datetime.datetime.now())
        #camera_list.append(GenericDevice(name=name,address=source,uid=name, discovery_method=discovery_method,lastseen=now))
        camera_list.append({'name':name,'address':source,'uid':name, 'discovery_method': discovery_method,'lastseen':now})

    return camera_list,errors
