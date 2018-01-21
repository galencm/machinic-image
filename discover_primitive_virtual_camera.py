import redis
import datetime
import uuid
import local_tools
import zerorpc

r_ip,r_port = local_tools.lookup('redis')
r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))

def discover_primitive_virtual_camera():

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

def slurp_primitive_virtual_camera(device):

    source = r.get("primitive_virtual_camera:{}".format(device['name']))
    source_ip,source_port = lookup(source)

    zc = zerorpc.Client()
    zc.connect("tcp://{}:{}".format(source_ip,source_port))
    #would prefer a single source() to avoid specifying
    #parameters, but device name is needed for certain
    #types of state, ie index position

    #could pass device name in
    result = zc('source',device['name'])
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
    render_img_from_kv(binary_key,device['name'])

    errors=[]
    return [binary_key],errors
