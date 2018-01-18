import pytest
import os
import sys
from PIL import Image
import io
sys.path.insert(0, "../")
sys.path.insert(0, ".")
import local_tools
import img_pipe
import uuid
import redis

@pytest.fixture(scope='session')
def redis_binary_conn():

    r_ip,r_port = local_tools.lookup('redis')
    binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))
    return binary_r

@pytest.fixture(scope='session')
def redis_conn():

    r_ip,r_port = local_tools.lookup('redis')
    r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
    return r

@pytest.fixture(scope='session')
def glworb_image(redis_conn,redis_binary_conn):

    im = Image.new('RGBA', (3000, 3000), (128, 128, 128, 0))
    stream = io.BytesIO()
    im.save(stream,format='JPEG')
    binary_key = "glworb_binary:{}".format(str(uuid.uuid4()))
    stream.seek(0)
    redis_binary_conn.set(binary_key, stream.read())
    im.close()
    stream.close()
    yield binary_key
    #cleanup
    redis_conn.delete(binary_key)
    assert redis_conn.get(binary_key) is None

@pytest.fixture(scope='session')
def glworb(redis_conn,redis_binary_conn,glworb_image):

    glworb_fields = {}
    guuid = str(uuid.uuid4())
    glworb_fields['image_binary_key'] = glworb_image
    glworb_fields['method'] = "pytest"
    glworb_fields['uuid'] = guuid
    glworb_key = "glworb:{}".format(guuid)
    redis_conn.hmset(glworb_key,glworb_fields)
    yield glworb_key
    #cleanup
    redis_conn.delete(glworb_key)
    assert redis_conn.get(glworb_key) is None

@pytest.fixture(scope='session')
def context(glworb):

    glworb_context = {'uuid':glworb,
                        'key':'image_binary_key',
                        'binary_prefix':'glworb_binary:'}

    yield glworb_context

def test_img_ocr(context,glworb,redis_conn):

    assert redis_conn.hgetall(glworb)
    #write some text on image
    img_pipe.img_overlay(context ,"hello",800,100,20)
    img_pipe.img_ocr(context,"ocr_test")
    #strip any trailing newlines...
    assert redis_conn.hget(glworb,"ocr_test").strip() == "hello"

    img_pipe.img_overlay(context ,"again",900,300,20)
    img_pipe.img_ocr(context,"ocr_test")

    for word in ["hello","again"]:
        assert word in redis_conn.hget(glworb,"ocr_test")

def test_img_ocr_rectangle(context,glworb,redis_conn):

    # make a bounding box that should
    # bound the 'hello', but not the
    # 'again'

    img_pipe.img_ocr_rectangle(context,"ocr_rectangle_test",790,90,100,100)
    for word in ["hello"]:
        assert word in redis_conn.hget(glworb,"ocr_rectangle_test")
    
    for word in ["again"]:
        assert word not in redis_conn.hget(glworb,"ocr_rectangle_test")

def ztest_img_rotation(context,glworb,redis_conn):

    img_pipe.img_rotate(context,90)
    img_pipe.img_orientation(context)
    img_pipe.img_ocr(context,"ocr_test")

    # check that ocr fails on excessively rotated image
    for word in ["hello","again"]:
        assert word not in redis_conn.hget(glworb,"ocr_test")

    # rotate image back to 0 orientation
    img_pipe.img_rotate(context,-90)
    img_pipe.img_orientation(context)
    img_pipe.img_ocr(context,"ocr_test")
    for word in ["hello","again"]:
        assert word in redis_conn.hget(glworb,"ocr_test")

    # second img_orientation call fails 
    # if using rotations 67,-67
