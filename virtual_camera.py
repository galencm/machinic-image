# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import subprocess
import jinja2
import os
import io
import random
import redis
import consul

#render_img("image",width=3200,height=1800,zoom=-.1,focus=10,sampling=1)

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


virtual_camera_config={
    "image":"",
    "zoom": -.1,
    "aperture": .01,
    "focus":1,
    "sampling":20,
    "camera_x":.3,
    "camera_y":.5,
    "camera_jitter_x":.1,
    "camera_jitter_y":.1,
    "camera_jitter_z":0
}

virtual_camera_pov = """
//povray povtest.pov 
box { <0,0,0> <1,1,0.01>

      pigment { image_map 
                 { jpeg "{{ image }}" 
                  map_type 0 // 0=planar
                  interpolate 2 // bilinear
                 } } 
      //scale <5/7,1,1> 
      scale <0.5,1,1> 
  translate <0, 0, 0.8>
}

light_source{ <1,1,1>
              color rgb<200,200,200>
              area_light
              <5, 5, 5> <5, 5, 5>
              4,4 // numbers in directions
              adaptive 0  // 0,1,2,3...
              jitter // random softening
              translate<10, 10,  0>
            }//---- end of area_light

camera {
    perspective
    location <0,0,1.3>
    up    <0,0,3>
    right  <3,0,0>
    look_at <0,0,1.2>
    focal_point < 0, 0, {{ focus }}>  // focal   
    aperture {{ aperture }} // aperture is blur .01
    blur_samples {{ sampling }} //20     
    translate <{{ camera_x + camera_jitter_x  }},{{ camera_y + camera_jitter_y  }} , {{ zoom + camera_jitter_z  }}> //-.1 is zoom
}
"""

def render_img_from_kv(key,source_name):
    img_bytes = binary_r.get(key)
    tmp_dir = "/tmp"
    #should check extension...
    #add source_name to avoid collisons if 2+ active
    tmp_fname = "virtual_camera_input_{}.jpg".format(source_name)
    tmp_file = os.path.join(tmp_dir,tmp_fname)
    with open(tmp_file,'wb+') as f:
        f.write(img_bytes)

    img_bytes = render_img(tmp_file)
    binary_r.set(key, img_bytes)

def render_img_from_bytes():
    pass
def render_img_from_file():
    pass

def render_img(image,width=1600,height=900,zoom=None,focus=None,aperture=None,sampling=None):
    #bytes in?
    #image_key?
    pov_file_path = "/tmp"
    pov_file_name = "virtual_camera.pov"
    output_name = "virtual_camera.jpg"
    pov_file = os.path.join(pov_file_path,pov_file_name)
    output_file =  os.path.join(pov_file_path,output_name)
    virtual_camera_config['image'] = image
    for value,var_name in [(zoom,'zoom'),(focus,'focus'),(aperture,'aperture'),(sampling,'sampling')]:
        if value is not None:
            virtual_camera_config[var_name] = value
            print(virtual_camera_config[var_name],value)
    
    for jitter in ['x','y','z']:
        key = "camera_jitter_{}".format(jitter)
        virtual_camera_config[key] = random.uniform(0,virtual_camera_config[key])
        virtual_camera_config[key] *= random.choice([1, -1])

    print(virtual_camera_config)
    pov = jinja2.Environment().from_string(virtual_camera_pov).render(virtual_camera_config)

    with open(pov_file,'w+') as f:
        f.write(pov)

    #example command line call
    #povray povtest.pov -H900 -W1600 +O/tmp/foo.jpg +FJ

    subprocess.call(["povray",
                        pov_file,
                        "-H{}".format(height),
                        "-W{}".format(width),
                        "+O{}".format(output_file),
                        "+FJ",
                        "-D"
                        ])

    #slurp and return bytes
    contents = io.BytesIO
    with open(output_file,'rb') as f:
        contents = io.BytesIO(f.read())

    contents.seek(0)
    return contents.getvalue()

