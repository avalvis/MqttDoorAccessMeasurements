# File: mqtt_pub_simulated.py
# Author: Antonis Valvis
# Date: May 2023

# Imports
from time import sleep
from machine import Pin
from neopixel import NeoPixel
from iot_app import IoTApp
from bme680 import BME680, OS_2X, OS_4X, OS_8X, FILTER_SIZE_3, ENABLE_GAS_MEAS

import pandas as pd
from datetime import datetime
import time
import threading


class MainApp(IoTApp):
    """
    This is your custom class that is instantiated as the main app object instance,
    it inherits from the supplied IoTApp class found in the libs/iot_app.py module
    which is copied when the Huzzah32 is prepared.
    This IoTApp in turn encapsulates an instance of the ProtoRig class (which is
    found in libs/proto_rig.py) and exposes a number of properties of this ProtoRig
    instance so you do not have to do this yourself.
    Also, the IoTApp provides an execution loop that can be started by calling the
    run() method of the IoTApp class (which is of course inherited into your custom
    app class). All you have to do is define your program by providing implementations
    of the init(), loop() and deinit() methods.
    Looping of your program can be controlled using the finished flag property of
    your custom class.
    """
    AP_SSID = "DCETLocalVOIP"
    AP_PSWD = ""
    AP_TOUT = 5000
    MQTT_ADDR = "broker.hivemq.com"  # DNS of the public MQTT server
    MQTT_PORT = 1883
    NTP_ADDR = "13.86.101.172"  # IP address of time.windows.com, NTP server at Microsoft
    NTP_PORT = 123  # NTP server port number (by default this is port 123)

    # Some notes on the Hive MQTT public broker: be aware that the MQTT broker used (which
    # is located at "broker.hivemq.com") is a public broker and any topic you publish on
    # will be able to be subscribed to by anyone connected to this broker, the URL for the
    # Hive MQTT public broker web site is:-
    #
    #       https://www.hivemq.com/public-mqtt-broker/
    #
    # There are a few issues to address when using this broker:-
    # 1. It is public, do not use it for sensitive information
    # 2. You need to use unique topic names to ensure you do not clash with existing topics
    #    published to on the broker, this is almost impossible to ensure since you cannot
    #    access the topics being published, however, you should be able to come up with a
    #    pseudo-unique topic name, maybe use the same as below but change the "-00" part
    #    to a number associated with yourself, it is suggested that you look down the list
    #    of people on the CET235 module Canvas entry, count down to your name and use that
    #    as your unique number, so the 8th name would be "-08" and the twentieth name would
    #    be "-20" for instance, hopefully this will prevent clashes with topic names as you
    #    work on your solutions along side all the other students on the module
    # 3. Because the Hive MQTT public broker is beyond our control, it may disappear for
    #    shutdown and maintenance, it has not done in the time it has been used but this
    #    could happen (hopefully for short periods only), that bridge will be crossed if
    #    it should happen
    MQTT_TOPIC_1 = "uos/cet235-bi10sg/door/enter"  # Topic name for time entered
    MQTT_TOPIC_2 = "uos/cet235-bi10sg/door/exit"  # Topic name for time exited
    MQTT_TOPIC_3 = "uos/cet235-bi10sg/door/user"  # Topic name for user code

    def init(self):

        """
        initialize measurements
        """
        # Initialise the BME680 driver instance with the I2C bus from the ProtoRig instance and
        # with the I2C address where the BME680 device is found on the shared I2C bus (0x76 hex,
        # 118 decimal), note: the I2C object is encapsulated in an I2CAdapter object, you do
        # not need to know anything further just that some device drivers require the I2C to be
        # provided in this way
        self.sensor_bme680 = BME680(i2c=self.rig.i2c_adapter, i2c_addr=0x76)

        # These calibration data can safely be commented out if desired, the oversampling settings
        # can be tweaked to change the balance between accuracy and noise in the data, the values
        # provided are a good balance and are the recommended settings for your work
        self.sensor_bme680.set_humidity_oversample(OS_2X)
        self.sensor_bme680.set_pressure_oversample(OS_4X)
        self.sensor_bme680.set_temperature_oversample(OS_8X)
        self.sensor_bme680.set_filter(FILTER_SIZE_3)

        # This specifies that you wish to use the VOC gas measuring sensor, use DISABLE_GAS_MEAS
        # disable the VOC gas sensor (remember to import this value if you need it)
        self.sensor_bme680.set_gas_status(ENABLE_GAS_MEAS)

        # Up to 10 heater profiles can be configured, each with their own temperature and duration
        # eg.
        #    sensor.set_gas_heater_profile(200, 150, nb_profile = 1)  # Set profile 1
        #    sensor.select_gas_heater_profile(1)  # Select profile 1
        # You are not using a custom profile here, just the default profile and using direct values
        # for the heater used on the gas sensor, the values provided are a good balance and are the
        # recommended settings for your work
        self.sensor_bme680.set_gas_heater_temperature(320)
        self.sensor_bme680.set_gas_heater_duration(150)
        self.sensor_bme680.select_gas_heater_profile(0)  # Default to settings given above

        # Pin 21 is connected to the NeoPixel FeatherWing via a jumper wire, note: the
        # instance of pin 21 is taken from the property ProtoRig instance
        self.neopixel_pin = self.rig.PIN_21

        # Set pin 21 to be a digital output pin that is initially pulled down (off)
        self.neopixel_pin.init(mode=Pin.OUT, pull=Pin.PULL_DOWN)

        # Instantiate a NeoPixel object with the required NeoPixel FeatherWing pin,
        # number of NeoPixels (4 x 8 = 32), bytes used for colour of each NeoPixel
        # and a timing value (keep as 1)
        self.npm = NeoPixel(self.neopixel_pin, 32, bpp=3, timing=1, app=self)

        # Colours are set using a RGB channel tuple value with first element of the
        # tuple the red value (0..255), the second element the green value and the
        # third element the blue value, note: "black" uses tuple value (0, 0, 0)
        # whilst bright white use tuple value (255, 255, 255), "black" is actually
        # all NeoPixels switched off
        #
        # *****************************************************************************
        # CAUTION - BRIGHT WHITE IS VERY BRIGHT, DO NOT LOOK DIRECTLY AT THIS FOR ANY
        # LENGTH OF TIME, PLEASE USE MUTED VALUES FOR COLOURS, USE A MAXIMUM OF 10 FOR
        # EACH COLOUR CHANNEL (THIS IS STILL QUITE BRIGHT)
        # *****************************************************************************
        #
        # Each NeoPixel can be changed using the [] indexing from 0..31, this splits
        # the matrix into 4 rows of 8 NeoPixels with the following indices:-
        #
        #      0  1  2  3  4  5  6  7
        #      8  9 10 11 12 13 14 15
        #     16 17 18 19 20 21 22 23
        #     24 25 26 27 28 29 30 31
        #
        # Note: index 0 is the NeoPixel furthest to the top left under the FeatherWing
        # text on the NeoPixel FeatherWing board
        #

        # Use NeoPixel.fill() method sets all NeoPixels to off, uses the npm property from this
        # object instance
        self.npm.fill((0, 0, 0))
        # You must use NeoPixel.write() method when you want the matrix to change
        self.npm.write()

        self.time_str = ""

        self.target_indicator = "N"
        self.temperature_target = None
        self.humidity_target = None
        self.temperature_str = ""


        #initialize connection with wifi
        self.wifi_msg = "No WIFI"
        connect_count = 0
        # Try to connect to WiFi 5 times, if unsuccessful then only try again if button A on
        # the OLED is pressed
        while connect_count < 5 and not self.is_wifi_connected():
            self.oled_clear()
            self.wifi_msg = "Connect WIFI:{0}".format(connect_count + 1)
            self.oled_text(self.wifi_msg, 0, 0)
            self.oled_display()
            self.connect_to_wifi(wifi_settings=(self.AP_SSID, self.AP_PSWD, True, self.AP_TOUT))
            connect_count += 1

        if self.is_wifi_connected():
            self.wifi_msg = "WIFI"
            # Register to the MQTT broker
            self.register_to_mqtt(server=self.MQTT_ADDR, port=self.MQTT_PORT)
        else:
            self.oled_clear()
            self.wifi_msg = "No WIFI"
            self.oled_text(self.wifi_msg, 0, 0)
            self.oled_display()
            sleep(2)

        # initialize ntp server settings to get the time from the internet

        self.ntp_msg = "No NTP - RTC bad"
        connect_count = 0
        # Try to connect to WiFi 5 times
        while connect_count < 5 and not self.is_wifi_connected():
            self.oled_clear()
            self.oled_text("Connect WIFI:{0}".format(connect_count + 1), 0, 0)
            self.oled_display()
            self.connect_to_wifi(wifi_settings=(self.AP_SSID, self.AP_PSWD, True, self.AP_TOUT))
            connect_count += 1

        if self.is_wifi_connected():
            self.ntp_msg = "NTP - RTC good"
            # Contact the NTP server and update the RTC with the correct date and time as
            # provided by this server, the method set_rtc_by_ntp() is a convenience method
            # that is implemented in the IoTApp class and therefore inherited by your own
            # application class
            self.set_rtc_by_ntp(ntp_ip=self.NTP_ADDR, ntp_port=self.NTP_PORT)

        else:
            # In this case the NTP server was not able to be contacted so the RTC is not
            # correct
            self.oled_clear()
            self.oled_text("No WIFI", 0, 0)
            self.oled_display()
            sleep(4)

        # initialize the door opening

        # List of valid user codes
        valid_user_codes = ["MJ235AA", "CK523BB"]

        # Track whether the controlled area is currently occupied
        occupied = False
        current_user = None

        self.valid_user_codes = valid_user_codes
        self.occupied = occupied
        self.current_user = current_user

    # The function that will run in a separate thread
    # This helps showing current time all the time even when waiting for an input
    def display_time(self):
        while True:
            date_ntp = self.rtc.datetime()
            ct = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(date_ntp[2], date_ntp[1], date_ntp[0],
                                                                    date_ntp[4], date_ntp[5], date_ntp[6])

            output_time = "Time: {0}".format(ct)

            self.oled_clear()

            self.oled_text(output_time, 0, 6)
            self.oled_text(self.output, 0, 12)
            time.sleep(1)

    def loop(self):

        # Create and start the time thread
        time_thread = threading.Thread(target=self.display_time, daemon=True)
        time_thread.start()

        #get the door opening values
        valid_user_codes = self.valid_user_codes
        occupied = self.occupied
        current_user = self.current_user

        while True:

            if occupied:
                occupant_str = "Occupant: {0}".format(current_user)
                output = occupant_str
            else:
                output = "No Current Occupant"

            self.output = output

            user_choice = input("Do you want to enter or exit? Type 'enter' or 'exit': ")
            user_code = input("Please enter your user code: ")

            if user_code in valid_user_codes:
                if user_choice == 'enter':
                    if not occupied:
                        # If the controlled area is not occupied, grant access and publish a message
                        print("Access Allowed")
                        self.mqtt_client.publish(self.MQTT_TOPIC_3, user_code)
                        self.npm.fill((255, 0, 0))  # Red light signifies occupancy
                        self.npm.write()
                        # self.oled_clear()

                        occupied = True
                        current_user = user_code

                        date_ntp_enter = self.rtc.datetime()
                        ct_enter = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(date_ntp_enter[2],
                                                                                      date_ntp_enter[1],
                                                                                      date_ntp_enter[0],
                                                                                      date_ntp_enter[4],
                                                                                      date_ntp_enter[5],
                                                                                      date_ntp_enter[6])

                        print(f"Access granted to {user_code} at {ct_enter}.")
                        self.mqtt_client.publish(self.MQTT_TOPIC_1, ct_enter)

                    elif user_code == current_user:
                        print(f"Access denied. You are already inside.")

                    else:
                        # If the controlled area is occupied by another user, deny access
                        print(f"Access denied to {user_code}. Controlled area is currently occupied.")

                elif user_choice == 'exit':
                    if user_code == current_user:
                        # If the controlled area is occupied by the same user, end the access period and publish a message
                        occupied = False

                        date_ntp_exit = self.rtc.datetime()
                        ct_exit = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(date_ntp_exit[2], date_ntp_exit[1],
                                                                                     date_ntp_exit[0],
                                                                                     date_ntp_exit[4], date_ntp_exit[5],
                                                                                     date_ntp_exit[6])

                        print(f"Access period ended for {user_code} at {ct_exit}.")

                        self.mqtt_client.publish(self.MQTT_TOPIC_2, ct_exit)
                        current_user = None

                        self.npm.fill((0, 255, 0))  # Green light signifies no occupancy
                        self.npm.write()
                        self.oled_clear()

                    else:
                        print(f"Access denied to {user_code}. You are not the current occupant.")

                else:
                    print("Invalid choice. Please type 'enter' or 'exit'.")

            else:
                print("Invalid user code.")

            # Wait for a short period before the next iteration
            time.sleep(1)

    def deinit(self):
        """
        The deinit() method is called after the loop() method has finished, is designed
        to contain the part of the program that closes down and cleans up app specific
        properties, for instance shutting down sensor devices. It can also be used to
        display final information on output devices (such as the OLED FeatherWing)
        """
        # In this specific implementation the deint() method does nothing, only included
        # for completeness sake
        pass

    def btnA_handler(self, pin):
        """
        This method overrides the inherited btnA_handler method which is provided by
        the inherited IoTApp class, you do not need to set up the pin used for the
        OLED FeatherWing button as this is done in the IoTApp class already for you
        """
        self.target_indicator = "H"
        self.temperature_target = 35.0

    def btnB_handler(self, pin):
        """
        This method overrides the inherited btnB_handler method which is provided by
        the inherited IoTApp class, you do not need to set up the pin used for the
        OLED FeatherWing button as this is done in the IoTApp class already for you
        """
        self.target_indicator = "L"
        self.temperature_target = 20.0

    def btnC_handler(self, pin):
        """
        This method overrides the inherited btnA_handler method which is provided by
        the inherited IoTApp class, you do not need to set up the pin used for the
        OLED FeatherWing button as this is done in the IoTApp class already for you
        """
        self.target_indicator = "N"
        self.temperature_target = None


# Program entrance function
def main():
    """
    Main function, this instantiates an instance fo your custom class (where you can
    initialise your custom class instance to how you wish your app to operate) and
    then executes the run() method to get the app running
    """
    # Instantiate an instance of the custom IoTApp class (MainApp class) with the following
    # property values:-
    #
    #   name: "MQTT Pub Sim", this should be a maximum of 14 characters else it is truncated
    #   has_oled_board: set to True as you are using the OLED FeatherWing
    #   finish_button: set to None which designates Button C on the OLED FeatherWing as not
    #                  used so it can be programmed
    #   start_verbose: set to True and the OLED FeatherWing will display a message as it
    #                  starts up the program
    #
    app = MainApp(name="MQTT Pub Sim", has_oled_board=True, finish_button=None, start_verbose=True)

    # Run the app
    app.run()


# Invoke main() program entrance
if __name__ == "__main__":
    # execute only if run as a script
    main()
