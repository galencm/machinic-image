#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import os
import sys
from discover import discover,GenericDevice
from capture import capture
import attr
import redis
import itertools
import uuid
from logzero import logger
import logzero
import redis
from lings.routeling import route_broadcast
import local_tools

try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    logger.warn(ex)

r_ip,r_port = local_tools.lookup('redis')
r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))

def FlexibleObj(fields,obj_type=None,return_obj=None):
    """Provided a dictionary of values and a desired return type. Prune fields to match those in desired type and return populated type.

        Args:
            fields(dict): A dictionary
            obj_type(): Type of object to prune against
            return_obj(str): Type of class to return as populated object. Defaults to dict
        
        Keyword Args:
            asdict(bool): If True, return a dictionary instead of object. Defaults to False
        
        Returns:
            (obj): populated with intersecting fields.

    """
    if return_obj is None:
        return_obj = dict

    if obj_type:
        #type_attributes = [s for s in return_obj.__dict__.keys() if not s.startswith("_")]
        type_attributes = [s for s in obj_type().__dict__.keys() if not s.startswith("_")]
        #type_attributes = [s for s in obj_type.__dict__.keys() if not s.startswith("_")]
        logger.debug("obj: {} attributes: {}".format(obj_type,type_attributes))
        pruned_attributes = {key: fields[key] for key in fields if key in type_attributes}
    else:
        pruned_attributes = fields

    if return_obj is dict:
        return pruned_attributes
    else:
        return return_obj(**pruned_attributes)

def update_devices(*args,**kwargs):
    """Discover devices and update db.
        Adjust foundnow and lastseen for all devices in db
        
        Returns:
            devices: a list of Devices 
            errors: a list of strings 
    """
    return_obj=dict
    #rpc hack?
    try:
        for i,a in enumerate(args[0]):
            print(i,a)
            if a == 'dict':
                return_obj=dict
    except Exception as ex:
        logger.warn(ex)

    logger.info("discovering & updating devices")
    logger.info("args: {}".format(args))
    logger.info("return ob: {}".format(return_obj))

    devs=[]
    discovered_devs=[]
    errs=[]
    discovered_devs,errs = discover()
    foundnow = {}
    for d in discovered_devs:
        dev = attr.asdict(d)
        device_key = "device:{}{}".format(dev['uid'],dev['name'])
        r.hmset(device_key,dev) 
        foundnow[device_key] = dev['foundnow']

    persisted_devices = r.scan_iter("device:*")

    for d in persisted_devices:
        if d not in set(foundnow.keys()):
            #empty string will be considered False by graphene
            #sets foundnow to False 
            r.hset(d,"foundnow","") 
        devs.append(FlexibleObj(r.hgetall(d),obj_type=GenericDevice,return_obj=return_obj))
    logger.info("devices: {}, errors: {}".format(devs,errs))
    return devs,errs

def create_glworb(uids):
    """
    Creates Glworb(s)
    
    Given list of identifying_ids via GlworbInput,
    ids are searched for in redis matching id*.
    Found ids are converted to a GenericDevice and
    handled by capture(GenericDevice).

    Probably good to add method ie (<serial>,'gphoto2')

    capture returns a list of (binary_keys,errors)
    which are used to construct glworbs 

    Args:
    
    Returns:
        out (Glworbs): object

    """
    #make sure uids is list
    if isinstance(uids, str):
        uids = [uids]

    errors = []
    devs,errs = update_devices()
    errors.extend(errs)

    glworbs = []
    matches = []
    for source in uids:
        matched = r.scan_iter("device:*{}*".format(source))
        matches.append(matched)
        #create a single iterator from redis-result generators
        creating_sources = itertools.chain(*matches)

        logger.info("creating sources: {}".format(creating_sources))
        for dev in creating_sources:
            logger.info("capturing for: ".format(dev))
            dev_data = r.hgetall(dev)
            dev_data =  FlexibleObj(dev_data,return_obj=GenericDevice)
            method = dev_data.discovery_method

            try:
                keys,err = capture(method,dev_data)
            except Exception as ex:
                print(ex)
                errors.append(ex)

            errors.extend(err)
            for k in keys:
                guuid = str(uuid.uuid4())
                glworb_fields = attr.asdict(dev_data)
                glworb_fields['image_binary_key'] = k
                glworb_fields['source_uid'] = glworb_fields['uid']
                glworb_fields['method'] = method
                glworb_fields['uuid'] = guuid

                glworb = FlexibleObj(glworb_fields,return_obj=dict)
                write_glworb(dev_data.uid, guuid, glworb)
                glworbs.append(glworb)

    return [g,errors]

@route_broadcast(channel=source, message=uuid)
def write_glworb(source, uuid, glworb):
    r.hmset("glworb:{}".format(guuid),FlexibleObj(glworb_fields,return_obj=dict))
