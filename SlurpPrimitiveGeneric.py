import datetime
import io
import uuid
from logzero import logger
import local_tools
import redis
import sys
import zerorpc

class SlurpPrimitiveGeneric(object):

    def __init__(self):

        redis_ip, redis_port = local_tools.lookup('redis')
        self.r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
        self.binary_r = redis.StrictRedis(host=redis_ip, port=str(redis_port))
        self.channel_delimiter = "/"

    def broadcast(self, channel="", message="", subs=None):

        # subs is a list of dicts,
        # handle merging here
        substitutions={}
        substitutions.update({"class": type(self).__name__ })

        if subs is None:
            subs = []

        for s in subs:
            substitutions.update(s)

        formatted_channel = channel.format(**substitutions)
        formatted_channel = formatted_channel.replace("::",self.channel_delimiter)

        # prepend a '/' for mqtt style channels
        if self.channel_delimiter == "/":
            formatted_channel = "/"+formatted_channel

        formatted_message = message.format(**substitutions)
        self.r.publish(formatted_channel,formatted_message)

    def discover(self):

        method = "primitive_generic"
        discoverable = []
        matched = self.r.scan_iter("primitive_generic:*")

        try:

            for match in matched:
                name = match.split(":")[-1]
                source = self.r.get(match)
                now = str(datetime.datetime.now())
                discoverable.append({'name':name,'address':source,'uid':name, 'discovery_method': method,'lastseen':now})

        except Exception as ex:
            logger.warn(ex)
            self.broadcast(channel = "{class}::{function}::stderr",
                            message = ex,
                            subs = [{"function": sys._getframe().f_code.co_name}])

        return discoverable

    def slurp(self, device=None):

        if device is None:
            devices = self.discover()
        else:
            devices = [device]

        slurped = []

        for device in devices:
            slurped.extend(self.slurpd(device))
        
        return slurped

    def slurpd(self, device):
     
        slurped = []

        try:

            logger.info(device)
            name = device['name']
            addr = device['address']

            source = self.r.get("primitive_generic:{}".format(device['name']))
            source_ip,source_port = local_tools.lookup(source)

            zc = zerorpc.Client()
            zc.connect("tcp://{}:{}".format(source_ip,source_port))
    
            contents = zc('source',device['name'])   

            blob_uuid = str(uuid.uuid4())
            blob_key = "glworb_binary:"+blob_uuid
            self.binary_r.set(blob_key, contents)
            
            self.broadcast(channel = "slurp::{uid}::blob",
                            message = blob_key,
                            subs = [device,{"blob_key": blob_key}]
                            )

            slurped.append(blob_key)

        except Exception as ex:
            logger.warn(ex)
            self.broadcast(channel = "{class}::{function}::stderr",
                            message = str(ex),
                            subs = [{"function": sys._getframe().f_code.co_name}])
        return slurped
