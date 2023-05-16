"""
Author: Chris Knowles
Date: Apr 2020
Copyright: University of Sunderland, (c) 2020
File: machine.py
Version: 1.0.0
Notes: Dummy machine module for all simulated ESP32 MicroPython application code used on the CET235 IoT module, ie.
       when NOT able to utilise the prototyping hardware rig
"""
class Pin:
    OUT = None
    PULL_DOWN = None
   

    def __init__(self, num):
        self.num = num
        self.mode = None
        self.pull = 0
        self.irq = 0

    def init(self, mode, pull):
        self.mode = mode
        self.pull = pull