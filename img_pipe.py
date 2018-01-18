# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import redis
import consul
import io
import uuid
from contextlib import contextmanager
from PIL import Image, ImageDraw, ImageFont
from tesserocr import PyTessBaseAPI, PSM, image_to_text, OEM, RIL
from logzero import logger

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

@contextmanager
def open_image(uuid,key):
    key_bytes = None
    bytes_key = r.hget(uuid, key)
    key_bytes = binary_r.get(bytes_key)
    file = io.BytesIO()
    file.write(key_bytes)
    image = Image.open(file)
    yield image
    file = io.BytesIO()
    image.save(file,image.format)
    image.close()
    file.seek(0)
    binary_r.set(bytes_key, file.read())
    file.close()

@contextmanager
def open_bytes(uuid,key):
    key_bytes = None
    bytes_key = r.hget(uuid, key)
    key_bytes = binary_r.get(bytes_key)
    file = io.BytesIO()
    file.write(key_bytes)
    yield file
    file.seek(0)
    binary_r.set(bytes_key, file.read())
    file.close()

def write_bytes(hash_uuid,key,write_bytes,key_prefix=""):
    bytes_key_uuid = str(uuid.uuid4())
    bytes_key = "{}{}".format(key_prefix,bytes_key_uuid)
    binary_r.set(bytes_key, write_bytes)
    r.hset(hash_uuid,key,bytes_key)

def img_show(context,*args):
    """Display image

        Args:
            context(dict): dictionary of context info
            *args:

        Returns:
            dict
    """
    with open_image(context['uuid'],context['key']) as img:
        img.show()
    return context

def img_overlay(context, text, x, y, fontsize, *args):
    """Rotate in place

        Args:
            context(dict): dictionary of context info
            text(string): text to overlay
            x(int): x position of text
            y(int): y position of text
            *args:

        Returns:
            dict
    """
    text = str(text)

    with open_image(context['uuid'],context['key']) as img:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("FreeSerif.ttf", fontsize)
            draw.text((x, y),text,(255,255,255),font=font)
        except:
            font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSerif.ttf", fontsize)
            draw.text((x, y),text,(255,255,255),font=font)

    return context

def img_rotate(context, rotation,*args):
    """Rotate in place

        Args:
            context(dict): dictionary of context info
            rotation(float): degrees of rotation
            *args:

        Returns:
            dict
    """
    
    # use open_bytes instead of open_image
    # because yielded image does not seem
    # to be mutated despite img = img.rotate

    with open_bytes(context['uuid'],context['key']) as img:
        image = Image.open(img)
        ext = image.format
        image = image.rotate(float(rotation),expand=True)
        img.seek(0)
        image.save(img,ext)

    # with open_image(context['uuid'],context['key']) as img:
    #     img = img.rotate(float(rotation),expand=True)

    return context

def img_crop_inplace(context,x1,y1,w,h,*args):
    """Crop in place

        Args:
            context(dict): dictionary of context info
            x1(float): starting x coordinate
            y1(float): starting y coordinate
            w(float): width
            h(float): height
            *args:

        Returns:
            dict
    """
    #left upper right lower
    x1 = float(x1)
    y1 = float(y1)
    w = float(w)
    h = float(h)

    with open_image(context['uuid'],context['key']) as img:
        if "scale" in args:
            width, height = img.size
            x1 *= width
            y1 *= height
            w  *= width
            h  *= height
        box = (x1,y1,x1+w,y1+h)
        img = img.crop(box)

    return context

def img_crop_to_key(context,x1,y1,w,h,to_key,*args):
    """Crop selection from context to new key

        Args:
            context(dict): dictionary of context info
            x1(float): starting x coordinate
            y1(float):  starting y coordinate
            w(float): width
            h(float): height
            to_key: key to store crop
            *args:

        Returns:
            dict:
    """
    x1 = float(x1)
    y1 = float(y1)
    w = float(w)
    h = float(h)

    with open_image(context['uuid'],context['key']) as img:
        if "scale" in args:
            width, height = img.size
            x1 *= width
            y1 *= height
            w  *= width
            h  *= height
        box = (x1,y1,x1+w,y1+h)
        region = img.crop(box)
        filelike = io.BytesIO()
        region.save(filelike,img.format)
        filelike.seek(0)
        write_bytes(context['uuid'],
                    to_key,filelike.read(),
                    key_prefix=context['binary_prefix'])
        filelike.close()

    return context

def img_orientation(context,*args):
    """Calculate text orientation using tesseract

        Args:
            context(dict): dictionary of context info
            *args:

        Returns:
            dict
    """
    with PyTessBaseAPI(psm=PSM.AUTO_OSD) as api:
        with open_image(context['uuid'],context['key']) as img:
            api.SetImage(img)
            api.Recognize()
            it = api.AnalyseLayout()
            orientation, direction, order, deskew_angle = it.Orientation()
            logger.info("Orientation: {:d}".format(orientation))
            logger.info("WritingDirection: {:d}".format(direction))
            logger.info("TextlineOrder: {:d}".format(order))
            logger.info("Deskew angle: {:.4f}".format(deskew_angle))

    #LSTM_ONLY needs 4.0
    #https://github.com/tesseract-ocr/tesseract/wiki/4.0-with-LSTM
    return context

def img_ocr(context,to_key,*args):
    """Optical Character Recognition(OCR) using tesseract

        Args:
            context(dict): dictionary of context info
            to_key(str): key to store ocr results
            *args:

        Returns:
            dict
    """
    with open_image(context['uuid'],context['key']) as img:
        logger.info(image_to_text(img))
        # r redis conn basically global
        r.hset(context['uuid'],to_key,image_to_text(img))
    return context

def img_ocr_rectangle(context,to_key,left,top,width,height,*args):
    with PyTessBaseAPI() as api:
        with open_image(context['uuid'],context['key']) as img:
            api.SetImage(img)
            api.SetRectangle(left, top, width, height)
            result = api.GetUTF8Text()
            logger.info(result)
            r.hset(context['uuid'],to_key,result)

def img_ocr_boxes(context,to_key,*args):
    with PyTessBaseAPI() as api:
        with open_image(context['uuid'],context['key']) as img:
            api.SetImage(img)
            boxes = api.GetComponentImages(RIL.TEXTLINE, True)
            for i, (im, box, _, _) in enumerate(boxes):
                api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
                ocrResult = api.GetUTF8Text()
                conf = api.MeanTextConf()
                logger.info("Box[{0}]: x={x}, y={y}, w={w}, h={h}, confidence: {1}, text: {2}".format(i, conf, ocrResult, **box))
    
    return context