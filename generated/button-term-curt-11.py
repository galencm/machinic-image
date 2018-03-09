
#!/usr/bin/python3
import paho.mqtt.client as mosquitto
import sys
import time
from curtsies import Input

import consul
import zerorpc

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

print("Keybindings:")
print(" ' ':")
print("    -= 2 to /set/BYTEBOOOK/marker:capture1")
print("    -= 2 to /set/BYTEBOOOK/marker:capture2")
print("Press ESC or Ctrl-d to exit")
print("")
print("waiting for input...")
with Input(keynames='curtsies') as input_generator:
    for e in Input():
        if e in (u'<ESC>', u'<Ctrl-d>'):
            break
        elif e == ' ':
            print("{} pressed".format(e))
            cli.publish('/set/BYTEBOOOK/marker:capture1','-= 2')
            time.sleep(0.01)
            cli.publish('/set/BYTEBOOOK/marker:capture2','-= 2')
            time.sleep(0.01)

        else:
            #print(e)
            pass




