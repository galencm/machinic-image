import redis
import datetime
import uuid
import local_tools

def discover_primitive_virtual_camera():

    r_ip,r_port = local_tools.lookup('redis')
    r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
    binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))

    discovery_method = "primitive_virtual_camera"
    camera_list = []
    errors = []
    matched = r.scan_iter("primitive_virtual_camera:*")

    for match in matched:
        name = match.split(":")[-1]
        source = r.get(match)
        now = str(datetime.datetime.now())
        #camera_list.append(GenericDevice(name=name,address=source,uid=name, discovery_method=discovery_method,lastseen=now))
        camera_list.append({'name':name,'address':source,'uid':name, 'discovery_method': discovery_method,'lastseen':now})

    return camera_list,errors

def slurp_primitive_virtual_camera(generic_device):
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

    source = r.get("primitive_virtual_camera:{}".format(generic_device.name))
    source_ip,source_port = lookup(source)

    zc = zerorpc.Client()
    zc.connect("tcp://{}:{}".format(source_ip,source_port))
    #would prefer a single source() to avoid specifying
    #parameters, but device name is needed for certain
    #types of state, ie index position

    #could pass device name in
    result = zc('source',generic_device.name)
    #could dynamically generate function
    #result = zc('source_{}'.format(generic_device.name))
    #result = zc('source')
    gluuid = str(uuid.uuid4())
    binary_key = "glworb_binary:"+gluuid
    binary_r.set(binary_key, result)
    #process here...
    #problem should virtual camera be a widely available primitive?
    #not just in image_machine?
    from virtual_camera import render_img_from_kv
    #how to handle passing args if using zerorpc?
    render_img_from_kv(binary_key,generic_device.name)

    errors=[]
    return [binary_key],errors
