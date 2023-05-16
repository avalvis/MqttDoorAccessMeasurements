"""
Author: Chris Knowles
Date: Apr 2020
Copyright: University of Sunderland, (c) 2020
File: iot_app.py
Version: 1.0.0
Notes: Base module for all simulated ESP32 MicroPython application code used on the CET235 IoT module, ie.
       when NOT able to utilise the prototyping hardware rig
"""
# Imports
import datetime
import threading
import uuid
from time import sleep
from tkinter import *
from machine import Pin
from mqtt_simple_ex import MQTTClientEx

# Change this to get a good size for your OLED font to fit 16 characters by 3 lines, for a 4K screen the value
# 18 is about right, for a 1080 screen 36 is about the right size, screens of other sizes should be able to
# use proportionally smaller/larger font sizes
OLED_FONT_SIZE = "18"

class RTC:
    _DEFAULT_DATE_TIME = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)

    def __init__(self):
        self.date_time = RTC._DEFAULT_DATE_TIME
        self.base_date_time = datetime.datetime.now()

    def datetime(self, date_time=None):
        if date_time:
            self.date_time = datetime.datetime(date_time[0], date_time[1], date_time[2], date_time[3], date_time[4],
                                               date_time[5], date_time[6])
            self.base_date_time = datetime.datetime.now()
            return

        date_time_delta = datetime.datetime.now() - self.base_date_time
        curr_date_time = self.date_time + date_time_delta
        date_time_tuple = curr_date_time.timetuple()

        return (date_time_tuple[0], date_time_tuple[1], date_time_tuple[2], date_time_tuple[6],
                date_time_tuple[3], date_time_tuple[4], date_time_tuple[5],
                int(str(curr_date_time).split(".")[1]) if len(str(curr_date_time).split(".")) > 1 else 0)

class Rig:
    def __init__(self):
        self.PIN_21 = Pin(21)
        self.i2c_adapter = None
        self.id = str(uuid.uuid4())

class RunStates:
    NOT_STARTED = 1
    STARTING = 2
    INITIALISING = 3
    LOOPING = 4
    DEINITIALISING = 5
    SHUTTING_DOWN = 6

class IoTApp:
    _DEFAULT_LOOP_SLEEP_TIME = 0.1

    _NTP_DEFAULT_PORT = 123
    _NTP_DEFAULT_TIMEOUT = 1
    _DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

    def __init__(self, name, has_oled_board=True, i2c_freq=None, finish_button="C",
                 start_verbose=True, apply_bst=True, debug_on=True):
        self.name = name if len(name) < 15 else name[:15]
        self.start_verbose = start_verbose

        self.rig = Rig()
        self.has_oled_board = has_oled_board
        self.i2c_freq = i2c_freq
        self.apply_bst = apply_bst
        self.debug_on = debug_on

        self.oled_background = 0
        self.oled_foreground = 1
        self.oled_on = True

        self.finished = False
        
        self.cmd_btn_a = self.btnA_handler
        self.cmd_btn_b = self.btnB_handler
        self.cmd_btn_c = self.btnC_handler

        if finish_button:
            if finish_button.upper() == "A":
                self.cmd_btn_a = self.finish_handler
            elif finish_button.upper() == "B":
                self.cmd_btn_b = self.finish_handler
            elif finish_button.upper() == "C":
                self.cmd_btn_c = self.finish_handler

        self.npm = None

        self.gui_thread = threading.Thread(target=self.run_gui)
        self.gui_thread.daemon = True
        self.root = None
        self.oled_frame = None
        self.btn_frame = None
        self.canvas_frame = None
        self.neopixel_frame = None
        self.btn_a = None
        self.btn_b = None
        self.btn_c = None
        self.oled_canvas = None
        self.neopixel_lbls = []
        self.gui_ready = False

        self.wifi = False
        self.rtc = RTC()
        self.mqtt_id = "{0}-{1}".format("".join(self.name.split()), self.rig.id)
        self.mqtt_client = None
        
        self.exit_code = 0
        self.run_state = RunStates.NOT_STARTED

    def connect_to_wifi(self, wifi_settings=None, connect_now=False):
        sleep(5)
        self.wifi = True

    def run(self):
        self.gui_thread.start()

        while not self.gui_ready:
            pass

        self.run_loop()

    def run_gui(self):
        self.root = Tk()
        self.root.iconbitmap("mcu.ico")
        self.root.title(self.name)
        self.root.protocol("WM_DELETE_WINDOW", self.finish)
        self.root.resizable(width=False, height=False)

        self.oled_frame = Frame(self.root, width=562, height=186, bg="#000000")
        self.oled_frame.grid(row=0, column=0)
        self.btn_frame = Frame(self.oled_frame, width=62, height=186, bg="#00ff00")
        self.btn_frame.grid(row=0, column=0)
        self.canvas_frame = Frame(self.oled_frame, width=500, height=186, bg="#0000ff")
        self.canvas_frame.grid(row=0, column=1)

        self.neopixel_frame = Frame(self.root, width=562, height=228, bg="#778899")
        self.neopixel_frame.grid(row=1, column=0)

        self.btn_a = Button(self.btn_frame, text="A", font=("Lucida Console", "18"), bg="#808080",
                            command=lambda: self.cmd_btn_a(pin=None))
        self.btn_a.place(x=0, y=0, width=62, height=62)
        self.btn_b = Button(self.btn_frame, text="B", font=("Lucida Console", "18"), bg="#808080",
                            command=lambda: self.cmd_btn_b(pin=None))
        self.btn_b.place(x=0, y=62, width=62, height=62)
        self.btn_c = Button(self.btn_frame, text="C", font=("Lucida Console", "18"), bg="#808080",
                            command=lambda: self.cmd_btn_c(pin=None))
        self.btn_c.place(x=0, y=124, width=62, height=62)

        self.oled_canvas = Canvas(self.canvas_frame, bg="#000000")
        self.oled_canvas.place(x=0, y=0, width=500, height=186)

        for i in range(32):
            self.neopixel_lbls.append(Label(self.neopixel_frame, text="", bg="#708090"))
            self.neopixel_lbls[i].place(x=68 + ((i % 8) * 54), y=8 + ((i // 8) * 54), width=50, height=50)

        self.gui_ready = True
        self.root.mainloop()

    def run_loop(self):
        self.run_state = RunStates.STARTING
        self.startup()
            
        self.run_state = RunStates.INITIALISING
        self.init()

        self.run_state = RunStates.LOOPING
        while not self.finished:
            self.loop()
            
        self.run_state = RunStates.DEINITIALISING
        self.deinit()
            
        self.run_state = RunStates.SHUTTING_DOWN
        self.shutdown()

        self.exit_code = self.run_state
            
        if self.run_state < RunStates.SHUTTING_DOWN:
            print("\nTerminated with code: {0} <ERROR>".format(self.exit_code))
        
    def startup(self):
        if self.oled_on:
            if self.start_verbose:
                self.oled_invert()
                self.oled_clear()
                self.oled_text(self.name, int((128 - (len(self.name) * 8)) / 2), 12)
                sleep(2)
                self.oled_invert()
            else:
                self.oled_clear()

    def finish_handler(self, pin):
        self.finish()

    def finish(self):
        self.finished = True
        
    def oled_switch_on(self):
        self.oled_on = True

    def oled_switch_off(self):
        self.oled_on = False

    def oled_toggle(self):
        self.oled_on = not self.oled_on

    def oled_invert(self):
        if self.oled_on:
            self.oled_background = 0 if self.oled_background else 1
            self.oled_foreground = 0 if self.oled_foreground else 1
            self.oled_canvas.config(bg="#000000" if not self.oled_background else "#ffffff")

    def oled_display(self):
        pass

    def oled_clear(self, colour=None):
        if self.oled_on:
            if colour:
                self.oled_canvas.config(bg="#000000" if colour == 0 else "#ffffff")
            else:
                self.oled_canvas.config(bg="#000000" if not self.oled_background else "#ffffff")

            self.oled_canvas.delete("all")

    def oled_pixel(self, x, y, colour=None):
        pass

    def oled_fill(self, x, y, w, h, colour=None):
        pass

    def oled_rect(self, x, y, w, h, colour=None):
        pass

    def oled_hline(self, x, y, w, colour=None):
        pass

    def oled_vline(self, x, y, h, colour=None):
        pass

    def oled_line(self, x0, y0, x1, y1, colour=None):
        pass

    def oled_text(self, text, x, y, colour=None):
        if self.oled_on:
            fill = "#000000" if not self.oled_foreground else "#ffffff"
            xpos = int(x * 468 / 128) + 16
            ypos = int(y * 154 / 32) + 16

            if colour:
                fill = "#000000" if colour == 0 else "#ffffff"

            self.oled_canvas.create_text(xpos, ypos, anchor="nw", fill=fill,
                                         font=("Lucida Console", OLED_FONT_SIZE),
                                         text=text)

    def oled_scroll(self, dx=0, dy=0):
        if self.oled_on:
            pass
        
    def btnA_handler(self, pin):
        pass

    def btnB_handler(self, pin):
        pass
        
    def btnC_handler(self, pin):
        pass

    def is_wifi_connected(self):
        return self.wifi
        
    def wifi_activate(self):
        self.wifi = True

    def wifi_deactivate(self):
        self.wifi = False

    def get_ntp_datetime(self, ntp_ip, ntp_port=_NTP_DEFAULT_PORT, ntp_timeout=_NTP_DEFAULT_TIMEOUT):
        if self.is_wifi_connected():
            return datetime.datetime.now()

        return None
    
    def _set_rtc(self, ntp_ip=None, ntp_port=_NTP_DEFAULT_PORT, ntp_timeout=_NTP_DEFAULT_TIMEOUT,
                 datetime=RTC._DEFAULT_DATE_TIME):
        if ntp_ip:
             t = self.get_ntp_datetime(ntp_ip, ntp_port, ntp_timeout)
             if t:
                 tt = t.timetuple()
                 tm = (tt[0], tt[1], tt[2], tt[3], tt[4], tt[5],
                       int(str(t).split(".")[1]) if len(str(t).split(".")) > 1 else 0)
                 self.rtc.datetime(tm)
                 return True

             return False

        self.rtc.datetime(datetime)
        return True
        
    def set_rtc_by_ntp(self, ntp_ip, ntp_port, ntp_timeout=_NTP_DEFAULT_TIMEOUT):
        return self._set_rtc(ntp_ip, ntp_port, ntp_timeout)
        
    def set_rtc_by_datetime(self, datetime):
        return self._set_rtc(datetime=datetime)
        
    def reset_rtc(self):
        return self._set_rtc()
    
    def register_to_mqtt(self, server, port=0, last_will=None, sub_callback=None, user=None, password=None,
                         keepalive=0, ssl=False, ssl_params={}):
        self.mqtt_client = MQTTClientEx(client_id=self.mqtt_id)

        if sub_callback:
            self.mqtt_client.msg_callback = sub_callback

        self.mqtt_client.connect(server, port, keepalive=60)

    def init(self):
        pass
        
    def loop(self):
        pass
        
    def deinit(self):
        pass
        
    def shutdown(self):
        if self.mqtt_client:
            self.mqtt_client.disconnect()

        print("\nTerminated with code: {0} <OK>".format(self.exit_code))
