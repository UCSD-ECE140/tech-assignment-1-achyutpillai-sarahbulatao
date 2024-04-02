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
import time
import random

import paho.mqtt.client as paho
from paho import mqtt
import matplotlib.pyplot as plt




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
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))




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


tempData = []

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    tempData.append(msg.payload.decode('utf-8'))



user = "apillai"
pswrd = "apillai2024UCSD"
url = "f16914d0673d48389d1506f00b9613af.s1.eu.hivemq.cloud"
port = 8883

# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
pubClient1 = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="publisher1", userdata=None, protocol=paho.MQTTv5)
pubClient1.on_connect = on_connect
pubClient1.on_publish = on_publish
# enable TLS for secure connection
pubClient1.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
pubClient1.username_pw_set(user, pswrd)
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
pubClient1.connect(url, port)

pubClient2 = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="publisher2", userdata=None, protocol=paho.MQTTv5)
pubClient2.on_connect = on_connect
pubClient2.on_publish = on_publish
# enable TLS for secure connection
pubClient2.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
pubClient2.username_pw_set(user, pswrd)
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
pubClient2.connect(url, port)


subClient = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="subscriber", userdata=None, protocol=paho.MQTTv5)
subClient.on_connect = on_connect
subClient.on_subscribe = on_subscribe
subClient.on_message = on_message
# enable TLS for secure connection
subClient.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
subClient.username_pw_set(user, pswrd)
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
subClient.connect(url, port)


# subscribe to temperature topics of encyclopedia by using /temperature
subClient.subscribe("encyclopedia/temperature", qos=1)
time.sleep(1)
subClient.loop_start()

# loop for publishing data
for i in range(10): 
    randtemp1 = random.randint(1, 100) # random int between 1 and 100
    randtemp2 = random.randint(1, 100) # random int between 1 and 100
    pubClient1.publish("encyclopedia/temperature", payload=randtemp1, qos=1)
    time.sleep(0.01) # delay so that first client can send without interference
    pubClient2.publish("encyclopedia/temperature", payload=randtemp2, qos=1)
    time.sleep(3) # publishes data once every 3 seconds
    

# disconnects all clients and ends loop
pubClient1.disconnect()
pubClient2.disconnect()
subClient.loop_stop()
subClient.disconnect()

#data from subscriber client
tempData = [int(x) for x in tempData]
client1Data = tempData[::2]
client2Data = tempData[1::2]
print("All subscribed data on encyclopedia/temperature: ", tempData) #all data subscribed from topic
print("Data from Client 1: ", client1Data) # data published from client1
print("Data from Client 2: ", client2Data) # data published from client2

plt.figure(1)
plt.plot(client1Data, label='Client 1 Data')
plt.plot(client2Data, label='Client 2 Data')
plt.legend()
plt.title('Random numbers published to and subscribed from Broker')
plt.show()