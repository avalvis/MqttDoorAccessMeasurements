"""
Author: Chris Knowles
Date: Apr 2020
Copyright: University of Sunderland, (c) 2020
File: neopixel.py
Version: 1.0.0
Notes: NeoPixel module for all simulated ESP32 MicroPython application code used on the CET235 IoT module, ie.
       when NOT able to utilise the prototyping hardware rig
"""
class NeoPixel:
    def __init__(self, pin, num, bpp, timing, app):
        self.pin = pin
        self.num = num
        self.bpp = bpp
        self.timing = timing
        self.neopixel_lbls = app.neopixel_lbls

    def __getitem__(self, i):
        if self.neopixel_lbls:
            bg_str = self.neopixel_lbls[i]["bg"]
            return int(bg_str[1:3], 16), int(bg_str[3:5], 16), int(bg_str[5:], 16)

    def __setitem__(self, i, value):
        if self.neopixel_lbls:
            r, g, b = value

            if r == 0 and g == 0 and b == 0:
                r = 112
                g = 128
                b = 144

            self.neopixel_lbls[i].config(bg="#{0}{1}{2}".format("%02x" % r, "%02x" % g, "%02x" % b))

    def fill(self, colour):
        if self.neopixel_lbls:
            for i in range(self.num):
                self[i] = colour

    def write(self):
        pass
