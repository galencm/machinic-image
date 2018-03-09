#!/usr/bin/python3

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.core.window import Window

import paho.mqtt.client as mosquitto
import time

import consul
import zerorpc

#pip3 packages required:
#kivy
#consul
#zerorpc
#paho.mqtt
#install.sh -> bork ^^ ?

def lookup(service):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'],services[k]['Port']
                return service_ip,service_port
                break
    return None,None

mqtt_ip,mqtt_port = lookup('mqtt')
cli = mosquitto.Client()
cli.connect(mqtt_ip, mqtt_port, 60)
cli.loop_start()

Builder.load_string('''
<ButtonGui>:
    Button:
        id:button
        text: " "
        on_press: root.send_values()
''')

class ButtonGui(BoxLayout):
    def __init__(self, **kwargs):
        super(ButtonGui, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == ' ':
            self.ids.button.trigger_action()
        return True

    def send_values(self,*args):
        print('/set/BYTEBOOOK/marker:capture1','-= 2')
        cli.publish('/set/BYTEBOOOK/marker:capture1','-= 2')
        time.sleep(0.01)
        print('/set/BYTEBOOOK/marker:capture2','-= 2')
        cli.publish('/set/BYTEBOOOK/marker:capture2','-= 2')
        time.sleep(0.01)

class ButtonApp(App):
    def build(self):
        return ButtonGui()



if __name__ == '__main__':
    ButtonApp().run()

