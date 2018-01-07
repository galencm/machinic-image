# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

from PIL import Image
import redis
from io import BytesIO
import attr
import uuid
import sys
#from tesserocr import PyTessBaseAPI, RIL 
from tesserocr import PyTessBaseAPI, PSM,image_to_text,OEM
from logzero import logger

import redis
import consul
def lookup(service):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'],services[k]['Port']
                return service_ip,service_port
                break
    return None,None

r_ip,r_port = lookup('redis')
r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))


@attr.s 
class GlworbSelection():
    source_uuid = attr.ib()
    key_contents= attr.ib()
    key_name = attr.ib()
    working_file= attr.ib()
    working_metadata = attr.ib()
    errors= attr.ib()


#def starti(glworb_uuid:str,glworb_key:str,prefix:str="glworb:",*args) -> GlworbSelection:
def pipe_starti(glworb_uuid,glworb_key,prefix="glworb:",*args):
    """Load image bytes, start of pipe
        
        Args:
            glworb_uuid(str): glworb uuid
            glworb_key(str): hash key to use
            prefix(str): db key prefix, default is "glworb:"
        
        Returns:
            GlworbSelection:
    """
    logger.info(sys._getframe().f_code.co_name)
    #Pillow cannot in general close and reopen a file, so any access to that file needs to be prior to the close.
    errors = []

    bytes_key = r.hget(prefix+glworb_uuid, glworb_key)
    if bytes_key is None:
        logger.warn("retrieved {} from {}".format(bytes_key,glworb_key))
        logger.warn("did you mean: {}".format(r.hkeys(prefix+glworb_uuid)))
    else:
        logger.info("{} field {} has {}".format(prefix+glworb_uuid,glworb_key,bytes_key))

    key_bytes = binary_r.get(bytes_key)

    #leave file open until end of pipe
    file = BytesIO(key_bytes)

    gs = GlworbSelection(glworb_uuid,Image.open(file),glworb_key,file,dict({}),errors)
    gs.working_metadata['preserve_format'] = gs.key_contents.format

    return gs

#def endi(gs: GlworbSelection,*args)-> GlworbSelection:
def pipe_endi(gs,*args):
    """End of image pipe, write and close

        Args:
            gs(GlworbSelection): active GlworbSelection
            *args: args
        
        Returns:
            GlworbSelection:
    """

    logger.info(sys._getframe().f_code.co_name)
    binary_prefix="glworb_binary:"
    prefix="glworb:"

    file = BytesIO()
    extension =gs.working_metadata['preserve_format']
    gs.key_contents.save(file,extension)
    gs.key_contents.close()
    file.seek(0)
    contents = file.read()
    k = prefix+gs.source_uuid
    bytes_key = r.hget(k, gs.key_name)
    print("bytes key is......",bytes_key)
    binary_r.set(bytes_key, contents)
    file.close()
    gs.working_file.close()

    return "done!"

#def show(gs: GlworbSelection,*args):
def pipe_show(gs,*args):
    """Display image

        Args:
            gs(GlworbSelection): active glworbselection
            *args:

        Returns:
            GlworbSelection:
    """
    logger.info(sys._getframe().f_code.co_name)
    gs.key_contents.show()
    return gs

#crops as partials...
#def cropto(gs: GlworbSelection,x1:float,y1:float,w:float,h: float,to_key:str,*args) -> bytes:
def pipe_pcropto(gs,x1,y1,w,h,to_key,*args):
    """Crop selection from gs to new key

        Args:
            gs(GlworbSelection): active glworbselection
            x1(float): starting x coordinate
            y1(float):  starting y coordinate
            w(float): width
            h(float): height
            to_key: key to store crop
            *args:

        Returns:
            GlworbSelection:
    """
    print(sys._getframe().f_code.co_name)
    x1 = float(x1)
    y1 = float(y1)
    w = float(w)
    h = float(h)

    width, height = gs.key_contents.size
    x1 *= width
    y1 *= height
    w  *= width
    h  *= height
    
    box = (x1,y1,x1+w,y1+h)
    region = gs.key_contents.crop(box)

    file = BytesIO()
    extension = gs.working_metadata['preserve_format']
    region.save(file,extension)
    file.seek(0)
    contents = file.read()
    g_uuid = str(uuid.uuid4())
    bytes_key = "glworb_binary:{}".format(g_uuid)
    binary_r.set(bytes_key, contents)
    k = "glworb:"+gs.source_uuid
    r.hset(k,to_key,bytes_key)
    #region.show()
    region.close()
    file.close()

    return gs

def pipe_cropto(gs,x1,y1,w,h,to_key,*args):
    """Crop selection from gs to new key

        Args:
            gs(GlworbSelection): active glworbselection
            x1(float): starting x coordinate
            y1(float):  starting y coordinate
            w(float): width
            h(float): height
            to_key: key to store crop
            *args:

        Returns:
            GlworbSelection:
    """
    print(sys._getframe().f_code.co_name)
    x1 = float(x1)
    y1 = float(y1)
    w = float(w)
    h = float(h)
    box = (x1,y1,x1+w,y1+h)
    region = gs.key_contents.crop(box)

    file = BytesIO()
    extension = gs.working_metadata['preserve_format']
    region.save(file,extension)
    file.seek(0)
    contents = file.read()
    g_uuid = str(uuid.uuid4())
    bytes_key = "glworb_binary:{}".format(g_uuid)
    binary_r.set(bytes_key, contents)
    k = "glworb:"+gs.source_uuid
    r.hset(k,to_key,bytes_key)
    #region.show()
    region.close()
    file.close()

    return gs
#def crop(gs: GlworbSelection,x1:float,y1:float,x2:float,y2: float,*args) -> bytes:
def pipe_crop(gs,x1,y1,x2,y2,*args):
    """Crop in place

        Args:
            gs(GlworbSelection): active glworbselection
            x1(float): starting x coordinate
            y1(float):  starting y coordinate
            x2(float): width
            y2(float): height
            *args:

        Returns:
            GlworbSelection:
    """
    print(sys._getframe().f_code.co_name)
    #left upper right lower
    #(x, y, w, h)
    x1 = float(x1)
    y1 = float(y1)
    w = float(w)
    h = float(h)
    box = (x1,y1,x1+w,y1+h)    #box = floats#(x1, y1, x2, y2)
    region = gs.crop(box)
    gs.key_contents = region
    return gs

#def rotate(gs: GlworbSelection, rotation:float,*args):
def pipe_rotate(gs, rotation,*args):
    """Rotate in place

        Args:
            gs(GlworbSelection): active glworbselection
            rotation(float): starting x coordinate
            *args:

        Returns:
            GlworbSelection:
    """    
    print(sys._getframe().f_code.co_name)
    gs.key_contents = gs.key_contents.rotate(float(rotation),expand=True)
    return gs

#def orientation(gs: GlworbSelection,*args):
def pipe_orientation(gs,*args):
    """Calculate text orientation using tesseract

        Args:
            gs(GlworbSelection): active glworbselection
            *args:

        Returns:
            GlworbSelection:
    """    
    print(sys._getframe().f_code.co_name)

    with PyTessBaseAPI(psm=PSM.AUTO_OSD) as api:
        image = gs.key_contents
        #image = Image.open("/usr/src/tesseract/testing/eurotext.tif")
        api.SetImage(image)
        api.Recognize()

        it = api.AnalyseLayout()
        orientation, direction, order, deskew_angle = it.Orientation()
        logger.info("Orientation: {:d}".format(orientation))
        logger.info("WritingDirection: {:d}".format(direction))
        logger.info("TextlineOrder: {:d}".format(order))
        logger.info("Deskew angle: {:.4f}".format(deskew_angle))

    #needs 4.0
    #https://github.com/tesseract-ocr/tesseract/wiki/4.0-with-LSTM
    """
    with PyTessBaseAPI(psm=PSM.OSD_ONLY, oem=OEM.LSTM_ONLY) as api:
        #api.SetImageFile("/usr/src/tesseract/testing/eurotext.tif")
        image = gs.key_contents
        api.SetImage(image)

        os = api.DetectOrientationScript()
        print ("Orientation: {orient_deg}\nOrientation confidence: {orient_conf}\n"
               "Script: {script_name}\nScript confidence: {script_conf}").format(**os)
    return gs
    """

#def ocr(gs: GlworbSelection,ocr_results_key:str,*args):
def pipe_ocr(gs,ocr_results_key,*args):
    """Optical Character Recognition(OCR) using tesseract

        Args:
            gs(GlworbSelection): active glworbselection
            ocr_results_key(str): key to store ocr results
            *args:

        Returns:
            GlworbSelection:
    """        
    print(sys._getframe().f_code.co_name)

    print(image_to_text(gs.key_contents))

    """
    #image = Image.open('/usr/src/tesseract/testing/phototest.tif')
    image = gs.key_contents
    with PyTessBaseAPI() as api:
        api.SetImage(image)
        boxes = api.GetComponentImages(RIL.TEXTLINE, True)
        print 'Found {} textline image components.'.format(len(boxes))
        for i, (im, box, _, _) in enumerate(boxes):
            # im is a PIL image object
            # box is a dict with x, y, w and h keys
            api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
            ocrResult = api.GetUTF8Text()
            conf = api.MeanTextConf()
            print ("Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
                   "confidence: {1}, text: {2}").format(i, conf, ocrResult, **box)
    """
    return gs

