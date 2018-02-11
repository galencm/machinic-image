import datetime
import io
import uuid
from logzero import logger
import local_tools
import redis
import sys
import time
import subprocess
import fnmatch
import datetime
import glob

class Default(dict):
    def __missing__(self, key):
        return "{"+key+"}"

class SlurpWebCam(object):

    def __init__(self,service_prefix=""):

        redis_ip, redis_port = local_tools.lookup('redis')
        self.r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
        self.binary_r = redis.StrictRedis(host=redis_ip, port=str(redis_port))
        self.channel_delimiter = "/"
        self.channels = {}
        self.service_prefix = ""
        self.channels['exception'] = "{service}::{class}::stderr::{function}"
        self.channels['slurp'] = "slurp::{container}"
        self.channels['device'] = "slurp::{uid}::{container}"
        self.scripts =['webcam']

    def state(self, device=None):

        states = []

        if device == '_':
            device = None

        if device is None:
            devices = self.discover()
        else:
            devices = [{"uid" : device}]

        for dev in devices:
            states.append(self.r.hgetall("state:{}".format(dev['uid'])))

        return states

    def set(self, device, attribute, value, value_flag=None):

        set_values = []

        if device == '_':
            device = None

        if device is None:
            devices = self.discover()
        else:
            devices = [{"uid" : device}]

        for dev in devices:
            # allow wildcards in attribute
            # get attributes for device
            # run set on any that match
            # fnmatch.fnmatch

            attributes = self.get(dev['uid'])[0]
            for k,v in attributes.items():
                if fnmatch.fnmatch(k,attribute):
                    # simple inc / dec, assumes int
                    if value_flag == '+' or value_flag == 'add':
                        current = self.get(dev['uid'], k)[0]
                        print(current,value)
                        if current:
                            value = int(value)
                            current = int(current)
                            current += value
                    elif value_flag == '-' or value_flag == 'sub':
                        current = self.get(dev['uid'], k)[0]
                        if current:
                            value = int(value)
                            current = int(current)
                            current -= value
                    else:
                        current = value

                    self.r.hmset("state:{}".format(dev['uid']), {k : current})
                    set_values.append(self.get(device, k))

        return set_values

    def get(self, device, attribute=None):

        get_values = []

        if device == '_':
            device = None

        if device is None:
            devices = self.discover()
        else:
            devices = [{"uid" : device}]

        for dev in devices:
            if attribute:
                get_values.append(self.r.hget("state:{}".format(dev['uid']), attribute))
            else:
                get_values.append(self.r.hgetall("state:{}".format(dev['uid'])))

        return get_values

    def broadcast(self, channel="", message="", subs=None):

        # subs is a list of dicts,
        # handle merging here
        substitutions={}
        substitutions.update({"class": type(self).__name__ })

        #zerorpc should be passed in as part of prefix...
        service_name = "zerorpc-{}".format(self.service_prefix+type(self).__name__ )
        self_ip, self_port = local_tools.lookup(service_name)
        if self_ip and self_port:
            substitutions.update({"service": service_name })
            substitutions.update({"service_ip": self_ip })
            substitutions.update({"service_port": self_port })
            # hash of port:ip
            # substitutions.update({"service_hash":  })

        if subs is None:
            subs = []

        for s in subs:
            substitutions.update(s)

        formatted_channel = channel.format_map(Default(substitutions))
        formatted_channel = formatted_channel.replace("::",self.channel_delimiter)

        # prepend a '/' for mqtt style channels
        if self.channel_delimiter == "/":
            formatted_channel = "/"+formatted_channel

        formatted_message = message.format_map(Default(substitutions))
        self.r.publish(formatted_channel,formatted_message)

        return (formatted_channel,formatted_message)

    def ping(self, echo = "1"):

        pongs = []
        # broadcast echo value on all channels used
        for _, channel in self.channels.items():
            pong = self.broadcast(channel = channel,
                                message = echo,
                                subs = [])
            pongs.append(pong)

        return pongs

    def discover(self):

        method = "webcam"
        discoverable = []
        try:
            now = str(datetime.datetime.now())
            for webcam in glob.glob("/dev/video*"):
                discoverable.append({'name':webcam,'address':webcam,'uid':webcam, 'discovery': method,'lastseen':now})

        except Exception as ex:
            logger.warn(ex)
            self.broadcast(channel = self.channels['exception'],
                            message = ex,
                            subs = [{"function": sys._getframe().f_code.co_name}])

        return discoverable

    def slurp(self, device=None, container="glworb"):

        if device == '_':
            device = None

        if device is None:
            devices = self.discover()
        else:
            devices = [device]

        slurped = []

        for device in devices:
            slurped_bytes = self.slurpd(device)

            # check using 'in' to allow combinations
            # for example: file+glworb
            if 'file' in container:
                fname = "/tmp/{}.slurp".format(time.time())
                with open(fname,'wb+') as f:
                    f.write(slurped_bytes)
                self.broadcast(channel = self.channels['slurp'],
                            message = fname,
                            subs = [device,
                                    {"blob_uuid": fname},
                                    {"container": container}])
                slurped.append(fname)

            if 'blob' in container:
                slurped.append(slurped_bytes)

            if 'glworb' in container:
                blob_uuid = str(uuid.uuid4())
                blob_uuid = "binary:"+blob_uuid
                self.binary_r.set(blob_uuid, slurped_bytes)

                glworb = {}
                glworb['uuid'] = str(uuid.uuid4())
                glworb['source_uid'] = device['uid']
                glworb['method'] = "slurp_webcam"
                glworb['binary_key'] = blob_uuid
                glworb['created'] = str(datetime.datetime.now())


                glworb_uuid = "glworb:{}".format(glworb['uuid'])
                self.r.hmset(glworb_uuid, glworb)

                self.broadcast(channel = self.channels['slurp'],
                            message = glworb_uuid,
                            subs = [device,
                                    {"blob_uuid": glworb_uuid},
                                    {"container": container}])

                self.broadcast(channel = self.channels['device'],
                            message = glworb_uuid,
                            subs = [device,
                                    {"blob_uuid": glworb_uuid},
                                    {"container": container}])

                slurped.append(glworb_uuid)

        return slurped

    def apply_state(self,device):
        # no sanitization of strings
        state = self.r.hgetall("state:{}".format(device['uid']))

        for script in self.scripts:
            for scriptkey, fullscript in self.r.hgetall("scripts:{}".format(script)).items():
                try:
                    print(locals()[script+'_call'](fullscript,{**device, **state}))
                except Exception as ex:
                    print(ex)

    def slurpd(self, device, apply_state=True):

        if apply_state:
            self.apply_state(device)

        try:
            tmp_output_filename = "/tmp/slurp_webcam.jpg"
            logger.info(device)
            name = device['name']
            addr = device['address']
            subprocess.call(["fswebcam", "--no-banner","--save", tmp_output_filename, "-d", addr,"-r", "1280x960"])
            contents = io.BytesIO()

            with open(file_name, "rb") as f:
                contents = io.BytesIO(f.read())

            contents = contents.getvalue()

        except Exception as ex:
            logger.warn(ex)
            self.broadcast(channel = self.channels['exception'],
                            message = str(ex),
                            subs = [{"function": sys._getframe().f_code.co_name}])

        return contents
