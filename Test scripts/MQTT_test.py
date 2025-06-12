import paho.mqtt.client as paho
from paho import mqtt
import os
from dotenv import load_dotenv
load_dotenv()
mqtt_host, mqtt_port, mqtt_username, mqtt_password = os.getenv("mqtt_host"), int(os.getenv("mqtt_port")), os.getenv("mqtt_username"), os.getenv("mqtt_password")

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.enable_logger()
client.on_connect = on_connect
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(mqtt_username, mqtt_password)
client.connect(mqtt_host, mqtt_port)
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish
client.subscribe("encyclopedia/#", qos=1)
client.publish("encyclopedia/temperature", payload="hot", qos=1)
client.loop_forever()