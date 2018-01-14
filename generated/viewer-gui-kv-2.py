
#!/usr/bin/python3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.clock import mainthread
import threading
from kivy.uix.label import Label
from kivy.core.window import Window

import redis
import time
import io
import textwrap

import consul
import zerorpc
#https://github.com/kivy/kivy/wiki/Working-with-Python-threads-inside-a-Kivy-application
#https://github.com/kivy/kivy/issues/684

def lookup(service):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'],services[k]['Port']
                return service_ip,service_port
                break
    return None,None

def rpc(func,*args):
    rip,rport = lookup('zerorpc-tools')
    zc = zerorpc.Client()
    zc.connect("tcp://{}:{}".format(rip,rport))
    result = zc(func,*args)
    return result


rs_ip,rs_port = lookup('redis')
r = redis.StrictRedis(host=rs_ip, port=str(rs_port),decode_responses=True)
binary_r = redis.StrictRedis(host=rs_ip, port=str(rs_port))

# Builder.load_string("""
# <Viewer>:
#     orientation: 'vertical'

# """)

class ClickableImage(Image):
    def __init__(self, **kwargs):
        super(ClickableImage, self).__init__(**kwargs)
        self.selections=[]

    def on_touch_up(self, touch):
        print(touch.button)
        if touch.button == 'right':
            p = touch.pos
            o = touch.opos
            s = min(p[0],o[0]), min(p[1],o[1]), abs(p[0]-o[0]), abs(p[1]-o[1])
            s = min(p[0],o[0]), min(p[1],o[1]), abs(p[0]-o[0]), abs(p[1]-o[1])
            w  = s[2]
            h  = s[3]
            sx = s[0]
            sy = s[1]
            if abs(w) > 5 and abs(h) >5:
                if self.collide_point(touch.pos[0],touch.pos[1]):
                    #self.add_widget(Selection(pos=(sx,sy),size=(w, h)))
                    #self.canvas.add(Rectangle(pos=(sx,sy),size=(w, h),color=(155,155,155,0.5)))

                    #because getting resized image no knowldge of original geometry
                    #for scaling...

                    print("added widget for ",self)
                    print(self.texture_size,self.norm_image_size,self.size)
                    # width_scale  = self.texture_size[0] / self.norm_image_size[0]
                    # height_scale = self.texture_size[1] / self.norm_image_size[1]
                    x = touch.opos[0]
                    y = abs(touch.opos[1]-self.norm_image_size[1])
                    w = touch.pos[0]-touch.opos[0]
                    h =abs(touch.pos[1]-self.norm_image_size[1])-abs(touch.opos[1]-self.norm_image_size[1])

                    print(x,y,w,h)
                    px = x / self.norm_image_size[0]
                    py = y / self.norm_image_size[1]
                    pw = w / self.norm_image_size[0]
                    ph = h / self.norm_image_size[1]

                    # print(Window.size)
                    print(px,py,pw,ph)
                    print(px*self.norm_image_size[0],py*self.norm_image_size[1],pw*self.norm_image_size[0],ph*self.norm_image_size[1])
                    percents= "{} {} {} {}".format(px,py,pw,ph)

                    self.selections.append("pcropto {} crop_binary_key".format(percents))

                    config = {}
                    config['selections'] = self.selections

                    stanza = textwrap.dedent('''
                    pipe thing  {
                        start stanza: starti
                        #rotate?: rotate  90
                        {% for s in selections %}
                        {{ s }}
                        {% endfor %}
                        endi
                        #pipe ocrleft _ crop_binary_key
                    }
                    ''')
                    stanza = jinja2.Environment().from_string(stanza).render(config)
        return super().on_touch_up(touch)


class Viewer(BoxLayout):
    stop = threading.Event()

    def __init__(self, *args,**kwargs):
        super(Viewer, self).__init__()
        self.orientation = 'vertical'
        self.img = None
        self.text = Label(text="",size_hint_y=None,size_hint_x=1)
        img = ClickableImage(size_hint_y=1,size_hint_x=1,allow_stretch=True,keep_ratio=True)
        img.size=(600,600)
        print(img.pos)
        print(img.size)
        # img.texture = CoreImage(data,ext="jpg").texture
        self.img = img
        self.add_widget(self.text)
        self.add_widget(img)
        #threading.Thread(target=self.listen_for_subscriptions,args=(('capture1'),)).start()

        args = (
        'capture3',
        )

        threading.Thread(target=self.listen_for_subscriptions,args=(args,)).start()


    def listen_for_subscriptions(self,subscriptions):
        pubsub = r.pubsub()
        print("subscribing to {}".format(subscriptions))
        pubsub.subscribe(subscriptions)
        #uses a lot of cpu
        # while True:
        #     message = pubsub.get_message()
        #     if message:
        #         print(message)
        #         self.text.text=str(message['data'])
        #         time.sleep(0.01)  # be nice to the system :)

        #     if self.stop.is_set():
        #         return

        for message in pubsub.listen():
            print(message)
            self.text.text="{} -> {}".format(message['channel'],message['data'])
            time.sleep(1)
            self.load_glworb(str(message['data']))

    @mainthread
    def load_glworb(self,glworb_uuid):
        try:
            glworb = r.hgetall("glworb:"+glworb_uuid)
            binary = binary_r.get(glworb['image_binary_key'])
            if binary:
                data = io.BytesIO()
                data = io.BytesIO(binary)
                data.seek(0)
                self.img.texture = CoreImage(data,ext="jpg").texture
                self.img.size = self.img.texture_size
                print("setting img",self.img.size)
                #Window.size = self.img.texture_size
        except Exception as ex:
            print("exception? ",ex)

class ViewerApp(App):
    def build(self):
        Window.size = 1200,1000
        return Viewer()

    def on_stop(self):
        self.root.stop.set()

if __name__ == '__main__':
    ViewerApp().run()

