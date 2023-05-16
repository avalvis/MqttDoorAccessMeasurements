# File: mqtt_sub_simulated.py
# Author: Antonis Valvis
# Date: May 2023


# Imports
import random
import csv
from time import sleep
from machine import Pin
from neopixel import NeoPixel
from iot_app import IoTApp
from bme680 import BME680, OS_2X, OS_4X, OS_8X, FILTER_SIZE_3, ENABLE_GAS_MEAS

import pandas as pd
from datetime import datetime
import os.path
        
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
        initialize wifi connection
        """
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
            # Register with the MQTT broker and link the method mqtt_callback() as the callback
            # when messages are recieved
            self.register_to_mqtt(server=self.MQTT_ADDR, port=self.MQTT_PORT,
                                  sub_callback=self.mqtt_callback)

            # Subscribe to topic about time entered
            self.mqtt_client.subscribe(self.MQTT_TOPIC_1)

            # Subscribe to topic about time exited
            self.mqtt_client.subscribe(self.MQTT_TOPIC_2)

            # Subscribe to topic about user code
            self.mqtt_client.subscribe(self.MQTT_TOPIC_3)

            self.oled_clear()
            self.oled_display()
        else:
            self.wifi_msg = "No WIFI"
            self.oled_clear()
            self.oled_display()

        # These will hold the most recently received temperatures and times from the relevant MQTT
        # subscriptions, initially a "--------" string until a value for each is received
        self.time_enter_str = "--------"
        self.time_exit_str= "--------"

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

        """
        Here I initialize the measurements       
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
        # THE ONLY DIFFERENCE IS app=self addition. It tells to look in the code,
        # rather than the real HW
        self.npm = NeoPixel(self.neopixel_pin, 32, bpp=3, timing=1, app=self)


        self.npm.fill((0, 0, 0))

        self.npm.write()

        self.target_indicator = "N"
        self.temperature_target = None
        self.pressure_target = None
        self.humidity_target = None
        self.gas_resistance_target = None

        # Here I check if this is the first recorded access period.
        # If I have already recoded previous access periods, a csv file has been already created
        # So I just load it
        if os.path.isfile('bme680_data.csv'):
            df = pd.read_csv('bme680_data.csv')

            # Then I append an empty row to my data frame which indicates the start of a new access periods
            # This way I can simply keep track of the number of access periods recorded
            #df = df._append(pd.Series(), ignore_index=True)

            # Then I write my dataframe to a csv file
            df.to_csv('bme680_data.csv', index=False)
        else:
            print('No previous access period recorded.')

        # Setting up the  access period class. With the helo of that class I can create an access period, start it and stop it.
        class AccessPeriod:
            def __init__(self):
                self.active = False
                self.start_time = None
                self.elapsed_time = None
                self.end_time = None
                self.user_code = None

        # Define empty pandas dataframe to store temperature and humidity data
        data_log = pd.DataFrame(columns=['User', 'Timestamp', 'Temperature (C)', 'Humidity (%)'])
        self.data_log = data_log

        # create an instance of the access period class, and also start the current access period
        access_period = AccessPeriod()
        self.access_period = access_period

        self.time_enter_str = "--------"
        self.time_exit_str = "--------"

        self.just_ended = False #for when access period ends

    def loop(self):


        """
        The loop() method is called after the init() method and is designed to contain
        the part of the program which continues to execute until the finished property
        is set to True (which in the case of this implementation is when Button C on
        the OLED FeatherWing is pressed)
        """
        self.oled_clear()

        #taking measurements

        # If sensor readings are available, read them once a second or so
        if self.sensor_bme680.get_sensor_data(temperature_target=self.temperature_target,
                                              pressure_target=self.pressure_target,
                                              humidity_target=self.humidity_target,
                                              gas_resistance_target=self.gas_resistance_target):
            tm_reading = self.sensor_bme680.data.temperature  # In degrees Celsius
            pa_reading = self.sensor_bme680.data.pressure  # In Hectopascals (1 hPa = 100 Pascals)
            rh_reading = self.sensor_bme680.data.humidity  # As a percentage (ie. relative humidity)

            # The VOC gas sensor needs a short time (around 20-30 milliseconds) to warm up,
            # until then output a message to state it is stablising, the gas reading is provided in
            # electrical resistance (ohms) measured across the sensor and is not very useful on its own,
            # it needs to be compared to previous readings to make any use of this value, it is included
            # here to show how to read it but you will not be directly using this data in the future
            if self.sensor_bme680.data.heat_stable:
                gr_reading = self.sensor_bme680.data.gas_resistance
            else:
                gr_reading = None

            # A visual output of the current date, time, temperature and relative humidity readings
            # whether there is a currently active access period or not.

            #Getting time from ntp server
            date_ntp = self.rtc.datetime()
            ct = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(date_ntp[2], date_ntp[1], date_ntp[0],
                                                                    date_ntp[4], date_ntp[5], date_ntp[6])

            #visual outputs at oled screen
            self.oled_text(("Date/Time: " + ct), 0, 0)
            self.oled_text("Temperature: {0:.2f}c".format(tm_reading), 0, 10)
            self.oled_text("Relative Humidity: {0:.2f}%rh".format(rh_reading), 0, 20)
            # Also, a visual output of the approximate number of seconds the currently active access period has lasted.

            if self.access_period.active:
                duration = datetime.now() - self.access_period.start_time
                duration_str = str(duration)
                self.oled_text(self.access_period.user_code + " entered: " + duration_str, 0, 30)
            else:
                self.oled_text("Access Period: -", 0, 30)

            self.oled_display()

            # Display current target indicator on OLED
            self.oled_text(self.target_indicator, 120, 20)

            # Change the colours of the NeoPixels on the NeoPixel FeatherWing to match the current
            # temperature reading from the BME680 sensor, make this quite sensitive since there
            # will only be a small change in temperature, make all blue NeoPixels equivalent to
            # a reading of 20c and all red NeoPixels equivalent to a reading of 35c, then set the
            # colour channels using the actual read temperature
            min_tm = 20
            max_tm = 35

            # Clamp actual read temperature to minimum and maximum temperature range
            if tm_reading < min_tm:
                tm_reading = min_tm
            elif tm_reading > max_tm:
                tm_reading = max_tm

            # Calculate the factor the actual temperature reading contributes to the colour channels
            tm_factor = (tm_reading - min_tm) / (max_tm - min_tm)

            # Blue channel is maximum (255) when actual temperature is at 20c, make sure this value
            # ends up an integer
            blue_channel = int(255 * (1 - tm_factor))

            # Red channel is maximum (255) when actual temperature is at 35c, make sure this value
            # ends up an integer
            red_channel = int(255 * tm_factor)

            # Use NeoPixel.fill() method to set NeoPixels to the calculated colour channels, note: the
            # green colour channel is not used (it remains 0)
            # self.npm.fill((red_channel, 0, blue_channel))
            # You must use NeoPixel.write() method when you want the matrix to change
            self.npm.write()

        # Display the sensor readings on the OLED screen
        self.oled_display()

        # access period and data log were initialized at the init method but we also need them at the loop method
        access_period = self.access_period
        data_log = self.data_log



        if self.is_wifi_connected():
            # Check for any messages received from the MQTT broker, note this is a non-blocking
            # operation so if no messages are currently present the loop() method continues
            self.mqtt_client.check_msg()



        # Check if access period is active
        if access_period.active:

            print('-------------------------------------------')

            # Log data only during active access period
            date_ntp = self.rtc.datetime()
            ct = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(date_ntp[2], date_ntp[1], date_ntp[0],
                                                                    date_ntp[4], date_ntp[5], date_ntp[6])
            data_log = data_log._append(
                {'User': self.access_period.user_code,'Timestamp': ct, 'Temperature (C)': tm_reading, 'Humidity (%)': rh_reading},
                ignore_index=True)

            # Get elapsed time for current access period
            access_period.elapsed_time = (datetime.now() - access_period.start_time).total_seconds()

            # Update LED based on elapsed time
            if access_period.elapsed_time <= 5:
                self.npm.fill((0, 255, 0))  # Green LED
            elif access_period.elapsed_time <= 10:
                self.npm.fill((255, 191, 0))  # Amber LED
            else:
                self.npm.fill((255, 0, 0))  # Red LED

            # Display date, time, temperature and humidity on console

            #Getting time from ntp server
            date_ntp = self.rtc.datetime()
            ct = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(date_ntp[2], date_ntp[1], date_ntp[0],
                                                                    date_ntp[4], date_ntp[5], date_ntp[6])
            print("Time: " + ct)
            print("Temperature: {:.2f} C".format(tm_reading))
            print("Humidity: {:.2f} %".format(rh_reading))

            # Set up the loop to run every second
            #sleep(1)

            # Write data_log to CSV file only when the access period is active
            file_path = 'bme680_data.csv'
            if os.path.isfile(file_path):
                # Load existing CSV file and append new data
                df = pd.read_csv(file_path)
                df = df._append(data_log, ignore_index=True)
            else:
                # Create a pandas dataframe with the current data_log
                df = pd.DataFrame(data_log)
            # Write data_log to CSV file
            df.to_csv(file_path, index=False)

            # Clear the data_log for the next access period
            self.data_log = pd.DataFrame(columns=['User', 'Timestamp', 'Temperature (C)', 'Humidity (%)'])

            # Update the access period of the current instance of the main class with latest data
            self.access_period = access_period


        else:
            # Reset LED to off
            self.npm.fill((0, 0, 0))

            if self.just_ended:
                file_path = 'bme680_data.csv'
                if os.path.isfile(file_path):
                    df = pd.read_csv(file_path)
                    df = df._append(pd.Series(), ignore_index=True)
                    df.to_csv(file_path, index=False)
                self.just_ended = False  # Reset the flag


    def deinit(self):
        """
        The deinit() method is called after the loop() method has finished, is designed
        to contain the part of the program that closes down and cleans up app specific
        properties, for instance shutting down sensor devices. It can also be used to
        display final information on output devices (such as the OLED FeatherWing)
        """
        # Make sure the NeoPixel matrix is displaying black colour
        self.npm.fill((0, 0, 0))
        self.npm.write()

        sleep(2)

    # To gracefully stop and shut down the run of my prototype,
    # I define this method that sets the finished flag of iotapp class to True,
    # which will cause the main loop  method to exit.
    def finish(self):
        self.finished = True

    def mqtt_callback(self, topic, msg):
        # """
        # MQTT callback method, note how the topic is checked to determine how the received
        # message from the MQTT broker should be handled, you could also base the operation
        # of this callback method on the value of the received message, either way is
        # acceptable
        # """
        # # Note: msg is a list of bytes so you need to convert these into a proper string
        # # using the .decode("utf-8") method
        # if topic == self.MQTT_TOPIC_1:
        #     self.time_enter_str = str(msg.decode("utf-8"))
        #
        # if topic == self.MQTT_TOPIC_2:
        #     self.time_exit_str = str(msg.decode('utf-8'))


        """
        The callback method is called when a message is received on a subscribed topic
        """
        #print("Received message on topic {0} payload {1}".format(topic, msg))

        # Parse the datetime string into a datetime object
        msg_string = msg.decode('utf-8')



        # Depending on the topic, set the start or end time for the access period
        if topic == self.MQTT_TOPIC_1:  # If the message was received on the 'enter' topic
            msg_datetime = datetime.strptime(msg_string, "%d/%m/%Y %H:%M:%S")
            self.access_period.start_time = msg_datetime
            self.access_period.active = True  # Start the access period
            self.just_ended = False  # Reset the flag

        elif topic == self.MQTT_TOPIC_2:  # If the message was received on the 'exit' topic
            msg_datetime = datetime.strptime(msg_string, "%d/%m/%Y %H:%M:%S")
            self.access_period.end_time = msg_datetime
            self.access_period.active = False  # End the access period
            self.just_ended = True  # Set the flag to True when an access period ends


        if topic == self.MQTT_TOPIC_3:  # If the message was received on the 'user code' topic
            self.access_period.user_code = msg_string


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
    #   name: "MQTT Sub Sim", this should be a maximum of 14 characters else it is truncated
    #   has_oled_board: set to True as you are using the OLED FeatherWing
    #   finish_button: set to "C" which designates Button C on the OLED FeatherWing as the
    #                  button that sets finished property to True
    #   start_verbose: set to True and the OLED FeatherWing will display a message as it
    #                  starts up the program
    #
    app = MainApp(name="MQTT Sub Sim", has_oled_board=True, finish_button="C", start_verbose=True)
    
    # Run the app
    try:
        app.run()
    except KeyboardInterrupt:
        # Gracefully exit the program when closing the gui or pressing ctrl + c
        pass
    finally:
        # Make sure to always call finish before exiting the program
        app.finish()

# Invoke main() program entrance
if __name__ == "__main__":
    # execute only if run as a script
    main()
