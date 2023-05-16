"""
Author: Chris Knowles
Date: Apr 2020
Copyright: University of Sunderland, (c) 2020
File: mqtt_simple_ex.py
Version: 1.0.0
Notes: Module for simulated MQTT client for use with simulated ESP32 MicroPython application code, this
       uses the Paho MQTT package
"""
# Imports
import paho.mqtt.client as MQTTPaho

class MQTTClientEx(MQTTPaho.Client):
    def __init__(self, client_id):
        super().__init__(client_id)
        self.msg_callback = None

    def check_msg(self):
        self.loop()

    def on_message(self, mqttc, obj, msg):
        if self.msg_callback:
            self.msg_callback(msg.topic, msg.payload)
