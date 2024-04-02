#
# Copyright 2021 HiveMQ GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import random
import time


import paho.mqtt.client as paho
from paho import mqtt




# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)




# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, reasonCode, properties=None):
    print("Published message with mid {}.".format(mid))
# def on_publish(client, userdata, mid, properties=None):
#     """
#         Prints mid to stdout to reassure a successful publish ( used as callback for publish )
#         :param client: the client itself
#         :param userdata: userdata is set when initiating the client, here it is userdata=None
#         :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
#         :param properties: can be used in MQTTv5, but is optional
#     """
#     print("mid: " + str(mid))




# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))




# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))




# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
# client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2, client_id="client", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

otherClient = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2, client_id="otherClient", userdata=None, protocol=paho.MQTTv5)
otherClient.on_connect = on_connect


# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
otherClient.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

# set username and password
client.username_pw_set("sbulatao", "Meow1sqxst*") 
otherClient.username_pw_set("Benson", "Catson1!")

# connect to HiveMQ Cloud on port 8883 (default for MQTT)

# client.connect("f16914d0673d48389d1506f00b9613af.s1.eu.hivemq.cloud", 8883)
# otherClient.connect("f16914d0673d48389d1506f00b9613af.s1.eu.hivemq.cloud", 8883)

client.connect("afa1d2d417284e7cb702e7a83f757095.s1.eu.hivemq.cloud", 8883)
otherClient.connect("afa1d2d417284e7cb702e7a83f757095.s1.eu.hivemq.cloud", 8883)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish

otherClient.on_subscribe = on_subscribe
otherClient.on_message = on_message
otherClient.on_publish = on_publish


client.loop_start()
otherClient.loop_start()


for _ in range(5):
    client.publish("encyclopedia/temperature", random.randint(1, 10), qos=1)
    otherClient.publish("encyclopedia/light", random.randint(1, 10), qos=1)
    time.sleep(1)

client.loop_stop()
otherClient.loop_stop() 


# receives messages from the topics "encyclopedia/temperature" and "encyclopedia/light"
receivingClient = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2, client_id="receivingClient", userdata=None, protocol=paho.MQTTv5)

receivingClient.on_connect = on_connect
receivingClient.on_message = on_message

receivingClient.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

receivingClient.username_pw_set("receive", "Received1!")

receivingClient.connect("afa1d2d417284e7cb702e7a83f757095.s1.eu.hivemq.cloud", 8883)

receivingClient.on_subscribe = on_subscribe
receivingClient.on_message = on_message
receivingClient.on_publish = on_publish

receivingClient.subscribe("encyclopedia/temperature", qos=1)
receivingClient.subscribe("encyclopedia/light", qos=1)

receivingClient.loop_start()

time.sleep(5)

receivingClient.loop_stop()


# subscribe to all topics of encyclopedia by using the wildcard "#"
# client.subscribe("encyclopedia/#", qos=1)
# otherClient.subscribe("encyclopedia/#", qos=1)


# a single publish, this can also be done in loops, etc.
# client.publish("encyclopedia/temperature", payload="hot", qos=1)
# otherClient.publish("encyclopedia/temperature", payload="cold", qos=1)


# loop_forever for simplicity, here you need to stop the loop manually
# you can also use loop_start and loop_stop
# client.loop_forever()
